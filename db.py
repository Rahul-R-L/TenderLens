import sqlite3
import pandas as pd
from datetime import (datetime, timedelta)
import secrets

DB_NAME = (
    "tenders.db"
)


# =====================================================
# CONNECTION
# =====================================================

def get_connection():

    conn = sqlite3.connect(
        DB_NAME
    )

    conn.row_factory = (
        sqlite3.Row
    )

    return conn


# =====================================================
# INIT DATABASE
# =====================================================

def init_db():

    conn = (
        get_connection()
    )

    cursor = (
        conn.cursor()
    )

    # =================================================
    # TENDERS
    # =================================================

    cursor.execute(
    
        """
        CREATE TABLE
        IF NOT EXISTS
        tenders (

            id INTEGER
            PRIMARY KEY
            AUTOINCREMENT,

            tender_id TEXT
            UNIQUE,

            title TEXT,

            organisation_name TEXT,

            organisation_chain_raw TEXT,

            location TEXT,

            tender_value TEXT,
            
            tender_value_num REAL,

            form_of_contract TEXT,

            bid_submission_end_date TEXT,
            
            bid_end_iso TEXT,

            tender_active INTEGER
            DEFAULT 1,

            tender_inviting_authority TEXT,

            authority_address TEXT,

            work_description TEXT,

            tender_url TEXT,

            needs_review INTEGER
            DEFAULT 0,

            scraped_at TEXT,

            updated_at TEXT
        )
        """
    )

    # =================================================
    # BOQ ITEMS
    # =================================================

    cursor.execute(
        """
        CREATE TABLE
        IF NOT EXISTS
        boq_items (

            id INTEGER
            PRIMARY KEY
            AUTOINCREMENT,

            tender_id TEXT,

            item_no TEXT,

            description TEXT,

            quantity REAL,

            unit TEXT,

            estimated_rate REAL,

            amount REAL,

            FOREIGN KEY (
                tender_id
            )
            REFERENCES tenders(
                tender_id
            )
        )
        """
    )

    # =================================================
    # BOQ HEADINGS
    # =================================================

    cursor.execute(
        """
        CREATE TABLE
        IF NOT EXISTS
        boq_headings (

            id INTEGER
            PRIMARY KEY
            AUTOINCREMENT,

            tender_id TEXT,

            heading_no TEXT,

            heading_text TEXT,

            FOREIGN KEY (
                tender_id
            )
            REFERENCES tenders(
                tender_id
            )
        )
        """
    )

    # =================================================
    # USERS
    # =================================================

    cursor.execute(
        """
        CREATE TABLE
        IF NOT EXISTS
        users (

            id INTEGER
            PRIMARY KEY
            AUTOINCREMENT,

            name TEXT
            NOT NULL,

            email TEXT
            UNIQUE
            NOT NULL,

            mobile TEXT,
            
            company_name TEXT,

            password_hash TEXT
            NOT NULL,

            is_verified INTEGER
            DEFAULT 0,

            is_active INTEGER
            DEFAULT 1,

            email_verified_at TEXT,

            verification_token TEXT,

            role TEXT
            DEFAULT 'user',
            
            status TEXT 
            DEFAULT 'active',

            plan_type TEXT
            DEFAULT 'early_adopter',

            referral_source TEXT,

            created_at TEXT,

            last_login TEXT
        )
        """
    )

    # =================================================
    # FEEDBACK
    # =================================================

    cursor.execute(
        """
        CREATE TABLE
        IF NOT EXISTS
        feedback (

            id INTEGER
            PRIMARY KEY
            AUTOINCREMENT,

            user_id INTEGER,

            subject TEXT,

            message TEXT,

            status TEXT
            DEFAULT 'Open',

            created_at TEXT,

            FOREIGN KEY (
                user_id
            )
            REFERENCES users(
                id
            )
        )
        """
    )

    # =================================================
    # SECURITY ALERTS
    # =================================================

    cursor.execute(
        """
        CREATE TABLE
        IF NOT EXISTS
        security_alerts (

            id INTEGER
            PRIMARY KEY
            AUTOINCREMENT,

            user_id INTEGER,

            alert_type TEXT,

            message TEXT,

            is_read INTEGER
            DEFAULT 0,

            created_at TEXT
        )
        """
    )
    # =================================================
    # PASSWORD RESET
    # =================================================

    cursor.execute(
        """
        CREATE TABLE
        IF NOT EXISTS
        password_resets (

            id INTEGER
            PRIMARY KEY
            AUTOINCREMENT,

            email TEXT
            NOT NULL,

            reset_code TEXT
            NOT NULL,

            created_at TEXT,

            used INTEGER
            DEFAULT 0
        )
        """
    )

    # =================================================
    # SECURITY EVENTS
    # =================================================

    cursor.execute(
        """
        CREATE TABLE
        IF NOT EXISTS
        security_events (

            id INTEGER
            PRIMARY KEY
            AUTOINCREMENT,

            email TEXT,

            event_type TEXT,

            created_at TEXT
        )
        """
    )

    # =================================================
    # USER ACTIVITY
    # =================================================

    cursor.execute(
        """
        CREATE TABLE
        IF NOT EXISTS
        user_activity (

            id INTEGER
            PRIMARY KEY
            AUTOINCREMENT,

            user_id INTEGER,

            action TEXT,

            value TEXT,

            created_at TEXT,

            FOREIGN KEY (
                user_id
            )
            REFERENCES users(
                id
            )
        )
        """
    )

    # =================================================
    # SCRAPER ERRORS
    # =================================================

    cursor.execute(
        """
        CREATE TABLE
        IF NOT EXISTS
        scraper_errors (

            id INTEGER
            PRIMARY KEY
            AUTOINCREMENT,

            tender_id TEXT,

            organisation_name TEXT,

            error_type TEXT,

            error_message TEXT,

            stage TEXT,

            status TEXT
            DEFAULT 'Open',

            created_at TEXT,

            resolved_at TEXT
        )
        """
    )

    # =================================================
    # SCRAPER RUNS
    # =================================================

    cursor.execute(
        """
        CREATE TABLE
        IF NOT EXISTS
        scraper_runs (

            id INTEGER
            PRIMARY KEY
            AUTOINCREMENT,

            started_at TEXT,

            completed_at TEXT,

            status TEXT,

            tenders_found INTEGER,

            tenders_added INTEGER,

            boq_downloaded INTEGER,

            errors_count INTEGER
        )
        """
    )

    # =================================================
    # INDEXES
    # =================================================

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_tender_id
        ON tenders(
            tender_id
        )
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_org_name
        ON tenders(
            organisation_name
        )
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_active
        ON tenders(
            tender_active
        )
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_boq_tender
        ON boq_items(
            tender_id
        )
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_heading_tender
        ON boq_headings(
            tender_id
        )
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_user_email
        ON users(
            email
        )
        """
    )

    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
        idx_boq_unique
        ON boq_items(
            tender_id,
            item_no
        )
        """
    )

    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
        idx_heading_unique
        ON boq_headings(
            tender_id,
            heading_no
        )
        """
    )
    

    
    cursor.execute(
    	"""
    	CREATE INDEX IF NOT EXISTS
    	idx_org_chain
    	ON tenders(
        	organisation_chain_raw
    	)	
    	"""
    )
    cursor.execute(
    """
    CREATE INDEX IF NOT EXISTS
    	idx_location
    	ON tenders(
        	location
    	)
    	"""
    )

    cursor.execute(
    """
    CREATE INDEX IF NOT EXISTS
    	idx_tender_value_num
    	ON tenders(
        	tender_value_num
    	)
    	"""
    )
    
    cursor.execute(
    """
    CREATE INDEX IF NOT EXISTS
    	idx_bid_end_iso
    	ON tenders(
        	bid_end_iso
    	)
    	"""
    )    



    conn.commit()

    conn.close()

    print(
        "Database initialized."
    )

# =====================================================
# INSERT BOQ ITEM
# =====================================================

def insert_boq_item(

    tender_id,

    item_no,

    description,

    quantity,

    unit,

    estimated_rate,

    amount
):

    conn = (
        get_connection()
    )

    cursor = (
        conn.cursor()
    )

    try:

        cursor.execute(
            """
            INSERT INTO
            boq_items (

                tender_id,

                item_no,

                description,

                quantity,

                unit,

                estimated_rate,

                amount
            )

            VALUES (

                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?
            )
            """,

            (

                tender_id,

                item_no,

                description,

                quantity,

                unit,

                estimated_rate,

                amount
            )
        )

        conn.commit()

        return True

    except sqlite3.IntegrityError:

        return False

    finally:

        conn.close()


# =====================================================
# INSERT BOQ HEADING
# =====================================================

def insert_boq_heading(

    tender_id,

    heading_no,

    heading_text
):

    conn = (
        get_connection()
    )

    cursor = (
        conn.cursor()
    )

    try:

        cursor.execute(
            """
            INSERT INTO
            boq_headings (

                tender_id,

                heading_no,

                heading_text
            )

            VALUES (

                ?,
                ?,
                ?
            )
            """,

            (

                tender_id,

                heading_no,

                heading_text
            )
        )

        conn.commit()

        return True

    except sqlite3.IntegrityError:

        return False

    finally:

        conn.close()



# =====================================================
# GET BOQ HEADINGS
# =====================================================

def get_boq_headings(

    tender_id

):

    conn = (
        get_connection()
    )

    cursor = (
        conn.cursor()
    )

    cursor.execute(
        """
        SELECT

            heading_no,

            heading_text

        FROM
            boq_headings

        WHERE
            tender_id = ?

        ORDER BY
            heading_no
        """,

        (
            tender_id,
        )
    )

    rows = (
        cursor.fetchall()
    )

    conn.close()

    return rows


# =====================================================
# GET BOQ HEADINGS DF
# =====================================================

def get_boq_headings_df(

    tender_id

):

    conn = (
        get_connection()
    )

    query = """
        SELECT

            heading_no,

            heading_text

        FROM
            boq_headings

        WHERE
            tender_id = ?

        ORDER BY
            heading_no
    """

    df = pd.read_sql_query(

        query,

        conn,

        params=[
            tender_id
        ]
    )

    conn.close()

    return df




#----------------------------PART 2-----------------------------------------------------------------------------

# =====================================================
# CHECK TENDER EXISTS
# =====================================================

def tender_exists(

    tender_id

):

    conn = (
        get_connection()
    )

    cursor = (
        conn.cursor()
    )

    cursor.execute(

        """
        SELECT
            tender_id

        FROM
            tenders

        WHERE
            tender_id = ?
        """,

        (
            tender_id,
        )
    )

    result = (
        cursor.fetchone()
    )

    conn.close()

    return (
        result
        is not None
    )


# =====================================================
# INSERT TENDER
# =====================================================

def insert_tender(

    tender

):

    tender_id = (
        tender.get(
            "tender_id"
        )
    )

    if (

        tender_exists(
            tender_id
        )

    ):

        return False

    conn = (
        get_connection()
    )

    cursor = (
        conn.cursor()
    )

    cursor.execute(

        """
        INSERT INTO
        tenders (

            tender_id,

            title,

            organisation_name,

            organisation_chain_raw,

            location,

            tender_value,
            
            tender_value_num,

            form_of_contract,

            bid_submission_end_date,
            
            bid_end_iso,

            tender_active,

            tender_inviting_authority,

            authority_address,

            work_description,

            tender_url,

            needs_review,

            scraped_at,

            updated_at
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

            datetime('now'),

            datetime('now')
        )
        """,

        (

            tender.get(
                "tender_id"
            ),

            tender.get(
                "title"
            ),

            tender.get(
                "organisation_name"
            ),

            tender.get(
                "organisation_chain_raw"
            ),

            tender.get(
                "location"
            ),

            tender.get(
                "tender_value"
            ),
            
            tender.get(
    		"tender_value_num"
	    ),

            tender.get(
                "form_of_contract"
            ),

            tender.get(
                "bid_submission_end_date"
            ),
            
            tender.get(
                "bid_end_iso"
            ),

            tender.get(
                "tender_active",
                1
            ),

            tender.get(
                "tender_inviting_authority"
            ),

            tender.get(
                "authority_address"
            ),

            tender.get(
                "work_description"
            ),

            tender.get(
                "tender_url"
            ),

            tender.get(
                "needs_review",
                0
            )
        )
    )

    conn.commit()

    conn.close()

    return True


# =====================================================
# GET OPEN ERRORS
# =====================================================

def get_open_errors():

    conn = get_connection()

    df = pd.read_sql_query(

        """
        SELECT *
        FROM scraper_errors
        WHERE status = 'Open'
        ORDER BY id DESC
        """,

        conn
    )

    conn.close()

    return df

# =====================================================
# EMAIL CHECKING
# =====================================================
def email_exists(email):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT 1
        FROM users
        WHERE email = ?
        """,
        (email,)
    )

    result = cursor.fetchone()

    conn.close()

    return result is not None
    
    
def create_user(
    name,
    email,
    mobile,
    company_name,
    password_hash,
    verification_token,
    referral_source=None
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO users (

            name,
            email,
            mobile,
            company_name,

            password_hash,

            verification_token,

            referral_source,

            created_at

        )

        VALUES (

            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,

            datetime('now')
        )
        """,

        (
            name,
            email,
            mobile,
            company_name,
            password_hash,
            verification_token,
            referral_source
        )
    )

    conn.commit()
    conn.close()
    
    
def get_user_by_email(
    email
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE email = ?
        """,

        (
            email,
        )
    )

    row = cursor.fetchone()

    conn.close()

    return row
    
  
def get_user_by_token(token):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE verification_token = ?
        """,
        (token,)
    )

    user = cursor.fetchone()

    conn.close()

    return user
    
def verify_user(token):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET
            is_verified = 1,
            email_verified_at = datetime('now'),
            verification_token = NULL
        WHERE verification_token = ?
        """,
        (token,)
    )

    conn.commit()

    success = (
        cursor.rowcount > 0
    )

    conn.close()

    return success
    

def update_last_login(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET last_login = datetime('now')
        WHERE id = ?
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()
    
# =====================================================
# DASH BOARD
# =====================================================
    
    
    
def get_dashboard_stats():

    conn = get_connection()

    cursor = conn.cursor()

    stats = {}

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM tenders
        WHERE tender_active = 1
        """
    )

    stats["active_tenders"] = (
        cursor.fetchone()[0]
    )

    cursor.execute(
        """
        SELECT
            organisation_name,
            COUNT(*)
        FROM tenders
        WHERE tender_active = 1
        GROUP BY organisation_name
        ORDER BY COUNT(*) DESC
        """
    )

    stats["departments"] = (
        cursor.fetchall()
    )

    conn.close()

    return stats    
    


# =====================================================
# ORGANISATION HIERARCHY
# =====================================================

def get_hierarchy_children(
    parent_path=""
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT DISTINCT
            organisation_chain_raw
        FROM tenders
        WHERE

            organisation_chain_raw IS NOT NULL

            AND tender_active = 1

            AND bid_end_iso >= datetime('now')

        """
    )

    rows = cursor.fetchall()

    conn.close()

    children = set()

    for row in rows:

        chain = row[0]

        parts = [
            p.strip()
            for p in chain.split("||")
            if p.strip()
        ]

        if not parts:
            continue

        # Root level
        if parent_path == "":

            children.add(
                parts[0]
            )

            continue

        parent_parts = [
            p.strip()
            for p in parent_path.split("||")
            if p.strip()
        ]

        if len(parts) <= len(parent_parts):
            continue

        if (
            parts[
                : len(parent_parts)
            ]
            ==
            parent_parts
        ):

            children.add(
                parts[
                    len(parent_parts)
                ]
            )

    return sorted(
        list(children)
    )

# =====================================================
# BUILD HIERARCHY PATH
# =====================================================

def build_hierarchy_path(
    selections
):

    parts = []

    for item in selections:

        if item:

            parts.append(
                item.strip()
            )

    return "||".join(
        parts
    )
# =====================================================
# GET BOQ HEADING TEXT
# =====================================================

def get_boq_heading_texts(
    tender_id
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT heading_text
        FROM boq_headings
        WHERE tender_id = ?
        ORDER BY heading_no
        """,
        (tender_id,)
    )

    rows = cursor.fetchall()

    conn.close()

    return [
        r[0]
        for r in rows
    ]
# =====================================================
# SEARCH TENDERS V2
# =====================================================

def search_tenders_v2(

    keyword="",

    organisation_paths=None,

    location="",

    min_value=None,

    max_value=None,

    closing_from=None,

    closing_to=None

):

    conn = get_connection()

    query = """
    SELECT

        id,

        tender_id,

        title,
        
        work_description,

        organisation_name,
        
        organisation_chain_raw,

        location,

        tender_value,

        bid_submission_end_date,

        form_of_contract,
        
        tender_inviting_authority

    FROM tenders

    WHERE tender_active = 1
    AND bid_end_iso >= datetime('now')
    """

    params = []

    # -----------------------------------
    # Keyword
    # -----------------------------------

    if keyword:

        query += """
        AND (

            title LIKE ?

            OR work_description LIKE ?

            OR tender_id LIKE ?

        )
        """

        params.extend(
            [
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%"
            ]
        )

# -----------------------------------
# Organisation hierarchy
# -----------------------------------

    if organisation_paths:

        query += " AND ("

        conditions = []

        for path in organisation_paths:

            conditions.append(
                "organisation_chain_raw LIKE ?"
            )

            params.append(
                path + "%"
            )

        query += " OR ".join(
            conditions
        )

        query += ")"

    # -----------------------------------
    # Location
    # -----------------------------------

    if location:

        query += """
        AND location
        LIKE ?
        """

        params.append(
            f"%{location}%"
        )

    # -----------------------------------
    # Min Value
    # -----------------------------------

    if (
        min_value is not None
        and min_value > 0
    ):

        query += """
        AND tender_value_num >= ?
        """

        params.append(
            min_value
        )

    # -----------------------------------
    # Max Value
    # -----------------------------------

    if (
        max_value is not None
        and max_value > 0
    ):

        query += """
        AND tender_value_num <= ?
        """

        params.append(
            max_value
        )

    # -----------------------------------
    # Closing Date From
    # -----------------------------------

    if closing_from:

        query += """
        AND bid_end_iso >= ?
        """

        params.append(
            str(closing_from)
        )

    # -----------------------------------
    # Closing Date To
    # -----------------------------------

    if closing_to:

        query += """
        AND bid_end_iso <= ?
        """

        params.append(
            str(closing_to)
            + " 23:59:59"
        )

    query += """
    ORDER BY
        bid_end_iso ASC
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=params
    )

    conn.close()

    return df

def has_hierarchy_children(
    parent_path
):

    children = get_hierarchy_children(
        parent_path
    )

    return len(children) > 0

# -----------------------------------
# GET TENDER DETAILS
# -----------------------------------
def get_tender_details(tender_id):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            *
        FROM tenders
        WHERE tender_id = ?
        """,
        (tender_id,)
    )

    row = cursor.fetchone()

    conn.close()

    return dict(row) if row else None

# -----------------------------------
# GET BOQ ITEMS
# -----------------------------------    
def get_boq_items(tender_id):

    conn = get_connection()

    query = """
    SELECT
        item_no,
        description,
        quantity,
        unit,
        estimated_rate,
        amount
    FROM boq_items
    WHERE tender_id = ?
    ORDER BY CAST(item_no AS INTEGER)
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(tender_id,)
    )

    conn.close()

    return df

# =====================================================
# GET BOQ 
# =====================================================
    
def get_boq_df(tender_id):

    conn = get_connection()

    query = """
    SELECT

        item_no,
        description,
        quantity,
        unit,
        estimated_rate,
        amount

    FROM boq_items

    WHERE tender_id = ?

    ORDER BY item_no
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(tender_id,)
    )

    conn.close()

    return df


# =====================================================
# GET BOQ HEADING BULK
# =====================================================
    
def get_boq_headings_bulk(
    tender_ids
):

    if not tender_ids:
        return {}

    conn = get_connection()

    placeholders = ",".join(
        ["?"] * len(tender_ids)
    )

    query = f"""
    SELECT
        tender_id,
        heading_text
    FROM boq_headings
    WHERE tender_id IN (
        {placeholders}
    )
    ORDER BY heading_no
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=tender_ids
    )

    conn.close()

    result = {}

    for tender_id, group in df.groupby(
        "tender_id"
    ):

        result[tender_id] = list(
            group["heading_text"]
        )

    return result

# =====================================================
# DASHBOARD
# =====================================================
def get_active_tender_count():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM tenders
        WHERE tender_active = 1
        AND bid_end_iso >= datetime('now')
        """
    )

    count = cursor.fetchone()[0]

    conn.close()

    return count    

def get_closing_this_week_count():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM tenders

        WHERE

            tender_active = 1

            AND bid_end_iso IS NOT NULL

            AND date(bid_end_iso)
                BETWEEN date('now')
                AND date('now', '+7 days')
        """
    )

    count = cursor.fetchone()[0]

    conn.close()

    return count
    
def get_high_value_tender_count():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM tenders

        WHERE

            tender_active = 1

            AND tender_value_num >= 10000000

            AND bid_end_iso >= datetime('now')
        """
    )

    count = cursor.fetchone()[0]

    conn.close()

    return count
    
def get_last_scraper_update():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT MAX(updated_at)
        FROM tenders
        """
    )

    result = cursor.fetchone()[0]

    conn.close()

    return result


# =====================================================
# CREATE PASSWORD RESET CODE
# =====================================================    
def create_password_reset_code(
    email
):

    conn = get_connection()

    cursor = conn.cursor()

    code = str(
        secrets.randbelow(
            900000
        ) + 100000
    )

    cursor.execute(
        """
        INSERT INTO password_resets (

            email,
            reset_code,
            created_at

        )

        VALUES (?, ?, ?)
        """,
        (
            email,
            code,
            datetime.now().isoformat()
        )
    )

    conn.commit()

    conn.close()

    return code 
    
       
# =====================================================
# VERIFY PASSWORD RESET CODE
# =====================================================     
def verify_reset_code(
    email,
    code
):

    conn = get_connection()

    cursor = conn.cursor()

    cutoff = (
        datetime.now()
        - timedelta(minutes=30)
    ).isoformat()

    cursor.execute(
        """
        SELECT *

        FROM password_resets

        WHERE

            email = ?

            AND reset_code = ?

            AND used = 0

            AND created_at >= ?

        ORDER BY id DESC

        LIMIT 1
        """,
        (
            email,
            code,
            cutoff
        )
    )

    result = cursor.fetchone()

    conn.close()

    return result
# =====================================================
# MARK RESET CODE USED
# =====================================================
def mark_reset_code_used(
    reset_id
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE password_resets

        SET used = 1

        WHERE id = ?
        """,
        (
            reset_id,
        )
    )

    conn.commit()

    conn.close()
    

# =====================================================
# UPDATE PASSWORD
# =====================================================    
def update_user_password(
    email,
    password_hash
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users

        SET password_hash = ?

        WHERE email = ?
        """,
        (
            password_hash,
            email
        )
    )

    conn.commit()

    conn.close()

# =====================================================
#LOG SECURITY EVENT
# =====================================================    
def log_security_event(

    email,

    event_type

):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO security_events (

            email,

            event_type,

            created_at

        )

        VALUES (?, ?, ?)
        """,
        (
            email,
            event_type,
            datetime.now().isoformat()
        )
    )

    conn.commit()

    conn.close()

# =====================================================
# RATE LIMIT
# =====================================================    
def is_rate_limited(

    email,

    event_type,

    max_attempts,

    minutes

):

    conn = get_connection()

    cursor = conn.cursor()

    cutoff = (
        datetime.now()
        -
        timedelta(
            minutes=minutes
        )
    ).isoformat()

    cursor.execute(
        """
        SELECT COUNT(*)

        FROM security_events

        WHERE

            email = ?

            AND event_type = ?

            AND created_at >= ?
        """,
        (
            email,
            event_type,
            cutoff
        )
    )

    count = cursor.fetchone()[0]

    conn.close()

    return count >= max_attempts


# =====================================================
# DELETE OLD RESET CODE
# =====================================================
def delete_old_reset_codes(

    email

):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE password_resets

        SET used = 1

        WHERE email = ?
        """,
        (
            email,
        )
    )

    conn.commit()

    conn.close()



# =====================================================
# CREATE SECURITY EVENT
# =====================================================
def create_security_alert(

    user_id,

    alert_type,

    message

):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO security_alerts (

            user_id,

            alert_type,

            message,

            created_at

        )

        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            alert_type,
            message,
            datetime.now().isoformat()
        )
    )

    conn.commit()

    conn.close()

# =====================================================
# GET UNREAD SECURITY EVENT
# =====================================================
def get_unread_security_alerts(

    user_id

):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *

        FROM security_alerts

        WHERE

            user_id = ?

            AND is_read = 0

        ORDER BY id DESC
        """,
        (
            user_id,
        )
    )

    rows = cursor.fetchall()

    conn.close()

    return rows


# =====================================================
# MARK SECURITY EVENT READ
# =====================================================
def mark_security_alert_read(

    alert_id

):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE security_alerts

        SET is_read = 1

        WHERE id = ?
        """,
        (
            alert_id,
        )
    )

    conn.commit()

    conn.close()


# =====================================================
# COUNT SECURITY EVENTS
# =====================================================

def count_recent_security_events(

    email,

    event_type,

    minutes

):

    conn = get_connection()

    cursor = conn.cursor()

    cutoff = (
        datetime.now()
        -
        timedelta(
            minutes=minutes
        )
    ).isoformat()

    cursor.execute(
        """
        SELECT COUNT(*)

        FROM security_events

        WHERE

            email = ?

            AND event_type = ?

            AND created_at >= ?
        """,
        (
            email,
            event_type,
            cutoff
        )
    )

    count = cursor.fetchone()[0]

    conn.close()

    return count

# =====================================================
# GET TENDERS CLOSING TODAY
# =====================================================
def get_closing_today_count():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM tenders
        WHERE
            tender_active = 1
            AND bid_end_iso IS NOT NULL
            AND date(bid_end_iso) = date('now')
        """
    )

    count = cursor.fetchone()[0]

    conn.close()

    return count
# =====================================================
# GET TOP DEPARTMENTS
# =====================================================
def get_top_departments(limit=4):

    conn = get_connection()

    query = f"""
    SELECT

        organisation_name,

        COUNT(*) AS tender_count

    FROM tenders

    WHERE tender_active = 1

    AND bid_end_iso >= datetime('now')

    GROUP BY organisation_name

    ORDER BY tender_count DESC

    LIMIT {limit}
    """

    df = pd.read_sql_query(
        query,
        conn
    )

    conn.close()

    return df

# =====================================================
# GET HIGH VALUE TENDERS
# =====================================================
def get_high_value_tenders():

    conn = get_connection()

    query = f"""
    SELECT

        tender_id,

        title,

        organisation_name,

        tender_value,

        bid_submission_end_date

    FROM tenders

    WHERE

        tender_active = 1

        AND tender_value_num >= 10000000

        AND bid_end_iso >= datetime('now')

    ORDER BY tender_value_num DESC

    
    """

    df = pd.read_sql_query(
        query,
        conn
    )

    conn.close()

    return df

# =====================================================
# UPDATE ACTIVE TENDER STATUS
# =====================================================

def update_tender_status():

    conn = get_connection()
    cursor = conn.cursor()

    # Mark expired tenders inactive
    cursor.execute("""
        UPDATE tenders
        SET tender_active = 0
        WHERE
            bid_end_iso IS NOT NULL
            AND datetime(bid_end_iso) < datetime('now')
    """)

    # Mark future tenders active
    cursor.execute("""
        UPDATE tenders
        SET tender_active = 1
        WHERE
            bid_end_iso IS NOT NULL
            AND datetime(bid_end_iso) >= datetime('now')
    """)

    conn.commit()
    conn.close()
# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    init_db()

