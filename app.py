import altair as alt
import pandas as pd
import streamlit as st

import data
import theme as th

st.set_page_config(page_title="DG — Data Guild", layout="wide")
st.markdown(th.css(), unsafe_allow_html=True)

if "view" not in st.session_state:
    st.session_state.view = "home"

WINDOWS = {"Last 30 days": 30, "Last 90 days": 90, "Last year": 365}


def fmt_money(v: float) -> str:
    """Unit chosen so a real value never prints as zero (B17)."""
    if abs(v) >= 1_000_000:
        return f"${v / 1_000_000:,.2f}M"
    if abs(v) >= 1_000:
        return f"${v / 1_000:,.0f}K"
    return f"${v:,.0f}"


def masthead() -> None:
    st.markdown(
        '<div class="dg-top"><span class="dg-mark">DG</span>'
        '<span class="dg-tag">Data Guild &nbsp;·&nbsp; analytics, in-house</span></div>',
        unsafe_allow_html=True,
    )


def completeness(d0, d1) -> None:
    st.markdown(
        f'<div class="dg-complete">Complete through <b>{d1:%d %B %Y}</b>. '
        f"This dataset ends there — every window below is measured back from it, "
        f"not from today.</div>",
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

    t = data.totals(days)
    d = data.daily(days)
    completeness(t["d0"], t["d1"])

    c1, c2, c3, c4 = st.columns(4, gap="small")

    with c1:
        st.markdown(th.tile(
            "Buyers", f"{t['buyers']:,}",
            f"unique · {days}d",
            th.spark(data.series(d, "buyers")["value"].tolist()),
        ), unsafe_allow_html=True)

    with c2:
        st.markdown(th.tile(
            "Net revenue", fmt_money(t["net_revenue"]),
            "recognised less refunds",
            th.spark(data.series(d, "net_revenue")["value"].tolist()),
        ), unsafe_allow_html=True)

    with c3:
        st.markdown(th.tile(
            "New subscriptions", f"{t['new_subs']:,}",
            f"started in window",
            th.spark(data.series(d, "new_subs")["value"].tolist()),
        ), unsafe_allow_html=True)

    with c4:
        # More is worse -> red (house rule), and a rate always shows its denominator (B1).
        rr = t["refund_rate"]
        st.markdown(th.tile(
            "Refund rate",
            f"{rr * 100:,.1f}%" if rr is not None else "–",
            (f"{fmt_money(t['refunds'])} of {fmt_money(t['gross_revenue'])} gross"
             if rr is not None else "gross revenue not positive"),
            value_color=th.BAD,
        ), unsafe_allow_html=True)

    with st.expander("What these four measure", expanded=False):
        st.markdown(f"""
**Buyers** — distinct users with a `succeeded` payment that is not a refund or chargeback.
Cannot be summed from the daily sparkline: a user buying on two days is one buyer.

**Net revenue** — `recognized_amount_usd` **plus** `refund_adjustment_usd`, which is stored
negative. Note `payment` uses the opposite convention, storing refunds as positive rows.

**New subscriptions** — rows in `subscription` started inside the window. Subscriptions, not
subscribers: {t['new_subs']:,} started, from fewer distinct users.

**Refund rate** — refunds ÷ gross recognised revenue, computed inside the window rather than
scaled from a total. Blank rather than shown if gross revenue is not positive.

**No period-over-period deltas anywhere on this page.** Buyers grow in every one of the 36
months on record, from 11 in Jun 2023 to 17,562 in May 2026 — so any "vs last period" figure
here would report the data generator, not performance. This is generated demo data.

**Not shown, deliberately:** credit-refund rate and affiliate conversion both split ~50/50,
which is a random generator rather than behaviour. Active MRR is a snapshot that would ignore
the window control above. Trial→paid conversion is biased down, because trials starting near
the window's end have not had time to convert.
""")

    st.markdown('<div class="dg-sec">Dashboards</div>', unsafe_allow_html=True)
    n1, n2, n3 = st.columns(3, gap="small")
    with n1:
        if st.button("Buyers  ›", key="nav_buyers", use_container_width=True):
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


# --------------------------------------------------------------- buyers
def buyers() -> None:
    masthead()
    if st.button("‹  Back", key="nav_home"):
        st.session_state.view = "home"
        st.rerun()

    days = 30
    t = data.totals(days)
    s = data.series(data.daily(days), "buyers")

    st.markdown('<div class="dg-h1">Buyers</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="dg-complete">{t["d0"]:%d %b %Y} – {t["d1"]:%d %b %Y} &nbsp;·&nbsp; '
        f'<b>{t["buyers"]:,}</b> unique buyers &nbsp;·&nbsp; '
        f"y-axis does not start at zero</div>",
        unsafe_allow_html=True,
    )

    axis_x = alt.Axis(format="%d %b", labelFontSize=13, grid=False,
                      labelColor=th.MUTED, tickColor=th.GRID, domainColor=th.GRID)
    axis_y = alt.Axis(labelFontSize=13, labelColor=th.MUTED, gridColor=th.GRID,
                      domain=False, ticks=False)

    line = alt.Chart(s).mark_line(
        strokeWidth=2, color=th.ACCENT, interpolate="linear"   # C36: no smoothing
    ).encode(
        x=alt.X("d:T", title=None, axis=axis_x),
        y=alt.Y("value:Q", title=None, axis=axis_y,
                scale=alt.Scale(zero=False, nice=True)),       # B6: labelled above
    )
    dots = alt.Chart(s).mark_point(               # C22: countable periods
        size=26, filled=True, color=th.ACCENT, opacity=1
    ).encode(
        x="d:T", y="value:Q",
        tooltip=[                                  # C13: whitelist, no internal columns
            alt.Tooltip("d:T", title="Day", format="%a %d %b %Y"),
            alt.Tooltip("value:Q", title="Buyers", format=","),
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
| unique buyers in the window | **{t['buyers']:,}** |
| sum of the daily values | {int(s['value'].sum()):,} |

The daily values cannot be summed — a user buying on two days appears in both, overstating
by {int(s['value'].sum()) - t['buyers']:,}.

The rise is a property of this generated dataset, not a result: buyers grow in every one of
the 36 months on record.
""")


{"home": home, "buyers": buyers}[st.session_state.view]()
