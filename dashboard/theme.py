"""Design system du dashboard (Jalon 9). Palette catégorielle/séquentielle/statuts
issue de la palette de référence validée (skill dataviz) ; jetons de mise en
page (sidebar, cartes, ombres) construits par-dessus pour un rendu soigné."""

# --- Palette de référence (skill dataviz) ------------------------------------
SURFACE = "#ffffff"
PAGE_PLANE = "#f4f5f7"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#898781"
GRIDLINE = "#ecebe7"
BASELINE = "#c3c2b7"
BORDER = "rgba(11,11,11,0.08)"

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
STATUS = {"good": "#0ca30c", "warning": "#fab219", "serious": "#ec835a", "critical": "#d03b3b"}

# --- Chrome (sidebar sombre + cartes claires) --------------------------------
SIDEBAR_BG = "#14161c"
SIDEBAR_TEXT = "#a7a9b4"
SIDEBAR_TEXT_ACTIVE = "#ffffff"
SIDEBAR_ACCENT = "#2a78d6"
SIDEBAR_ITEM_HOVER = "#1e2129"

CARD_RADIUS = "18px"
CARD_SHADOW = "0 1px 2px rgba(16,15,10,0.04), 0 8px 24px rgba(16,15,10,0.06)"

# Fond pastel des badges d'icône par tuile (couleur de texte = valeur du dict CATEGORICAL correspondante)
TILE_TINTS = {
    "blue": "#e8f0fc",
    "orange": "#fdece3",
    "aqua": "#e4f7ef",
    "yellow": "#fdf1dc",
    "magenta": "#fce9f0",
    "violet": "#ece9f8",
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
    """Statut de risque de rupture (jours de stock estimés)."""
    if days_of_stock is None:
        return "good"
    if days_of_stock < 3:
        return "critical"
    if days_of_stock < 7:
        return "serious"
    if days_of_stock < 14:
        return "warning"
    return "good"
