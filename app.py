import streamlit as st

st.set_page_config(
    page_title="TenderLens",
    page_icon="assets/TL_logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>

/* Hide Streamlit header */
[data-testid="stHeader"] {
    display: none;
}

/* Remove top padding from main content */
.block-container {
    padding-top: 1rem !important;
}

/* Remove top padding from sidebar */
[data-testid="stSidebarUserContent"] {
    padding-top: 0rem !important;
}

</style>
""", unsafe_allow_html=True)
st.markdown(
    """
    <style>

    [data-testid="stSidebarNav"] {
        display:none;
    }

    [data-testid="stSidebarUserContent"] {
        padding-top: 0rem;
    }

    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("""
<style>

/* Hide top toolbar */
[data-testid="stToolbar"] {
    display: none;
}

/* Hide Streamlit header */
[data-testid="stHeader"] {
    display: none;
}

/* Remove top padding */
.block-container {
    padding-top: 1rem !important;
}

</style>
""", unsafe_allow_html=True)

st.title("TenderLens")

st.write("Redirecting...")

if st.session_state.get(
    "logged_in",
    False
):

    st.page_link(
        "pages/4_Dashboard.py",
        label="Open Dashboard"
    )

else:

    st.page_link(
        "pages/3_Login.py",
        label="Open Login"
    )
