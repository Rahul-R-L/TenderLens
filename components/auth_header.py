import streamlit as st
from PIL import Image


def render_auth_header():

    try:

        logo = Image.open(
            "assets/tenderlens_logo.png"
        )

        col1, col2, col3 = st.columns(
            [2, 3, 2]
        )

        with col2:

            st.image(
                logo,
                use_container_width=True
            )

    except:
        pass

