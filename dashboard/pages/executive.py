"""Page Executive (Jalon 9) : KPIs globaux, résultats OBSERVÉS depuis le Data Warehouse."""
import dash
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from dashboard.api_client import get_kpi_summary
from dashboard.components import disclaimer_banner, empty_state, page_title, stat_row, stat_tile
from dashboard.theme import CATEGORICAL_ORDER, PLOTLY_LAYOUT

dash.register_page(__name__, path="/", name="Executive")

layout = html.Div(
    [
        page_title("Executive — vue d'ensemble"),
        disclaimer_banner(
            "KPIs Commercial/Marge calculés directement sur l'historique observé (fact_sales). "
            "Le catalogue produit/client est réel (UCI Online Retail II) ; coût et stock restent synthétiques (voir docs/data_dictionary.md)."
        ),
        dcc.Loading(html.Div(id="executive-content")),
    ]
)


@callback(Output("executive-content", "children"), Input("executive-content", "id"))
def load_executive(_):
    summary = get_kpi_summary()
    if not summary:
        return empty_state("KPIs indisponibles — vérifier que l'API et PostgreSQL sont accessibles.")

    tiles = stat_row(
        stat_tile("Chiffre d'affaires", f"{summary['revenue_total']:,.0f}".replace(",", " "), "Cumul historique"),
        stat_tile("Marge", f"{summary['margin_total']:,.0f}".replace(",", " "), "Sous hypothèses cost_price synthétique"),
        stat_tile("Commandes", f"{summary['orders_total']:,}".replace(",", " ")),
        stat_tile("Panier moyen", f"{summary['average_order_value']:,.2f}".replace(",", " ")),
        stat_tile("Produits", f"{summary['n_products']:,}".replace(",", " ")),
        stat_tile("Clients", f"{summary['n_customers']:,}".replace(",", " ")),
    )

    fig = go.Figure(
        data=[
            go.Bar(
                x=["Chiffre d'affaires", "Marge"],
                y=[summary["revenue_total"], summary["margin_total"]],
                marker_color=[CATEGORICAL_ORDER[0], CATEGORICAL_ORDER[2]],
                width=0.5,
            )
        ]
    )
    fig.update_layout(**PLOTLY_LAYOUT, title="CA vs marge (cumul historique)", showlegend=False, height=340)

    return html.Div([tiles, dcc.Graph(figure=fig, config={"displayModeBar": False})])
