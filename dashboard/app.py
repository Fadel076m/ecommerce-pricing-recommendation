"""
Dashboard Dash (Jalon 9). Consomme l'API FastAPI (api/), ne recalcule aucune
logique métier lui-même (AGENTS.md §5).

Usage : python -m dashboard.app  (ou `make dashboard`)
"""
import dash
from dash import Dash, dcc, html

from dashboard.theme import BORDER, FONT_FAMILY, PAGE_PLANE, TEXT_PRIMARY, TEXT_SECONDARY

app = Dash(__name__, use_pages=True, pages_folder="pages", title="Ecommerce Data-Driven Pricing & Recommandation")
server = app.server

NAV_LINKS = [
    ("Executive", "/"),
    ("Forecast", "/forecast"),
    ("Pricing", "/pricing"),
    ("Recommendation", "/recommendation"),
    ("Inventory", "/inventory"),
]

app.layout = html.Div(
    style={"fontFamily": FONT_FAMILY, "backgroundColor": PAGE_PLANE, "minHeight": "100vh"},
    children=[
        html.Header(
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "24px",
                "padding": "16px 32px",
                "borderBottom": f"1px solid {BORDER}",
                "backgroundColor": "#fcfcfb",
            },
            children=[
                html.Span("Ecommerce — Pricing & Recommandation", style={"fontWeight": 700, "color": TEXT_PRIMARY}),
                html.Nav(
                    style={"display": "flex", "gap": "18px"},
                    children=[
                        dcc.Link(
                            label,
                            href=href,
                            style={"color": TEXT_SECONDARY, "textDecoration": "none", "fontSize": "14px"},
                        )
                        for label, href in NAV_LINKS
                    ],
                ),
            ],
        ),
        html.Main(style={"padding": "32px", "maxWidth": "1100px", "margin": "0 auto"}, children=[dash.page_container]),
        html.Footer(
            style={"padding": "16px 32px", "color": TEXT_SECONDARY, "fontSize": "12px", "textAlign": "center"},
            children="Prototype académique — résultats sous hypothèses des modèles et de données synthétiques (voir docs/).",
        ),
    ],
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
