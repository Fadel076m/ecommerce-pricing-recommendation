"""Page Forecast (Jalon 9) : prévision de demande J+1 à J+7 pour un produit, via l'API."""
import dash
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from dashboard.api_client import get_forecast, list_products
from dashboard.components import disclaimer_banner, empty_state, page_title, status_badge
from dashboard.theme import CATEGORICAL_ORDER, PLOTLY_LAYOUT

dash.register_page(__name__, path="/forecast", name="Forecast")

layout = html.Div(
    [
        page_title("Forecast — prévision de demande"),
        disclaimer_banner("Prévision sous les hypothèses du modèle — jamais une garantie (AGENTS.md §4)."),
        dcc.Dropdown(id="forecast-product-search", placeholder="Rechercher un produit (nom ou référence)…", style={"marginBottom": "20px"}),
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
        return empty_state("Sélectionner un produit pour afficher sa prévision.")

    result = get_forecast(product_id)
    if not result:
        return empty_state(f"Aucun historique de ventes pour le produit {product_id}.")

    dates = [point["date"] for point in result["forecast"]]
    values = [point["predicted_demand"] for point in result["forecast"]]

    fig = go.Figure(
        data=[
            go.Scatter(
                x=dates,
                y=values,
                mode="lines+markers",
                line=dict(color=CATEGORICAL_ORDER[0], width=2),
                marker=dict(size=8),
                hovertemplate="%{x}<br>Demande prévue : %{y}<extra></extra>",
            )
        ]
    )
    fig.update_layout(**PLOTLY_LAYOUT, title=f"Demande prévue — produit {product_id}", showlegend=False, height=380)

    model_label = "LightGBM (global)" if result["model_used"] == "lightgbm_global" else "Baseline Moving Average (historique insuffisant)"
    model_status = "good" if result["model_used"] == "lightgbm_global" else "warning"

    return html.Div(
        [
            html.Div(status_badge(model_status, model_label), style={"marginBottom": "12px"}),
            dcc.Graph(figure=fig, config={"displayModeBar": False}),
        ]
    )
