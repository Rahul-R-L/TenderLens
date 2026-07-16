import streamlit as st

from db import (
    search_tenders_v2,
    get_hierarchy_children,
    get_boq_headings_bulk
)

from PIL import Image

icon_image = Image.open("assets/TL_logo.png")
# =====================================================
# AUTH CHECK
# =====================================================

if not st.session_state.get(
    "logged_in",
    False
):
    st.switch_page(
        "pages/3_Login.py"
    )
# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Search-TenderLens",
    page_icon="assets/TL_logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>

    [data-testid="stSidebarNav"] {
        display: none;
    }

    </style>
    """,
    unsafe_allow_html=True
)

from components.sidebar import (
    render_sidebar
)

render_sidebar()

from components.topbar import (
    render_topbar
)

render_topbar()



from components.styles import (
    apply_global_styles
)

apply_global_styles()



# ====================================
# SEARCH STATE
# ====================================

if "search_keyword" not in st.session_state:
    st.session_state.search_keyword = ""

if "search_location" not in st.session_state:
    st.session_state.search_location = ""

if "search_min_value" not in st.session_state:
    st.session_state.search_min_value = 0

if "search_max_value" not in st.session_state:
    st.session_state.search_max_value = 0

if "search_page" not in st.session_state:
    st.session_state.search_page = 1

if "search_filters" not in st.session_state:

    st.session_state["search_filters"] = {

        "keyword": "",

        "organisation_paths": [],

        "location": "",

        "min_value": 0,

        "max_value": 0,

        "closing_from": None,

        "closing_to": None

    }
def reset_search_filters():

    st.session_state["search_filters"] = {

        "keyword": "",

        "organisation_paths": [],

        "location": "",

        "min_value": 0,

        "max_value": 100000000000000,

        "closing_from": None,

        "closing_to": None

    }

    st.session_state.search_page = 1

st.title(
    "Tender Search"
)


# =====================================================
# FILTERS
# =====================================================

with st.expander(
    "Search Filters",
    expanded=True
):


    keyword = st.text_input(
        "Keyword",
        value=st.session_state.search_keyword
    )

    st.session_state.search_keyword = keyword

    organisation_paths = []

    parent_path = ""

    level = 1

    while True:

        options = get_hierarchy_children(parent_path)

        if not options:
            break

        selected = st.multiselect(

            f"Level {level}" if level > 1 else "Organisation",

            options,

            key=f"org_level_{level}"

        )

        # -----------------------------
        # Nothing selected
        # -----------------------------

        if len(selected) == 0:

            if parent_path:
                organisation_paths = [parent_path]

            break

        # -----------------------------
        # Multiple selected
        # -----------------------------

        if len(selected) > 1:

            if parent_path:

                organisation_paths = [

                    parent_path + "||" + x

                    for x in selected

                ]

            else:

                organisation_paths = selected

            break

        # -----------------------------
        # Single selected
        # -----------------------------

        if parent_path:

            parent_path += "||" + selected[0]

        else:

            parent_path = selected[0]

        organisation_paths = [

            parent_path

        ]

        level += 1

    # =================================================
    # LOCATION
    # =================================================

    location = st.text_input(
        "Location",
        value=st.session_state.search_location
    )

    st.session_state.search_location = location

    # =================================================
    # VALUE
    # =================================================

    col1, col2 = st.columns(2)

    with col1:

        min_value = st.number_input(
            "Min Tender Value",
            min_value=0,
            value=st.session_state.search_min_value,
            step=100000
        )

        st.session_state.search_min_value = min_value

    with col2:

        max_value = st.number_input(
            "Max Tender Value",
            min_value=0,
            value=st.session_state.search_max_value,
            step=100000
        )

        st.session_state.search_max_value = max_value

    # =================================================
    # DATE RANGE
    # =================================================

    col1, col2 = st.columns(2)

    with col1:

        closing_from = st.date_input(
            "Closing Date From",
            value=None
        )

    with col2:

        closing_to = st.date_input(
            "Closing Date To",
            value=None
        )

    search_clicked = st.button(
        "🔍 Search",
        type="primary"
    )
    
# =====================================================
# SEARCH
# =====================================================

if search_clicked:

    st.session_state[
    "search_filters"
    ] = {

    "keyword": keyword,

    "organisation_paths":
    organisation_paths,

    "location":
    location,

    "min_value":
    min_value,

    "max_value":
    max_value,

    "closing_from":
    closing_from,

    "closing_to":
    closing_to
    }

    st.session_state.search_page = 1

    st.switch_page(
    "pages/6_Search_Results.py"
    )