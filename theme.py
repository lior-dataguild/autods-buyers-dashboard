from __future__ import annotations   # local venv is 3.9; PEP 604 unions are 3.10+

"""Cyber palette + shared CSS for the DG dashboard suite.

Dark ground with a single accent is the most literal reading of "the data is the only
thing at full contrast" -- so the cyber look and the house style agree here rather than
fighting. No glow: a blurred stroke makes a point's position ambiguous, which spends
precision on decoration.
"""

BG = "#0B0F14"
PANEL = "#0E141B"
BORDER = "#1B242E"
BORDER_SOFT = "#151C24"
ACCENT = "#22D3EE"     # the one accent; carries the data
GOOD = "#34D399"       # a movement in the good direction, per metric
BAD = "#F87171"        # a movement in the bad direction, per metric
TEXT = "#E6EDF3"
MUTED = "#93A1B0"      # lifted from #7D8A99 -- body text was too dim on this ground
DIM = "#6B7A8A"        # lifted from #5B6B7C -- sublabels were barely legible
GRID = "#18202A"

# Filter chips need more contrast than ordinary muted text: they are controls, and an
# unreadable control is worse than an ugly one.
CHIP_TEXT = "#B6C2CF"
CHIP_EDGE = "#2A3542"
CHIP_EDGE_HOVER = "#3D4B5C"

MONO = 'ui-monospace,"SF Mono",Menlo,monospace'


def css() -> str:
    return f"""
<style>
  .stApp, [data-testid="stAppViewContainer"] {{ background:{BG}; }}
  [data-testid="stHeader"] {{ background:{BG}; }}
  /* Streamlit's header floats over the container, so the masthead needs clearance
     or its first line is clipped at the viewport edge. */
  .block-container {{ padding-top:3.6rem; padding-bottom:2rem; max-width:1500px; }}
  [data-testid="stVerticalBlock"] {{ gap:0.35rem !important; }}

  /* Masthead is the wordmark alone -- the tagline it used to carry said nothing a
     reader of this page needs, and competed with the greeting directly beneath it. */
  .dg-top {{ padding-bottom:15px; border-bottom:1px solid {BORDER_SOFT};
             margin-bottom:22px; }}
  .dg-logo {{ font-family:{MONO}; font-size:30px; font-weight:700;
              letter-spacing:.16em; color:{ACCENT}; line-height:1;
              display:inline-block; }}

  .dg-h1 {{ font-size:27px; font-weight:600; color:{TEXT};
            margin:0 0 4px; padding-bottom:16px; }}
  .dg-complete {{ font-family:{MONO}; font-size:12px; color:{MUTED};
                 margin:0; padding-bottom:20px; }}
  .dg-complete b {{ color:#A8B6C4; font-weight:600; }}

  .dg-sec {{ font-size:10px; letter-spacing:.13em; text-transform:uppercase;
             color:{ACCENT}; font-weight:700; margin:28px 0 0;
             padding-bottom:14px; }}
  .dg-fl {{ font-size:10px; letter-spacing:.1em; text-transform:uppercase;
            color:{DIM}; margin:0; padding-bottom:18px; }}
  .dg-rule {{ height:1px; background:{BORDER_SOFT}; margin:22px 0 20px; }}
  .dg-blank {{ font-size:16px; font-weight:600; color:#3A4653; }}
  .dg-navgap {{ height:4px; }}

  /* --- sidebar navigation -------------------------------------------------
     Scoped by ancestor, so the main page's chip rules cannot leak in and the
     ancestor selector wins on specificity without !important gymnastics. If the
     scoping ever fails the nav merely looks like chips -- ugly, never broken. */
  section[data-testid="stSidebar"] {{ background:{PANEL};
      border-right:1px solid {BORDER_SOFT}; }}
  section[data-testid="stSidebar"] .block-container,
  section[data-testid="stSidebar"] > div {{ padding-top:1.4rem; }}
  .dg-navlogo {{ font-family:{MONO}; font-size:24px; font-weight:700;
      letter-spacing:.16em; color:{ACCENT}; line-height:1;
      padding:0 14px 4px; display:block; }}
  .dg-navlabel {{ font-size:10px; letter-spacing:.13em; text-transform:uppercase;
      color:{DIM}; padding:0 14px 22px; margin:24px 0 0; }}
  /* Nav items are buttons, so the active one can be rendered as its own element and
     styled without fighting a widget's internal state. */
  section[data-testid="stSidebar"] .stButton > button {{
      width:100% !important; text-align:left !important;
      border:0 !important; border-left:2px solid transparent !important;
      border-radius:0 !important; padding:8px 12px 8px 12px !important;
      background:transparent !important; color:{CHIP_TEXT} !important;
      font-size:13px !important; font-weight:400 !important; min-height:0 !important;
      justify-content:flex-start !important; }}
  section[data-testid="stSidebar"] .stButton > button:hover {{
      background:rgba(255,255,255,.04) !important; color:{TEXT} !important;
      border-left-color:{CHIP_EDGE_HOVER} !important; }}
  .dg-navactive {{ border-left:2px solid {ACCENT}; background:rgba(34,211,238,.09);
      padding:8px 12px 8px 12px; font-size:13px; font-weight:600; color:{ACCENT}; }}

  /* Group headers: tap to open. Collapsed by default so the whole suite is not on
     screen at once. */
  section[data-testid="stSidebar"] [data-testid="stExpander"] {{
      margin:22px 0 0 !important; border:0 !important; }}
  section[data-testid="stSidebar"] [data-testid="stExpander"] summary {{
      padding:8px 14px 11px !important; }}
  section[data-testid="stSidebar"] [data-testid="stExpander"] summary p {{
      font-size:10px !important; letter-spacing:.13em; text-transform:uppercase;
      font-weight:700 !important; color:{DIM} !important; }}
  section[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover p {{
      color:{CHIP_TEXT} !important; }}
  section[data-testid="stSidebar"] [data-testid="stExpander"] details > div {{
      padding:0 !important; }}
  section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
      gap:0 !important; }}
  .dg-soon {{ font-size:11px; color:{DIM}; padding:0 14px; margin-top:3px; }}

  /* Bottom dashboard tabs */
  [data-testid="stTabs"] [data-baseweb="tab-list"] {{ gap:4px; border-bottom:1px solid {BORDER_SOFT}; }}
  [data-testid="stTabs"] [data-baseweb="tab"] {{
      background:transparent; border-radius:6px 6px 0 0; padding:8px 15px;
      color:{MUTED}; font-size:13px; }}
  [data-testid="stTabs"] [aria-selected="true"] {{
      color:{ACCENT} !important; background:{PANEL}; }}
  [data-testid="stTabs"] [data-baseweb="tab-highlight"] {{ background:{ACCENT}; }}

  /* A panel is the same surface as a KPI card, for content that is not a metric --
     so a chart and a tile read as the same kind of object. */
  .dg-panel {{ border:1px solid {BORDER}; border-radius:7px; padding:17px 19px 19px;
               background:{PANEL}; }}
  .dg-ph {{ font-size:13px; color:{MUTED}; margin-top:7px; max-width:62ch;
            line-height:1.55; }}

  /* --- KPI tile --- */
  .dg-card {{ border:1px solid {BORDER}; border-radius:7px; padding:15px 17px 13px;
              background:{PANEL}; height:100%; }}
  /* Fixed-height slots so every card is the same height and the six sparklines sit on
     one baseline across both rows. */
  .dg-dslot {{ min-height:19px; }}
  .dg-sparkslot {{ min-height:44px; }}
  .dg-k {{ font-size:12px; color:{MUTED}; margin:0; padding-bottom:11px; }}
  .dg-v {{ font-size:31px; font-weight:700; color:{TEXT}; letter-spacing:-.015em;
           line-height:1.08; }}
  .dg-d {{ font-size:11.5px; margin-top:6px; font-weight:600; }}
  .dg-d span {{ color:{DIM}; font-weight:400; }}
  .dg-sub {{ font-family:{MONO}; font-size:11px; color:{DIM}; margin-top:5px;
             min-height:15px; }}
  .dg-spark {{ display:block; margin-top:10px; }}

  /* --- filter chips: a real control, it moves every tile --- */
  div[role="radiogroup"] {{ gap:6px !important; }}
  div[role="radiogroup"] label {{
      border:1px solid {CHIP_EDGE}; border-radius:99px; padding:5px 11px;
      background:transparent; font-size:12px; margin:0 !important; }}
  /* Hide the selection dot. It says nothing the border and text colour do not already
     say, and it costs a third of the chip's width. Streamlit's class rules outrank a
     bare selector, hence !important.
     Every rule here is guarded with :not(:has(p)) so it can only ever match a box that
     does NOT contain the chip's text. An earlier version matched [data-baseweb="radio"]
     outright, which is harmless on the Streamlit build in this venv but wraps the whole
     chip -- text included -- on the newer build Cloud runs, and blanked every chip
     there. Never hide a container by structure alone when a text-bearing one can take
     the same shape. */
  div[role="radiogroup"] label > div:first-child:not(:has(p)) {{ display:none !important; }}
  div[role="radiogroup"] label input {{ display:none !important; }}
  /* Fallback for a nested structure where the dot is not a direct child: strip its
     paint rather than its box. Harmless if it lands on a wrapper that was never
     painted, and it can never blank the label. */
  div[role="radiogroup"] label div:not(:has(p)) {{
      background:transparent !important; box-shadow:none !important;
      border-color:transparent !important; }}
  /* The <p> carries its own colour, so setting it on the label does nothing. */
  div[role="radiogroup"] label p {{
      font-size:12px !important; color:{CHIP_TEXT} !important; }}
  div[role="radiogroup"] label:hover {{ border-color:{CHIP_EDGE_HOVER}; }}
  div[role="radiogroup"] label:hover p {{ color:{TEXT} !important; }}
  div[role="radiogroup"] label:has(input:checked) {{
      border-color:{ACCENT}; background:rgba(34,211,238,.10); }}
  div[role="radiogroup"] label:has(input:checked) p {{
      color:{ACCENT} !important; font-weight:600 !important; }}

  /* --- ask the data --- */
  .dg-ask {{ font-size:15px; font-weight:600; color:{TEXT};
             margin:0; padding-bottom:19px; }}
  [data-testid="stTextInput"] input {{
      background:{PANEL} !important; border:1px solid #1E2833 !important;
      border-radius:7px !important; color:{TEXT} !important;
      font-size:13px !important; padding:11px 14px !important; }}
  [data-testid="stTextInput"] input::placeholder {{ color:{DIM} !important; }}

  /* --- buttons: nav cards and suggestion chips --- */
  /* Suggestion chips hug their own text, as in the reference -- a chip stretched to a
     column width stops reading as a chip. */
  .stButton > button {{
      background:{PANEL}; border:1px solid {BORDER}; border-radius:99px;
      padding:6px 15px; color:{MUTED}; font-size:12px; font-weight:400;
      width:auto; min-height:0; }}
  .stButton > button:hover {{ border-color:{ACCENT}; color:{ACCENT}; background:{PANEL}; }}
  .dg-navrow .stButton > button {{
      border-radius:7px; padding:14px 16px; min-height:62px; width:100%;
      color:{TEXT}; font-size:14px; font-weight:600; text-align:left; }}

  [data-testid="stExpander"] {{ border:0 !important; background:none !important;
      margin-top:16px; }}
  [data-testid="stExpander"] details {{ background:none !important; border:0 !important; }}
  /* Streamlit animates the expander with an explicit height + overflow:hidden; when
     that animation does not run the content stays clipped to the summary. */
  [data-testid="stExpander"] details[open] {{ height:auto !important; overflow:visible !important; }}
  [data-testid="stExpander"] summary {{ padding:0 !important; }}
  [data-testid="stExpander"] summary p {{ font-size:.82rem; font-weight:600; color:{TEXT}; }}
  [data-testid="stExpander"] p, [data-testid="stExpander"] li,
  [data-testid="stExpander"] td, [data-testid="stExpander"] th {{ color:{MUTED}; }}
</style>
"""


def spark(vals, w: int = 200, h: int = 34, color: str | None = None) -> str:
    """Direction only, never level (C21): scaled to the series' own min and max.

    Two tiles 10x apart therefore show the same amplitude. That is correct -- level is
    the job of the number printed above it. Segments are straight (C36): a curve would
    assert values between days nobody measured.
    """
    vals = [None if v is None or v != v else float(v) for v in vals]
    real = [v for v in vals if v is not None]
    if len(real) < 2:
        return '<div class="dg-sub">–</div>'          # C23: too few points is a state
    c = color or ACCENT
    lo, hi = min(real), max(real)
    span = (hi - lo) or 1.0
    step = w / (len(vals) - 1)

    # A day that was never measured breaks the line rather than being bridged (C37).
    segs, cur = [], []
    for i, v in enumerate(vals):
        if v is None:
            if len(cur) > 1:
                segs.append(cur)
            cur = []
            continue
        cur.append(f"{i * step:.1f},{h - 2 - (v - lo) / span * (h - 6):.1f}")
    if len(cur) > 1:
        segs.append(cur)

    # A faint fill under the line, as in the reference. It carries no extra information,
    # so it stays well below the stroke in contrast -- the line is still the data.
    rgb = ",".join(str(int(c.lstrip("#")[i:i + 2], 16)) for i in (0, 2, 4))
    fills = "".join(
        f'<polygon points="{s[0].split(",")[0]},{h} {" ".join(s)} '
        f'{s[-1].split(",")[0]},{h}" fill="rgba({rgb},0.13)" stroke="none"/>'
        for s in segs
    )
    paths = fills + "".join(
        f'<polyline points="{" ".join(s)}" fill="none" stroke="{c}" '
        f'stroke-width="1.7" stroke-linejoin="round"/>' for s in segs
    )
    last_i = max(i for i, v in enumerate(vals) if v is not None)
    lx = last_i * step
    ly = h - 2 - (vals[last_i] - lo) / span * (h - 6)
    return (
        f'<svg class="dg-spark" viewBox="0 0 {w + 5} {h}" width="100%" height="{h}" '
        f'preserveAspectRatio="none" role="img" aria-hidden="true">{paths}'
        f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="2.3" fill="{c}"/></svg>'
    )


def delta(cur, pri, kind: str, up_is_good: bool, period_label: str) -> str:
    """The change in the unit that belongs to the metric, coloured by whether the
    movement is good for THIS metric (C33).

    kind 'level' -> percent · 'rate' -> percentage points · 'ratio' -> absolute units.
    Direction is declared per metric, never inferred from the sign: refunds rising is
    bad, revenue rising is good, and the arrow must not imply otherwise.
    """
    if cur is None or pri is None:
        return f'<div class="dg-d"><span>no comparable prior {period_label}</span></div>'
    if kind == "level":
        if pri <= 0:
            return f'<div class="dg-d"><span>prior {period_label} not positive</span></div>'
        diff, txt = cur - pri, f"{abs(cur / pri - 1) * 100:,.1f}%"
    elif kind == "rate":
        diff, txt = cur - pri, f"{abs(cur - pri):,.2f}pp"
    else:
        diff, txt = cur - pri, f"{abs(cur - pri):,.2f}"

    if abs(diff) < 1e-12:
        return f'<div class="dg-d" style="color:{DIM}">– 0 <span>vs prior {period_label}</span></div>'
    rising = diff > 0
    colour = GOOD if (rising == up_is_good) else BAD
    return (f'<div class="dg-d" style="color:{colour}">{"▲" if rising else "▼"} {txt} '
            f"<span>vs prior {period_label}</span></div>")


def kpi(label: str, value: str, delta_html: str = "", spark_html: str = "",
        sub: str = "") -> str:
    # The sub slot is always emitted, even when empty. Rendering it conditionally made
    # cards that carry a sublabel 23px taller than the ones that do not, so within a row
    # the sparklines sat at different heights and the cards would not bottom-align.
    return (
        '<div class="dg-card">'
        '<div class="dg-k">%s</div>'
        '<div class="dg-v">%s</div>'
        '<div class="dg-dslot">%s</div>'
        '<div class="dg-sparkslot">%s</div>'
        '<div class="dg-sub">%s</div>'
        "</div>" % (label, value, delta_html, spark_html, sub or "&nbsp;")
    )
