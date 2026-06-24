from playwright.sync_api import sync_playwright
import pandas as pd
import re
import json
import os
import random
import time
import zipfile
import shutil
import pandas as pd
from db import (
    init_db,
    insert_tender,
    tender_exists,
    insert_boq_item,
    insert_boq_heading
)

# =====================================================
# CONFIG
# =====================================================

BASE_URL = (
    "https://etenders.kerala.gov.in"
)

TEMP_CSV = (
    "all_active_tenders_temp.csv"
)

FINAL_CSV = (
    "all_active_tenders.csv"
)

PROGRESS_FILE = (
    "progress.json"
)

FAILED_LOG = (
    "failed_tenders.txt"
)

# retry stale session
MAX_RETRIES = 2

# next stability test
# change to None for full scrape
MAX_PAGES = None



# =====================================================
# DATABASE
# =====================================================

init_db()

# =====================================================
# DELAYS
# =====================================================

def random_delay():

    time.sleep(
        random.uniform(2, 4)
    )


def retry_delay():

    time.sleep(
        random.uniform(2, 3)
    )


# =====================================================
# TEXT HELPERS
# =====================================================

def extract_between(
    text,
    start,
    end
):

    try:

        pattern = (
            rf"{re.escape(start)}"
            rf"(.*?)"
            rf"{re.escape(end)}"
        )

        match = re.search(
            pattern,
            text,
            re.DOTALL
        )

        if match:

            return " ".join(
                match.group(1)
                .split()
            )

        return None

    except:

        return None

def extract_form_of_contract(text):

    match = re.search(

        r"Form\s+Of\s+Contract\s+(.*?)\s+Tender\s+Category",

        text,

        re.IGNORECASE | re.DOTALL
    )

    if not match:

        return ""

    value = match.group(1).strip()

    valid_contracts = [

        "Percentage",
        "Item Rate",
        "Lump Sum",
        "Service",
        "Supply",
        "Empanelment",
        "EOI",
        "EPC Contract",
        "Item Wise",
        "Piece-work",
        "Supplu and Service",
        "Tender cum Auction",
        "Turn-key",
        "Works"
    ]

    for contract in valid_contracts:

        if contract.lower() in value.lower():

            return contract

    return value

def clean_value(value):

    if value is None:
        return None

    value = (
        str(value)
        .strip()
    )

    if (
        value == ""
        or
        value.upper()
        == "NA"
    ):

        return None

    return value



# =====================================================
# TENDER VALUE
# =====================================================
def parse_tender_value(
    value
):

    try:

        if not value:
            return None

        return float(
            str(value)
            .replace(",", "")
            .strip()
        )

    except:

        return None


# =====================================================
# TENDER END DATE ISO
# =====================================================  

def convert_to_iso_date(
    value
):

    try:

        if not value:
            return None

        dt = datetime.strptime(
            value,
            "%d-%b-%Y %I:%M %p"
        )

        return dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    except:

        return None  

def clean_processing_fee(
    value
):

    if value is None:
        return None

    value = re.sub(
        r"\(.*?\)",
        "",
        str(value)
    )

    value = value.strip()

    if (
        value == ""
        or
        value.upper()
        == "NA"
    ):

        return None

    return value


# =====================================================
# ORGANISATION HELPER
# =====================================================

def get_parent_organisation(

    organisation_chain
):

    if not organisation_chain:

        return None

    return (

        str(
            organisation_chain
        )

        .split(
            "||"
        )[0]

        .strip()
    )
    
# =====================================================
# TENDER ACTIVE STATUS
# =====================================================

from datetime import datetime


def get_tender_active_status(

    bid_end_date
):

    try:

        if not bid_end_date:

            return 1

        bid_date = datetime.strptime(

            bid_end_date,

            "%d-%b-%Y %I:%M %p"
        )

        if (
            bid_date
            < datetime.now()
        ):

            return 0

        return 1

    except Exception:

        return 1
# =====================================================
# RANDOM UTILITIES
# =====================================================

def build_seen_ids(
    all_tenders
):

    seen = set()

    for tender in all_tenders:

        tender_id = (
            tender.get(
                "tender_id"
            )
        )

        if tender_id:

            seen.add(
                tender_id
            )

    return seen


# =====================================================
# PROGRESS SAVE / LOAD
# =====================================================

def save_progress(
    page_number,
    tender_index,
    completed=False
):

    progress = {

        "page_number":
        page_number,

        "tender_index":
        tender_index,

        "completed":
        completed
    }

    with open(
        PROGRESS_FILE,
        "w"
    ) as f:

        json.dump(
            progress,
            f,
            indent=4
        )


def load_progress():

    if not os.path.exists(
        PROGRESS_FILE
    ):

        return None

    try:

        with open(
            PROGRESS_FILE,
            "r"
        ) as f:

            return json.load(
                f
            )

    except:

        return None


def delete_progress():

    if os.path.exists(
        PROGRESS_FILE
    ):

        os.remove(
            PROGRESS_FILE
        )


# =====================================================
# FAILED TENDER LOG
# =====================================================

def log_failed_tender(
    page_number,
    tender_number,
    reason
):

    with open(
        FAILED_LOG,
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            "\n"
            + "=" * 60
            + "\n"
        )

        f.write(
            f"PAGE: "
            f"{page_number}\n"
        )

        f.write(
            f"TENDER: "
            f"{tender_number}\n"
        )

        f.write(
            f"REASON: "
            f"{reason}\n"
        )


# =====================================================
# CSV CHECKPOINT
# =====================================================

def save_temp_csv(
    all_tenders,
    page_number=None
):

    try:

        df = pd.DataFrame(
            all_tenders
        )

        if not df.empty:

            df.drop_duplicates(
                subset=[
                    "tender_id"
                ],
                inplace=True
            )

        df.to_csv(
            TEMP_CSV,
            index=False
        )

        print(
            "\n"
            + "=" * 50
        )

        if page_number:

            print(
                f"PAGE "
                f"{page_number} "
                f"COMPLETE"
            )

        print(
            f"Checkpoint saved:"
            f" {len(df)} "
            f"unique tenders"
        )

        print(
            "=" * 50
        )

    except Exception as e:

        print(
            f"Checkpoint "
            f"save error: "
            f"{e}"
        )


def load_existing_csv():

    if not os.path.exists(
        TEMP_CSV
    ):

        return []

    try:

        df = pd.read_csv(
            TEMP_CSV
        )

        print(
            f"\nLoaded "
            f"{len(df)} "
            f"existing tenders"
        )

        return (
            df.to_dict(
                "records"
            )
        )

    except:

        return []


# =====================================================
# RESUME STATE
# =====================================================

def get_resume_state():

    progress = (
        load_progress()
    )

    if not progress:

        return {

            "resume":
            False,

            "page":
            1,

            "tender_index":
            0
        }

    print(
        "\nFound previous run."
    )

    choice = input(
        "Resume previous run? "
        "(y/n): "
    ).strip().lower()

    if choice != "y":

        delete_progress()

        if os.path.exists(
            TEMP_CSV
        ):

            os.remove(
                TEMP_CSV
            )

        return {

            "resume":
            False,

            "page":
            1,

            "tender_index":
            0
        }

    return {

        "resume":
        True,

        "page":
        progress.get(
            "page_number",
            1
        ),

        "tender_index":
        progress.get(
            "tender_index",
            0
        )
    }  
#------------------------PART 2-------------------------------------------------------------------------------------------------
# =====================================================
# PAGE VALIDATION
# =====================================================

def valid_tender_page(
    page
):

    try:

        body = (
            page
            .locator("body")
            .inner_text()
            .lower()
        )

        # HARD FAIL
        if (
            "stale session"
            in body
        ):

            return False

        # POSITIVE CHECKS
        required = [

            "basic details",

            "tender inviting authority",

            "tender id"
        ]

        return all(
            item in body
            for item in required
        )

    except:

        return False


def valid_search_page(
    page
):

    try:

        body = (
            page
            .locator("body")
            .inner_text()
            .lower()
        )

        # if search result table exists
        if (
            "tender list"
            in body
        ):

            return True

        return False

    except:

        return False


# =====================================================
# AUTHORITY EXTRACTION
# =====================================================

def extract_authority_details(
    full_text
):

    authority_name = None
    authority_address = None

    try:

        authority_start = (
            full_text.find(
                "Tender Inviting Authority"
            )
        )

        if (
            authority_start
            == -1
        ):

            return (
                None,
                None
            )

        authority_text = (
            full_text[
                authority_start:
                authority_start + 800
            ]
        )

        name_match = re.search(
            r"Name\s+(.*?)\s+Address",
            authority_text,
            re.DOTALL
        )

        address_match = re.search(
            r"Address\s+(.*?)\s+Back",
            authority_text,
            re.DOTALL
        )

        if name_match:

            authority_name = (
                " ".join(
                    name_match
                    .group(1)
                    .split()
                )
            )

        if address_match:

            authority_address = (
                " ".join(
                    address_match
                    .group(1)
                    .split()
                )
            )

    except:

        pass

    return (
        authority_name,
        authority_address
    )


# =====================================================
# TENDER EXTRACTION
# =====================================================

def extract_tender_data(
    page
):

    full_text = (
        page
        .locator("body")
        .inner_text()
    )

    # ---------------------------------
    # MAIN SECTION
    # ---------------------------------

    start = (
        full_text.find(
            "Basic Details"
        )
    )

    end = (
        full_text.find(
            "Visitor No:"
        )
    )

    if (
        start == -1
    ):

        text = full_text

    else:

        text = (
            full_text[
                start:end
            ]
        )

    # ---------------------------------
    # AUTHORITY
    # ---------------------------------

    (
        authority_name,
        authority_address
    ) = extract_authority_details(
        full_text
    )

    # ---------------------------------
    # DATA
    # ---------------------------------

    organisation_chain_raw = (
        clean_value(
            extract_between(
                text,
                "Organisation Chain",
                "Tender Reference Number"
            )
        )
    )

    tender = {

        "organisation_chain_raw":
        organisation_chain_raw,

        "organisation_name":
        get_parent_organisation(
            organisation_chain_raw
        ),

	"tender_active":
	get_tender_active_status(

    		clean_value(
        		extract_between(
            			text,
           			"Bid Submission End Date",
            			"Tenders Documents"
        		)
    		)
	),

        "tender_url":
        page.url,

        "tender_id":
        clean_value(
            extract_between(
                text,
                "Tender ID",
                "Withdrawal Allowed"
            )
        ),

        "tender_category":
        clean_value(
            extract_between(
                text,
                "Tender Category",
                "No. of Covers"
            )
        ),

        "no_of_covers":
        clean_value(
            extract_between(
                text,
                "No. of Covers",
                "General Technical Evaluation Allowed"
            )
        ),

        "emd_amount":
        clean_value(
            extract_between(
                text,
                "EMD Amount in ₹",
                "EMD Exemption Allowed"
            )
        ),

        "tender_fee":
        clean_value(
            extract_between(
                text,
                "Tender Fee in ₹",
                "Processing Fee in ₹"
            )
        ),

        "processing_fee":
        clean_processing_fee(
            extract_between(
                text,
                "Processing Fee in ₹",
                "Fee Payable To"
            )
        ),

        "title":
        clean_value(
            extract_between(
                text,
                "Title",
                "Work Description"
            )
        ),

        "work_description":
        clean_value(
            extract_between(
                text,
                "Work Description",
                "NDA/Pre Qualification"
            )
        ),

        "tender_value":
        clean_value(
            extract_between(
                text,
                "Tender Value in ₹",
                "Product Category"
            )
        ),

        "tender_value_num":
        parse_tender_value(

            clean_value(
                extract_between(
                    text,
                    "Tender Value in ₹",
                    "Product Category"
                )
            )
        ),

        "product_category":
        clean_value(
            extract_between(
                text,
                "Product Category",
                "Sub category"
            )
        ),

        "period_of_work_days":
        clean_value(
            extract_between(
                text,
                "Period Of Work(Days)",
                "Location"
            )
        ),
        
	"form_of_contract":
	extract_form_of_contract(
	    text
	),

        "location":
        clean_value(
            extract_between(
                text,
                "Location",
                "Pincode"
            )
        ),

        "bid_submission_end_date":
        clean_value(
            extract_between(
                text,
                "Bid Submission End Date",
                "Tenders Documents"
            )
        ),

        "bid_end_iso":
        convert_to_iso_date(

            clean_value(
                extract_between(
                    text,
                    "Bid Submission End Date",
                    "Tenders Documents"
                )
            )
        ),

        "tender_inviting_authority":
        authority_name,

        "authority_address":
        authority_address
    }

    print(
    	"ORG:",
    	tender.get(
        	"organisation_chain_raw"
    	)
    )
    
    print(
    "FORM:",
    tender.get(
        "form_of_contract"
    )
)
    
    return tender
 #---------------------------------------------------PART 3-----------------------------------------------------------------------------------
# =====================================================
# GET TENDER ROWS
# =====================================================

def get_tender_rows(
    search_page
):

    valid_rows = []

    try:

        table = (
            search_page
            .locator("table")
            .nth(18)
        )

        rows = table.locator(
            "tr"
        )

        row_count = (
            rows.count()
        )

        for i in range(
            1,
            row_count
        ):

            try:

                row = (
                    rows.nth(i)
                )

                row_text = (
                    row.inner_text()
                )

                match = re.search(
                    r"\d{4}_[A-Za-z0-9]+_\d+_\d+",
                    row_text
                )

                if not match:
                    continue

                links = (
                    row.locator("a")
                )

                if (
                    links.count()
                    == 0
                ):

                    continue

                valid_rows.append(
                    i
                )

            except:

                continue

    except Exception as e:

        print(
            f"Row detection "
            f"error: {e}"
        )

    return valid_rows


# =====================================================
# OPEN TENDER TAB
# SAME WINDOW
# =====================================================

def open_tender_tab(
    context,
    search_page,
    row_index
):

    try:

        table = (
            search_page
            .locator("table")
            .nth(18)
        )

        row = (
            table
            .locator("tr")
            .nth(row_index)
        )

        first_link = (
            row
            .locator("a")
            .first
        )

        with context.expect_page() as new_page_info:

            first_link.click(
                modifiers=[
                    "Control"
                ]
            )

        tender_page = (
            new_page_info.value
        )

        tender_page.wait_for_load_state(
            "networkidle"
        )

        time.sleep(2)

        return tender_page

    except Exception as e:

        print(
            f"Tender open "
            f"error: {e}"
        )

        return None


# =====================================================
# OPEN VALID TENDER
# RETRY ON STALE SESSION
# =====================================================

def open_valid_tender(
    context,
    search_page,
    row_index
):

    for attempt in range(
        MAX_RETRIES
    ):

        print(
            f"Attempt "
            f"{attempt+1}/"
            f"{MAX_RETRIES}"
        )

        tender_page = (
            open_tender_tab(
                context,
                search_page,
                row_index
            )
        )

        if not tender_page:

            retry_delay()

            continue

        try:

            try:

                tender_page.wait_for_selector(
                    "text=Basic Details",
                    timeout=10000
                )

            except:

                pass

            if valid_tender_page(
                tender_page
            ):

                return tender_page

            print(
                "Stale session "
                "detected"
            )

            try:

                tender_page.close()

            except:

                pass

        except Exception as e:

            print(
                f"Validation "
                f"error: {e}"
            )

            try:

                tender_page.close()

            except:

                pass

        retry_delay()

    return None


# =====================================================
# PAGE NAVIGATION
# =====================================================

def goto_first_page(
    search_page
):

    search_page.wait_for_load_state(
        "networkidle"
    )

    time.sleep(2)

    if not valid_search_page(
        search_page
    ):

        input(
            "\nSearch page "
            "invalid.\n"
            "Reload manually "
            "and press ENTER..."
        )


def goto_next_page(
    search_page
):

    try:

        link_fwd = (
            search_page
            .locator(
                "#linkFwd"
            )
        )

        if (
            link_fwd.count()
            == 0
        ):

            return False

        link_fwd.click()

        search_page.wait_for_load_state(
            "networkidle"
        )

        time.sleep(2)

        return True

    except Exception as e:

        print(
            f"Pagination "
            f"error: {e}"
        )

        return False


# =====================================================
# LAST PAGE CHECK
# =====================================================

def is_last_page(
    search_page
):

    try:

        return (

            search_page
            .locator(
                "#linkLast"
            )
            .count()

            == 0
        )

    except:

        return True
        
        
#------------------------------------------PART 4---------------------------------------------------------------
# ======================================================
# DOWNLOAD & PARSE BOQ
# ======================================================

def download_and_parse_boq(

    page,

    tender_id,

    tender_title
):

    temp_folder = (
        f"temp_{tender_id}"
    )

    zip_path = None

    try:

        if not os.path.exists(
            temp_folder
        ):

            os.makedirs(
                temp_folder
            )

        # ---------------------------------
        # DOWNLOAD ZIP
        # ---------------------------------

        with page.expect_download() as download_info:

            page.locator(
                "text=Download as zip file"
            ).first.click()

        download = (
            download_info.value
        )

        zip_path = (
            os.path.join(
                temp_folder,
                f"{tender_id}.zip"
            )
        )

        download.save_as(
            zip_path
        )

        print(
            f"Downloaded ZIP:"
            f" {tender_id}"
        )

        # ---------------------------------
        # EXTRACT ZIP
        # ---------------------------------

        with zipfile.ZipFile(
            zip_path,
            "r"
        ) as zip_ref:

            zip_ref.extractall(
                temp_folder
            )

        # ---------------------------------
        # FIND BOQ FILE
        # ---------------------------------

        boq_file = None

        files = os.listdir(
            temp_folder
        )

        for file in files:

            file_lower = (
                file.lower()
            )

            if (
                "boq"
                in file_lower
            ) and (

                file_lower.endswith(
                    ".xls"
                )

                or

                file_lower.endswith(
                    ".xlsx"
                )
            ):

                boq_file = (
                    os.path.join(
                        temp_folder,
                        file
                    )
                )

                break

        if (
            boq_file
            is None
        ):

            print(
                f"No BOQ found:"
                f" {tender_id}"
            )

            return

        print(
            f"BOQ Found:"
            f" {boq_file}"
        )

        # ---------------------------------
        # READ BOQ
        # ---------------------------------

        if boq_file.endswith(
            ".xls"
        ):

            df = pd.read_excel(

                boq_file,

                header=None,

                engine="xlrd"
            )

        else:

            df = pd.read_excel(

                boq_file,

                header=None,

                engine="openpyxl"
            )

        # -----------------------------
        # FIND WORK NAME
        # -----------------------------

        boq_work_name = ""

        for i in range(

            min(
                10,
                len(df)
            )
        ):

            row_text = (
                " ".join(

                    map(

                        str,

                        df.iloc[i]
                        .fillna("")
                        .tolist()
                    )

                )
                .lower()
            )

            if (

                "name of work"
                in row_text

                or

                "work name"
                in row_text

            ):

                boq_work_name = (
                    row_text
                )

                break

        # -----------------------------
        # VALIDATE TITLE
        # -----------------------------

        title_words = set(

            tender_title
            .lower()
            .replace(
                "-",
                " "
            )
            .split()
        )

        boq_words = set(

            boq_work_name
            .replace(
                "-",
                " "
            )
            .split()
        )

        common_words = (
            title_words
            &
            boq_words
        )

        similarity = (
            len(
                common_words
            )
            /
            max(
                1,
                len(
                    title_words
                )
            )
        )

        if (
            similarity
            < 0.15
        ):

            print(
                "\nWARNING:"
                " BOQ mismatch"
            )

            print(
                f"Tender:"
                f" {tender_title}"
            )

            print(
                f"BOQ:"
                f" {boq_work_name}"
            )

            return

        print(
            "BOQ verified"
        )

        # -----------------------------
        # FIND HEADER ROW
        # -----------------------------

        header_row = None

        for i in range(
            len(df)
        ):

            row_text = (
                " ".join(

                    map(

                        str,

                        df.iloc[i]
                        .fillna("")
                        .tolist()
                    )

                )
                .lower()
            )

            if (

                "item description"
                in row_text

                and

                "quantity"
                in row_text
            ):

                header_row = i

                break

        if (
            header_row
            is None
        ):

            print(
                "BOQ header "
                "not found"
            )

            return

        print(
            f"Header row:"
            f" {header_row}"
        )
        
        # -----------------------------
        # DETECT HIERARCHICAL BOQ
        # -----------------------------

        has_sub_items = False

        for r in range(

            header_row + 1,

            len(df)
        ):

            try:

                test_item_no = str(

                    df.iloc[
                        r,
                        0
                    ]

                ).strip()

                if re.match(

                    r"^\d+\.\d+",

                    test_item_no
                ):

                    has_sub_items = True

                    break

            except Exception:

                pass


        print(

            f"Hierarchical BOQ: "
            f"{has_sub_items}"
        )

        # -----------------------------
        # EXTRACT ITEMS
        # -----------------------------

        boq_count = 0

        heading_count = 0

        for i in range(

            header_row + 1,

            len(df)
        ):

            row = df.iloc[i]

            try:

                item_no = str(
                    row.iloc[0]
                ).strip()

                description = str(
                    row.iloc[1]
                ).strip()

                quantity = (
                    row.iloc[3]
                    if len(row) > 3
                    else None
                )

                unit = (
                    str(
                        row.iloc[4]
                    ).strip()
                    if len(row) > 4
                    else None
                )

                estimated_rate = (
                    row.iloc[5]
                    if len(row) > 5
                    else None
                )

                amount = (
                    row.iloc[9]
                    if len(row) > 9
                    else None
                )

                # -------------------------
                # HEADING DETECTION
                # -------------------------

                if has_sub_items:

                    if (

                        not re.match(
                            r"^\d+\.\d+",
                            item_no
                        )

                        and

                        description
                        not in [
                            "",
                            "nan"
                        ]

                        and

                        len(
                            description
                        ) > 5
                    ):

                        insert_boq_heading(

                            tender_id,

                            item_no,

                            description
                        )

                        heading_count += 1

                        continue
                # -------------------------
                # SKIP EMPTY ROWS
                # -------------------------

                if (

                    description
                    in [
                        "",
                        "nan"
                    ]

                    or

                    len(
                        description
                    ) < 8
                ):

                    continue

                insert_boq_item(

                    tender_id,

                    item_no,

                    description,

                    quantity,

                    unit,

                    estimated_rate,

                    amount
                )

                boq_count += 1

            except Exception:

                continue

        print(
            f"Saved "
            f"{boq_count} "
            f"BOQ items"
        )

    except Exception as e:

        print(
            f"BOQ Parse Failed:"
            f" {e}"
        )

    finally:

        try:

            if os.path.exists(
                temp_folder
            ):

                shutil.rmtree(
                    temp_folder
                )

        except Exception:

            pass
            

# =====================================================
# MAIN EXECUTION
# =====================================================

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False
    )

    context = (
        browser.new_context()
    )

    search_page = (
        context.new_page()
    )

    # ---------------------------------
    # RESUME STATE
    # ---------------------------------

    state = (
        get_resume_state()
    )

    start_page = (
        state["page"]
    )

    start_tender_index = (
        state[
            "tender_index"
        ]
    )

    # ---------------------------------
    # LOAD OLD DATA
    # ---------------------------------

    if state["resume"]:

        all_tenders = (
            load_existing_csv()
        )

    else:

        all_tenders = []

    seen_ids = (
        build_seen_ids(
            all_tenders
        )
    )

    # ---------------------------------
    # OPEN SEARCH PAGE
    # ---------------------------------

    search_page.goto(
        BASE_URL
    )

    print(
        "\nGo to Advanced Search,"
    )

    print(
        "Select Open Tender,"
    )

    print(
        "Solve CAPTCHA,"
    )

    print(
        "Click Search."
    )

    input(
        "\nAfter result "
        "page loads, "
        "press ENTER..."
    )

    goto_first_page(
        search_page
    )

    # ---------------------------------
    # RESUME PAGE NAVIGATION
    # ---------------------------------

    current_page = 1

    while (
        current_page
        < start_page
    ):

        print(
            f"\nNavigating "
            f"to page "
            f"{current_page+1}"
        )

        success = (
            goto_next_page(
                search_page
            )
        )

        if not success:

            print(
                "Failed to "
                "reach resume page"
            )

            input(
                "\nManually "
                "navigate to "
                f"page "
                f"{start_page} "
                "and press ENTER..."
            )

            break

        current_page += 1

    page_number = (
        start_page
    )

    # ---------------------------------
    # PAGE LOOP
    # ---------------------------------

    while True:

        # -----------------------------
        # TEST LIMIT
        # -----------------------------

        if (
            MAX_PAGES
            is not None
        ):

            if (
                page_number
                > MAX_PAGES
            ):

                print(
                    "\nReached "
                    "MAX_PAGES limit."
                )

                break

        print(
            "\n"
            + "=" * 60
        )

        print(
            f"PAGE "
            f"{page_number}"
        )

        print(
            "=" * 60
        )

        row_indexes = (
            get_tender_rows(
                search_page
            )
        )

        print(
            f"\nCollected "
            f"{len(row_indexes)} "
            f"tenders "
            f"from page "
            f"{page_number}"
        )

        if (
            len(row_indexes)
            == 0
        ):

            print(
                "No tenders found."
            )

            break

        # -----------------------------
        # RESUME INDEX
        # -----------------------------

        if (
            page_number
            == start_page
        ):

            tender_start = (
                start_tender_index
            )

        else:

            tender_start = 0

        # -----------------------------
        # TENDER LOOP
        # -----------------------------

        for i in range(
            tender_start,
            len(
                row_indexes
            )
        ):

            row_index = (
                row_indexes[i]
            )

            print(
                f"\nOpening "
                f"tender "
                f"{i+1}/"
                f"{len(row_indexes)}"
            )

            tender_page = (
                open_valid_tender(
                    context,
                    search_page,
                    row_index
                )
            )

            if not tender_page:

                print(
                    "Failed "
                    "to open "
                    "valid tender"
                )

                log_failed_tender(
                    page_number,
                    i + 1,
                    "Stale session "
                    "after retries"
                )

                continue

            try:

                tender = (
                    extract_tender_data(
                        tender_page
                    )
                )

                tender_id = (
                    tender.get(
                        "tender_id"
                    )
                )

                # ---------------------
                # VALIDATION
                # ---------------------

                if not tender_id:

                    print(
                        "Blank extraction"
                    )

                    log_failed_tender(
                        page_number,
                        i + 1,
                        "Blank extraction"
                    )

                    tender_page.close()

                    continue

                # ---------------------
                # DUPLICATE CHECK
                # ---------------------

                if (
                    tender_id
                    in seen_ids
                ):

                    print(
                        f"Duplicate:"
                        f" {tender_id}"
                    )

                    tender_page.close()

                    continue

                                # ---------------------
                # SAVE
                # ---------------------

                all_tenders.append(
                    tender
                )

                seen_ids.add(
                    tender_id
                )

                # ---------------------
                # SAVE TO DATABASE
                # ---------------------

                try:

                    inserted = (
                        insert_tender(
                            tender
                        )
                    )

                    if inserted:

                        print(
                            "Added to DB"
                        )
                        # ---------------------
                        # TEST BOQ DOWNLOAD
                        # ---------------------

                        print(
                            "\nTesting BOQ "
                            "download..."
                        )

                        download_and_parse_boq(

                            tender_page,

                            tender_id,
                            
                            tender.get("title")
                        )

                    else:

                        print(
                            "Already in DB"
                        )

                except Exception as e:

                    print(
                        f"DB error: "
                        f"{e}"
                    )

                print(
                    f"Collected:"
                    f" "
                    f"{tender_id}"
                )

                print(
                    f"TOTAL UNIQUE:"
                    f" "
                    f"{len(seen_ids)}"
                )

                # ---------------------
                # SAVE PROGRESS
                # ---------------------

                save_progress(
                    page_number,
                    i+1
                )

                tender_page.close()

            except Exception as e:

                print(
                    f"Extraction "
                    f"error: "
                    f"{e}"
                )

                log_failed_tender(
                    page_number,
                    i + 1,
                    str(e)
                )

                try:

                    tender_page.close()

                except:

                    pass

            random_delay()

        # -----------------------------
        # PAGE CHECKPOINT
        # -----------------------------

        save_temp_csv(
            all_tenders
        )

        # -----------------------------
        # LAST PAGE CHECK
        # -----------------------------

        if is_last_page(
            search_page
        ):

            print(
                "\nReached "
                "last page."
            )

            break

        # -----------------------------
        # NEXT PAGE
        # -----------------------------

        success = (
            goto_next_page(
                search_page
            )
        )

        if not success:

            print(
                "Pagination failed"
            )

            input(
                "\nNavigate "
                "manually and "
                "press ENTER..."
            )

        page_number += 1

    # =================================
    # FINAL SAVE
    # =================================

    df = pd.DataFrame(
        all_tenders
    )

    if not df.empty:

        df.drop_duplicates(
            subset=[
                "tender_id"
            ],
            inplace=True
        )

    df.to_csv(
        FINAL_CSV,
        index=False
    )

    save_progress(
        page_number,
        0,
        completed=True
    )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "SCRAPING COMPLETE"
    )

    print(
        f"Saved "
        f"{len(df)} "
        f"unique tenders"
    )

    print(
        f"\nFinal file:"
        f" {FINAL_CSV}"
    )

    print(
        "=" * 60
    )

    input(
        "\nPress ENTER "
        "to close..."
    )

    browser.close()
