from __future__ import annotations

import altair as alt
import streamlit as st

import data
import theme as th

st.set_page_config(page_title="DG — Data Guild", layout="wide")
st.markdown(th.css(), unsafe_allow_html=True)
st.session_state.setdefault("ask", "")

WINDOWS = {"Last 30 days": 30, "Last 90 days": 90, "Last year": 365}
SOURCES = [data.ALL] + data.CHANNELS

QUESTIONS = [
    "How many buyers per day last month?",
    "Which plan holds the most subscribers?",
    "How did refund rate move this year?",
]

# Names are placeholders except Buyers, which is real. Nothing behind the others yet.
TABS = ["Buyers", "Revenue & recognition", "Trials & conversion",
        "Subscriptions & churn", "Support load", "Affiliates"]


def money(v) -> str:
    """Unit chosen so a real value never prints as zero (B17)."""
    if v is None:
        return "–"
    if abs(v) >= 1_000_000:
        return f"${v / 1_000_000:,.2f}M"
    if abs(v) >= 1_000:
        return f"${v / 1_000:,.0f}K"
    return f"${v:,.0f}"


def pct(v) -> str:
    return "–" if v is None else f"{v:,.1f}%"


def ratio(v) -> str:
    return "–" if v is None else f"{v:,.2f}"


def kpis(days: int, channel: str, t: dict, d) -> None:
    c, p = t["cur"], t["pri"]
    plabel = f"{days}d"
    spend_ok = data.has_spend(channel)
    no_spend_note = "no ad spend in this channel"

    # (label, value, cur, pri, delta kind, up_is_good, daily column, sub)
    spec = [
        ("Net revenue", money(c["net_revenue"]), c["net_revenue"], p["net_revenue"],
         "level", True, "net_revenue", ""),
        ("Refunds", pct(c["refund_pct"]), c["refund_pct"], p["refund_pct"],
         "rate", False, "refund_pct",
         f'{money(c["refunds"])} of {money(c["gross_revenue"])} gross'),
        ("CM %", pct(c["cm_pct"]), c["cm_pct"], p["cm_pct"],
         "rate", True, "cm_pct",
         f'{money(c["ad_spend"])} ad · {money(c["support_cost"])} support'
         if spend_ok else f"support cost only · {no_spend_note}"),
        # B4: a blank must say which gate stopped it. MER is undefined, not zero, where
        # a channel carries revenue and no ad spend at all.
        ("MER", ratio(c["mer"]), c["mer"], p["mer"],
         "ratio", True, "mer", "" if spend_ok else no_spend_note),
        ("Purchases", f'{c["purchases"]:,}', c["purchases"], p["purchases"],
         "level", True, "purchases", ""),
        ("Customers", f'{c["customers"]:,}', c["customers"], p["customers"],
         "level", True, "customers", ""),
    ]

    for row in (spec[:3], spec[3:]):
        cols = st.columns(3, gap="small")
        for col, (lab, val, cv, pv, kind, good, dcol, sub) in zip(cols, row):
            with col:
                blank = val == "–"
                st.markdown(th.kpi(
                    lab,
                    f'<span class="dg-blank">–</span>' if blank else val,
                    "" if blank else th.delta(cv, pv, kind, good, plabel),
                    "" if blank else th.spark(d[dcol].tolist()),
                    sub,
                ), unsafe_allow_html=True)


def buyers_chart(t: dict, s) -> None:
    st.markdown(
        f'<div class="dg-complete">{t["d0"]:%d %b %Y} – {t["d1"]:%d %b %Y} &nbsp;·&nbsp; '
        f'<b>{t["cur"]["customers"]:,}</b> unique buyers &nbsp;·&nbsp; '
        f"y-axis does not start at zero</div>",
        unsafe_allow_html=True,
    )
    axis_x = alt.Axis(format="%d %b", labelFontSize=13, grid=False,
                      labelColor=th.MUTED, tickColor=th.GRID, domainColor=th.GRID)
    axis_y = alt.Axis(labelFontSize=13, labelColor=th.MUTED, gridColor=th.GRID,
                      domain=False, ticks=False)
    line = alt.Chart(s).mark_line(
        strokeWidth=2, color=th.ACCENT, interpolate="linear"      # C36: no smoothing
    ).encode(
        x=alt.X("d:T", title=None, axis=axis_x),
        y=alt.Y("customers:Q", title=None, axis=axis_y,
                scale=alt.Scale(zero=False, nice=True)),          # B6: stated on screen
    )
    dots = alt.Chart(s).mark_point(                                # C22: countable
        size=26, filled=True, color=th.ACCENT, opacity=1
    ).encode(
        x="d:T", y="customers:Q",
        tooltip=[                                # C13: whitelist, no internal columns
            alt.Tooltip("d:T", title="Day", format="%a %d %b %Y"),
            alt.Tooltip("customers:Q", title="Buyers", format=","),
        ],
    )
    st.altair_chart(
        (line + dots)
        .properties(height=280, padding={"left": 0, "top": 6, "right": 16, "bottom": 0})
        .configure_view(strokeWidth=0).configure(background=th.BG),
        use_container_width=True,
    )


# ---------------------------------------------------------------- page
st.markdown(
    '<div class="dg-top"><span class="dg-mark">DG</span>'
    '<span class="dg-tag">Data Guild &nbsp;·&nbsp; analytics, in-house</span></div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="dg-h1">Hello Lior</div>', unsafe_allow_html=True)

f1, f2 = st.columns([1, 1.55], gap="large")
with f1:
    st.markdown('<div class="dg-fl">Date range</div>', unsafe_allow_html=True)
    wlabel = st.radio("Date range", list(WINDOWS), horizontal=True,
                      label_visibility="collapsed")
with f2:
    st.markdown('<div class="dg-fl">Source</div>', unsafe_allow_html=True)
    channel = st.radio("Source", SOURCES, horizontal=True,
                       label_visibility="collapsed",
                       format_func=lambda s: s.replace("_", " "))

days = WINDOWS[wlabel]
t = data.totals(days, channel)
d = data.daily(days, channel)

st.markdown(
    f'<div class="dg-complete">Complete through <b>{t["d1"]:%d %B %Y}</b>. Today is '
    f"excluded — this dataset ends there, so every window is measured back from it. "
    f'Prior period: {t["p0"]:%d %b} – {t["p1"]:%d %b %Y}.</div>',
    unsafe_allow_html=True,
)

# C8: the caveat is a tap target, never a hover-only title= attribute.
with st.expander("ⓘ  What the date range and source do", expanded=False):
    st.markdown(f"""
**Date range** is measured back from the data's last day ({t['d1']:%d %b %Y}), not from
today, and the delta compares it against the equally-long window immediately before.

**Source** is `user.acquisition_channel` for revenue, purchases, customers and support
cost, and `marketing_campaign.channel` for ad spend. Those are two different vocabularies
that overlap on six values only:

| | |
|---|---|
| revenue **and** ad spend | paid search · paid social · youtube ads · tiktok ads · content seo · email |
| revenue, **no** ad spend | organic direct · referral · affiliate |
| ad spend, no attributed users | display — only ever inside "All channels" |

On the three channels with no ad spend, **MER is blank rather than a number** — a channel
earning revenue on zero spend is unmeasurable, not infinitely efficient. CM % still shows,
because a channel with no ad cost genuinely has none, but it is then not comparable with
channels that carry one.
""")

st.markdown('<div class="dg-rule"></div>', unsafe_allow_html=True)

kpis(days, channel, t, d)

with st.expander("How these six are defined", expanded=False):
    c = t["cur"]
    st.markdown(f"""
| | |
|---|---|
| Net revenue | `recognized_amount_usd` **+** `refund_adjustment_usd` (stored negative). `payment` uses the opposite convention. |
| Refunds | refunds ÷ gross recognised revenue |
| CM % | (net revenue − ad spend − support cost) ÷ net revenue |
| MER | net revenue ÷ ad spend |
| Purchases | `succeeded` payment rows that are not refunds or chargebacks |
| Customers | distinct users behind those purchases |

**CM % is an upper bound, not a true contribution margin.** Ad spend and support cost are
the only variable costs this dataset carries — there is no COGS or payment-processing
table, so real contribution margin is lower by whatever those would add.

**"Purchases", not "Orders".** Subscription SaaS has no order entity; this counts purchase
transactions, so reconciling it against an orders table will fail — no such table exists.

**Ad spend is windowed on `period_start` alone.** `period_end` is unusable: on 1,482 of
2,000 rows (74.1%, carrying $15.99M of $21.46M) it falls *before* `period_start`. MER and
CM % both inherit that.

**Deltas** are in each metric's own unit — percent for levels, percentage points for rates,
absolute for MER — and the arrow is coloured by whether that direction is good for that
metric, so refunds falling is green.

**One fact about every rise here:** buyers grow in all 36 months on record, from 11 in
Jun 2023 to 17,562 in May 2026. This is generated demo data with a growth ramp.
""")

# ---- ask the data (layout per the reference; not connected to a query engine) ----
st.markdown('<div class="dg-ask">Ask the data</div>', unsafe_allow_html=True)
st.text_input(
    "Ask the data", key="ask", label_visibility="collapsed",
    placeholder='What do you want to know today? Ask in your own words — add "chart" for a picture.',
)
for col, q in zip(st.columns(len(QUESTIONS), gap="small"), QUESTIONS):
    with col:
        if st.button(q, key=f"q_{q[:18]}"):
            st.session_state.ask = q
            st.rerun()
if st.session_state.ask:
    st.caption(
        "Natural-language querying is not wired up yet — this box is layout only. "
        "Ask me in chat and I will write the query."
    )

# ---- dashboards, as tabs at the foot of the page ----
st.markdown('<div class="dg-rule"></div>', unsafe_allow_html=True)
st.markdown('<div class="dg-sec">Dashboards</div>', unsafe_allow_html=True)

tabs = st.tabs(TABS)
with tabs[0]:
    buyers_chart(t, d)
for i, name in enumerate(TABS[1:], start=1):
    with tabs[i]:
        st.markdown(
            f'<div class="dg-card" style="margin-top:8px"><div class="dg-k">{name}</div>'
            '<div class="dg-sub">placeholder — this dashboard is not built. The name is '
            "a stand-in, not a commitment to what it will measure.</div></div>",
            unsafe_allow_html=True,
        )
