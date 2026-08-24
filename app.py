from __future__ import annotations

import altair as alt
import streamlit as st

import data
import theme as th

st.set_page_config(page_title="DG — Data Guild", layout="wide")
st.markdown(th.css(), unsafe_allow_html=True)

st.session_state.setdefault("view", "home")
st.session_state.setdefault("ask", "")

WINDOWS = {"Last 30 days": 30, "Last 90 days": 90, "Last year": 365}

QUESTIONS = [
    "How many buyers per day last month?",
    "Which plan holds the most subscribers?",
    "How did refund rate move this year?",
]


def money(v: float) -> str:
    """Unit chosen so a real value never prints as zero (B17)."""
    if v is None:
        return "–"
    if abs(v) >= 1_000_000:
        return f"${v / 1_000_000:,.2f}M"
    if abs(v) >= 1_000:
        return f"${v / 1_000:,.0f}K"
    return f"${v:,.0f}"


def pct(v: float) -> str:
    return "–" if v is None else f"{v:,.1f}%"


def ratio(v: float) -> str:
    return "–" if v is None else f"{v:,.2f}"


def masthead() -> None:
    st.markdown(
        '<div class="dg-top"><span class="dg-mark">DG</span>'
        '<span class="dg-tag">Data Guild &nbsp;·&nbsp; analytics, in-house</span></div>',
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------- home
def home() -> None:
    masthead()
    st.markdown('<div class="dg-h1">Welcome</div>', unsafe_allow_html=True)

    st.markdown('<div class="dg-fl">Window</div>', unsafe_allow_html=True)
    label = st.radio("Window", list(WINDOWS), horizontal=True,
                     label_visibility="collapsed")
    days = WINDOWS[label]
    plabel = f"{days}d"

    t = data.totals(days)
    d = data.daily(days)
    c, p = t["cur"], t["pri"]

    st.markdown(
        f'<div class="dg-complete">Complete through <b>{t["d1"]:%d %B %Y}</b>. '
        f"This dataset ends there — every window is measured back from it, not from "
        f'today. Prior period: {t["p0"]:%d %b} – {t["p1"]:%d %b %Y}.</div>',
        unsafe_allow_html=True,
    )

    # (label, value, cur, pri, delta kind, up_is_good, daily column)
    SPEC = [
        ("Net revenue",  money(c["net_revenue"]), c["net_revenue"], p["net_revenue"],
         "level", True,  "net_revenue"),
        ("Refunds",      pct(c["refund_pct"]),    c["refund_pct"],  p["refund_pct"],
         "rate",  False, "refund_pct"),
        ("CM %",         pct(c["cm_pct"]),        c["cm_pct"],      p["cm_pct"],
         "rate",  True,  "cm_pct"),
        ("MER",          ratio(c["mer"]),         c["mer"],         p["mer"],
         "ratio", True,  "mer"),
        ("Purchases",    f'{c["purchases"]:,}',   c["purchases"],   p["purchases"],
         "level", True,  "purchases"),
        ("Customers",    f'{c["customers"]:,}',   c["customers"],   p["customers"],
         "level", True,  "customers"),
    ]

    for row in (SPEC[:3], SPEC[3:]):
        cols = st.columns(3, gap="small")
        for col, (lab, val, cv, pv, kind, good, dcol) in zip(cols, row):
            with col:
                st.markdown(th.kpi(
                    lab, val,
                    th.delta(cv, pv, kind, good, plabel),
                    th.spark(d[dcol].tolist()),
                ), unsafe_allow_html=True)

    with st.expander("How these six are defined", expanded=False):
        st.markdown(f"""
| | |
|---|---|
| Net revenue | `recognized_amount_usd` **+** `refund_adjustment_usd` (stored negative). `payment` uses the opposite convention. |
| Refunds | refunds ÷ gross recognised revenue — {money(c['refunds'])} of {money(c['gross_revenue'])} |
| CM % | (net revenue − ad spend − support cost) ÷ net revenue — {money(c['ad_spend'])} ad, {money(c['support_cost'])} support |
| MER | net revenue ÷ ad spend |
| Purchases | `succeeded` payment rows that are not refunds or chargebacks |
| Customers | distinct users behind those purchases |

**CM % is an upper bound, not a true contribution margin.** The only variable costs this
dataset carries are ad spend and support cost. There is no COGS or payment-processing
table, so real contribution margin is lower than the figure shown by however much those
would add.

**"Purchases", not "Orders".** This is subscription SaaS — there is no order entity. The
count is purchase transactions, so reconciling it against an orders table will fail
because no such table exists.

**Ad spend is windowed on `period_start` alone.** `period_end` is unusable: on 1,482 of
2,000 rows (74.1%, carrying $15.99M of $21.46M) it falls *before* `period_start`. MER and
CM % both inherit that limitation.

**Deltas compare the {plabel} window against the {plabel} immediately before it**, in each
metric's own unit — percent for levels, percentage points for rates, absolute for MER —
and the arrow is coloured by whether that direction is good for that metric, so refunds
falling is green.

**One fact about every rise on this page:** buyers grow in all 36 months on record, from 11
in Jun 2023 to 17,562 in May 2026. This is generated demo data with a growth ramp, so the
positive deltas describe the generator as much as the business.
""")

    # ---- ask the data (visual per request; not connected to a query engine) ----
    st.markdown('<div class="dg-ask">Ask the data</div>', unsafe_allow_html=True)
    st.text_input(
        "Ask the data", key="ask", label_visibility="collapsed",
        placeholder='What do you want to know today? Ask in your own words — add "chart" for a picture.',
    )
    qcols = st.columns(len(QUESTIONS), gap="small")
    for col, q in zip(qcols, QUESTIONS):
        with col:
            if st.button(q, key=f"q_{q[:18]}"):
                st.session_state.ask = q
                st.rerun()
    if st.session_state.ask:
        st.caption(
            "Natural-language querying is not wired up yet — this box is layout only. "
            "Ask me in chat and I will write the query."
        )

    st.markdown('<div class="dg-sec">Dashboards</div>', unsafe_allow_html=True)
    st.markdown('<div class="dg-navrow">', unsafe_allow_html=True)
    n1, n2, n3 = st.columns(3, gap="small")
    with n1:
        if st.button("Buyers  ›", key="nav_buyers"):
            st.session_state.view = "buyers"
            st.rerun()
    with n2:
        st.markdown('<div class="dg-card" style="min-height:62px"><div class="dg-k">&nbsp;</div>'
                    '<div class="dg-sub">next dashboard — not built</div></div>',
                    unsafe_allow_html=True)
    with n3:
        st.markdown('<div class="dg-card" style="min-height:62px"><div class="dg-k">&nbsp;</div>'
                    '<div class="dg-sub">next dashboard — not built</div></div>',
                    unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# --------------------------------------------------------------- buyers
def buyers() -> None:
    masthead()
    if st.button("‹  Back", key="nav_home"):
        st.session_state.view = "home"
        st.rerun()

    days = 30
    t = data.totals(days)
    s = data.daily(days)

    st.markdown('<div class="dg-h1">Buyers</div>', unsafe_allow_html=True)
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
        tooltip=[                                    # C13: whitelist, no internal columns
            alt.Tooltip("d:T", title="Day", format="%a %d %b %Y"),
            alt.Tooltip("customers:Q", title="Buyers", format=","),
        ],
    )

    st.altair_chart(
        (line + dots)
        .properties(height=300, padding={"left": 0, "top": 6, "right": 16, "bottom": 0})
        .configure_view(strokeWidth=0)
        .configure(background=th.BG),
        use_container_width=True,
    )

    with st.expander("Daily buyers", expanded=False):
        st.markdown(f"""
**Buyer** — a distinct `user_id` with a `succeeded` payment that is not a `refund` or
`chargeback`.

| | |
|---|---|
| unique buyers in the window | **{t['cur']['customers']:,}** |
| sum of the daily values | {int(s['customers'].sum()):,} |

The daily values cannot be summed — a user buying on two days appears in both, overstating
by {int(s['customers'].sum()) - t['cur']['customers']:,}.

The rise is a property of this generated dataset, not a result: buyers grow in every one of
the 36 months on record.
""")


{"home": home, "buyers": buyers}[st.session_state.view]()
