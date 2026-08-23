"""BigQuery access for the DG dashboard suite.

Every window is measured back from the data's own last date, never CURRENT_DATE():
this dataset ends 2026-06-17, so a now-relative window returns nothing at all.
"""
import pandas as pd
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

PROJECT_ID = "dg-demo-data"
DATASET = "demo_autods_demo_v1_v1"
T = f"`{PROJECT_ID}.{DATASET}"

# A purchase = a SUCCEEDED payment that is not a refund or chargeback.
# Both filters are load-bearing: 14.9% of payment rows are not succeeded, and this
# dataset stores refunds/chargebacks as POSITIVE rows, so they would count as buys.
PURCHASE = "status = 'succeeded' AND payment_type NOT IN ('refund','chargeback')"


@st.cache_resource
def client() -> bigquery.Client:
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    return bigquery.Client(credentials=creds, project=PROJECT_ID)


@st.cache_data(ttl=3600, show_spinner=False)
def totals(days: int) -> dict:
    sql = f"""
    WITH win AS (
      SELECT DATE_SUB(DATE(MAX(occurred_at)), INTERVAL {days - 1} DAY) AS d0,
             DATE(MAX(occurred_at)) AS d1
      FROM {T}.payment`
    )
    SELECT
      (SELECT d0 FROM win) AS d0,
      (SELECT d1 FROM win) AS d1,
      -- NOT the sum of the daily values: a user buying on two days is one buyer.
      (SELECT COUNT(DISTINCT user_id) FROM {T}.payment`, win
         WHERE DATE(occurred_at) BETWEEN d0 AND d1 AND {PURCHASE}) AS buyers,
      (SELECT SUM(recognized_amount_usd + refund_adjustment_usd)
         FROM {T}.revenue_recognition`, win
         WHERE recognized_month BETWEEN d0 AND d1) AS net_revenue,
      (SELECT SUM(recognized_amount_usd) FROM {T}.revenue_recognition`, win
         WHERE recognized_month BETWEEN d0 AND d1) AS gross_revenue,
      (SELECT -SUM(refund_adjustment_usd) FROM {T}.revenue_recognition`, win
         WHERE recognized_month BETWEEN d0 AND d1) AS refunds,
      (SELECT COUNT(*) FROM {T}.subscription`, win
         WHERE DATE(started_at) BETWEEN d0 AND d1) AS new_subs
    """
    r = client().query(sql).to_dataframe().iloc[0]
    gross = float(r["gross_revenue"] or 0)
    refunds = float(r["refunds"] or 0)
    return {
        "d0": pd.to_datetime(r["d0"]),
        "d1": pd.to_datetime(r["d1"]),
        "buyers": int(r["buyers"]),
        "net_revenue": float(r["net_revenue"] or 0),
        "gross_revenue": gross,
        "refunds": refunds,
        "new_subs": int(r["new_subs"]),
        # Q3: guard the denominator's SIGN, not just zero. 5.3% of revrec rows net
        # below zero, so a bare SAFE_DIVIDE here can return a flattering nonsense rate.
        "refund_rate": (refunds / gross) if gross > 0 else None,
    }


@st.cache_data(ttl=3600, show_spinner=False)
def daily(days: int) -> pd.DataFrame:
    """Long format: one row per (day, metric). Reindexed so a quiet day is a real zero
    (B19) rather than a gap the line would bridge."""
    sql = f"""
    WITH win AS (
      SELECT DATE_SUB(DATE(MAX(occurred_at)), INTERVAL {days - 1} DAY) AS d0,
             DATE(MAX(occurred_at)) AS d1
      FROM {T}.payment`
    ), b AS (
      SELECT DATE(occurred_at) AS d, 'buyers' AS metric,
             CAST(COUNT(DISTINCT user_id) AS FLOAT64) AS value
      FROM {T}.payment`, win
      WHERE DATE(occurred_at) BETWEEN d0 AND d1 AND {PURCHASE} GROUP BY 1
    ), r AS (
      SELECT recognized_month AS d, 'net_revenue',
             SUM(recognized_amount_usd + refund_adjustment_usd)
      FROM {T}.revenue_recognition`, win
      WHERE recognized_month BETWEEN d0 AND d1 GROUP BY 1
    ), s AS (
      SELECT DATE(started_at) AS d, 'new_subs', CAST(COUNT(*) AS FLOAT64)
      FROM {T}.subscription`, win
      WHERE DATE(started_at) BETWEEN d0 AND d1 GROUP BY 1
    )
    SELECT * FROM b UNION ALL SELECT * FROM r UNION ALL SELECT * FROM s
    ORDER BY metric, d
    """
    df = client().query(sql).to_dataframe()
    # BigQuery DATE arrives as db_dtypes.dbdate, which has no datetime methods.
    df["d"] = pd.to_datetime(df["d"])

    full = pd.date_range(df["d"].min(), df["d"].max(), freq="D")
    out = []
    for m, g in df.groupby("metric"):
        g = g.set_index("d").reindex(full, fill_value=0.0)
        g["metric"] = m
        out.append(g.rename_axis("d").reset_index())
    return pd.concat(out, ignore_index=True)


def series(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    return df[df["metric"] == metric].sort_values("d").reset_index(drop=True)
