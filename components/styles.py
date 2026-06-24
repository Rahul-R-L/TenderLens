# components/styles.py

import streamlit as st

def apply_global_styles():

    st.markdown(
        """
        <style>

        [data-testid="stSidebarNav"] {
            display:none;
        }

        </style>
        """,
        unsafe_allow_html=True
    )

st.markdown("""
<style>

/* Hide default navigation */
[data-testid="stSidebarNav"] {
    display: none;
}

/* Remove top padding from sidebar */
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 0rem;
}

/* Optional: reduce left/right padding slightly */
section[data-testid="stSidebar"] .block-container {
    padding-top: 0rem;
}

</style>
""", unsafe_allow_html=True)
