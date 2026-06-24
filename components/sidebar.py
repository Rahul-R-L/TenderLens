import streamlit as st
from PIL import Image
from db import (
    get_active_tender_count,
    get_closing_this_week_count,
    get_high_value_tender_count,
    get_last_scraper_update
)

active_tenders = (
    get_active_tender_count()
)

closing_week = (
    get_closing_this_week_count()
)

high_value = (
    get_high_value_tender_count()
)

last_update = (
    get_last_scraper_update()
)

def render_sidebar():

    # ====================================
    # LOGO
    # ====================================

    try:

        logo = Image.open(
            "assets/tenderlens_logo.png"
        )

        st.sidebar.image(
            logo,
            use_container_width=True
        )

    except:
        pass

    st.sidebar.markdown(
        """
        <div style="
            text-align:center;
            margin-top:-15px;
            margin-bottom:20px;
            color:#64748b;
            font-size:14px;
        ">
            Track Faster. Bid Smarter.
        </div>
        """,
        unsafe_allow_html=True
    )

    # ====================================
    # NAVIGATION
    # ====================================

    if st.sidebar.button(
        "🏠 Dashboard",
        key="sidebar_dashboard",
        use_container_width=True
    ):

        st.switch_page(
            "pages/4_Dashboard.py"
        )

    if st.sidebar.button(
        "🔍 Search",
        key="sidebar_search",
        use_container_width=True
    ):

        st.switch_page(
            "pages/5_Search.py"
        )

    st.sidebar.markdown("---")
    st.sidebar.markdown(
    	"### 📊 Market Snapshot"
    )

    st.sidebar.markdown(
    	f"""
    **Active Tenders**

    {active_tenders:,}

    **Closing This Week**

    {closing_week:,}

    **₹1 Cr+ Works**

    {high_value:,}
    """
    )
