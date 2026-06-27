import streamlit as st

from database.db_postgres import (
    email_exists,
    create_user
)

from auth import (
    hash_password,
    generate_token,
    send_verification_email
)

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Register-TenderLens",
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
#================================================

st.title(
    "Create Account"
)

st.caption(
    "Get complimentary access to TenderLens Pro during the launch period."
)

name = st.text_input(
    "Full Name *"
)

email = st.text_input(
    "Email *"
)

email = email.strip().lower()

mobile = st.text_input(
    "Mobile *"
)

company_name = st.text_input(
    "Company Name"
)

password = st.text_input(
    "Password *",
    type="password"
)

referral_source = st.selectbox(
    "How did you hear about us?",
    [
        "Google",
        "WhatsApp",
        "Friend",
        "Facebook",
        "YouTube",
        "Other"
    ]
)

if st.button(
    "Create Account",
    use_container_width=True
):

    if not name:

        st.error(
            "Name is required."
        )

        st.stop()

    if not email:

        st.error(
            "Email is required."
        )

        st.stop()

    if not password:

        st.error(
            "Password is required."
        )

        st.stop()

    if email_exists(
        email
    ):

        st.error(
            "Email already registered."
        )

        st.stop()

    password_hash = (
        hash_password(
            password
        )
    )

    verification_token = (
        generate_token()
    )

    create_user(

        name=name,

        email=email,

        mobile=mobile,

        company_name=company_name,

        password_hash=password_hash,

        verification_token=verification_token,

        referral_source=referral_source
    )

    send_verification_email(

        email,

        verification_token
    )

    st.success(
        "Registration successful. "
        "Please check your email "
        "to verify your account."
    )
