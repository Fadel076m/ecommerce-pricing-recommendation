"""Page Aperçu (Executive) : indicateurs clés de l'activité."""
import dash
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from dashboard.api_client import get_kpi_summary
from dashboard.components import card, empty_state, page_header, stat_row, stat_tile
from dashboard.theme import CATEGORICAL_ORDER, PLOTLY_LAYOUT

dash.register_page(__name__, path="/", name="Aperçu")

layout = html.Div(
    [
        page_header("Bonjour 👋", "Voici la performance de votre activité en un coup d'œil."),
        dcc.Loading(html.Div(id="executive-content")),
    ]
)


@callback(Output("executive-content", "children"), Input("executive-content", "id"))
def load_executive(_):
    summary = get_kpi_summary()
    if not summary:
        return empty_state("Les indicateurs ne sont pas disponibles pour le moment.")

    tiles = stat_row(
        stat_tile("Chiffre d'affaires", f"{summary['revenue_total']:,.0f} €".replace(",", " "), "Cumul", icon="coin", tint="blue"),
        stat_tile("Marge", f"{summary['margin_total']:,.0f} €".replace(",", " "), "Cumul", icon="trend", tint="aqua"),
        stat_tile("Commandes", f"{summary['orders_total']:,}".replace(",", " "), icon="cart", tint="violet"),
        stat_tile("Panier moyen", f"{summary['average_order_value']:,.2f} €".replace(",", " "), icon="tag", tint="orange"),
        stat_tile("Produits actifs", f"{summary['n_products']:,}".replace(",", " "), icon="box", tint="magenta"),
        stat_tile("Clients", f"{summary['n_customers']:,}".replace(",", " "), icon="users", tint="yellow"),
    )

    fig = go.Figure(
        data=[
            go.Bar(
                x=["Chiffre d'affaires", "Marge"],
                y=[summary["revenue_total"], summary["margin_total"]],
                marker_color=[CATEGORICAL_ORDER[0], CATEGORICAL_ORDER[2]],
                width=0.45,
            )
        ]
    )
    fig.update_layout(**PLOTLY_LAYOUT, title="Chiffre d'affaires vs marge", showlegend=False, height=340)

    return html.Div([tiles, card(dcc.Graph(figure=fig, config={"displayModeBar": False}))])
