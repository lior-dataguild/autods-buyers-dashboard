import altair as alt
import pandas as pd
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

PROJECT_ID = "dg-demo-data"
DATASET = "demo_autods_demo_v1_v1"

BAR_BLUE = "#2563EB"
INK = "#111827"
MUTED = "#6B7280"
GRID = "#E5E7EB"

CHART_H = 260  # C12: read for shape, not level -> 240px+

st.set_page_config(page_title="Data Guild — Buyers", layout="wide")

st.markdown(
    """
    <style>
      .ui-h1{font-size:1.45rem;font-weight:600;color:#111827;margin:0 0 14px 0}
      .ui-scope{font-size:0.85rem;color:#6B7280;margin:0 0 6px 0}
      /* C34: tight inside a block, generous between blocks */
      [data-testid="stVerticalBlock"]{gap:0.3rem !important}
      /* L7 / C31: the section title IS the disclosure control, not a bordered card */
      [data-testid="stExpander"]{border:0 !important;background:none !important;
        margin-top:18px;margin-bottom:0 !important}
      [data-testid="stExpander"] details{background:none !important;border:0 !important}
      /* Streamlit animates the open/close with an explicit height + overflow:hidden.
         When that animation does not run the content stays clipped to the summary,
         so pin an open expander to its content height. */
      [data-testid="stExpander"] details[open]{height:auto !important;overflow:visible !important}
      [data-testid="stExpander"] summary{padding:0 !important}
      [data-testid="stExpander"] summary p{font-size:0.82rem;font-weight:600;color:#111827}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_bigquery_client() -> bigquery.Client:
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    return bigquery.Client(credentials=credentials, project=PROJECT_ID)


# A buyer = a distinct user with a SUCCEEDED payment that is an actual purchase.
#   status = 'succeeded'                     -> 14.9% of payment rows are not succeeded
#   payment_type NOT IN (refund, chargeback) -> those are stored as POSITIVE rows in this
#                                               dataset, so they would otherwise count as buys
# Window is anchored to MAX(occurred_at), never CURRENT_DATE(): the data stops 2026-06-17.
SQL = f"""
WITH mx AS (
  SELECT DATE(MAX(occurred_at)) AS max_d
  FROM `{PROJECT_ID}.{DATASET}.payment`
), purch AS (
  SELECT DATE(occurred_at) AS d, user_id
  FROM `{PROJECT_ID}.{DATASET}.payment`
  WHERE DATE(occurred_at) BETWEEN (SELECT DATE_SUB(max_d, INTERVAL 29 DAY) FROM mx)
                              AND (SELECT max_d FROM mx)
    AND status = 'succeeded'
    AND payment_type NOT IN ('refund', 'chargeback')
), daily AS (
  SELECT d, COUNT(DISTINCT user_id) AS buyers FROM purch GROUP BY d
), tot AS (
  -- Deliberately NOT the sum of `buyers`: a user active on several days would be
  -- counted once per day. Summing the daily column overstates by ~12% here.
  SELECT COUNT(DISTINCT user_id) AS window_buyers FROM purch
)
SELECT daily.d AS day, daily.buyers, tot.window_buyers
FROM daily CROSS JOIN tot
ORDER BY day
"""


@st.cache_data(ttl=3600)
def load_buyers() -> pd.DataFrame:
    df = get_bigquery_client().query(SQL).to_dataframe()
    # BigQuery DATE arrives as db_dtypes.dbdate, which has no datetime methods.
    df["day"] = pd.to_datetime(df["day"])
    return df


df = load_buyers()

window_buyers = int(df["window_buyers"].iloc[0])
d_from, d_to = df["day"].min(), df["day"].max()

st.markdown('<div class="ui-h1">Buyers</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="ui-scope">{d_from:%d %b %Y} – {d_to:%d %b %Y} · '
    f"{window_buyers:,} unique buyers</div>",
    unsafe_allow_html=True,
)

with st.expander("Daily buyers", expanded=False):
    st.markdown(
        f"""
**Buyer** — a distinct `user_id` with a `succeeded` payment that is not a `refund` or
`chargeback`. Both filters are load-bearing: 14.9% of payment rows are not `succeeded`,
and this dataset stores refunds and chargebacks as *positive* rows.

**Three different counts sit behind this window**, and only the first answers "how many buyers":

| | |
|---|---|
| unique buyers in the window | **{window_buyers:,}** |
| sum of the daily values below | {int(df['buyers'].sum()):,} |
| purchase transactions | 23,581 |

The daily values cannot be summed — a user buying on two days appears in both. Summing them
overstates by {int(df['buyers'].sum()) - window_buyers:,} ({(df['buyers'].sum() / window_buyers - 1):.1%}).

**The window is the last 30 days the data covers, not the last 30 days.** The dataset ends
2026-06-17. Every day in the window is present and the final day runs to 23:59, so no period
is partial.

**The rise is a property of the dataset, not a result.** Monthly buyers grow in every one of
the 36 months on record, from 11 in Jun 2023 to 17,562 in May 2026. This is generated demo
data with a built-in growth ramp.
"""
    )

base = alt.Chart(df)

line = base.mark_line(strokeWidth=2, color=BAR_BLUE, interpolate="linear").encode(
    x=alt.X(
        "day:T",
        title=None,
        axis=alt.Axis(format="%d %b", labelFontSize=13, grid=False,
                      labelColor=MUTED, tickColor=GRID, domainColor=GRID),
    ),
    y=alt.Y(
        "buyers:Q",
        title=None,
        scale=alt.Scale(domainMin=0, nice=True),
        axis=alt.Axis(labelFontSize=13, labelColor=MUTED, gridColor=GRID,
                      domain=False, ticks=False),
    ),
)

# C22: mark every point so the reader can count the periods.
dots = base.mark_point(size=26, filled=True, color=BAR_BLUE, opacity=1).encode(
    x="day:T", y="buyers:Q",
    tooltip=[  # C13: whitelist. No internal columns.
        alt.Tooltip("day:T", title="Day", format="%a %d %b %Y"),
        alt.Tooltip("buyers:Q", title="Buyers", format=","),
    ],
)

# The final value, labelled. Not a legend and not identity (one series, named by the
# title) -- it prints the most recent number, which is the thing most often read off.
last = df.iloc[[-1]]
last_label = alt.Chart(last).mark_text(
    align="left", dx=8, dy=0, fontSize=13, fontWeight=600, color=BAR_BLUE
).encode(x="day:T", y="buyers:Q", text=alt.Text("buyers:Q", format=","))

st.altair_chart(
    (line + dots + last_label)
    .properties(height=CHART_H, padding={"left": 0, "top": 6, "right": 46, "bottom": 0})
    .configure_view(strokeWidth=0)          # C30: chrome recessive
    .configure_axis(labelFont="sans-serif"),
    use_container_width=True,
)
