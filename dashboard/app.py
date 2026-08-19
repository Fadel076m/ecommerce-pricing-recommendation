"""Dashboard Dash (Jalon 9). Consomme l'API FastAPI (api/) — aucun calcul métier ici.

Usage : python -m dashboard.app  (ou `make dashboard`)
"""
import dash
from dash import Dash, Input, Output, callback, dcc, html

from dashboard.icons import icon_svg
from dashboard.theme import (
    FONT_FAMILY,
    PAGE_PLANE,
    SIDEBAR_ACCENT,
    SIDEBAR_BG,
    SIDEBAR_ITEM_HOVER,
    SIDEBAR_TEXT,
    SIDEBAR_TEXT_ACTIVE,
)

app = Dash(__name__, use_pages=True, pages_folder="pages", title="Ecommerce Intelligence")
server = app.server

NAV_LINKS = [
    ("home", "Aperçu", "/"),
    ("trend", "Prévision", "/forecast"),
    ("tag", "Tarification", "/pricing"),
    ("cart", "Recommandations", "/recommendation"),
    ("box", "Stock", "/inventory"),
]


def _nav_item(icon, label, href, active: bool):
    color = SIDEBAR_TEXT_ACTIVE if active else SIDEBAR_TEXT
    return dcc.Link(
        href=href,
        style={"textDecoration": "none"},
        children=html.Div(
            style={
                "display": "flex",
                "alignItems": "center",
                "gap": "12px",
                "padding": "10px 14px",
                "borderRadius": "10px",
                "color": color,
                "backgroundColor": SIDEBAR_ITEM_HOVER if active else "transparent",
                "fontSize": "14px",
                "fontWeight": 600 if active else 500,
                "marginBottom": "4px",
                "borderLeft": f"3px solid {SIDEBAR_ACCENT}" if active else "3px solid transparent",
            },
            className="nav-item",
            children=[html.Img(src=icon_svg(icon, color=color, size=17)), html.Span(label)],
        ),
    )


def _sidebar(pathname: str):
    return html.Div(
        style={
            "width": "232px",
            "minHeight": "100vh",
            "backgroundColor": SIDEBAR_BG,
            "padding": "22px 16px",
            "position": "fixed",
            "top": 0,
            "left": 0,
            "boxSizing": "border-box",
        },
        children=[
            html.Div(
                style={"display": "flex", "alignItems": "center", "gap": "10px", "padding": "4px 10px", "marginBottom": "28px"},
                children=[
                    html.Div(
                        "◆",
                        style={
                            "color": SIDEBAR_ACCENT,
                            "fontSize": "18px",
                            "width": "30px",
                            "height": "30px",
                            "borderRadius": "9px",
                            "backgroundColor": "rgba(42,120,214,0.16)",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                        },
                    ),
                    html.Span("Nova Retail", style={"color": SIDEBAR_TEXT_ACTIVE, "fontWeight": 700, "fontSize": "15px"}),
                ],
            ),
            html.Div([_nav_item(icon, label, href, active=(pathname == href)) for icon, label, href in NAV_LINKS]),
        ],
    )


app.layout = html.Div(
    style={"fontFamily": FONT_FAMILY, "backgroundColor": PAGE_PLANE, "minHeight": "100vh"},
    children=[
        dcc.Location(id="url", refresh=False),
        html.Div(id="sidebar-container"),
        html.Main(
            style={"marginLeft": "232px", "padding": "36px 40px", "maxWidth": "1180px"},
            children=[dash.page_container],
        ),
    ],
)


@callback(Output("sidebar-container", "children"), Input("url", "pathname"))
def render_sidebar(pathname):
    return _sidebar(pathname or "/")


app.index_string = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            * { box-sizing: border-box; }
            body { margin: 0; }
            .nav-item:hover { background-color: #1e2129 !important; color: #ffffff !important; }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>{%config%}{%scripts%}{%renderer%}</footer>
    </body>
</html>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
