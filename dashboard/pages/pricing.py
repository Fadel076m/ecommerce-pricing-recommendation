"""Page Pricing (Jalon 9) : prix recommandé et simulation de marge, via l'API."""
import dash
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from dashboard.api_client import get_pricing, list_products, simulate_pricing
from dashboard.components import disclaimer_banner, empty_state, page_title, stat_row, stat_tile
from dashboard.theme import CATEGORICAL_ORDER, PLOTLY_LAYOUT

dash.register_page(__name__, path="/pricing", name="Pricing")

layout = html.Div(
    [
        page_title("Pricing — simulation de prix"),
        disclaimer_banner("Résultat de simulation sous hypothèses du modèle — jamais une vérité mesurée (AGENTS.md §4/§10)."),
        dcc.Dropdown(id="pricing-product-search", placeholder="Rechercher un produit (nom ou référence)…", style={"marginBottom": "20px"}),
        dcc.Loading(html.Div(id="pricing-content")),
    ]
)


@callback(Output("pricing-product-search", "options"), Input("pricing-product-search", "search_value"))
def search_products(search_value):
    products = list_products(search=search_value, limit=25) or []
    return [{"label": f"{p['product_id']} — {p['product_name']}", "value": p["product_id"]} for p in products]


@callback(Output("pricing-content", "children"), Input("pricing-product-search", "value"))
def load_pricing(product_id):
    if not product_id:
        return empty_state("Sélectionner un produit pour afficher sa simulation de prix.")

    pricing = get_pricing(product_id)
    simulation = simulate_pricing(product_id)
    if not pricing or not simulation:
        return empty_state(f"Produit {product_id} introuvable côté pricing.")

    elasticity_note = "estimée par régression" if pricing["elasticity_is_estimated"] else "assumée par défaut (pas mesurée)"
    tiles = stat_row(
        stat_tile("Prix actuel", f"{pricing['current_price']:.2f}"),
        stat_tile("Prix recommandé", f"{pricing['recommended_price']:.2f}", f"Écart : {pricing['price_difference']:+.2f}"),
        stat_tile("Marge (prix actuel)", f"{pricing['estimated_margin_at_current_price']:.2f}"),
        stat_tile("Marge (prix recommandé)", f"{pricing['estimated_margin_at_recommended_price']:.2f}"),
        stat_tile("Élasticité", f"{pricing['elasticity']:.2f}", elasticity_note),
    )

    points = simulation["simulation"]
    prices = [p["price"] for p in points]
    margins = [p["estimated_margin"] for p in points]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=prices, y=margins, mode="lines+markers", line=dict(color=CATEGORICAL_ORDER[0], width=2),
            hovertemplate="Prix %{x:.2f}<br>Marge estimée %{y:.2f}<extra></extra>", name="Marge simulée",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[pricing["current_price"]], y=[pricing["estimated_margin_at_current_price"]], mode="markers",
            marker=dict(size=12, color=CATEGORICAL_ORDER[7], symbol="circle"), name="Prix actuel",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[pricing["recommended_price"]], y=[pricing["estimated_margin_at_recommended_price"]], mode="markers",
            marker=dict(size=12, color=CATEGORICAL_ORDER[2], symbol="star"), name="Prix recommandé",
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title="Marge estimée selon le prix (grille de simulation)",
        xaxis_title="Prix", yaxis_title="Marge estimée",
        legend=dict(orientation="h", y=-0.2),
        height=380,
    )

    return html.Div([tiles, dcc.Graph(figure=fig, config={"displayModeBar": False})])
