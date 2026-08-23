import pandas as pd
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

from ui_components import PALETTE, bar_css, data_bars

PROJECT_ID = "dg-demo-data"

st.set_page_config(page_title="Data Guild — Buyers", layout="wide")
st.markdown(bar_css(PALETTE), unsafe_allow_html=True)


@st.cache_resource
def get_bigquery_client() -> bigquery.Client:
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    return bigquery.Client(credentials=credentials, project=PROJECT_ID)


@st.cache_data(ttl=3600)
def run_query(sql: str) -> pd.DataFrame:
    client = get_bigquery_client()
    return client.query(sql).to_dataframe()


st.markdown('<div class="ui-h1">Buyers</div>', unsafe_allow_html=True)
st.markdown('<div class="ui-scope">All figures are for the last 2 days.</div>',
            unsafe_allow_html=True)

with st.expander("Buyers", expanded=False):
    st.markdown("Placeholder data — not yet connected to a live query.")

# Fake data — real numbers pending dashboard-scope validation against demo_autods_demo_v1_v1.
buyers_df = pd.DataFrame([
    {"day": "Yesterday", "buyers": 184},
    {"day": "Today", "buyers": 231},
])

st.markdown(
    data_bars(buyers_df, "day", [("BUYERS", "", "buyers", "n0")], "DAY"),
    unsafe_allow_html=True,
)
