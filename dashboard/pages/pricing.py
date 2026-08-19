"""Page Tarification : prix recommandé et simulation de marge."""
import dash
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from dashboard.api_client import get_pricing, list_products, simulate_pricing
from dashboard.components import card, empty_state, note_banner, page_header, stat_row, stat_tile
from dashboard.theme import CATEGORICAL_ORDER, PLOTLY_LAYOUT

dash.register_page(__name__, path="/pricing", name="Tarification")

layout = html.Div(
    [
        page_header("Tarification intelligente", "Trouvez le prix qui maximise votre marge pour chaque produit."),
        card(
            dcc.Dropdown(id="pricing-product-search", placeholder="Rechercher un produit par nom ou référence…"),
            padding="10px 16px",
        ),
        html.Div(style={"height": "20px"}),
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
        return empty_state("Sélectionnez un produit pour afficher sa simulation de prix.")

    pricing = get_pricing(product_id)
    simulation = simulate_pricing(product_id)
    if not pricing or not simulation:
        return empty_state("Ce produit n'est pas disponible pour la simulation.")

    confidence_note = (
        "Sensibilité au prix mesurée sur l'historique de ce produit."
        if pricing["elasticity_is_estimated"]
        else "Sensibilité au prix estimée par défaut (peu d'historique de variation de prix pour ce produit)."
    )

    tiles = stat_row(
        stat_tile("Prix actuel", f"{pricing['current_price']:.2f} €", icon="tag", tint="blue"),
        stat_tile("Prix recommandé", f"{pricing['recommended_price']:.2f} €", f"Écart {pricing['price_difference']:+.2f} €", icon="trend", tint="aqua"),
        stat_tile("Marge actuelle", f"{pricing['estimated_margin_at_current_price']:.2f} €", icon="coin", tint="orange"),
        stat_tile("Marge potentielle", f"{pricing['estimated_margin_at_recommended_price']:.2f} €", icon="coin", tint="violet"),
    )

    points = simulation["simulation"]
    prices = [p["price"] for p in points]
    margins = [p["estimated_margin"] for p in points]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=prices, y=margins, mode="lines", line=dict(color=CATEGORICAL_ORDER[0], width=2.5, shape="spline"),
            fill="tozeroy", fillcolor="rgba(42,120,214,0.06)",
            hovertemplate="Prix %{x:.2f} €<br>Marge estimée %{y:.2f} €<extra></extra>", name="Marge simulée",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[pricing["current_price"]], y=[pricing["estimated_margin_at_current_price"]], mode="markers",
            marker=dict(size=13, color=CATEGORICAL_ORDER[7], symbol="circle", line=dict(width=2, color="white")), name="Prix actuel",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[pricing["recommended_price"]], y=[pricing["estimated_margin_at_recommended_price"]], mode="markers",
            marker=dict(size=14, color=CATEGORICAL_ORDER[2], symbol="star", line=dict(width=1.5, color="white")), name="Prix recommandé",
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title="Marge estimée selon le prix de vente",
        xaxis_title="Prix (€)", yaxis_title="Marge (€)",
        legend=dict(orientation="h", y=-0.22),
        height=380,
    )

    return html.Div([tiles, note_banner(confidence_note), card(dcc.Graph(figure=fig, config={"displayModeBar": False}))])
