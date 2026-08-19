"""Page Stock : produits à risque de rupture."""
import dash
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from dashboard.api_client import get_kpi_inventory
from dashboard.components import card, empty_state, page_header, status_badge
from dashboard.theme import BORDER, PLOTLY_LAYOUT, STATUS, TEXT_MUTED, TEXT_PRIMARY, stock_risk_status

dash.register_page(__name__, path="/inventory", name="Stock")

STATUS_LABELS = {"critical": "Rupture imminente", "serious": "Risque élevé", "warning": "À surveiller", "good": "Stock sain"}

layout = html.Div(
    [
        page_header("Suivi du stock", "Identifiez rapidement les produits à réapprovisionner en priorité."),
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
                marker_line_width=0,
                hovertemplate="%{y}<br>%{x} jours de stock restants<extra></extra>",
            )
        ]
    )
    fig.update_layout(**PLOTLY_LAYOUT, title="Produits les plus urgents à réapprovisionner", showlegend=False, height=max(360, 26 * len(items)))

    rows = [
        html.Tr(
            [
                html.Td(item["product_id"], style={"padding": "12px 16px", "color": TEXT_PRIMARY, "fontWeight": 600}),
                html.Td(item["product_name"], style={"padding": "12px 16px", "color": TEXT_PRIMARY}),
                html.Td(str(item["closing_stock"]), style={"padding": "12px 16px", "color": TEXT_MUTED}),
                html.Td(f"{item['days_of_stock_estimated']:.1f} j" if item["days_of_stock_estimated"] is not None else "—", style={"padding": "12px 16px", "color": TEXT_MUTED}),
                html.Td(status_badge(item["status"], STATUS_LABELS[item["status"]]), style={"padding": "12px 16px"}),
            ],
            style={"borderTop": f"1px solid {BORDER}"},
        )
        for item in items
    ]
    table = html.Table(
        style={"width": "100%", "borderCollapse": "collapse"},
        children=[
            html.Thead(
                html.Tr(
                    [
                        html.Th("Produit", style={"textAlign": "left", "padding": "0 16px 10px", "color": TEXT_MUTED, "fontSize": "12px", "fontWeight": 500}),
                        html.Th("Nom", style={"textAlign": "left", "padding": "0 16px 10px", "color": TEXT_MUTED, "fontSize": "12px", "fontWeight": 500}),
                        html.Th("Stock", style={"textAlign": "left", "padding": "0 16px 10px", "color": TEXT_MUTED, "fontSize": "12px", "fontWeight": 500}),
                        html.Th("Autonomie", style={"textAlign": "left", "padding": "0 16px 10px", "color": TEXT_MUTED, "fontSize": "12px", "fontWeight": 500}),
                        html.Th("Statut", style={"textAlign": "left", "padding": "0 16px 10px", "color": TEXT_MUTED, "fontSize": "12px", "fontWeight": 500}),
                    ]
                )
            ),
            html.Tbody(rows),
        ],
    )

    return html.Div(
        [
            card(dcc.Graph(figure=fig, config={"displayModeBar": False})),
            html.Div(style={"height": "24px"}),
            card(table, padding="20px 8px"),
        ]
    )
