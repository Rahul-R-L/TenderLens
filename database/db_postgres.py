import pandas as pd
import secrets
import psycopg2
from datetime import (datetime, timedelta)
from psycopg2.extras import RealDictCursor
from database.connection import get_connection



# =====================================================
# CONNECTION
# =====================================================


# =====================================================
# INIT DATABASE
# =====================================================


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
        WHERE email = %s
        """,
        (email,)
    )

    result = cursor.fetchone()

    cursor.close()
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

            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            CURRENT_TIMESTAMP
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

    cursor.close()
    conn.close()   
    
def get_user_by_email(email):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE email = %s
        """,
        (email,)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return user


def get_user_by_token(token):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE verification_token = %s
        """,
        (token,)
    )

    user = cursor.fetchone()

    cursor.close()
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
            email_verified_at = CURRENT_TIMESTAMP,
            verification_token = NULL

        WHERE verification_token = %s
        """,

        (token,)
    )

    conn.commit()

    success = cursor.rowcount > 0

    cursor.close()
    conn.close()

    return success


def update_last_login(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users

        SET last_login = CURRENT_TIMESTAMP

        WHERE id = %s
        """,

        (user_id,)
    )

    conn.commit()

    cursor.close()
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
        WHERE organisation_chain_raw IS NOT NULL
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
import secrets

def create_password_reset_code(
    email
):

    conn = get_connection()
    cursor = conn.cursor()

    code = str(
        secrets.randbelow(900000) + 100000
    )

    cursor.execute(
        """
        INSERT INTO password_resets (

            email,
            reset_code,
            created_at

        )

        VALUES (

            %s,
            %s,
            CURRENT_TIMESTAMP
        )
        """,
        (
            email,
            code
        )
    )

    conn.commit()

    cursor.close()
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

    cursor.execute(
        """
        SELECT *

        FROM password_resets

        WHERE

            email = %s

            AND reset_code = %s

            AND used = 0

            AND created_at >= (
                CURRENT_TIMESTAMP
                - INTERVAL '30 minutes'
            )

        ORDER BY id DESC

        LIMIT 1
        """,
        (
            email,
            code
        )
    )

    result = cursor.fetchone()

    cursor.close()
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

        WHERE id = %s
        """,
        (
            reset_id,
        )
    )

    conn.commit()

    cursor.close()
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

        SET password_hash = %s

        WHERE email = %s
        """,
        (
            password_hash,
            email
        )
    )

    conn.commit()

    cursor.close()
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

        VALUES (

            %s,
            %s,
            CURRENT_TIMESTAMP
        )
        """,
        (
            email,
            event_type
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

# =====================================================
# RATE LIMIT
# =====================================================    
from datetime import timedelta

def is_rate_limited(
    email,
    event_type,
    max_attempts,
    minutes
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) AS count

        FROM security_events

        WHERE

            email = %s

            AND event_type = %s

            AND created_at >= (
                CURRENT_TIMESTAMP
                - (%s * INTERVAL '1 minute')
            )
        """,
        (
            email,
            event_type,
            minutes
        )
    )

    count = cursor.fetchone()["count"]

    cursor.close()
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

        WHERE email = %s
        """,
        (
            email,
        )
    )

    conn.commit()

    cursor.close()
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

        VALUES (

            %s,
            %s,
            %s,
            CURRENT_TIMESTAMP
        )
        """,
        (
            user_id,
            alert_type,
            message
        )
    )

    conn.commit()

    cursor.close()
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

            user_id = %s
            AND is_read = 0

        ORDER BY id DESC
        """,
        (
            user_id,
        )
    )

    rows = cursor.fetchall()

    cursor.close()
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

        WHERE id = %s
        """,
        (
            alert_id,
        )
    )

    conn.commit()

    cursor.close()
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

    cursor.execute(
        """
        SELECT COUNT(*)

        FROM security_events

        WHERE

            email = %s

            AND event_type = %s

            AND created_at >= (
                CURRENT_TIMESTAMP
                - (%s * INTERVAL '1 minute')
            )
        """,
        (
            email,
            event_type,
            minutes
        )
    )

    count = cursor.fetchone()["count"]

    cursor.close()
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
def get_high_value_tenders(limit=10):

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

    ORDER BY tender_value_num DESC

    LIMIT {limit}
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

