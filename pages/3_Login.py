from db import get_user_by_email, update_last_login
from auth import verify_password
import streamlit as st

from db import (
    get_user_by_email,
    update_last_login,
    log_security_event,
    count_recent_security_events,
    create_security_alert,
    get_unread_security_alerts,
    mark_security_alert_read
)

from auth import (
    verify_password
)

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Login - TenderLens",
    page_icon="assets/TL_logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)


from components.auth_header import (
    render_auth_header
)

render_auth_header()

from components.styles import (
    apply_global_styles
)

apply_global_styles()
#=====================================================
email = st.text_input(
    "Email"
)

email = email.strip().lower()

password = st.text_input(
    "Password",
    type="password"
)

col1, col2 = st.columns(2)

with col1:

    login_btn = st.button(
        "Login",
        type="primary",
        use_container_width=True
    )

with col2:

    forgot_btn = st.button(
        "Forgot Password",
        use_container_width=True
    )

st.write("")

register_btn = st.button(
    "Create New Account",
    use_container_width=True
)

# =====================================================
# LOGIN
# =====================================================

if login_btn:


    user = get_user_by_email(
        email
    )

    

    failed_count = count_recent_security_events(

        email,

        "login_failed",

        30

    )

    if failed_count >= 5:

        st.error(
            "Account temporarily locked. Try again in 30 minutes."
        )

        st.stop()

    if not user:

        st.error(
            "Invalid email or password"
        )

        st.stop()

    if user["is_active"] != 1:

        st.error(
            "Account disabled"
        )

        st.stop()

    if user["is_verified"] != 1:

        st.warning(
            "Please verify your email first."
        )

        st.stop()

    if not verify_password(

        password,

        user["password_hash"]

    ):

        log_security_event(

            email,

            "login_failed"

        )

        failed_count = count_recent_security_events(

            email,

            "login_failed",

            30

        )

        if failed_count >= 5:

            create_security_alert(

                user["id"],

                "failed_login_lockout",

                "Five failed login attempts triggered a temporary account lock."
            )

            st.error(
                "Too many failed login attempts. Account locked for 30 minutes."
            )

        else:

            st.error(
                "Invalid email or password"
            )

        st.stop()

    update_last_login(
        user["id"]
    )

    st.session_state[
        "logged_in"
    ] = True

    st.session_state[
        "user_id"
    ] = user["id"]

    st.session_state[
        "user_name"
    ] = user["name"]

    st.session_state[
        "role"
    ] = user["role"]
    alerts = get_unread_security_alerts(

        user["id"]

    )

    for alert in alerts:

        st.session_state[
            "security_warning"
        ] = alert["message"]

        mark_security_alert_read(
            alert["id"]
        )
    st.success(
        "Login successful"
    )

    st.switch_page(
        "pages/4_Dashboard.py"
    )

# =====================================================
# FORGOT PASSWORD
# =====================================================

if forgot_btn:

    st.switch_page(
        "pages/8_Reset_Password.py"
    )

# =====================================================
# REGISTER
# =====================================================

if register_btn:

    st.switch_page(
        "pages/1_Register.py"
    )
