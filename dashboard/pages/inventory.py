"""Page Inventory (Jalon 9) : risque de rupture de stock, via l'API.

Stock synthétique (Jalon 2, seed=42) — cf. docs/data_dictionary.md. Jours de
stock estimés = closing_stock / vente_moyenne_quotidienne observée."""
import dash
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from dashboard.api_client import get_kpi_inventory
from dashboard.components import disclaimer_banner, empty_state, page_title, status_badge
from dashboard.theme import BORDER, PLOTLY_LAYOUT, STATUS, SURFACE, TEXT_MUTED, TEXT_PRIMARY, stock_risk_status

dash.register_page(__name__, path="/inventory", name="Inventory")

STATUS_LABELS = {"critical": "Rupture imminente", "serious": "Risque élevé", "warning": "À surveiller", "good": "Stock sain"}

layout = html.Div(
    [
        page_title("Inventory — risque de rupture de stock"),
        disclaimer_banner(
            "Stock généré synthétiquement (seed=42, cf. docs/data_dictionary.md) — instantané, pas une série "
            "temporelle quotidienne réelle (voir docs/data_dictionary.md, section fact_inventory)."
        ),
        dcc.Loading(html.Div(id="inventory-content")),
    ]
)


@callback(Output("inventory-content", "children"), Input("inventory-content", "id"))
def load_inventory(_):
    items = get_kpi_inventory(20)
    if not items:
        return empty_state("Aucune donnée de stock disponible.")

    for item in items:
        item["status"] = stock_risk_status(item.get("days_of_stock_estimated"))

    fig = go.Figure(
        data=[
            go.Bar(
                x=[item["days_of_stock_estimated"] for item in items][::-1],
                y=[f"{item['product_id']} — {item['product_name'][:28]}" for item in items][::-1],
                orientation="h",
                marker_color=[STATUS[item["status"]] for item in items][::-1],
                hovertemplate="%{y}<br>%{x} jours de stock estimés<extra></extra>",
            )
        ]
    )
    fig.update_layout(**PLOTLY_LAYOUT, title="Produits les plus à risque (jours de stock estimés)", showlegend=False, height=max(360, 24 * len(items)))

    rows = [
        html.Tr(
            [
                html.Td(item["product_id"], style={"padding": "8px 12px", "color": TEXT_PRIMARY, "fontWeight": 600}),
                html.Td(item["product_name"], style={"padding": "8px 12px", "color": TEXT_PRIMARY}),
                html.Td(str(item["closing_stock"]), style={"padding": "8px 12px", "color": TEXT_MUTED}),
                html.Td(f"{item['days_of_stock_estimated']:.1f} j" if item["days_of_stock_estimated"] is not None else "—", style={"padding": "8px 12px", "color": TEXT_MUTED}),
                html.Td(status_badge(item["status"], STATUS_LABELS[item["status"]]), style={"padding": "8px 12px"}),
            ]
        )
        for item in items
    ]
    table = html.Table(
        style={"width": "100%", "borderCollapse": "collapse", "backgroundColor": SURFACE, "border": f"1px solid {BORDER}", "borderRadius": "8px", "marginTop": "20px"},
        children=[
            html.Thead(
                html.Tr(
                    [
                        html.Th("Produit", style={"textAlign": "left", "padding": "8px 12px"}),
                        html.Th("Nom", style={"textAlign": "left", "padding": "8px 12px"}),
                        html.Th("Stock", style={"textAlign": "left", "padding": "8px 12px"}),
                        html.Th("Jours de stock", style={"textAlign": "left", "padding": "8px 12px"}),
                        html.Th("Statut", style={"textAlign": "left", "padding": "8px 12px"}),
                    ]
                )
            ),
            html.Tbody(rows),
        ],
    )

    return html.Div([dcc.Graph(figure=fig, config={"displayModeBar": False}), table])
