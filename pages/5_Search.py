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

    with st.form(
        "search_form"
    ):

        keyword = st.text_input(
            "Keyword",
            value=st.session_state.search_keyword
        )

        st.session_state.search_keyword = keyword

        organisation_paths = []

        # =================================================
        # LEVEL 1
        # =================================================

        level1_options = (
            get_hierarchy_children("")
        )

        level1_selected = st.multiselect(
            "Organisation",
            level1_options
        )

        # ---------------------------------------------
        # NOTHING SELECTED
        # ---------------------------------------------

        if len(level1_selected) == 0:

            organisation_paths = []

        # ---------------------------------------------
        # MULTIPLE LEVEL 1
        # ---------------------------------------------

        elif len(level1_selected) > 1:

            organisation_paths = (
                level1_selected
            )

        # ---------------------------------------------
        # SINGLE LEVEL 1
        # ---------------------------------------------

        elif len(level1_selected) == 1:

            organisation_path = (
                level1_selected[0]
            )

            organisation_paths = [
                organisation_path
            ]

            # =========================================
            # LEVEL 2
            # =========================================

            level2_options = (
                get_hierarchy_children(
                    organisation_path
                )
            )

            if level2_options:

                level2_selected = (
                    st.multiselect(
                        "Level 2",
                        level2_options
                    )
                )

                if len(level2_selected) > 1:

                    organisation_paths = [

                        organisation_path
                        + "||" + x

                        for x in level2_selected
                    ]

                elif len(level2_selected) == 1:

                    organisation_path += (
                        "||"
                        +
                        level2_selected[0]
                    )

                    organisation_paths = [
                        organisation_path
                    ]

                    # =================================
                    # LEVEL 3
                    # =================================

                    level3_options = (
                        get_hierarchy_children(
                            organisation_path
                        )
                    )

                    if level3_options:

                        level3_selected = (
                            st.multiselect(
                                "Level 3",
                                level3_options
                            )
                        )

                        if len(level3_selected) > 1:

                            organisation_paths = [

                                organisation_path
                                + "||" + x

                                for x in level3_selected
                            ]

                        elif len(level3_selected) == 1:

                            organisation_path += (
                                "||"
                                +
                                level3_selected[0]
                            )

                            organisation_paths = [
                                organisation_path
                            ]

                            # =========================
                            # LEVEL 4
                            # =========================

                            level4_options = (
                                get_hierarchy_children(
                                    organisation_path
                                )
                            )

                            if level4_options:

                                level4_selected = (
                                    st.multiselect(
                                        "Level 4",
                                        level4_options
                                    )
                                )

                                if len(level4_selected) > 1:

                                    organisation_paths = [

                                        organisation_path
                                        + "||" + x

                                        for x in level4_selected
                                    ]

                                elif len(level4_selected) == 1:

                                    organisation_path += (
                                        "||"
                                        +
                                        level4_selected[0]
                                    )

                                    organisation_paths = [
                                        organisation_path
                                    ]

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

        search_clicked = st.form_submit_button(
            "🔍 Search"
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
