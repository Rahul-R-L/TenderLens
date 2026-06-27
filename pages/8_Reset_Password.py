import streamlit as st

from database.db_postgres import (
    get_user_by_email,
    create_password_reset_code,
    verify_reset_code,
    mark_reset_code_used,
    update_user_password,
    is_rate_limited,
    log_security_event,
    delete_old_reset_codes
)

from auth import (
    hash_password,
    send_password_reset_email
)

from components.auth_header import (
    render_auth_header
)

from components.styles import (
    apply_global_styles
)

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Reset Password - TenderLens",
    page_icon="assets/TL_logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

render_auth_header()
apply_global_styles()

st.title(
    "Reset Password"
)

st.caption(
    "Recover access to your TenderLens account."
)

# =====================================================
# SESSION INIT
# =====================================================

if "reset_email" not in st.session_state:

    st.session_state[
        "reset_email"
    ] = None

# =====================================================
# STEP 1 - REQUEST RESET CODE
# =====================================================

if not st.session_state.get(
    "reset_email"
):

    email = st.text_input(
        "Email"
    )

    email = (
        email
        .strip()
        .lower()
    )

    if st.button(
        "Send Reset Code",
        type="primary",
        use_container_width=True
    ):

        if not email:

            st.error(
                "Please enter your email."
            )

            st.stop()

        user = get_user_by_email(
            email
        )

        if not user:

            st.error(
                "Account not found."
            )

            st.stop()

        # ============================================
        # RATE LIMIT
        # 3 REQUESTS / DAY
        # ============================================

        if is_rate_limited(

            email,

            "password_reset_request",

            3,

            1440

        ):

            st.error(
                "Password reset limit reached. Please try again tomorrow."
            )

            st.stop()

        delete_old_reset_codes(
            email
        )

        code = (
            create_password_reset_code(
                email
            )
        )

        send_password_reset_email(

            email,

            code

        )

        log_security_event(

            email,

            "password_reset_request"

        )

        st.session_state[
            "reset_email"
        ] = email

        st.success(
            "Password reset code sent to your email."
        )

        st.rerun()

# =====================================================
# STEP 2 - VERIFY CODE
# =====================================================

else:

    st.success(
        f"Reset requested for: {st.session_state['reset_email']}"
    )

    reset_code = st.text_input(
        "Reset Code"
    )

    new_password = st.text_input(
        "New Password",
        type="password"
    )

    confirm_password = st.text_input(
        "Confirm Password",
        type="password"
    )

    col1, col2 = st.columns(2)

    with col1:

        reset_btn = st.button(
            "Reset Password",
            type="primary",
            use_container_width=True
        )

    with col2:

        cancel_btn = st.button(
            "Cancel",
            use_container_width=True
        )

    # ============================================
    # CANCEL
    # ============================================

    if cancel_btn:

        del st.session_state[
            "reset_email"
        ]

        st.switch_page(
            "pages/3_Login.py"
        )

    # ============================================
    # RESET
    # ============================================

    if reset_btn:

        email = st.session_state[
            "reset_email"
        ]

        if not reset_code:

            st.error(
                "Enter reset code."
            )

            st.stop()

        if not new_password:

            st.error(
                "Enter a new password."
            )

            st.stop()

        if len(
            new_password
        ) < 8:

            st.error(
                "Password must contain at least 8 characters."
            )

            st.stop()

        if new_password != confirm_password:

            st.error(
                "Passwords do not match."
            )

            st.stop()

        # ========================================
        # RATE LIMIT
        # 5 WRONG CODE ATTEMPTS / DAY
        # ========================================

        if is_rate_limited(

            email,

            "password_reset_verify",

            5,

            1440

        ):

            st.error(
                "Too many invalid reset attempts. Request a new reset code."
            )

            st.stop()

        reset_record = verify_reset_code(

            email,

            reset_code

        )

        if not reset_record:

            log_security_event(

                email,

                "password_reset_verify"

            )

            st.error(
                "Invalid reset code."
            )

            st.stop()

        password_hash = hash_password(
            new_password
        )

        update_user_password(

            email,

            password_hash

        )

        mark_reset_code_used(
            reset_record["id"]
        )

        st.success(
            "Password updated successfully."
        )

        del st.session_state[
            "reset_email"
        ]

        st.info(
            "Redirecting to login page..."
        )

        st.switch_page(
            "pages/3_Login.py"
        )