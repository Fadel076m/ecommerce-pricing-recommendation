"""Composants UI partagés entre les pages du dashboard (Jalon 9)."""
from dash import html

from dashboard.icons import icon_svg
from dashboard.theme import (
    BORDER,
    CARD_RADIUS,
    CARD_SHADOW,
    CATEGORICAL,
    STATUS,
    SURFACE,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TILE_TINTS,
)


def _icon_badge(icon: str, tint: str):
    color = CATEGORICAL.get(tint, CATEGORICAL["blue"])
    bg = TILE_TINTS.get(tint, TILE_TINTS["blue"])
    return html.Div(
        html.Img(src=icon_svg(icon, color=color, size=18)),
        style={
            "width": "36px",
            "height": "36px",
            "borderRadius": "10px",
            "backgroundColor": bg,
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "marginBottom": "14px",
        },
    )


def stat_tile(label: str, value: str, sublabel: str | None = None, icon: str = "trend", tint: str = "blue"):
    return html.Div(
        style={
            "backgroundColor": SURFACE,
            "border": f"1px solid {BORDER}",
            "borderRadius": CARD_RADIUS,
            "boxShadow": CARD_SHADOW,
            "padding": "20px 22px",
            "minWidth": "170px",
            "flex": "1",
        },
        children=[
            _icon_badge(icon, tint),
            html.Div(label, style={"color": TEXT_MUTED, "fontSize": "12.5px", "fontWeight": 500}),
            html.Div(value, style={"color": TEXT_PRIMARY, "fontSize": "26px", "fontWeight": 700, "marginTop": "2px", "letterSpacing": "-0.01em"}),
            html.Div(sublabel, style={"color": TEXT_SECONDARY, "fontSize": "12px", "marginTop": "4px"}) if sublabel else None,
        ],
    )


def stat_row(*tiles):
    return html.Div(style={"display": "flex", "gap": "18px", "flexWrap": "wrap", "marginBottom": "24px"}, children=list(tiles))


def card(children, padding="24px"):
    return html.Div(
        style={
            "backgroundColor": SURFACE,
            "border": f"1px solid {BORDER}",
            "borderRadius": CARD_RADIUS,
            "boxShadow": CARD_SHADOW,
            "padding": padding,
        },
        children=children,
    )


def note_banner(text: str):
    """Note contextuelle discrète — pas un avertissement alarmant, juste un repère de lecture."""
    return html.Div(
        text,
        style={
            "backgroundColor": "#f4f5f7",
            "color": TEXT_SECONDARY,
            "fontSize": "13px",
            "padding": "10px 16px",
            "borderRadius": "10px",
            "marginBottom": "22px",
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
            "padding": "4px 12px",
            "borderRadius": "999px",
            "display": "inline-block",
        },
    )


def page_header(title: str, subtitle: str | None = None):
    return html.Div(
        style={"marginBottom": "24px"},
        children=[
            html.H1(title, style={"color": TEXT_PRIMARY, "fontSize": "24px", "fontWeight": 700, "margin": 0}),
            html.Div(subtitle, style={"color": TEXT_MUTED, "fontSize": "13.5px", "marginTop": "4px"}) if subtitle else None,
        ],
    )


def empty_state(text: str):
    return html.Div(
        text,
        style={"color": TEXT_MUTED, "padding": "40px 0", "textAlign": "center", "fontSize": "14px"},
    )
