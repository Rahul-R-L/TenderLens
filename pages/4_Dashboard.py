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

    .kpi-card {

        background: linear-gradient(
            135deg,
            #1E63D5,
            #0F2B5B
        );

        border-radius: 12px;

        padding: 20px;

        text-align: center;

        color: white;

        min-height: 130px;

        box-shadow:
            0 4px 10px
            rgba(0,0,0,0.15);
    }

    .kpi-title {

        font-size: 14px;

        opacity: 0.9;
    }

    .kpi-value {

        font-size: 32px;

        font-weight: bold;

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
# DATABASE FUNCTIONS
# =====================================================

def get_dashboard_stats():

    conn = get_connection()

    stats = {}

    cursor = conn.cursor()

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
            COUNT(*) as cnt
        FROM tenders
        WHERE tender_active = 1
        GROUP BY organisation_name
        ORDER BY cnt DESC
        """
    )

    stats["departments"] = (
        cursor.fetchall()
    )

    conn.close()

    return stats


def get_departments():

    conn = get_connection()

    df = pd.read_sql_query(
        """
        SELECT DISTINCT
            organisation_name
        FROM tenders
        WHERE tender_active = 1
        ORDER BY organisation_name
        """,
        conn
    )

    conn.close()

    return df["organisation_name"].tolist()


def get_tenders(
    department=None
):

    conn = get_connection()

    query = """
    SELECT

        tender_id,
        title,
        organisation_name,
        location,
        bid_submission_end_date,
        form_of_contract

    FROM tenders

    WHERE tender_active = 1
    """

    params = []

    if (
        department
        and department != "All"
    ):
        query += """
        AND organisation_name = ?
        """

        params.append(
            department
        )

    query += """
    ORDER BY
        bid_submission_end_date ASC
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=params
    )

    conn.close()

    return df


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

active_tenders = (
    get_active_tender_count()
)

closing_today = (
    get_closing_today_count()
)

closing_week = (
    get_closing_this_week_count()
)

high_value = (
    get_high_value_tender_count()
)

c1, c2, c3, c4 = (
    st.columns(4)
)

with c1:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">
                Active Tenders
            </div>

            <div class="kpi-value">
                {active_tenders:,}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c2:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">
                Closing Today
            </div>

            <div class="kpi-value">
                {closing_today:,}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c3:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">
                Closing This Week
            </div>

            <div class="kpi-value">
                {closing_week:,}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with c4:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">
                ₹1 Cr+ Tenders
            </div>

            <div class="kpi-value">
                {high_value:,}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

st.subheader(
    "Top Departments"
)

top_departments = (
    get_top_departments()
)

cols = st.columns(4)

for i, row in enumerate(
    top_departments.itertuples()
):

    with cols[i]:

        if st.button(

            f"""
            {row.organisation_name}

            ({row.tender_count})
            """,

            key=f"dept_{i}",

            use_container_width=True

        ):

            st.session_state[
                "department_filter"
            ] = (
                row.organisation_name
            )

            st.switch_page(
                "pages/6_Search_Results.py"
            )

st.divider()

st.subheader(
    "₹1 Crore+ Opportunities"
)

high_value_df = (
    get_high_value_tenders()
)

if not high_value_df.empty:

    st.dataframe(
        high_value_df,
        use_container_width=True,
        hide_index=True
    )
# =====================================================
# FILTERS
# =====================================================

department_list = (
    get_departments()
)

department_list.insert(
    0,
    "All"
)

selected_department = (
    st.selectbox(
        "Department",
        department_list
    )
)

# =====================================================
# QUICK ACCESS
# =====================================================

st.subheader(
    "Quick Access"
)

c1, c2, c3, c4, c5 = st.columns(5)

with c1:

    if st.button(
        "All Active Tenders",
        use_container_width=True
    ):

        st.session_state[
            "department_filter"
        ] = "All"

        st.switch_page(
            "pages/5_Search.py"
        )

with c2:

    if st.button(
        "PWD",
        use_container_width=True
    ):

        st.session_state[
            "department_filter"
        ] = "PWD"

        st.switch_page(
            "pages/5_Search.py"
        )

with c3:

    if st.button(
        "LSGD",
        use_container_width=True
    ):

        st.session_state[
            "department_filter"
        ] = (
            "Local Self Government Department"
        )

        st.switch_page(
            "pages/5_Search.py"
        )

with c4:

    if st.button(
        "Forest",
        use_container_width=True
    ):

        st.session_state[
            "department_filter"
        ] = "Forest Department"

        st.switch_page(
            "pages/5_Search.py"
        )

with c5:

    if st.button(
        "KSIE",
        use_container_width=True
    ):

        st.session_state[
            "department_filter"
        ] = (
            "Kerala State Industrial Enterprises Ltd"
        )

        st.switch_page(
            "pages/5_Search.py"
        )
