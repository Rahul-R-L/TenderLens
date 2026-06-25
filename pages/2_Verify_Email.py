import streamlit as st

from db import (
    get_user_by_token,
    verify_user
)

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Verify - TenderLens",
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

from components.styles import (
    apply_global_styles
)

apply_global_styles()
#=======================================================
token = st.query_params.get(
    "token"
)

st.title(
    "Email Verification"
)

if not token:

    st.error(
        "Invalid verification link."
    )

    st.stop()

user = get_user_by_token(
    token
)

if not user:

    st.error(
        "Verification token not found."
    )

    st.stop()

if verify_user(token):

    st.success(
        "Email verified successfully."
    )

    st.info(
        "You can now login."
    )

else:

    st.error(
        "Verification failed."
    )
