"""
Tokens de couleur partagés par toutes les pages du dashboard (Jalon 9).
Palette de référence validée (skill dataviz) — mode clair uniquement (pas de
bascule dark mode dans ce prototype, hors périmètre du temps disponible).
"""

SURFACE = "#fcfcfb"
PAGE_PLANE = "#f9f9f7"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"
BORDER = "rgba(11,11,11,0.10)"

# Palette catégorielle (ordre fixe, jamais recyclé) — cf. skill dataviz.
CATEGORICAL = {
    "blue": "#2a78d6",
    "orange": "#eb6834",
    "aqua": "#1baf7a",
    "yellow": "#eda100",
    "magenta": "#e87ba4",
    "green": "#008300",
    "violet": "#4a3aa7",
    "red": "#e34948",
}
CATEGORICAL_ORDER = list(CATEGORICAL.values())

SEQUENTIAL_BLUE = ["#cde2fb", "#9ec5f4", "#5598e7", "#2a78d6", "#1c5cab", "#0d366b"]

STATUS = {
    "good": "#0ca30c",
    "warning": "#fab219",
    "serious": "#ec835a",
    "critical": "#d03b3b",
}

FONT_FAMILY = 'system-ui, -apple-system, "Segoe UI", sans-serif'

PLOTLY_LAYOUT = dict(
    paper_bgcolor=SURFACE,
    plot_bgcolor=SURFACE,
    font=dict(family=FONT_FAMILY, color=TEXT_PRIMARY, size=13),
    margin=dict(l=50, r=20, t=30, b=40),
    xaxis=dict(gridcolor=GRIDLINE, linecolor=BASELINE, zeroline=False),
    yaxis=dict(gridcolor=GRIDLINE, linecolor=BASELINE, zeroline=False),
    hoverlabel=dict(bgcolor=SURFACE, font=dict(family=FONT_FAMILY, color=TEXT_PRIMARY)),
)


def stock_risk_status(days_of_stock: float | None) -> str:
    """Statut de risque de rupture — cohérent avec le use case 2 du brief (section 50)."""
    if days_of_stock is None:
        return "good"
    if days_of_stock < 3:
        return "critical"
    if days_of_stock < 7:
        return "serious"
    if days_of_stock < 14:
        return "warning"
    return "good"
