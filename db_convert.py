"""
db_convert.py

TenderLens v1.1 Supabase/PostgreSQL
        ->
TenderLens v1.0 SQLite

Copies ONLY active tenders and the BOQ data belonging to those tenders.

ACTIVE CRITERIA
---------------
bid_submission_end > CURRENT_TIMESTAMP

TIMEZONE
--------
PostgreSQL session timezone:
    Asia/Kolkata

SQLite timestamps:
    IST (+0530)

V1.0 TARGET TABLES
------------------
tenders
boq_items
boq_headings

The target SQLite schema is kept compatible with the existing
TenderLens v1.0 database.

Required environment variables
-------------------------------

SUPABASE_DB_HOST
SUPABASE_DB_PORT
SUPABASE_DB_NAME
SUPABASE_DB_USER
SUPABASE_DB_PASSWORD

Optional:

SQLITE_DB_PATH

Default:
    tenders.db

Optional .env file is supported.
"""

# ============================================================
# IMPORTS
# ============================================================

import os
import sqlite3
import shutil
import sys
import tempfile

from datetime import datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

import psycopg2
from psycopg2.extras import RealDictCursor


# ============================================================
# LOAD .ENV
# ============================================================

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
    "port": os.getenv(
        "SUPABASE_DB_PORT",
        "5432"
    ),
    "dbname": os.getenv("SUPABASE_DB_NAME"),
    "user": os.getenv("SUPABASE_DB_USER"),
    "password": os.getenv("SUPABASE_DB_PASSWORD"),
}


# Explicit Indian Standard Time
IST = ZoneInfo("Asia/Kolkata")


# ============================================================
# V1.0 SQLITE SCHEMA
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
# CONFIG VALIDATION
# ============================================================

def validate_config():

    required = {
        "SUPABASE_DB_HOST": SUPABASE_CONFIG["host"],
        "SUPABASE_DB_NAME": SUPABASE_CONFIG["dbname"],
        "SUPABASE_DB_USER": SUPABASE_CONFIG["user"],
        "SUPABASE_DB_PASSWORD": SUPABASE_CONFIG["password"],
    }

    missing = [
        key
        for key, value in required.items()
        if not value
    ]

    if missing:

        raise RuntimeError(
            "Missing Supabase environment variables:\n"
            + "\n".join(
                f"  {key}"
                for key in missing
            )
        )


# ============================================================
# CONNECT TO SUPABASE
# ============================================================

def connect_supabase():

    validate_config()

    print(
        "Connecting to Supabase..."
    )

    conn = psycopg2.connect(
        host=SUPABASE_CONFIG["host"],
        port=SUPABASE_CONFIG["port"],
        dbname=SUPABASE_CONFIG["dbname"],
        user=SUPABASE_CONFIG["user"],
        password=SUPABASE_CONFIG["password"],
        sslmode="require",
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Set PostgreSQL session timezone to IST.
    # --------------------------------------------------------

    with conn.cursor() as cur:

        cur.execute(
            "SET TIME ZONE 'Asia/Kolkata';"
        )

    print(
        "Supabase connection successful."
    )

    print(
        "PostgreSQL session timezone: Asia/Kolkata"
    )

    return conn


# ============================================================
# DATETIME HELPERS
# ============================================================

def to_ist(dt):
    """
    Convert a datetime to IST.

    PostgreSQL returns timestamptz values as timezone-aware
    datetime objects.

    If a naive datetime is received, it is assumed to already
    represent IST.
    """

    if dt is None:
        return None

    if dt.tzinfo is None:

        return dt.replace(
            tzinfo=IST
        )

    return dt.astimezone(
        IST
    )


def datetime_to_sqlite_text(dt):
    """
    Convert datetime to SQLite-compatible IST text.

    Example:

        2026-08-11 22:30:00+0530
    """

    if dt is None:
        return None

    dt = to_ist(dt)

    return dt.strftime(
        "%Y-%m-%d %H:%M:%S%z"
    )


def datetime_to_iso(dt):
    """
    Convert datetime to ISO-8601 with IST offset.

    Example:

        2026-08-11T22:30:00+05:30
    """

    if dt is None:
        return None

    dt = to_ist(dt)

    return dt.isoformat()


# ============================================================
# TENDER VALUE CONVERSION
# ============================================================

def parse_tender_value(raw_value):
    """
    Convert portal_tender_value_raw to float.

    Examples:

        "1,25,00,000"
            ->
        12500000.0

        "₹ 1,25,00,000.00"
            ->
        12500000.0

    NULL/empty/invalid values become None.
    """

    if raw_value is None:
        return None

    value = str(
        raw_value
    ).strip()

    if not value:
        return None

    # Remove commas
    value = value.replace(
        ",",
        ""
    )

    # Remove common currency symbols/text
    value = value.replace(
        "₹",
        ""
    )

    value = value.replace(
        "Rs.",
        ""
    )

    value = value.replace(
        "Rs",
        ""
    )

    # Remove whitespace
    value = value.replace(
        " ",
        ""
    )

    try:

        number = Decimal(
            value
        )

        return float(
            number
        )

    except (
        InvalidOperation,
        ValueError
    ):

        print(
            "WARNING: Could not convert "
            f"tender value: {raw_value!r}"
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

        PWD|Buildings Division|Kozhikode

    becomes:

        PWD
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
    Fetch active tenders.

    IMPORTANT:
    ----------
    bid_submission_end is PostgreSQL timestamptz.

    CURRENT_TIMESTAMP is therefore compared against the
    actual absolute instant.

    The PostgreSQL session timezone has already been set to
    Asia/Kolkata, so returned timestamps are displayed in IST.
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
          AND bid_submission_end > CURRENT_TIMESTAMP
        ORDER BY bid_submission_end ASC
    """

    print(
        "\nFetching active tenders..."
    )

    with pg_conn.cursor(
        cursor_factory=RealDictCursor
    ) as cur:

        cur.execute(
            sql
        )

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
            header_name,
            display_order
        FROM tender_boq_headers
        WHERE tender_id = ANY(%s)
        ORDER BY
            tender_id,
            display_order,
            id
    """

    print(
        "\nFetching BOQ headings..."
    )

    with pg_conn.cursor(
        cursor_factory=RealDictCursor
    ) as cur:

        cur.execute(
            sql,
            (
                list(
                    supabase_tender_ids
                ),
            )
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
            amount,
            display_order
        FROM tender_boq_items
        WHERE tender_id = ANY(%s)
        ORDER BY
            tender_id,
            display_order,
            id
    """

    print(
        "\nFetching BOQ items..."
    )

    with pg_conn.cursor(
        cursor_factory=RealDictCursor
    ) as cur:

        cur.execute(
            sql,
            (
                list(
                    supabase_tender_ids
                ),
            )
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
    Insert tenders using the exact v1.0 schema.

    SQLite IDs are generated locally.
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
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """

    data = []

    for sqlite_id, row in enumerate(
        tenders,
        start=1
    ):

        # ----------------------------------------------------
        # Organisation
        # ----------------------------------------------------

        organisation_chain_raw = (
            row["organisation_chain_raw"]
        )

        organisation_name = (
            get_organisation_name(
                organisation_chain_raw
            )
        )

        # ----------------------------------------------------
        # Tender value
        # ----------------------------------------------------

        tender_value = (
            parse_tender_value(
                row[
                    "portal_tender_value_raw"
                ]
            )
        )

        # ----------------------------------------------------
        # Dates
        # ----------------------------------------------------

        bid_end = (
            row[
                "bid_submission_end"
            ]
        )

        scraped_at = (
            datetime_to_sqlite_text(
                row[
                    "scraped_at"
                ]
            )
        )

        bid_submission_end_date = (
            datetime_to_sqlite_text(
                bid_end
            )
        )

        bid_end_iso = (
            datetime_to_iso(
                bid_end
            )
        )

        # ----------------------------------------------------
        # Build row
        # ----------------------------------------------------

        data.append(
            (
                sqlite_id,

                # v1.0 tender_id
                row[
                    "portal_tender_id"
                ],

                # title
                row[
                    "title"
                ],

                # organisation_name
                organisation_name,

                # organisation_chain_raw
                organisation_chain_raw,

                # location
                row[
                    "location"
                ],

                # tender_value
                tender_value,

                # form_of_contract
                None,

                # bid_submission_end_date
                bid_submission_end_date,

                # tender_active
                1,

                # tender_inviting_authority
                row[
                    "authority_name"
                ],

                # authority_address
                row[
                    "authority_address"
                ],

                # work_description
                row[
                    "work_description"
                ],

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

    print(
        f"Inserted {len(data)} tenders."
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
    Supabase:

        tender_boq_headers.tender_id
            ->
        Supabase tenders.id

    SQLite:

        boq_headings.tender_id
            ->
        v1.0 tender_id / portal_tender_id
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

    skipped = 0

    sqlite_id = 1

    for row in headings:

        supabase_tender_id = (
            row[
                "tender_id"
            ]
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

                row[
                    "header_no"
                ],

                row[
                    "header_name"
                ],
            )
        )

        sqlite_id += 1

    sqlite_conn.executemany(
        sql,
        data
    )

    print(
        f"Inserted {len(data)} BOQ headings."
    )

    if skipped:

        print(
            "WARNING: "
            f"Skipped {skipped} headings."
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
    Convert Supabase BOQ items to the v1.0 schema.
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

    skipped = 0

    sqlite_id = 1

    for row in boq_items:

        supabase_tender_id = (
            row[
                "tender_id"
            ]
        )

        portal_tender_id = (
            tender_id_map.get(
                supabase_tender_id
            )
        )

        if portal_tender_id is None:

            skipped += 1

            continue

        # ----------------------------------------------------
        # Numeric conversions
        # ----------------------------------------------------

        quantity = (
            float(
                row["quantity"]
            )
            if row["quantity"] is not None
            else None
        )

        rate = (
            float(
                row["rate"]
            )
            if row["rate"] is not None
            else None
        )

        amount = (
            float(
                row["amount"]
            )
            if row["amount"] is not None
            else None
        )

        data.append(
            (
                sqlite_id,

                portal_tender_id,

                row[
                    "item_no"
                ],

                row[
                    "description"
                ],

                quantity,

                row[
                    "unit"
                ],

                rate,

                amount,
            )
        )

        sqlite_id += 1

    sqlite_conn.executemany(
        sql,
        data
    )

    print(
        f"Inserted {len(data)} BOQ items."
    )

    if skipped:

        print(
            "WARNING: "
            f"Skipped {skipped} BOQ items."
        )


# ============================================================
# CREATE INDEXES
# ============================================================

def create_indexes(
    conn
):

    print(
        "\nCreating indexes..."
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

        conn.execute(
            sql
        )

    conn.commit()

    print(
        "Indexes created."
    )


# ============================================================
# VALIDATE SQLITE DATABASE
# ============================================================

def validate_database(
    conn,
    active_tenders
):

    print(
        "\n" + "=" * 70
    )

    print(
        "VALIDATING SQLITE DATABASE"
    )

    print(
        "=" * 70
    )

    cursor = conn.cursor()

    # ========================================================
    # SQLite integrity
    # ========================================================

    cursor.execute(
        "PRAGMA integrity_check"
    )

    integrity = (
        cursor.fetchone()[0]
    )

    print(
        f"SQLite integrity : {integrity}"
    )

    if integrity != "ok":

        raise RuntimeError(
            "SQLite integrity check failed."
        )

    # ========================================================
    # Tender count
    # ========================================================

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
        f"Tenders          : {tender_count}"
        f" / {expected_count}"
    )

    if tender_count != expected_count:

        raise RuntimeError(
            "Tender count validation failed."
        )

    # ========================================================
    # BOQ counts
    # ========================================================

    cursor.execute(
        "SELECT COUNT(*) FROM boq_items"
    )

    boq_item_count = (
        cursor.fetchone()[0]
    )

    cursor.execute(
        "SELECT COUNT(*) FROM boq_headings"
    )

    boq_heading_count = (
        cursor.fetchone()[0]
    )

    print(
        f"BOQ items        : {boq_item_count}"
    )

    print(
        f"BOQ headings     : {boq_heading_count}"
    )

    # ========================================================
    # Missing tender IDs
    # ========================================================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM tenders
        WHERE tender_id IS NULL
           OR TRIM(tender_id) = ''
        """
    )

    missing_ids = (
        cursor.fetchone()[0]
    )

    if missing_ids:

        raise RuntimeError(
            f"{missing_ids} tenders "
            "have missing tender_id."
        )

    # ========================================================
    # Duplicate tender IDs
    # ========================================================

    cursor.execute(
        """
        SELECT tender_id, COUNT(*)
        FROM tenders
        GROUP BY tender_id
        HAVING COUNT(*) > 1
        """
    )

    duplicates = cursor.fetchall()

    if duplicates:

        print(
            "\nDuplicate tender IDs:"
        )

        for tender_id, count in duplicates:

            print(
                f"  {tender_id}: {count}"
            )

        raise RuntimeError(
            "Duplicate tender_id values found."
        )

    # ========================================================
    # Orphan BOQ items
    # ========================================================

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

    print(
        f"Orphan BOQ items : {orphan_items}"
    )

    if orphan_items:

        raise RuntimeError(
            "Orphan BOQ items found."
        )

    # ========================================================
    # Orphan BOQ headings
    # ========================================================

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

    print(
        f"Orphan headings  : {orphan_headings}"
    )

    if orphan_headings:

        raise RuntimeError(
            "Orphan BOQ headings found."
        )

    # ========================================================
    # Verify all tenders are marked active
    # ========================================================

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

    print(
        f"Inactive tenders : {inactive_count}"
    )

    if inactive_count:

        raise RuntimeError(
            "Inactive tenders found in "
            "the active-tender database."
        )

    # ========================================================
    # Verify deadline values
    # ========================================================

    cursor.execute(
        """
        SELECT
            tender_id,
            bid_submission_end_date
        FROM tenders
        """
    )

    rows = cursor.fetchall()

    now_ist = datetime.now(
        IST
    )

    expired = []

    for tender_id, deadline in rows:

        if not deadline:

            expired.append(
                tender_id
            )

            continue

        try:

            deadline_dt = datetime.strptime(
                deadline,
                "%Y-%m-%d %H:%M:%S%z"
            )

        except ValueError:

            raise RuntimeError(
                "Invalid deadline format for "
                f"{tender_id}: {deadline}"
            )

        if deadline_dt <= now_ist:

            expired.append(
                tender_id
            )

    print(
        f"Expired tenders  : {len(expired)}"
    )

    if expired:

        print(
            "\nExpired tender IDs:"
        )

        for tender_id in expired[:20]:

            print(
                f"  {tender_id}"
            )

        if len(expired) > 20:

            print(
                f"  ... and "
                f"{len(expired) - 20} more"
            )

        raise RuntimeError(
            "Expired tenders were found "
            "in the generated database."
        )

    # ========================================================
    # Check NULL form_of_contract
    # ========================================================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM tenders
        WHERE form_of_contract IS NOT NULL
        """
    )

    non_null_contract_type = (
        cursor.fetchone()[0]
    )

    if non_null_contract_type:

        raise RuntimeError(
            "form_of_contract should currently "
            "be NULL for all tenders."
        )

    # ========================================================
    # Check updated_at = scraped_at
    # ========================================================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM tenders
        WHERE updated_at != scraped_at
        """
    )

    timestamp_mismatch = (
        cursor.fetchone()[0]
    )

    if timestamp_mismatch:

        raise RuntimeError(
            "updated_at != scraped_at "
            "for some tenders."
        )

    print(
        "\nValidation successful."
    )


# ============================================================
# BACKUP EXISTING DATABASE
# ============================================================

def backup_existing_database(
    target_path
):

    if not os.path.exists(
        target_path
    ):

        print(
            "\nNo existing tenders.db found."
        )

        return None

    timestamp = datetime.now(
        IST
    ).strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = (
        f"{target_path}."
        f"{timestamp}.backup"
    )

    shutil.copy2(
        target_path,
        backup_path
    )

    print(
        "\nExisting database backed up:"
    )

    print(
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
        "\nReplacing tenders.db..."
    )

    backup_existing_database(
        target_db
    )

    shutil.copy2(
        temp_db,
        target_db
    )

    print(
        "\nDatabase replacement successful:"
    )

    print(
        f"  {os.path.abspath(target_db)}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    start_time = datetime.now(
        IST
    )

    print(
        "=" * 70
    )

    print(
        "TenderLens v1.1 → v1.0 "
        "ACTIVE TENDER SYNCHRONIZATION"
    )

    print(
        "=" * 70
    )

    print(
        f"\nCurrent IST:"
    )

    print(
        start_time.strftime(
            "%Y-%m-%d %H:%M:%S %Z"
        )
    )

    print(
        "\nTarget database:"
    )

    print(
        f"  {os.path.abspath(SQLITE_DB_PATH)}"
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
        # 2. FETCH ACTIVE TENDERS
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
        # 3. BUILD SUPABASE ID → PORTAL ID MAP
        # ====================================================

        tender_id_map = {}

        for tender in tenders:

            supabase_id = (
                tender["id"]
            )

            portal_tender_id = (
                tender[
                    "portal_tender_id"
                ]
            )

            if not portal_tender_id:

                raise RuntimeError(
                    f"Supabase tender ID "
                    f"{supabase_id} has no "
                    "portal_tender_id."
                )

            tender_id_map[
                supabase_id
            ] = portal_tender_id

        supabase_tender_ids = set(
            tender_id_map.keys()
        )

        print(
            "\nUnique active Supabase tender IDs:"
            f" {len(supabase_tender_ids)}"
        )

        # ====================================================
        # 4. FETCH BOQ HEADINGS
        # ====================================================

        boq_headings = fetch_boq_headings(
            pg_conn,
            supabase_tender_ids
        )

        # ====================================================
        # 5. FETCH BOQ ITEMS
        # ====================================================

        boq_items = fetch_boq_items(
            pg_conn,
            supabase_tender_ids
        )

        # ====================================================
        # 6. CREATE TEMP SQLITE DATABASE
        # ====================================================

        temp_file = tempfile.NamedTemporaryFile(
            suffix=".db",
            delete=False
        )

        temp_db = temp_file.name

        temp_file.close()

        print(
            "\nCreating temporary SQLite database:"
        )

        print(
            f"  {temp_db}"
        )

        sqlite_conn = create_sqlite_database(
            temp_db
        )

        # ====================================================
        # 7. INSERT TENDERS
        # ====================================================

        insert_tenders(
            sqlite_conn,
            tenders
        )

        # ====================================================
        # 8. INSERT BOQ HEADINGS
        # ====================================================

        insert_boq_headings(
            sqlite_conn,
            boq_headings,
            tender_id_map
        )

        # ====================================================
        # 9. INSERT BOQ ITEMS
        # ====================================================

        insert_boq_items(
            sqlite_conn,
            boq_items,
            tender_id_map
        )

        # ====================================================
        # 10. CREATE INDEXES
        # ====================================================

        create_indexes(
            sqlite_conn
        )

        # ====================================================
        # 11. VALIDATE
        # ====================================================

        validate_database(
            sqlite_conn,
            tenders
        )

        # ====================================================
        # 12. COMMIT
        # ====================================================

        sqlite_conn.commit()

        sqlite_conn.close()

        sqlite_conn = None

        # ====================================================
        # 13. REPLACE PRODUCTION DATABASE
        # ====================================================

        replace_database(
            temp_db,
            SQLITE_DB_PATH
        )

        # ====================================================
        # DONE
        # ====================================================

        elapsed = (
            datetime.now(IST)
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
            f"Active tenders : {len(tenders)}"
        )

        print(
            f"BOQ headings   : {len(boq_headings)}"
        )

        print(
            f"BOQ items      : {len(boq_items)}"
        )

        print(
            f"Database       : "
            f"{os.path.abspath(SQLITE_DB_PATH)}"
        )

        print(
            f"Elapsed        : {elapsed}"
        )

        print(
            "\nAll timestamps in the SQLite database "
            "are stored in IST."
        )

        # --------------------------------------------------------
        # 14. RUN TENDER ALERT AFTER SUCCESSFUL DATABASE SYNC
        # --------------------------------------------------------

        import subprocess

        alert_script = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "tender_alert.py"
        )

        if not os.path.exists(alert_script):
            raise FileNotFoundError(
                f"Tender alert script not found: {alert_script}"
            )

        print("\n" + "=" * 70)
        print("RUNNING TENDER ALERT")
        print("=" * 70)

        alert_result = subprocess.run(
            [sys.executable, alert_script],
            check=False
        )

        if alert_result.returncode != 0:
            raise RuntimeError(
                "Tender alert process failed with "
                f"exit code {alert_result.returncode}."
            )

        print("\nTender alert completed successfully.")

        # --------------------------------------------------------
        # 15. COMMIT AND PUSH UPDATED DATABASE TO GIT
        # --------------------------------------------------------

        print("\n" + "=" * 70)
        print("UPDATING GIT REPOSITORY")
        print("=" * 70)

        repo_dir = os.path.dirname(
            os.path.abspath(__file__)
        )

        git_commands = [
            ["git", "add", "."],
            ["git", "commit", "-m", "db_updation"],
            ["git", "push"],
        ]

        for command in git_commands:

            print(
                "\nRunning: "
                + " ".join(command)
            )

            result = subprocess.run(
                command,
                cwd=repo_dir,
                check=False,
                text=True
            )

            if result.returncode != 0:

                raise RuntimeError(
                    "Git command failed: "
                    + " ".join(command)
                    + f" (exit code {result.returncode})"
                )

        print("\nGit update completed successfully.")

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