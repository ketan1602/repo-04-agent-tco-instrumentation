"""TCO-specific SVG chart generators."""
from __future__ import annotations

import math

from dashboard.charts import BORDER, MUTED, SURFACE, TEXT

_PALETTE = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6"]


def pie_chart(
    slices: list[tuple[str, float]],
    title: str,
    width: int = 380,
    height: int = 300,
) -> str:
    """SVG pie chart. slices: list of (label, value). Values are raw amounts."""
    total = sum(v for _, v in slices)
    if total == 0:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}"><rect width="{width}" height="{height}" '
            f'rx="6" fill="{SURFACE}"/><text x="{width//2}" y="{height//2}" '
            f'text-anchor="middle" fill="{MUTED}" font-size="13">No data</text></svg>'
        )

    legend_h = len(slices) * 18 + 8
    pie_h = height - legend_h - 36
    cx = width // 2
    cy = 30 + pie_h // 2
    r = min(cx - 12, pie_h // 2 - 8)

    paths: list[str] = []
    angle = -math.pi / 2
    for i, (label, value) in enumerate(slices):
        sweep = 2 * math.pi * (value / total)
        x1 = cx + r * math.cos(angle)
        y1 = cy + r * math.sin(angle)
        x2 = cx + r * math.cos(angle + sweep)
        y2 = cy + r * math.sin(angle + sweep)
        large = 1 if sweep > math.pi else 0
        color = _PALETTE[i % len(_PALETTE)]
        pct = value / total * 100
        paths.append(
            f'<path d="M{cx} {cy} L{x1:.1f} {y1:.1f} A{r} {r} 0 {large} 1 '
            f'{x2:.1f} {y2:.1f}Z" fill="{color}" opacity="0.88">'
            f"<title>{label}: {pct:.1f}%</title></path>"
        )
        angle += sweep

    legend_y0 = cy + r + 16
    legend_items = "".join(
        f'<rect x="12" y="{legend_y0 + i * 18}" width="10" height="10" '
        f'rx="2" fill="{_PALETTE[i % len(_PALETTE)]}"/>'
        f'<text x="28" y="{legend_y0 + i * 18 + 9}" fill="{TEXT}" font-size="11">'
        f'{label} — {slices[i][1] / total * 100:.1f}%</text>'
        for i, (label, _) in enumerate(slices)
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f'<rect width="{width}" height="{height}" rx="6" fill="{SURFACE}" '
        f'stroke="{BORDER}" stroke-width="1"/>'
        f'<text x="{cx}" y="22" text-anchor="middle" fill="{TEXT}" '
        f'font-size="13" font-weight="600">{title}</text>'
        + "".join(paths) + legend_items + "</svg>"
    )


def trend_line(
    values: list[float],
    title: str,
    y_label: str = "Cost (USD)",
    width: int = 480,
    height: int = 200,
) -> str:
    """SVG line chart for a sequence of values (e.g. cumulative run costs)."""
    if not values:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}"><rect width="{width}" height="{height}" '
            f'rx="6" fill="{SURFACE}"/><text x="{width//2}" y="{height//2}" '
            f'text-anchor="middle" fill="{MUTED}" font-size="13">No data</text></svg>'
        )

    pad_l, pad_r, pad_t, pad_b = 48, 16, 32, 24
    chart_w = width - pad_l - pad_r
    chart_h = height - pad_t - pad_b
    y_max = max(values) or 1.0

    def _x(i: int) -> float:
        return pad_l + (i / max(len(values) - 1, 1)) * chart_w

    def _y(v: float) -> float:
        return pad_t + chart_h - (v / y_max) * chart_h

    points = " ".join(f"{_x(i):.1f},{_y(v):.1f}" for i, v in enumerate(values))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f'<rect width="{width}" height="{height}" rx="6" fill="{SURFACE}" '
        f'stroke="{BORDER}" stroke-width="1"/>'
        f'<text x="{width // 2}" y="20" text-anchor="middle" fill="{TEXT}" '
        f'font-size="13" font-weight="600">{title}</text>'
        f'<text x="10" y="{pad_t + chart_h // 2}" text-anchor="middle" '
        f'fill="{MUTED}" font-size="10" transform="rotate(-90,10,{pad_t + chart_h // 2})">'
        f'{y_label}</text>'
        f'<polyline points="{points}" fill="none" stroke="#6366f1" stroke-width="2" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f'<text x="{pad_l}" y="{height - 6}" fill="{MUTED}" font-size="10">run 1</text>'
        f'<text x="{width - pad_r}" y="{height - 6}" text-anchor="end" '
        f'fill="{MUTED}" font-size="10">run {len(values)}</text>'
        "</svg>"
    )
