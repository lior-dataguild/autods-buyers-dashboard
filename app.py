from __future__ import annotations

import altair as alt
import streamlit as st

import data
import theme as th

st.set_page_config(page_title="DG — Data Guild", layout="wide",
                   initial_sidebar_state="expanded")
st.markdown(th.css(), unsafe_allow_html=True)
st.session_state.setdefault("ask", "")

WINDOWS = {"Last 30 days": 30, "Last 90 days": 90, "Last year": 365}
SOURCES = [data.ALL] + data.CHANNELS

QUESTIONS = [
    "How many buyers per day last month?",
    "Which plan holds the most subscribers?",
    "How did refund rate move this year?",
]

HOME = "Overview"
BUYERS = "Buyers"
GREETING = "Hello Michael"   # hardcoded: Community Cloud cannot tell us who is viewing

# Dashboards, grouped. Groups collapse so the whole suite is not on screen at once;
# the group holding the current page opens itself.
# Everything except Overview and Buyers is a placeholder name, not a commitment to what
# it will measure. Add a dashboard by putting it in a group and giving it a branch below.
GROUPS = {
    "Growth": [BUYERS, "Trials & conversion", "Acquisition channels",
               "Cohort retention"],
    "Revenue": ["Revenue & recognition", "MRR movements", "Subscriptions & churn",
                "Pricing & plans"],
    "Marketing": ["Campaign performance", "Channel efficiency", "Affiliates"],
    "Product": ["Feature adoption", "Credit consumption", "Store connections"],
    "Operations": ["Support load", "Refunds & chargebacks"],
    "Finance": ["Unit economics", "Contribution margin"],
}
NAV = [HOME] + [item for items in GROUPS.values() for item in items]

# Pages that actually consume the filters. A filter shown on a page it cannot move is
# worse than no filter, so the placeholders do not get one.
FILTERED = {HOME, BUYERS}


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


# ------------------------------------------------------------------ nav
st.session_state.setdefault("page", HOME)
page = st.session_state.page


def nav_item(name: str) -> None:
    """The active item renders as its own element rather than a button, so its state is
    explicit instead of inferred from a widget's internals."""
    if name == page:
        st.markdown(f'<div class="dg-navactive">{name}</div>', unsafe_allow_html=True)
    elif st.button(name, key=f"nav_{name}"):
        st.session_state.page = name
        st.rerun()


with st.sidebar:
    st.markdown('<span class="dg-navlogo">DG</span>', unsafe_allow_html=True)
    st.markdown('<div class="dg-navlabel">Dashboards</div>', unsafe_allow_html=True)
    nav_item(HOME)
    # Overview is a top-level item, not a group, so it needs its own separation from
    # the first group title -- without this the GROWTH chevron collides with the
    # bottom edge of Overview's highlight block.
    st.markdown('<div class="dg-navgap"></div>', unsafe_allow_html=True)
    for group, items in GROUPS.items():
        # The group holding the current page opens itself, so the nav always shows
        # where you are without needing to remember which group it was in.
        with st.expander(group, expanded=page in items):
            for item in items:
                nav_item(item)
    st.markdown(
        '<div class="dg-navlabel" style="margin-top:26px">Data</div>'
        f'<div class="dg-soon">{data.DATASET}</div>',
        unsafe_allow_html=True,
    )

st.markdown(f'<div class="dg-h1">{GREETING if page == HOME else page}</div>',
            unsafe_allow_html=True)

# ------------------------------------------------------------- filters
days, channel, t, d = None, data.ALL, None, None
if page in FILTERED:
    # The completeness line sits ABOVE the filters but reports the window the filters
    # choose, so its position is reserved here and filled once they have been read.
    line_slot = st.empty()

    # One line, packed left. Two columns only: adding a spacer column costs another
    # gap and renormalises the weights, which shrank BOTH filter columns instead of
    # absorbing the remainder. Measured needs are 276px and 725px; this split leaves
    # each comfortably clear, because an exact fit is not a fit.
    f1, f2 = st.columns([1, 2.9], gap="small")
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

    # The date is read from the data, never typed, so this line cannot go stale or
    # claim a completeness the dataset does not have.
    #
    # Deliberately NOT "Today is excluded": that phrasing says one partial day is
    # missing. This dataset stops 68 days before today, so it would understate the gap
    # by two months. "Everything after is excluded" is the same shape and true.
    line_slot.markdown(
        f'<div class="dg-complete">Complete through <b>{t["d1"]:%A %d %B %Y}</b>. '
        f"Everything after is excluded.</div>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="dg-rule"></div>', unsafe_allow_html=True)


# ----------------------------------------------------------------- pages
def overview() -> None:
    c, p = t["cur"], t["pri"]
    plabel = f"{days}d"
    spend_ok = data.has_spend(channel)
    no_spend = "no ad spend in this channel"

    spec = [
        ("Net revenue", money(c["net_revenue"]), c["net_revenue"], p["net_revenue"],
         "level", True, "net_revenue", ""),
        ("Refunds", pct(c["refund_pct"]), c["refund_pct"], p["refund_pct"],
         "rate", False, "refund_pct",
         f'{money(c["refunds"])} of {money(c["gross_revenue"])} gross'),
        ("CM %", pct(c["cm_pct"]), c["cm_pct"], p["cm_pct"], "rate", True, "cm_pct",
         f'{money(c["ad_spend"])} ad · {money(c["support_cost"])} support'
         if spend_ok else f"support cost only · {no_spend}"),
        # B4: a blank must say which gate stopped it. MER is undefined, not zero, on a
        # channel that carries revenue and no ad spend at all.
        ("MER", ratio(c["mer"]), c["mer"], p["mer"], "ratio", True, "mer",
         "" if spend_ok else no_spend),
        ("Purchases", f'{c["purchases"]:,}', c["purchases"], p["purchases"],
         "level", True, "purchases", ""),
        ("Customers", f'{c["customers"]:,}', c["customers"], p["customers"],
         "level", True, "customers", ""),
    ]
    for row in (spec[:3], spec[3:]):
        for col, (lab, val, cv, pv, kind, good, dcol, sub) in zip(
                st.columns(3, gap="small"), row):
            with col:
                blank = val == "–"
                st.markdown(th.kpi(
                    lab, '<span class="dg-blank">–</span>' if blank else val,
                    "" if blank else th.delta(cv, pv, kind, good, plabel),
                    "" if blank else th.spark(d[dcol].tolist()), sub,
                ), unsafe_allow_html=True)

    with st.expander("How these six are defined", expanded=False):
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
transactions, so reconciling against an orders table will fail — no such table exists.

**Source attributes through two different vocabularies.** Revenue, purchases, customers
and support cost use `user.acquisition_channel`; ad spend uses
`marketing_campaign.channel`. They overlap on six values. On organic direct, referral and
affiliate there is **no ad spend at all**, so MER blanks rather than dividing by zero, and
CM % labels itself "support cost only" because it is then not comparable with a channel
that carries ad cost.

**Ad spend is windowed on `period_start` alone.** `period_end` is unusable: on 1,482 of
2,000 rows (74.1%, carrying $15.99M of $21.46M) it falls *before* `period_start`.

**The window is measured back from the data's last day, not from today.** The dataset ends
{t['d1']:%d %b %Y}; a window anchored to the current date would return nothing. The delta
compares the selected window against the equally-long one immediately before it —
currently **{t['p0']:%d %b} – {t['p1']:%d %b %Y}**.

**Deltas** are in each metric's own unit — percent for levels, percentage points for rates,
absolute for MER — coloured by whether that direction is good for that metric, so refunds
falling is green.

**One fact about every rise here:** buyers grow in all 36 months on record, from 11 in
Jun 2023 to 17,562 in May 2026. This is generated demo data with a growth ramp.
""")

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


def buyers() -> None:
    st.markdown(
        f'<div class="dg-complete">{t["cur"]["customers"]:,} unique buyers &nbsp;·&nbsp; '
        f"y-axis does not start at zero</div>", unsafe_allow_html=True,
    )
    axis_x = alt.Axis(format="%d %b", labelFontSize=13, grid=False,
                      labelColor=th.MUTED, tickColor=th.GRID, domainColor=th.GRID)
    axis_y = alt.Axis(labelFontSize=13, labelColor=th.MUTED, gridColor=th.GRID,
                      domain=False, ticks=False)
    line = alt.Chart(d).mark_line(
        strokeWidth=2, color=th.ACCENT, interpolate="linear"      # C36: no smoothing
    ).encode(
        x=alt.X("d:T", title=None, axis=axis_x),
        y=alt.Y("customers:Q", title=None, axis=axis_y,
                scale=alt.Scale(zero=False, nice=True)),          # B6: stated on screen
    )
    dots = alt.Chart(d).mark_point(                                # C22: countable
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
        .properties(height=300, padding={"left": 0, "top": 6, "right": 16, "bottom": 0})
        .configure_view(strokeWidth=0).configure(background=th.BG),
        use_container_width=True,
    )
    with st.expander("Daily buyers", expanded=False):
        st.markdown(f"""
**Buyer** — a distinct `user_id` with a `succeeded` payment that is not a `refund` or
`chargeback`.

| | |
|---|---|
| unique buyers in the window | **{t['cur']['customers']:,}** |
| sum of the daily values | {int(d['customers'].sum()):,} |

The daily values cannot be summed — a user buying on two days appears in both, overstating
by {int(d['customers'].sum()) - t['cur']['customers']:,}.
""")


# Which tables each planned dashboard would draw on. Every table named here exists in
# the dataset -- the names are placeholders, but they are not pointing at nothing.
BACKING = {
    "Trials & conversion": "trial · subscription",
    "Acquisition channels": "user · campaign_spend",
    "Cohort retention": "user · subscription · payment",
    "Revenue & recognition": "revenue_recognition",
    "MRR movements": "subscription",
    "Subscriptions & churn": "subscription",
    "Pricing & plans": "plan · subscription",
    "Campaign performance": "marketing_campaign · campaign_spend",
    "Channel efficiency": "campaign_spend · revenue_recognition",
    "Affiliates": "affiliate · affiliate_referral",
    "Feature adoption": "credit_consumption_event",
    "Credit consumption": "credit_consumption_event · credit_purchase",
    "Store connections": "store_connection",
    "Support load": "support_ticket",
    "Refunds & chargebacks": "payment · revenue_recognition",
    "Unit economics": "revenue_recognition · campaign_spend · support_ticket",
    "Contribution margin": "revenue_recognition · campaign_spend · support_ticket",
}


def placeholder(name: str) -> None:
    st.markdown(
        f'<div class="dg-panel"><div class="dg-k">Not built</div>'
        f'<div class="dg-ph">“{name}” is a name in the navigation, not a commitment to '
        "what it will measure — that gets decided with you before anything is queried."
        f'</div><div class="dg-fl" style="margin:18px 0 5px">Would draw on</div>'
        f'<div class="dg-sub">{BACKING.get(name, "—")}</div></div>',
        unsafe_allow_html=True,
    )


if page == HOME:
    overview()
elif page == BUYERS:
    buyers()
else:
    placeholder(page)
