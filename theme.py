from __future__ import annotations  # local venv is 3.9; `str | None` is 3.10+

"""Cyber palette + shared CSS for the DG dashboard suite.

Dark ground with a single accent is the most literal reading of "the data is the only
thing at full contrast" -- so the cyber look and the house style agree here rather than
fighting. No glow, no scanlines, no second accent: a blurred stroke makes a point's
position ambiguous, which costs precision for decoration.
"""

BG = "#0B0F14"
PANEL = "#0E141B"
BORDER = "#1B242E"
BORDER_SOFT = "#151C24"
ACCENT = "#22D3EE"     # the one accent; carries the data
BAD = "#F87171"        # reserved for measures where more is worse
TEXT = "#E6EDF3"
MUTED = "#7D8A99"
DIM = "#5B6B7C"
GRID = "#18202A"

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

  /* --- masthead --- */
  .dg-top {{ display:flex; align-items:baseline; gap:11px;
             padding-bottom:13px; border-bottom:1px solid {BORDER_SOFT}; margin-bottom:20px; }}
  .dg-mark {{ font-family:{MONO}; font-size:19px; font-weight:700;
              letter-spacing:.2em; color:{ACCENT}; }}
  .dg-tag {{ font-size:11px; letter-spacing:.16em; text-transform:uppercase; color:{DIM}; }}

  .dg-h1 {{ font-size:27px; font-weight:600; color:{TEXT}; margin:0 0 7px; }}
  .dg-complete {{ font-family:{MONO}; font-size:12px; color:{MUTED}; margin:0 0 22px; }}
  .dg-complete b {{ color:#A8B6C4; font-weight:600; }}

  .dg-sec {{ font-size:10px; letter-spacing:.13em; text-transform:uppercase;
             color:{ACCENT}; font-weight:700; margin:26px 0 11px; }}
  .dg-fl {{ font-size:10px; letter-spacing:.1em; text-transform:uppercase;
            color:{DIM}; margin:0 0 7px; }}
  /* The nav cards are buttons; keep them the same height as the placeholder cards
     beside them so the row does not read as three different kinds of thing. */
  .stButton > button {{ min-height:62px; }}

  /* --- KPI tile --- */
  .dg-card {{ border:1px solid {BORDER}; border-radius:7px; padding:14px 16px 12px;
              background:{PANEL}; height:100%; }}
  .dg-k {{ font-size:11px; color:{MUTED}; margin-bottom:9px; }}
  .dg-v {{ font-size:26px; font-weight:700; color:{TEXT}; letter-spacing:-.01em;
           line-height:1.1; }}
  .dg-sub {{ font-family:{MONO}; font-size:11px; color:{DIM}; margin-top:6px; }}
  .dg-spark {{ display:block; margin-top:9px; }}

  /* --- window chips (a real control: it moves every tile) --- */
  div[role="radiogroup"] {{ gap:7px !important; }}
  div[role="radiogroup"] label {{
      border:1px solid {BORDER}; border-radius:99px; padding:4px 13px;
      background:transparent; color:{MUTED}; font-size:12px; margin:0 !important; }}
  div[role="radiogroup"] label:has(input:checked) {{
      border-color:{ACCENT}; color:{ACCENT}; background:rgba(34,211,238,.07); }}
  div[role="radiogroup"] label > div:first-child {{ display:none; }}
  div[role="radiogroup"] label p {{ font-size:12px !important; }}

  /* --- nav cards, rendered as buttons --- */
  .stButton > button {{
      width:100%; text-align:left; background:{PANEL};
      border:1px solid {BORDER}; border-radius:7px; padding:14px 16px;
      color:{TEXT}; font-size:14px; font-weight:600; }}
  .stButton > button:hover {{ border-color:{ACCENT}; color:{ACCENT}; background:{PANEL}; }}

  .dg-ask {{ border:1px solid #1E2833; border-radius:7px; padding:12px 14px;
             font-size:13px; color:{DIM}; background:{PANEL}; }}

  /* Streamlit animates the expander with an explicit height + overflow:hidden; when
     that animation does not run the content stays clipped to the summary. */
  [data-testid="stExpander"] {{ border:0 !important; background:none !important;
      margin-top:16px; }}
  [data-testid="stExpander"] details {{ background:none !important; border:0 !important; }}
  [data-testid="stExpander"] details[open] {{ height:auto !important; overflow:visible !important; }}
  [data-testid="stExpander"] summary {{ padding:0 !important; }}
  [data-testid="stExpander"] summary p {{ font-size:.82rem; font-weight:600; color:{TEXT}; }}
  [data-testid="stExpander"] p, [data-testid="stExpander"] li,
  [data-testid="stExpander"] td, [data-testid="stExpander"] th {{ color:{MUTED}; }}
</style>
"""


def spark(vals, w: int = 168, h: int = 30, color: str | None = None) -> str:
    """Direction only, never level (C21): scaled to the series' own min and max.

    Two tiles 10x apart therefore show the same amplitude. That is correct -- level is
    the job of the number printed above it.
    """
    vals = [float(v) for v in vals if v is not None]
    if len(vals) < 2:
        return f'<span class="dg-sub">–</span>'   # C23: too few points is a state
    c = color or ACCENT
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    step = w / (len(vals) - 1)
    pts = " ".join(
        f"{i * step:.1f},{h - 2 - (v - lo) / span * (h - 5):.1f}"
        for i, v in enumerate(vals)
    )
    lx, ly = w, h - 2 - (vals[-1] - lo) / span * (h - 5)
    return (
        f'<svg class="dg-spark" viewBox="0 0 {w + 4} {h}" width="100%" height="{h}" '
        f'preserveAspectRatio="none" role="img" aria-hidden="true">'
        f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="1.6" '
        f'stroke-linejoin="round"/>'
        f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="2" fill="{c}"/></svg>'
    )


def tile(label: str, value: str, sub: str = "", spark_html: str = "",
         value_color: str | None = None) -> str:
    vc = ' style="color:%s"' % value_color if value_color else ""
    sub_html = '<div class="dg-sub">%s</div>' % sub if sub else ""
    return (
        '<div class="dg-card">'
        '<div class="dg-k">%s</div>'
        '<div class="dg-v"%s>%s</div>'
        "%s%s"
        "</div>" % (label, vc, value, spark_html, sub_html)
    )
