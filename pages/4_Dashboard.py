import streamlit as st
import pandas as pd

from db import (
    get_connection,
    get_active_tender_count,
    get_closing_today_count,
    get_closing_this_week_count,
    get_high_value_tender_count,
    get_top_departments,
    get_high_value_tenders,
    mark_security_alert_read
)


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
    page_title="Dashboard-TenderLens",
    page_icon="assets/TL_logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
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


st.markdown(
    """
    <style>

   div[data-testid="stMetric"] {

    background: #f5f7fb;

    padding: 15px;

    border-radius: 12px;

    border-left: 5px solid #1E63D5;

    box-shadow:
        0 4px 10px rgba(0,0,0,0.08);
}
    
    .department-card {

        background: #ffffff;

        border-radius: 12px;

        padding: 18px;

        text-align: center;

        border-left: 5px solid #1E63D5;

        box-shadow:
            0 4px 10px
            rgba(0,0,0,0.08);

        min-height: 110px;
    }

    .department-name {

        font-size: 15px;

        font-weight: 600;

        color: #1f2937;
    }

    .department-count {

        font-size: 28px;

        font-weight: 700;

        color: #1E63D5;

        margin-top: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


if st.session_state.get(
    "security_warning"
):

    st.warning(
        f"""
        🔒 Security Notice

        {st.session_state['security_warning']}
        """
    )

    if st.session_state.get(
        "security_alert_id"
    ):

        mark_security_alert_read(
            st.session_state[
                "security_alert_id"
            ]
        )

        del st.session_state[
            "security_alert_id"
        ]

    del st.session_state[
        "security_warning"
    ]



# =====================================================
# HEADER
# =====================================================

st.title(
    "TenderLens Dashboard"
)

st.caption(
    f"Welcome {st.session_state['user_name']}"
)


# =====================================================
# KPI CARDS
# =====================================================
st.subheader(
    "📈 Market Overview"
)

active_tenders = get_active_tender_count()

closing_today = get_closing_today_count()

closing_week = get_closing_this_week_count()

high_value = get_high_value_tender_count()

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "Active Tenders",
        f"{active_tenders:,}"
    )

with c2:
    st.metric(
        "Closing Today",
        f"{closing_today:,}"
    )

with c3:
    st.metric(
        "Closing This Week",
        f"{closing_week:,}"
    )

with c4:
    st.metric(
        "₹1 Cr+ Tenders",
        f"{high_value:,}"
    )
st.divider()


st.subheader(
    "🏛️ Top Departments"
)


top_departments = (
    get_top_departments()
)

cols = st.columns(
    min(
        len(top_departments),
        4
    )
)

for i, row in enumerate(
    top_departments.head(4).itertuples()
):

    with cols[i]:

        dept_name = row.organisation_name

        if dept_name == "Local Self Government Department":

            display_name = "LSGD"

        elif dept_name == "Forest Department":

            display_name = "Forest"

        elif dept_name == "Irrigation Department":

            display_name = "Irrigation"

        elif dept_name == "Public Works Department":

            display_name = "PWD"

        elif dept_name == "Kerala State Industrial Enterprises Ltd":

            display_name = "KSIE"

        elif dept_name == "Kerala Water Authority":

            display_name = "KWA"

        else:

            display_name = dept_name

        st.metric(
            display_name,
            f"{row.tender_count:,}"
        )

        if st.button(

            "View Tenders",

            key=f"dept_{i}",

            use_container_width=True

        ):

            st.session_state[
                "search_filters"
            ] = {

                "keyword": "",

                "organisation_paths": [
                    dept_name
                ],

                "location": "",

                "min_value": 0,

                "max_value": 0,

                "closing_from": None,

                "closing_to": None
            }

            st.switch_page(
                "pages/6_Search_Results.py"
            )

st.divider()

st.subheader(
    "💰 ₹1 Crore+ Opportunities"
)

st.info(
    f"{high_value:,} active tenders above ₹1 Crore currently available."
)

high_value_df = (
    get_high_value_tenders()
)

if not high_value_df.empty:

    display_df = high_value_df.copy()

    display_df = display_df[
        [
            "title",
            "organisation_name",
            "tender_value",
            "bid_submission_end_date"
        ]
    ]

    display_df.columns = [

        "Title",
        "Organisation",
        "Tender Value  (₹)",
        "Closing Date"

    ]

    st.dataframe(

        display_df,

        use_container_width=True,

        hide_index=True,

        height=350
    )

    # =====================================================
    # QUICK ACCESS
    # =====================================================


