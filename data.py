from __future__ import annotations   # local venv is 3.9; PEP 604 unions are 3.10+

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
D = f"`{PROJECT_ID}.{DATASET}"

# Bump whenever the RETURN SHAPE or signature of a cached function below changes.
#
# Streamlit Cloud hot-reloads new code into the running process without restarting it,
# so st.cache_data entries computed by the previous version can survive the update and
# be handed to code that expects a different shape. That happened once here: the new
# app.py asked for t["cur"] while the cache still held the old flat dict, and the app
# died with a bare KeyError. Threading this constant through the cache key makes a
# shape change invalidate the cache instead of relying on a manual reboot.
_CACHE_V = 3

# A purchase = a SUCCEEDED payment that is not a refund or chargeback. Both filters are
# load-bearing: 14.9% of payment rows are not succeeded, and this dataset stores refunds
# and chargebacks as POSITIVE rows, so they would otherwise count as purchases.
PURCHASE = "t.status = 'succeeded' AND t.payment_type NOT IN ('refund','chargeback')"

# Ad spend is windowed on period_start only. period_end is unusable: on 1,482 of 2,000
# rows (74.1%, carrying $15.99M of $21.46M) it falls BEFORE period_start.
AD_DATE = "period_start"

ALL = "All channels"

# Selectable sources. Whitelisted rather than interpolated from user input.
#
# user.acquisition_channel also holds `content_seo` and `email`; both are deliberately
# not offered as individual selections. Their rows are still inside "All channels", so
# the all-up figures are unchanged -- they simply cannot be isolated from the UI.
CHANNELS = [
    "paid_search", "paid_social", "youtube_ads", "tiktok_ads",
    "organic_direct", "referral", "affiliate",
]

# marketing_campaign.channel carries only these. The three acquisition channels absent
# here -- organic_direct, referral, affiliate -- have revenue but structurally $0 ad
# spend, so MER is undefined for them and must blank with a reason (B2, B23). A fourth,
# `display`, has spend but no attributable users, so it only ever lands in the all-up
# figure.
SPEND_CHANNELS = {
    "paid_search", "paid_social", "youtube_ads", "tiktok_ads",
    "content_seo", "email", "display",
}


def has_spend(channel: str) -> bool:
    return channel == ALL or channel in SPEND_CHANNELS


@st.cache_resource
def client() -> bigquery.Client:
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    return bigquery.Client(credentials=creds, project=PROJECT_ID)


def _guard(channel: str) -> str:
    if channel != ALL and channel not in CHANNELS:
        raise ValueError(f"unknown channel {channel!r}")
    return channel


def _clauses(channel: str):
    """Returns (user-side join, user-side predicate, campaign-side join, predicate).

    Revenue, purchases, customers and support cost are attributed through
    `user.acquisition_channel`; ad spend through `marketing_campaign.channel`. Those are
    two different vocabularies that overlap on six values -- see SPEND_CHANNELS.
    """
    if channel == ALL:
        return "", "", "", ""
    uj = f"JOIN {D}.user` u ON u.user_id = t.user_id"
    up = f"AND u.acquisition_channel = '{channel}'"
    cj = f"JOIN {D}.marketing_campaign` mc ON mc.campaign_id = c.campaign_id"
    cp = f"AND mc.channel = '{channel}'"
    return uj, up, cj, cp


def _components_sql(days: int, channel: str) -> str:
    """Raw components for the current window and the equally-long window before it.

    Deltas are computed from these, never from a ratio scaled off a total (B3).
    """
    uj, up, cj, cp = _clauses(channel)
    return f"""
    WITH mx AS (SELECT DATE(MAX(occurred_at)) AS d1 FROM {D}.payment`),
    w AS (
      SELECT 'cur' AS per, DATE_SUB(d1, INTERVAL {days - 1} DAY) AS a, d1 AS b FROM mx
      UNION ALL
      SELECT 'pri', DATE_SUB(d1, INTERVAL {2 * days - 1} DAY),
                    DATE_SUB(d1, INTERVAL {days} DAY) FROM mx
    ), rev AS (
      SELECT w.per, SUM(t.recognized_amount_usd) AS gross,
             -SUM(t.refund_adjustment_usd) AS refunds,
             SUM(t.recognized_amount_usd + t.refund_adjustment_usd) AS net
      FROM {D}.revenue_recognition` t {uj}
      JOIN w ON t.recognized_month BETWEEN w.a AND w.b
      WHERE TRUE {up} GROUP BY 1
    ), pay AS (
      SELECT w.per, COUNT(*) AS purchases, COUNT(DISTINCT t.user_id) AS customers
      FROM {D}.payment` t {uj}
      JOIN w ON DATE(t.occurred_at) BETWEEN w.a AND w.b
      WHERE {PURCHASE} {up} GROUP BY 1
    ), ad AS (
      SELECT w.per, SUM(c.amount_usd) AS ad_spend
      FROM {D}.campaign_spend` c {cj}
      JOIN w ON c.{AD_DATE} BETWEEN w.a AND w.b
      WHERE TRUE {cp} GROUP BY 1
    ), sup AS (
      SELECT w.per, SUM(t.cost_usd) AS support_cost
      FROM {D}.support_ticket` t {uj}
      JOIN w ON DATE(t.created_at) BETWEEN w.a AND w.b
      WHERE TRUE {up} GROUP BY 1
    )
    SELECT w.per, w.a AS win_from, w.b AS win_to,
           rev.net, rev.gross, rev.refunds, pay.purchases, pay.customers,
           IFNULL(ad.ad_spend, 0) AS ad_spend, IFNULL(sup.support_cost, 0) AS support_cost
    FROM w JOIN rev USING(per) JOIN pay USING(per)
           LEFT JOIN ad USING(per) LEFT JOIN sup USING(per)
    """


def _derive(r) -> dict:
    """Derived measures, each guarding its denominator's SIGN and not just zero (Q3).

    5.3% of revenue_recognition rows net below zero, so a bare divide here can return a
    confident, flattering number rather than an obviously broken one.
    """
    net = float(r["net"])
    gross = float(r["gross"])
    ad = float(r["ad_spend"])
    sup = float(r["support_cost"])
    cm = net - ad - sup
    return {
        "net_revenue": net,
        "gross_revenue": gross,
        "refunds": float(r["refunds"]),
        "purchases": int(r["purchases"]),
        "customers": int(r["customers"]),
        "ad_spend": ad,
        "support_cost": sup,
        "cm": cm,
        "refund_pct": (100 * float(r["refunds"]) / gross) if gross > 0 else None,
        "cm_pct": (100 * cm / net) if net > 0 else None,
        # Undefined where the channel carries no ad spend at all (B2/B23) -- a channel
        # with revenue and zero spend is not infinitely efficient, it is unmeasurable.
        "mer": (net / ad) if ad > 0 else None,
    }


@st.cache_data(ttl=3600, show_spinner=False)
def _totals(days: int, channel: str, cache_v: int) -> dict:
    df = client().query(_components_sql(days, channel)).to_dataframe()
    cur = df[df["per"] == "cur"].iloc[0]
    pri = df[df["per"] == "pri"].iloc[0]
    out = {"cur": _derive(cur), "pri": _derive(pri)}
    out["d0"] = pd.to_datetime(cur["win_from"])
    out["d1"] = pd.to_datetime(cur["win_to"])
    out["p0"] = pd.to_datetime(pri["win_from"])
    out["p1"] = pd.to_datetime(pri["win_to"])
    return out


def totals(days: int, channel: str = ALL) -> dict:
    return _totals(days, _guard(channel), _CACHE_V)


@st.cache_data(ttl=3600, show_spinner=False)
def _daily(days: int, channel: str, cache_v: int) -> pd.DataFrame:
    """One row per calendar day, built off a date spine so a quiet day is a real zero
    (B19) rather than a gap the line would silently bridge. Ratios are computed inside
    each day, never scaled from the window total (B3)."""
    uj, up, cj, cp = _clauses(channel)
    sql = f"""
    WITH mx AS (SELECT DATE(MAX(occurred_at)) AS d1 FROM {D}.payment`),
    w AS (SELECT DATE_SUB(d1, INTERVAL {days - 1} DAY) AS a, d1 AS b FROM mx),
    spine AS (SELECT d FROM w, UNNEST(GENERATE_DATE_ARRAY(a, b)) AS d),
    rev AS (
      SELECT t.recognized_month AS d, SUM(t.recognized_amount_usd) AS gross,
             -SUM(t.refund_adjustment_usd) AS refunds,
             SUM(t.recognized_amount_usd + t.refund_adjustment_usd) AS net
      FROM {D}.revenue_recognition` t {uj} CROSS JOIN w
      WHERE t.recognized_month BETWEEN a AND b {up} GROUP BY 1
    ), pay AS (
      SELECT DATE(t.occurred_at) AS d, COUNT(*) AS purchases,
             COUNT(DISTINCT t.user_id) AS customers
      FROM {D}.payment` t {uj} CROSS JOIN w
      WHERE DATE(t.occurred_at) BETWEEN a AND b AND {PURCHASE} {up} GROUP BY 1
    ), ad AS (
      SELECT c.{AD_DATE} AS d, SUM(c.amount_usd) AS ad_spend
      FROM {D}.campaign_spend` c {cj} CROSS JOIN w
      WHERE c.{AD_DATE} BETWEEN a AND b {cp} GROUP BY 1
    ), sup AS (
      SELECT DATE(t.created_at) AS d, SUM(t.cost_usd) AS support_cost
      FROM {D}.support_ticket` t {uj} CROSS JOIN w
      WHERE DATE(t.created_at) BETWEEN a AND b {up} GROUP BY 1
    )
    SELECT spine.d,
      IFNULL(rev.net, 0)        AS net_revenue,
      IFNULL(pay.purchases, 0)  AS purchases,
      IFNULL(pay.customers, 0)  AS customers,
      IF(rev.gross > 0, 100 * rev.refunds / rev.gross, NULL) AS refund_pct,
      IF(rev.net > 0,
         100 * (rev.net - IFNULL(ad.ad_spend,0) - IFNULL(sup.support_cost,0)) / rev.net,
         NULL) AS cm_pct,
      IF(IFNULL(ad.ad_spend, 0) > 0, rev.net / ad.ad_spend, NULL) AS mer
    FROM spine LEFT JOIN rev USING(d) LEFT JOIN pay USING(d)
               LEFT JOIN ad USING(d) LEFT JOIN sup USING(d)
    ORDER BY d
    """
    df = client().query(sql).to_dataframe()
    # BigQuery DATE arrives as db_dtypes.dbdate, which has no datetime methods.
    df["d"] = pd.to_datetime(df["d"])
    for c in ("net_revenue", "purchases", "customers", "refund_pct", "cm_pct", "mer"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def daily(days: int, channel: str = ALL) -> pd.DataFrame:
    return _daily(days, _guard(channel), _CACHE_V)
