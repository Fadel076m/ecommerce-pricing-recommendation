"""Page Recommandations : suggestions produit personnalisées pour un client."""
import dash
from dash import Input, Output, callback, dcc, html

from dashboard.api_client import get_recommendations, get_sample_visitors
from dashboard.components import card, empty_state, page_header, status_badge
from dashboard.theme import BORDER, TEXT_MUTED, TEXT_PRIMARY

dash.register_page(__name__, path="/recommendation", name="Recommandations")

layout = html.Div(
    [
        page_header("Recommandations personnalisées", "Les produits les plus pertinents à suggérer à chaque client."),
        card(
            dcc.Dropdown(id="recommendation-visitor-select", placeholder="Choisir un client…"),
            padding="10px 16px",
        ),
        html.Div(style={"height": "20px"}),
        dcc.Loading(html.Div(id="recommendation-content")),
    ]
)


@callback(Output("recommendation-visitor-select", "options"), Input("recommendation-visitor-select", "id"))
def load_sample_visitors(_):
    visitor_ids = get_sample_visitors(20)
    return [{"label": f"Client #{v}", "value": v} for v in visitor_ids]


@callback(Output("recommendation-content", "children"), Input("recommendation-visitor-select", "value"))
def load_recommendations(visitor_id):
    if not visitor_id:
        return empty_state("Sélectionnez un client pour afficher ses recommandations.")

    result = get_recommendations(visitor_id)
    if not result:
        return empty_state("Aucune recommandation disponible pour ce client.")

    badge = (
        status_badge("warning", "Sélection populaire (nouveau client)")
        if result["is_cold_start_fallback"]
        else status_badge("good", "Recommandation personnalisée")
    )

    rows = [
        html.Tr(
            [
                html.Td(
                    f"{item['score_rank']}",
                    style={"padding": "12px 16px", "color": TEXT_MUTED, "fontWeight": 600, "width": "40px"},
                ),
                html.Td(f"Produit {item['product_id']}", style={"padding": "12px 16px", "color": TEXT_PRIMARY, "fontWeight": 600}),
            ],
            style={"borderTop": f"1px solid {BORDER}"},
        )
        for item in result["recommendations"]
    ]

    table = html.Table(
        style={"width": "100%", "borderCollapse": "collapse"},
        children=[
            html.Thead(
                html.Tr(
                    [
                        html.Th("Rang", style={"textAlign": "left", "padding": "0 16px 10px", "color": TEXT_MUTED, "fontSize": "12px", "fontWeight": 500}),
                        html.Th("Produit suggéré", style={"textAlign": "left", "padding": "0 16px 10px", "color": TEXT_MUTED, "fontSize": "12px", "fontWeight": 500}),
                    ]
                )
            ),
            html.Tbody(rows),
        ],
    )

    return html.Div([html.Div(badge, style={"marginBottom": "16px"}), card(table, padding="20px 8px")])
