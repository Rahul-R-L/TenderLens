import streamlit as st
import textwrap
import html
import streamlit.components.v1 as components
from pdf_generator import create_tender_pdf
from PIL import Image

icon_image = Image.open("assets/TL_logo.png")

from streamlit.column_config import (
    TextColumn,
    NumberColumn
)

from db import (
    get_tender_details,
    get_boq_df
)
# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="TenderLens",
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


from components.topbar import (
    render_topbar
)

render_topbar()




from components.styles import (
    apply_global_styles
)

apply_global_styles()
#=====================================================


if not st.session_state.get(
    "logged_in",
    False
):
    st.switch_page(
        "pages/3_Login.py"
    )

if st.button("← Back to Search"):
    st.switch_page("pages/6_Search_Results.py")

if (
    "selected_tender_id"
    not in st.session_state
):

    st.warning(
        "No tender selected."
    )

    st.stop()

tender_id = (
    st.session_state[
        "selected_tender_id"
    ]
)

tender = (
    get_tender_details(
        tender_id
    )
)

if not tender:

    st.error(
        "Tender not found."
    )

    st.stop()

st.title(
    "Tender Details"
)

st.subheader(
    tender["title"]
)

col1, col2 = st.columns(2)

with col1:

    st.write(
        "**Tender ID:**",
        tender["tender_id"]
    )

    st.write(
        "**Organisation:**",
        tender["organisation_name"]
    )

    st.write(
        "**Location:**",
        tender["location"]
    )

    st.write(
        "**Contract Type:**",
        tender["form_of_contract"]
    )

with col2:

    st.write(
    	"**Tender Value:**",
    	tender["tender_value"] or "-"
    )

    st.write(
        "**Closing Date:**",
        tender["bid_submission_end_date"]
    )

    st.write(
        "**Authority:**",
        tender[
            "tender_inviting_authority"
        ]
    )

st.divider()

st.subheader(
    "Organisation Hierarchy"
)

st.markdown(
    tender["organisation_chain_raw"].replace(
        "||",
        " → "
    )
)

st.subheader(
    "Authority Address"
)

st.write(
    tender[
        "authority_address"
    ]
)

st.subheader(
    "Work Description"
)

st.write(
    tender[
        "work_description"
    ]
)

st.divider()

st.subheader(
    "BoQ"
)



    
    
boq_df = get_boq_df(
    tender_id
)

pdf_bytes = create_tender_pdf(
    tender,
    boq_df
)

st.download_button(

    "📄 Download Tender PDF",

    data=pdf_bytes,

    file_name=f"{tender_id}.pdf",

    mime="application/pdf"

)

if not boq_df.empty:

    html_table = f"""
<style>

body {{
    background: white;
    color: #111827;
}}

.boq-table {{
    border-collapse: collapse;
    width: 100%;
}}

.boq-table th {{
    background: #F3F4F6;
    color: #111827;
}}

.boq-table td,
.boq-table th {{
    border: 1px solid #D1D5DB;
}}

</style>

<table class="boq-table">

<colgroup>

<col style="width:8%;">
<col style="width:74%;">
<col style="width:10%;">
<col style="width:8%;">

</colgroup>

<tr>

<th>Item No</th>
<th>Description</th>
<th>Qty</th>
<th>Unit</th>

</tr>
"""
    for _, row in boq_df.iterrows():

        description = html.escape(
            str(
                row["description"]
            )
        )

        html_table += f"""

        <tr>

            <td class="boq-item">
                {row["item_no"]}
            </td>

            <td class="boq-desc">
                {description}
            </td>

            <td class="boq-qty">
                {row["quantity"]}
            </td>

            <td class="boq-unit">
                {row["unit"]}
            </td>

        </tr>

        """

    html_table += "</table>"

    components.html(
    	html_table,
    	height=800,
    	scrolling=True
    )

else:

    st.info(
        "No BOQ available."
    )


