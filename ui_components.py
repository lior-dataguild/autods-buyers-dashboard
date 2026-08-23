import pandas as pd

_BAR_RGB = (37, 99, 235)
_BAR_TRACK_PX = 420

PALETTE = {
    "text": "#111827",
    "muted": "#6B7280",
    "heading": "#111827",
    "border": "#E5E7EB",
}


def _fmt(kind: str, v) -> str:
    if v is None or pd.isna(v):
        return "–"
    if kind == "n0":
        return f"{v:,.0f}"
    return f"{v:,.0f}"


def bar_css(pal: dict) -> str:
    return (
        "<style>"
        ".ui-h1{font-size:1.45rem;font-weight:600;color:%(heading)s;margin-bottom:2px}"
        ".ui-scope{font-size:0.85rem;color:%(muted)s;margin-bottom:24px}"
        ".bl-wrap{overflow-x:auto}"
        ".bl-t{width:100%%;border-collapse:collapse;border:0 !important}"
        ".bl-t tr,.bl-t tbody,.bl-t thead{border:0 !important;background:none !important}"
        ".bl-t th{font-size:10px;letter-spacing:.06em;text-transform:uppercase;font-weight:500;"
        "text-align:left;padding:0 4px 5px 0;color:%(muted)s;"
        "border:0 !important;background:none !important;white-space:nowrap}"
        ".bl-t td{padding:3px 4px 3px 0;border:0 !important;background:none !important;"
        "vertical-align:middle}"
        ".bl-lbl{white-space:nowrap;font-size:13px;color:%(text)s;padding-right:14px}"
        ".bl-track{width:%(track)dpx;flex:none;height:12px;display:inline-block;"
        "background:rgba(37,99,235,0.16);overflow:hidden;vertical-align:middle}"
        ".bl-fill{height:12px;min-width:2px;display:inline-block}"
        ".bl-bc{padding-right:6px !important}"
        ".bl-v{font-size:13px;font-variant-numeric:tabular-nums;white-space:nowrap;"
        "text-align:left;padding-right:12px !important;color:%(text)s}"
        "</style>"
    ) % {**pal, "track": _BAR_TRACK_PX}


def data_bars(df: pd.DataFrame, index_col: str, specs: list, index_label: str) -> str:
    """One row per entity, a bar then its value. specs = [(name, unit, column, kind)]."""
    fill = f"rgba({_BAR_RGB[0]},{_BAR_RGB[1]},{_BAR_RGB[2]},0.92)"

    head = f'<th class="bl-h">{index_label}</th>' + "".join(
        f'<th class="bl-h" colspan="2">{name}</th>' if not unit
        else f'<th class="bl-h">{name}</th><th class="bl-u">{unit}</th>'
        for name, unit, _, _ in specs
    )

    maxes = {col: (float(df[col].max()) if df[col].notna().any() else 0.0)
             for _, _, col, _ in specs}

    rows = []
    for _, row in df.iterrows():
        cells = [f'<td class="bl-lbl">{row[index_col]}</td>']
        for _name, _unit, col, kind in specs:
            v, mx = row[col], maxes[col]
            norm = 0.0 if (mx <= 0 or pd.isna(v) or v <= 0) else min(1.0, float(v) / mx)
            cells.append(
                f'<td class="bl-bc"><span class="bl-track"><span class="bl-fill" '
                f'style="width:{norm * _BAR_TRACK_PX:.1f}px;background:{fill}"></span></span></td>'
                f'<td class="bl-v">{_fmt(kind, v)}</td>'
            )
        rows.append("<tr>" + "".join(cells) + "</tr>")

    return (f'<div class="bl-wrap"><table class="bl-t"><tr>{head}</tr>'
            f'{"".join(rows)}</table></div>')
