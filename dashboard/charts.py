"""Server-side SVG charts using the dark-theme palette."""
from __future__ import annotations

SURFACE, BORDER, TEXT, MUTED = "#1a1d27", "#2a2d3a", "#e2e8f0", "#6b7280"
COLORS = {"model": "#22c55e", "runtime": "#6366f1", "observability": "#06b6d4",
          "control": "#a855f7", "human_review": "#f59e0b", "remediation": "#ef4444"}
MIN_BAR_PX = 3  # a component that is tiny must still be visible


def breakdown_chart(title: str, parts: dict[str, float], shares: dict[str, float],
                    width: int = 520, row_h: int = 34) -> str:
    """One bar per cost component, scaled to the largest, labelled with dollars and share."""
    pad_left, pad_right, pad_top = 110, 190, 40
    chart_w = width - pad_left - pad_right
    height = pad_top + row_h * len(parts) + 12
    top = max(parts.values(), default=0.0)
    rows = []
    for i, (name, value) in enumerate(parts.items()):
        y = pad_top + i * row_h
        bar_w = max(MIN_BAR_PX, chart_w * value / top) if top > 0 else MIN_BAR_PX
        rows.append(
            f'<text x="{pad_left - 8}" y="{y + 15}" text-anchor="end" fill="{TEXT}" '
            f'font-size="12">{name.replace("_", " ")}</text>'
            f'<rect x="{pad_left}" y="{y}" width="{bar_w:.1f}" height="20" rx="3" '
            f'fill="{COLORS.get(name, MUTED)}"/>'
            f'<text x="{pad_left + bar_w + 6}" y="{y + 15}" fill="{MUTED}" font-size="11">'
            f'${value:,.6f} ({shares.get(name, 0.0):.3f}%)</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}"><rect width="{width}" height="{height}" rx="6" '
            f'fill="{SURFACE}" stroke="{BORDER}"/><text x="{width // 2}" y="24" '
            f'text-anchor="middle" fill="{TEXT}" font-size="13" font-weight="600">{title}</text>'
            + "".join(rows) + "</svg>")
