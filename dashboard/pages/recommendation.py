"""Page Recommendation (Jalon 9) : recommandations produit pour un visiteur, via l'API.

customer_id correspond à un visitor_id RetailRocket (espace d'identifiants
distinct de UCI, jamais fusionné — cf. docs/recommendation.md, docs/api.md)."""
import dash
from dash import Input, Output, callback, dcc, html

from dashboard.api_client import get_recommendations, get_sample_visitors
from dashboard.components import disclaimer_banner, empty_state, page_title, status_badge
from dashboard.theme import BORDER, SURFACE, TEXT_MUTED, TEXT_PRIMARY

dash.register_page(__name__, path="/recommendation", name="Recommendation")

layout = html.Div(
    [
        page_title("Recommendation — produits recommandés"),
        disclaimer_banner(
            "customer_id = visitor_id RetailRocket (comportement view/add_to_cart/purchase), "
            "pas un customer_id UCI — espaces d'identifiants distincts, jamais fusionnés (voir docs/recommendation.md)."
        ),
        dcc.Dropdown(id="recommendation-visitor-select", placeholder="Choisir un visiteur (échantillon)…", style={"marginBottom": "10px"}),
        dcc.Loading(html.Div(id="recommendation-content")),
    ]
)


@callback(Output("recommendation-visitor-select", "options"), Input("recommendation-visitor-select", "id"))
def load_sample_visitors(_):
    visitor_ids = get_sample_visitors(20)
    return [{"label": f"Visiteur {v}", "value": v} for v in visitor_ids]


@callback(Output("recommendation-content", "children"), Input("recommendation-visitor-select", "value"))
def load_recommendations(visitor_id):
    if not visitor_id:
        return empty_state("Sélectionner un visiteur pour afficher ses recommandations.")

    result = get_recommendations(visitor_id)
    if not result:
        return empty_state(f"Aucune recommandation pour le visiteur {visitor_id}.")

    badge = (
        status_badge("warning", "Fallback Most Popular (visiteur inconnu du modèle)")
        if result["is_cold_start_fallback"]
        else status_badge("good", "Recommandation hybride personnalisée")
    )

    rows = [
        html.Tr(
            [
                html.Td(f"#{item['score_rank']}", style={"padding": "8px 12px", "color": TEXT_MUTED}),
                html.Td(item["product_id"], style={"padding": "8px 12px", "color": TEXT_PRIMARY, "fontWeight": 600}),
            ]
        )
        for item in result["recommendations"]
    ]

    table = html.Table(
        style={"width": "100%", "borderCollapse": "collapse", "backgroundColor": SURFACE, "border": f"1px solid {BORDER}", "borderRadius": "8px"},
        children=[
            html.Thead(html.Tr([html.Th("Rang", style={"textAlign": "left", "padding": "8px 12px"}), html.Th("Produit (item_id RetailRocket)", style={"textAlign": "left", "padding": "8px 12px"})])),
            html.Tbody(rows),
        ],
    )

    return html.Div([html.Div(badge, style={"marginBottom": "12px"}), table])
