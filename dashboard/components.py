"""Composants UI partagés entre les pages du dashboard (Jalon 9)."""
from dash import html

from dashboard.theme import BORDER, STATUS, SURFACE, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY


def stat_tile(label: str, value: str, sublabel: str | None = None):
    return html.Div(
        style={
            "backgroundColor": SURFACE,
            "border": f"1px solid {BORDER}",
            "borderRadius": "8px",
            "padding": "16px 20px",
            "minWidth": "160px",
            "flex": "1",
        },
        children=[
            html.Div(label, style={"color": TEXT_MUTED, "fontSize": "12px", "textTransform": "uppercase", "letterSpacing": "0.03em"}),
            html.Div(value, style={"color": TEXT_PRIMARY, "fontSize": "28px", "fontWeight": 700, "marginTop": "4px"}),
            html.Div(sublabel, style={"color": TEXT_SECONDARY, "fontSize": "12px", "marginTop": "2px"}) if sublabel else None,
        ],
    )


def stat_row(*tiles):
    return html.Div(style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "24px"}, children=list(tiles))


def disclaimer_banner(text: str):
    return html.Div(
        text,
        style={
            "backgroundColor": "#f0efec",
            "color": TEXT_SECONDARY,
            "fontSize": "13px",
            "padding": "10px 16px",
            "borderRadius": "6px",
            "marginBottom": "20px",
            "borderLeft": f"3px solid {TEXT_MUTED}",
        },
    )


def status_badge(status: str, label: str):
    return html.Span(
        label,
        style={
            "backgroundColor": STATUS.get(status, TEXT_MUTED),
            "color": "#ffffff",
            "fontSize": "11px",
            "fontWeight": 600,
            "padding": "3px 10px",
            "borderRadius": "999px",
            "display": "inline-block",
        },
    )


def page_title(text: str):
    return html.H1(text, style={"color": TEXT_PRIMARY, "fontSize": "22px", "marginBottom": "16px"})


def empty_state(text: str):
    return html.Div(text, style={"color": TEXT_MUTED, "fontStyle": "italic", "padding": "24px 0"})
