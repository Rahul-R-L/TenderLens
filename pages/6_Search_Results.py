import streamlit as st
from PIL import Image

from db import (
    search_tenders_v2,
    get_boq_headings_bulk
)



icon_image = Image.open("assets/TL_logo.png")
# =====================================================
# AUTH CHECK
# =====================================================

if not st.session_state.get(
    "logged_in",
    False
):
    st.switch_page(
        "pages/3_Login.py"
    )
# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Search-TenderLens",
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


if (
    "search_filters"
    not in st.session_state
):

    st.warning(
        "No search filters found."
    )

    st.stop()

filters = st.session_state[
    "search_filters"
]

df = search_tenders_v2(

    keyword=
    filters.get(
        "keyword",
        ""
    ),

    organisation_paths=
    filters.get(
        "organisation_paths",
        []
    ),

    location=
    filters.get(
        "location",
        ""
    ),

    min_value=
    filters.get(
        "min_value",
        0
    ),

    max_value=
    filters.get(
        "max_value",
        0
    ),

    closing_from=
    filters.get(
        "closing_from"
    ),

    closing_to=
    filters.get(
        "closing_to"
    )

)


# =====================================================
# CURRENCY AND STATUS 
# =====================================================
def format_currency(value):

    if value is None:
        return "-"

    try:

        value = int(
            float(
                str(value).replace(",", "")
            )
        )

        s = str(value)

        if len(s) <= 3:
            return f"₹{s}"

        last_three = s[-3:]
        remaining = s[:-3]

        parts = []

        while len(remaining) > 2:

            parts.insert(
                0,
                remaining[-2:]
            )

            remaining = remaining[:-2]

        if remaining:

            parts.insert(
                0,
                remaining
            )

        return (
            "₹"
            + ",".join(parts)
            + ","
            + last_three
        )

    except:

        return f"₹{value}"


def get_status(end_date):

    return "🟢 Active"



col1, col2 = st.columns(
    [1, 5]
)

with col1:

    if st.button(
        "← Modify Search"
    ):

        st.switch_page(
            "pages/5_Search.py"
        )

with col2:

    st.title(
        "Search Results"
    )
# =====================================================
# RESULTS
# =====================================================

st.subheader(
    "Results"
)

st.write(
    f"{len(df)} tenders found"
)

PAGE_SIZE = 25

if "search_page" not in st.session_state:

    st.session_state.search_page = 1

total_pages = max(
    1,
    (len(df) + PAGE_SIZE - 1)
    // PAGE_SIZE
)

if st.session_state.search_page > total_pages:
    st.session_state.search_page = 1

if st.session_state.search_page < 1:
    st.session_state.search_page = 1
    
col_prev, col_page, col_next = st.columns(
    [1, 2, 1]
)

with col_prev:

    if st.button(
        "⬅ Previous",
        disabled=
        st.session_state.search_page == 1
    ):

        st.session_state.search_page -= 1

        st.rerun()

with col_page:

    st.markdown(

        f"<center>Page "
        f"{st.session_state.search_page}"
        f" of "
        f"{total_pages}</center>",

        unsafe_allow_html=True

    )

with col_next:

    if st.button(
        "Next ➡",
        disabled=
        st.session_state.search_page
        >= total_pages
    ):

        st.session_state.search_page += 1

        st.rerun()

start_idx = (

    st.session_state.search_page - 1

) * PAGE_SIZE

end_idx = start_idx + PAGE_SIZE

page_df = df.iloc[
    start_idx:end_idx
]

heading_map = get_boq_headings_bulk(

    page_df[
        "tender_id"
    ].tolist()

)


if not page_df.empty:

    for _, row in page_df.iterrows():

        with st.container(border=True):

            # ==================================
            # TITLE
            # ==================================

            st.markdown(
                f"""
                <div style="
                    font-size:26px;
                    font-weight:700;
                    margin-bottom:12px;
                ">
                    {row['title']}
                </div>
                """,
                unsafe_allow_html=True
            )

            # ==================================
            # VALUE | STATUS | LOCATION
            # ==================================

            col1, col2, col3 = st.columns(
                [2, 1, 2]
            )

            with col1:

                st.markdown(
                    f"""
                    <div style="
                        font-size:30px;
                        font-weight:bold;
                        color:#0A66C2;
                    ">
                        {format_currency(
                            row.get(
                                "tender_value"
                            )
                        )}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:

                st.write(
                    get_status(
                        row.get(
                            "bid_submission_end_date"
                        )
                    )
                )

            with col3:

                st.write(
                    f"📍 {row.get('location','-')}"
                )

            # ==================================
            # CLOSING DATE
            # ==================================

            st.caption(
                f"🗓 Closing: "
                f"{row.get('bid_submission_end_date','-')}"
            )

            # ==================================
            # BOQ HEADINGS
            # ==================================

            headings = heading_map.get(
                row["tender_id"],
                []
            )

            if headings:

                st.caption(
                    "Works: "
                    +
                    " | ".join(
                        headings[:4]
                    )
                )

            # ==================================
            # ORGANISATION
            # ==================================

            chain = str(
                row.get(
                    "organisation_chain_raw",
                    ""
                )
            ).replace(
                "||",
                " → "
            )

            st.caption(
                f"Organisation: {chain}"
            )

            # ==================================
            # AUTHORITY
            # ==================================

            authority = row.get(
                "tender_inviting_authority",
                "-"
            )

            st.caption(
                f"Authority: {authority}"
            )

            # ==================================
            # TENDER ID + BUTTON
            # ==================================

            left_col, right_col = st.columns(
                [8, 2]
            )

            with left_col:

                st.caption(
                    f"Tender ID: "
                    f"{row['tender_id']}"
                )

            with right_col:

                if st.button(
                    "View Details",
                    key=f"view_{row['tender_id']}",
                    type="primary"
                ):



                    st.session_state[
                        "selected_tender_id"
                    ] = row[
                        "tender_id"
                    ]

                    st.switch_page(
                        "pages/7_Tender_Details.py"
                    )

else:

    st.info(
        "No tenders found."
    )

# ==================================
# BOTTOM PAGINATION
# ==================================

st.divider()

col_prev, col_page, col_next = st.columns(
    [1, 2, 1]
)

with col_prev:

    if st.button(
        "⬅ Previous",
        key="bottom_prev",
        disabled=
        st.session_state.search_page == 1
    ):

        st.session_state.search_page -= 1

        st.rerun()

with col_page:

    st.markdown(
        f"""
        <center>
        Page
        {st.session_state.search_page}
        of
        {total_pages}
        </center>
        """,
        unsafe_allow_html=True
    )

with col_next:

    if st.button(
        "Next ➡",
        key="bottom_next",
        disabled=
        st.session_state.search_page
        >= total_pages
    ):

        st.session_state.search_page += 1

        st.rerun()
