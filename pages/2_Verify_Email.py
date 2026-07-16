import streamlit as st
from textwrap import dedent
from database.db_postgres import (
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

    st.success("✅ Email verified successfully!")

    st.balloons()

    st.container(border=True)

    st.subheader("🎉 Welcome to TenderLens!")

    st.write(
        """
        Your email has been successfully verified.

        As one of our early users, you have secured
        **TenderLens Early Adopter Status**.
        """
    )

    st.markdown("### 🎁 Your Early Adopter Benefits")

    st.markdown("""
    - ✅ Unlimited Tender Searches
    - ✅ Advanced BOQ Search
    - ✅ Tender PDF Generation
    - ✅ Email Tender Alerts
    - ✅ Access to all TenderLens features
    - ✅ All Premium features released during the Early Adopter period
    """)

    st.warning(
        "🎊 Complimentary Premium Access\n\n"
        "**FREE access to all TenderLens Premium features "
        "until 31 October 2026.**"
    )

    st.info(
        "Thank you for joining TenderLens during its launch phase. "
        "Your feedback will help us build the most powerful tender "
        "discovery platform in India."
    )

    if st.button(
        "🚀 Continue to Login",
        type="primary",
        use_container_width=True
    ):
        st.switch_page("pages/1_Login.py")