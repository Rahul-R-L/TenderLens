"""
sync_active_tenders.py

Sync ACTIVE tenders from TenderLens v1.1 Supabase/PostgreSQL
into the TenderLens v1.0 SQLite database.

SOURCE
------
Supabase/PostgreSQL

    tenders
    tender_boq_headers
    tender_boq_items

TARGET
------
SQLite

    tenders
    boq_headings
    boq_items

IMPORTANT
---------
Only ACTIVE tenders are copied.

A tender is considered active when:

    bid_submission_end > current UTC time

The SQLite database is rebuilt as a clean snapshot.

Existing tenders.db is backed up before replacement.

Required environment variables:

    SUPABASE_DB_HOST
    SUPABASE_DB_PORT
    SUPABASE_DB_NAME
    SUPABASE_DB_USER
    SUPABASE_DB_PASSWORD

Optional:

    SQLITE_DB_PATH

    Defaults to:
        tenders.db
"""

import os
import sqlite3
import shutil
import tempfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from dotenv import load_dotenv



import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()
# ============================================================
# CONFIGURATION
# ============================================================

SQLITE_DB_PATH = os.getenv(
    "SQLITE_DB_PATH",
    "tenders.db"
)

SUPABASE_CONFIG = {
    "host": os.getenv("SUPABASE_DB_HOST"),
    "port": os.getenv("SUPABASE_DB_PORT", "5432"),
    "dbname": os.getenv("SUPABASE_DB_NAME"),
    "user": os.getenv("SUPABASE_DB_USER"),
    "password": os.getenv("SUPABASE_DB_PASSWORD"),
}


# ============================================================
# SQLITE V1.0 SCHEMA
# ============================================================

CREATE_TENDERS_SQL = """
CREATE TABLE tenders (
    id INTEGER PRIMARY KEY,
    tender_id TEXT,
    title TEXT,
    organisation_name TEXT,
    organisation_chain_raw TEXT,
    location TEXT,
    tender_value REAL,
    form_of_contract TEXT,
    bid_submission_end_date TEXT,
    tender_active INTEGER DEFAULT 1,
    tender_inviting_authority TEXT,
    authority_address TEXT,
    work_description TEXT,
    tender_url TEXT,
    needs_review INTEGER DEFAULT 0,
    scraped_at TEXT,
    updated_at TEXT,
    tender_value_num REAL,
    bid_end_iso TEXT
);
"""


CREATE_BOQ_ITEMS_SQL = """
CREATE TABLE boq_items (
    id INTEGER PRIMARY KEY,
    tender_id TEXT,
    item_no TEXT,
    description TEXT,
    quantity REAL,
    unit TEXT,
    estimated_rate REAL,
    amount REAL
);
"""


CREATE_BOQ_HEADINGS_SQL = """
CREATE TABLE boq_headings (
    id INTEGER PRIMARY KEY,
    tender_id TEXT,
    heading_no TEXT,
    heading_text TEXT
);
"""


# ============================================================
# SUPABASE CONNECTION
# ============================================================

def validate_config():

    required = [
        "SUPABASE_DB_HOST",
        "SUPABASE_DB_PORT",
        "SUPABASE_DB_NAME",
        "SUPABASE_DB_USER",
        "SUPABASE_DB_PASSWORD",
    ]

    missing = [
        key
        for key in required
        if not (
            os.getenv(key)
            if key != "SUPABASE_DB_PORT"
            else os.getenv(key, "5432")
        )
    ]

    if missing:
        raise RuntimeError(
            "Missing Supabase environment variables:\n"
            + "\n".join(
                f"  {key}"
                for key in missing
            )
        )


def connect_supabase():

    validate_config()

    print("Connecting to Supabase...")

    conn = psycopg2.connect(
        host=SUPABASE_CONFIG["host"],
        port=SUPABASE_CONFIG["port"],
        dbname=SUPABASE_CONFIG["dbname"],
        user=SUPABASE_CONFIG["user"],
        password=SUPABASE_CONFIG["password"],
        sslmode="require",
    )

    print("Supabase connection successful.")

    return conn


# ============================================================
# DATE / TIME HELPERS
# ============================================================

def ensure_utc(dt):
    """
    Convert datetime to timezone-aware UTC.
    """

    if dt is None:
        return None

    if dt.tzinfo is None:
        return dt.replace(
            tzinfo=timezone.utc
        )

    return dt.astimezone(timezone.utc)


def is_active(bid_submission_end):
    """
    Return True when the tender deadline is still in the future.
    """

    if bid_submission_end is None:
        return False

    dt = ensure_utc(
        bid_submission_end
    )

    now = datetime.now(
        timezone.utc
    )

    return dt > now


def datetime_to_text(dt):
    """
    Convert PostgreSQL timestamp to SQLite-friendly text.

    Example:
        2026-08-09 12:30:00+00:00
    """

    if dt is None:
        return None

    dt = ensure_utc(dt)

    return dt.strftime(
        "%Y-%m-%d %H:%M:%S%z"
    )


def datetime_to_iso(dt):
    """
    Convert PostgreSQL timestamp to ISO-8601.
    """

    if dt is None:
        return None

    dt = ensure_utc(dt)

    return dt.isoformat()


# ============================================================
# VALUE CONVERSION
# ============================================================

def parse_tender_value(raw_value):
    """
    Convert portal_tender_value_raw into a REAL-compatible
    Python float.

    Example:

        "1,25,00,000.00"
            ->
        125000000.0

    Handles:
        commas
        whitespace
        currency symbols
        empty values
        NULL
    """

    if raw_value is None:
        return None

    value = str(raw_value).strip()

    if not value:
        return None

    # Remove commas
    value = value.replace(",", "")

    # Remove common currency symbols/text
    value = (
        value
        .replace("₹", "")
        .replace("Rs.", "")
        .replace("Rs", "")
        .strip()
    )

    # Remove whitespace
    value = value.replace(" ", "")

    try:
        number = Decimal(value)

        return float(number)

    except (InvalidOperation, ValueError):

        print(
            f"WARNING: Could not convert tender value: "
            f"{raw_value!r}"
        )

        return None


# ============================================================
# ORGANISATION NAME
# ============================================================

def get_organisation_name(
    organisation_chain_raw
):
    """
    Extract organisation_name from organisation_chain_raw.

    Example:

        "PWD|Kerala|Buildings Division|Kozhikode"

    becomes:

        "PWD"
    """

    if organisation_chain_raw is None:
        return None

    value = str(
        organisation_chain_raw
    )

    return value.split(
        "|",
        1
    )[0].strip()


# ============================================================
# FETCH ACTIVE TENDERS
# ============================================================

def fetch_active_tenders(
    pg_conn
):
    """
    Fetch only the fields needed to construct
    the v1.0 tenders table.

    We intentionally do not use SELECT *.
    """

    sql = """
        SELECT
            id,
            portal_tender_id,
            organisation_chain_raw,
            title,
            work_description,
            location,
            portal_tender_value_raw,
            bid_submission_end,
            authority_name,
            authority_address,
            scraped_at
        FROM tenders
        WHERE bid_submission_end IS NOT NULL
          AND bid_submission_end > NOW()
        ORDER BY bid_submission_end ASC
    """

    print(
        "\nFetching active tenders..."
    )

    with pg_conn.cursor(
        cursor_factory=RealDictCursor
    ) as cur:

        cur.execute(sql)

        rows = cur.fetchall()

    print(
        f"Active tenders found: {len(rows)}"
    )

    return rows


# ============================================================
# FETCH BOQ HEADINGS
# ============================================================

def fetch_boq_headings(
    pg_conn,
    supabase_tender_ids
):
    """
    Fetch BOQ headers belonging only to active tenders.
    """

    if not supabase_tender_ids:
        return []

    sql = """
        SELECT
            id,
            tender_id,
            header_no,
            header_name
        FROM tender_boq_headers
        WHERE tender_id = ANY(%s)
        ORDER BY
            tender_id,
            display_order,
            id
    """

    print(
        "Fetching BOQ headings..."
    )

    with pg_conn.cursor(
        cursor_factory=RealDictCursor
    ) as cur:

        cur.execute(
            sql,
            (list(supabase_tender_ids),)
        )

        rows = cur.fetchall()

    print(
        f"BOQ headings found: {len(rows)}"
    )

    return rows


# ============================================================
# FETCH BOQ ITEMS
# ============================================================

def fetch_boq_items(
    pg_conn,
    supabase_tender_ids
):
    """
    Fetch BOQ items belonging only to active tenders.
    """

    if not supabase_tender_ids:
        return []

    sql = """
        SELECT
            id,
            tender_id,
            item_no,
            description,
            unit,
            quantity,
            rate,
            amount
        FROM tender_boq_items
        WHERE tender_id = ANY(%s)
        ORDER BY
            tender_id,
            display_order,
            id
    """

    print(
        "Fetching BOQ items..."
    )

    with pg_conn.cursor(
        cursor_factory=RealDictCursor
    ) as cur:

        cur.execute(
            sql,
            (list(supabase_tender_ids),)
        )

        rows = cur.fetchall()

    print(
        f"BOQ items found: {len(rows)}"
    )

    return rows


# ============================================================
# CREATE SQLITE DATABASE
# ============================================================

def create_sqlite_database(
    path
):

    conn = sqlite3.connect(
        path
    )

    conn.execute(
        "PRAGMA journal_mode=WAL"
    )

    conn.execute(
        "PRAGMA synchronous=NORMAL"
    )

    conn.execute(
        CREATE_TENDERS_SQL
    )

    conn.execute(
        CREATE_BOQ_ITEMS_SQL
    )

    conn.execute(
        CREATE_BOQ_HEADINGS_SQL
    )

    return conn


# ============================================================
# INSERT TENDERS
# ============================================================

def insert_tenders(
    sqlite_conn,
    tenders
):
    """
    Convert Supabase tender records to the exact v1.0 schema.
    """

    sql = """
        INSERT INTO tenders (
            id,
            tender_id,
            title,
            organisation_name,
            organisation_chain_raw,
            location,
            tender_value,
            form_of_contract,
            bid_submission_end_date,
            tender_active,
            tender_inviting_authority,
            authority_address,
            work_description,
            tender_url,
            needs_review,
            scraped_at,
            updated_at,
            tender_value_num,
            bid_end_iso
        )
        VALUES (
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        )
    """

    data = []

    for sqlite_id, row in enumerate(
        tenders,
        start=1
    ):

        portal_tender_id = (
            row["portal_tender_id"]
        )

        organisation_chain_raw = (
            row["organisation_chain_raw"]
        )

        organisation_name = (
            get_organisation_name(
                organisation_chain_raw
            )
        )

        tender_value = (
            parse_tender_value(
                row["portal_tender_value_raw"]
            )
        )

        bid_end = (
            row["bid_submission_end"]
        )

        scraped_at = (
            datetime_to_text(
                row["scraped_at"]
            )
        )

        bid_submission_end_date = (
            datetime_to_text(
                bid_end
            )
        )

        bid_end_iso = (
            datetime_to_iso(
                bid_end
            )
        )

        data.append(
            (
                sqlite_id,

                # tender_id
                portal_tender_id,

                # title
                row["title"],

                # organisation_name
                organisation_name,

                # organisation_chain_raw
                organisation_chain_raw,

                # location
                row["location"],

                # tender_value
                tender_value,

                # form_of_contract
                None,

                # bid_submission_end_date
                bid_submission_end_date,

                # tender_active
                1,

                # tender_inviting_authority
                row["authority_name"],

                # authority_address
                row["authority_address"],

                # work_description
                row["work_description"],

                # tender_url
                None,

                # needs_review
                0,

                # scraped_at
                scraped_at,

                # updated_at = scraped_at
                scraped_at,

                # tender_value_num
                tender_value,

                # bid_end_iso
                bid_end_iso,
            )
        )

    sqlite_conn.executemany(
        sql,
        data
    )


# ============================================================
# INSERT BOQ HEADINGS
# ============================================================

def insert_boq_headings(
    sqlite_conn,
    headings,
    tender_id_map
):
    """
    Convert:

        Supabase tender_boq_headers

    into:

        SQLite boq_headings

    The Supabase tender_id is a numeric internal ID.

    SQLite needs portal_tender_id.
    """

    sql = """
        INSERT INTO boq_headings (
            id,
            tender_id,
            heading_no,
            heading_text
        )
        VALUES (?, ?, ?, ?)
    """

    data = []

    sqlite_id = 1

    skipped = 0

    for row in headings:

        supabase_tender_id = (
            row["tender_id"]
        )

        portal_tender_id = (
            tender_id_map.get(
                supabase_tender_id
            )
        )

        if portal_tender_id is None:
            skipped += 1
            continue

        data.append(
            (
                sqlite_id,
                portal_tender_id,
                row["header_no"],
                row["header_name"],
            )
        )

        sqlite_id += 1

    sqlite_conn.executemany(
        sql,
        data
    )

    if skipped:
        print(
            f"WARNING: skipped {skipped} BOQ headings "
            f"because their tender was not found."
        )


# ============================================================
# INSERT BOQ ITEMS
# ============================================================

def insert_boq_items(
    sqlite_conn,
    boq_items,
    tender_id_map
):
    """
    Convert:

        Supabase tender_boq_items

    into:

        SQLite boq_items
    """

    sql = """
        INSERT INTO boq_items (
            id,
            tender_id,
            item_no,
            description,
            quantity,
            unit,
            estimated_rate,
            amount
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    data = []

    sqlite_id = 1

    skipped = 0

    for row in boq_items:

        supabase_tender_id = (
            row["tender_id"]
        )

        portal_tender_id = (
            tender_id_map.get(
                supabase_tender_id
            )
        )

        if portal_tender_id is None:
            skipped += 1
            continue

        data.append(
            (
                sqlite_id,
                portal_tender_id,
                row["item_no"],
                row["description"],
                float(row["quantity"])
                if row["quantity"] is not None
                else None,
                row["unit"],
                float(row["rate"])
                if row["rate"] is not None
                else None,
                float(row["amount"])
                if row["amount"] is not None
                else None,
            )
        )

        sqlite_id += 1

    sqlite_conn.executemany(
        sql,
        data
    )

    if skipped:
        print(
            f"WARNING: skipped {skipped} BOQ items "
            f"because their tender was not found."
        )


# ============================================================
# INDEXES
# ============================================================

def create_indexes(
    conn
):

    print(
        "Creating SQLite indexes..."
    )

    indexes = [

        """
        CREATE INDEX idx_tenders_tender_id
        ON tenders(tender_id)
        """,

        """
        CREATE INDEX idx_tenders_bid_end
        ON tenders(bid_submission_end_date)
        """,

        """
        CREATE INDEX idx_tenders_active
        ON tenders(tender_active)
        """,

        """
        CREATE INDEX idx_boq_items_tender_id
        ON boq_items(tender_id)
        """,

        """
        CREATE INDEX idx_boq_items_description
        ON boq_items(description)
        """,

        """
        CREATE INDEX idx_boq_headings_tender_id
        ON boq_headings(tender_id)
        """,
    ]

    for sql in indexes:
        conn.execute(sql)

    conn.commit()


# ============================================================
# VALIDATION
# ============================================================

def validate_database(
    conn,
    active_tenders
):
    """
    Perform consistency checks before replacing
    the production SQLite database.
    """

    print(
        "\nValidating generated SQLite database..."
    )

    cursor = conn.cursor()

    # --------------------------------------------------------
    # Count tenders
    # --------------------------------------------------------

    cursor.execute(
        "SELECT COUNT(*) FROM tenders"
    )

    tender_count = (
        cursor.fetchone()[0]
    )

    expected_count = len(
        active_tenders
    )

    print(
        f"Tenders      : {tender_count} "
        f"(expected {expected_count})"
    )

    if tender_count != expected_count:
        raise RuntimeError(
            "Tender count validation failed."
        )

    # --------------------------------------------------------
    # Count BOQ
    # --------------------------------------------------------

    cursor.execute(
        "SELECT COUNT(*) FROM boq_items"
    )

    boq_item_count = (
        cursor.fetchone()[0]
    )

    cursor.execute(
        "SELECT COUNT(*) FROM boq_headings"
    )

    heading_count = (
        cursor.fetchone()[0]
    )

    print(
        f"BOQ items    : {boq_item_count}"
    )

    print(
        f"BOQ headings : {heading_count}"
    )

    # --------------------------------------------------------
    # Verify tender IDs
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM tenders
        WHERE tender_id IS NULL
           OR TRIM(tender_id) = ''
        """
    )

    missing_tender_ids = (
        cursor.fetchone()[0]
    )

    if missing_tender_ids:
        raise RuntimeError(
            f"{missing_tender_ids} tenders "
            "have missing tender_id."
        )

    # --------------------------------------------------------
    # Verify BOQ relationships
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM boq_items b
        LEFT JOIN tenders t
            ON b.tender_id = t.tender_id
        WHERE t.tender_id IS NULL
        """
    )

    orphan_items = (
        cursor.fetchone()[0]
    )

    if orphan_items:
        raise RuntimeError(
            f"{orphan_items} orphan BOQ items found."
        )

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM boq_headings h
        LEFT JOIN tenders t
            ON h.tender_id = t.tender_id
        WHERE t.tender_id IS NULL
        """
    )

    orphan_headings = (
        cursor.fetchone()[0]
    )

    if orphan_headings:
        raise RuntimeError(
            f"{orphan_headings} orphan BOQ headings found."
        )

    # --------------------------------------------------------
    # Verify every tender is actually active
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM tenders
        WHERE tender_active != 1
        """
    )

    inactive_count = (
        cursor.fetchone()[0]
    )

    if inactive_count:
        raise RuntimeError(
            f"{inactive_count} inactive tenders "
            "were included."
        )

    # --------------------------------------------------------
    # Verify no expired tender
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT
            tender_id,
            bid_submission_end_date
        FROM tenders
        """
    )

    rows = cursor.fetchall()

    now = datetime.now(
        timezone.utc
    )

    expired = []

    for tender_id, end_date in rows:

        try:

            dt = datetime.strptime(
                end_date,
                "%Y-%m-%d %H:%M:%S%z"
            )

            if dt <= now:
                expired.append(
                    tender_id
                )

        except Exception:
            # The format was generated by this script,
            # so this should never happen.
            raise RuntimeError(
                f"Invalid bid_submission_end_date "
                f"for tender {tender_id}: {end_date}"
            )

    if expired:

        raise RuntimeError(
            f"{len(expired)} expired tenders "
            "were included in the database."
        )

    print(
        "Validation successful."
    )


# ============================================================
# DATABASE BACKUP
# ============================================================

def backup_existing_database(
    target_path
):
    """
    Make a backup before replacing tenders.db.
    """

    if not os.path.exists(
        target_path
    ):
        print(
            "No existing tenders.db found. "
            "No backup required."
        )
        return None

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = (
        f"{target_path}.{timestamp}.backup"
    )

    shutil.copy2(
        target_path,
        backup_path
    )

    print(
        f"Backup created:\n"
        f"  {backup_path}"
    )

    return backup_path


# ============================================================
# REPLACE DATABASE
# ============================================================

def replace_database(
    temp_db,
    target_db
):

    print(
        "\nReplacing SQLite database..."
    )

    backup_existing_database(
        target_db
    )

    shutil.copy2(
        temp_db,
        target_db
    )

    print(
        f"SQLite database updated:\n"
        f"  {os.path.abspath(target_db)}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    start_time = datetime.now()

    print("=" * 70)
    print(
        "TenderLens v1.1 → v1.0 "
        "ACTIVE TENDER SYNCHRONIZATION"
    )
    print("=" * 70)

    print(
        f"\nTarget database:"
        f"\n  {os.path.abspath(SQLITE_DB_PATH)}"
    )

    pg_conn = None
    sqlite_conn = None
    temp_db = None

    try:

        # ====================================================
        # 1. CONNECT TO SUPABASE
        # ====================================================

        pg_conn = connect_supabase()

        # ====================================================
        # 2. GET ACTIVE TENDERS
        # ====================================================

        tenders = fetch_active_tenders(
            pg_conn
        )

        if not tenders:

            print(
                "\nNo active tenders found."
            )

            return

        # ====================================================
        # 3. CREATE SUPABASE ID → PORTAL ID MAP
        # ====================================================

        tender_id_map = {}

        for tender in tenders:

            tender_id_map[
                tender["id"]
            ] = tender["portal_tender_id"]

        supabase_tender_ids = set(
            tender_id_map.keys()
        )

        print(
            f"\nUnique active Supabase tender IDs: "
            f"{len(supabase_tender_ids)}"
        )

        # ====================================================
        # 4. FETCH BOQ
        # ====================================================

        boq_headings = fetch_boq_headings(
            pg_conn,
            supabase_tender_ids
        )

        boq_items = fetch_boq_items(
            pg_conn,
            supabase_tender_ids
        )

        # ====================================================
        # 5. CREATE TEMPORARY SQLITE DB
        # ====================================================

        temp_file = tempfile.NamedTemporaryFile(
            suffix=".db",
            delete=False
        )

        temp_db = temp_file.name

        temp_file.close()

        print(
            f"\nTemporary SQLite database:"
            f"\n  {temp_db}"
        )

        sqlite_conn = create_sqlite_database(
            temp_db
        )

        # ====================================================
        # 6. INSERT TENDERS
        # ====================================================

        print(
            "\nWriting tenders..."
        )

        insert_tenders(
            sqlite_conn,
            tenders
        )

        # ====================================================
        # 7. INSERT BOQ HEADINGS
        # ====================================================

        print(
            "Writing BOQ headings..."
        )

        insert_boq_headings(
            sqlite_conn,
            boq_headings,
            tender_id_map
        )

        # ====================================================
        # 8. INSERT BOQ ITEMS
        # ====================================================

        print(
            "Writing BOQ items..."
        )

        insert_boq_items(
            sqlite_conn,
            boq_items,
            tender_id_map
        )

        # ====================================================
        # 9. CREATE INDEXES
        # ====================================================

        create_indexes(
            sqlite_conn
        )

        # ====================================================
        # 10. VALIDATE
        # ====================================================

        validate_database(
            sqlite_conn,
            tenders
        )

        sqlite_conn.commit()

        sqlite_conn.close()

        sqlite_conn = None

        # ====================================================
        # 11. REPLACE PRODUCTION DATABASE
        # ====================================================

        replace_database(
            temp_db,
            SQLITE_DB_PATH
        )

        # ====================================================
        # COMPLETE
        # ====================================================

        elapsed = (
            datetime.now()
            - start_time
        )

        print(
            "\n" + "=" * 70
        )

        print(
            "SYNC COMPLETED SUCCESSFULLY"
        )

        print(
            "=" * 70
        )

        print(
            f"Tenders      : {len(tenders)}"
        )

        print(
            f"BOQ headings : {len(boq_headings)}"
        )

        print(
            f"BOQ items    : {len(boq_items)}"
        )

        print(
            f"SQLite DB    : {SQLITE_DB_PATH}"
        )

        print(
            f"Elapsed time : {elapsed}"
        )

        print(
            "\nThe v1.0 database now contains "
            "only active tenders."
        )

    except Exception as e:

        print(
            "\n" + "=" * 70
        )

        print(
            "SYNC FAILED"
        )

        print(
            "=" * 70
        )

        print(
            f"{type(e).__name__}: {e}"
        )

        raise

    finally:

        if sqlite_conn is not None:
            sqlite_conn.close()

        if pg_conn is not None:
            pg_conn.close()

        if temp_db and os.path.exists(
            temp_db
        ):

            try:
                os.remove(
                    temp_db
                )
            except OSError:
                pass


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()