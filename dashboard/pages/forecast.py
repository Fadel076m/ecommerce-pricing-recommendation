"""Page Prévision : anticiper la demande d'un produit sur les 7 prochains jours."""
import dash
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from dashboard.api_client import get_forecast, list_products
from dashboard.components import card, empty_state, note_banner, page_header
from dashboard.theme import CATEGORICAL_ORDER, PLOTLY_LAYOUT

dash.register_page(__name__, path="/forecast", name="Prévision")

layout = html.Div(
    [
        page_header("Prévision de la demande", "Anticipez les ventes des 7 prochains jours pour ajuster vos réassorts."),
        card(
            dcc.Dropdown(id="forecast-product-search", placeholder="Rechercher un produit par nom ou référence…"),
            padding="10px 16px",
        ),
        html.Div(style={"height": "20px"}),
        dcc.Loading(html.Div(id="forecast-content")),
    ]
)


@callback(Output("forecast-product-search", "options"), Input("forecast-product-search", "search_value"))
def search_products(search_value):
    products = list_products(search=search_value, limit=25) or []
    return [{"label": f"{p['product_id']} — {p['product_name']}", "value": p["product_id"]} for p in products]


@callback(Output("forecast-content", "children"), Input("forecast-product-search", "value"))
def load_forecast(product_id):
    if not product_id:
        return empty_state("Sélectionnez un produit pour afficher sa prévision de demande.")

    result = get_forecast(product_id)
    if not result:
        return empty_state("Historique de ventes insuffisant pour ce produit.")

    dates = [point["date"] for point in result["forecast"]]
    values = [point["predicted_demand"] for point in result["forecast"]]

    fig = go.Figure(
        data=[
            go.Scatter(
                x=dates,
                y=values,
                mode="lines+markers",
                line=dict(color=CATEGORICAL_ORDER[0], width=2.5, shape="spline"),
                marker=dict(size=8, color=CATEGORICAL_ORDER[0]),
                fill="tozeroy",
                fillcolor="rgba(42,120,214,0.08)",
                hovertemplate="%{x}<br>Demande prévue : %{y}<extra></extra>",
            )
        ]
    )
    fig.update_layout(**PLOTLY_LAYOUT, title=f"Produit {product_id}", showlegend=False, height=380)

    confidence_note = (
        "Prévision basée sur l'historique récent du produit."
        if result["model_used"] == "lightgbm_global"
        else "Historique limité pour ce produit — estimation basée sur la moyenne récente."
    )

    return html.Div([note_banner(confidence_note), card(dcc.Graph(figure=fig, config={"displayModeBar": False}))])
