import streamlit as st

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

    st.success(
        "✅ Email verified successfully!"
    )

    st.balloons()

    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, #FFFBEA, #FFF3C4);
            border: 2px solid #D4AF37;
            border-radius: 12px;
            padding: 28px;
            margin-top: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.10);
        ">

            <h2 style="color:#B8860B; margin-top:0;">
                🎉 Welcome to TenderLens!
            </h2>

            <p style="font-size:18px; line-height:1.7;">

                Your email has been successfully verified.

            </p>

            <p style="font-size:18px; line-height:1.7;">

                As one of our early users, you have
                <b>secured TenderLens Early Adopter Status.</b>

            </p>

            <hr>

            <h3 style="margin-bottom:12px;">
                🎁 Your Early Adopter Benefits
            </h3>

            <ul style="font-size:16px; line-height:1.8;">

                <li>✔ Unlimited Tender Searches</li>

                <li>✔ Advanced BOQ Search</li>

                <li>✔ Tender PDF Generation</li>

                <li>✔ Email Tender Alerts</li>

                <li>✔ Access to every TenderLens feature</li>

                <li>✔ All Premium features released during the Early Adopter period</li>

            </ul>

            <div style="
                margin-top:18px;
                padding:16px;
                border-radius:8px;
                background:#FFF8DC;
                border-left:6px solid #D4AF37;
            ">

                <b style="font-size:17px;">
                    🎊 Complimentary Premium Access
                </b>

                <p style="margin-top:8px; font-size:16px;">

                    You will enjoy
                    <b>FREE access to all TenderLens Premium features</b>
                    until

                    <span style="color:#C62828;">
                        <b>31 October 2026</b>
                    </span>.

                </p>

            </div>

            <p style="
                margin-top:20px;
                font-size:15px;
                color:#555;
            ">

                Thank you for joining TenderLens during its launch phase.
                Your feedback will help us build the most powerful tender discovery platform in India.

            </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "🚀 Continue to Login",
        type="primary",
        use_container_width=True
    ):

        st.switch_page(
            "pages/1_Login.py"
        )

else:

    st.error(
        "Verification failed."
    )