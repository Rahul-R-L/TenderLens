import streamlit as st

def render_topbar():

    user_name = st.session_state.get(
        "user_name",
        "User"
    )

    col1, col2 = st.columns(
        [8, 2]
    )

    with col1:

        st.markdown(
            """
            <h3 style="
                margin-top:0px;
                margin-bottom:0px;
            ">
                TenderLens
            </h3>
            """,
            unsafe_allow_html=True
        )

    with col2:

        if st.button(
            f"👤 {user_name}",
            key="topbar_profile",
            use_container_width=True
        ):

            st.session_state[
                "show_profile_menu"
            ] = not st.session_state.get(
                "show_profile_menu",
                False
            )

    if st.session_state.get(
        "show_profile_menu",
        False
    ):

        st.info(
            f"""
            {user_name}

            ⭐ Early Adopter (Premium Access until 31 Oct 2026)
            """
        )

        if st.button(
            "🚪 Logout",
            key="topbar_logout"
        ):

            st.session_state.clear()

            st.switch_page(
                "pages/3_Login.py"
            )

    st.divider()
