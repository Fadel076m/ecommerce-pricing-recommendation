"""Icônes SVG minimalistes (traits fins, style ligne) encodées en data-URI — pas
de dépendance à une librairie d'icônes externe."""
from urllib.parse import quote

_PATHS = {
    "home": '<path d="M4 12L12 5l8 7"/><path d="M6 10.5V19a1 1 0 0 0 1 1h4v-5h2v5h4a1 1 0 0 0 1-1v-8.5"/>',
    "trend": '<path d="M4 17l5-5 4 4 7-8"/><path d="M15 8h5v5"/>',
    "tag": '<path d="M3 11l8-8h6a2 2 0 0 1 2 2v6l-8 8a2 2 0 0 1-3 0l-5-5a2 2 0 0 1 0-3z"/><circle cx="15" cy="9" r="1.4" fill="{color}" stroke="none"/>',
    "users": '<circle cx="9" cy="8" r="3.2"/><path d="M3.5 19c0-3 2.5-5.2 5.5-5.2s5.5 2.2 5.5 5.2"/><circle cx="17" cy="9" r="2.6"/><path d="M15.8 13.6c2.4.3 4.2 2.3 4.2 5.4"/>',
    "box": '<path d="M3 8l9-5 9 5-9 5-9-5z"/><path d="M3 8v9l9 5 9-5V8"/><path d="M12 13v9"/>',
    "cart": '<circle cx="9" cy="20" r="1.2"/><circle cx="17" cy="20" r="1.2"/><path d="M3 4h2l2.4 12.2a2 2 0 0 0 2 1.6h7.4a2 2 0 0 0 2-1.6L21 8H6"/>',
    "coin": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5v9M9.3 9.5a2.4 2 0 0 1 2.7-1.6c1.6 0 2.7.8 2.7 1.9 0 2.6-5.4 1.3-5.4 3.9 0 1.1 1.1 1.9 2.7 1.9s2.9-.7 2.9-1.9"/>',
    "alert": '<path d="M12 3.5L2.5 20h19L12 3.5z"/><path d="M12 10v4.5"/><circle cx="12" cy="17.3" r="0.4" fill="{color}" stroke="none"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M20 20l-5-5"/>',
}


def icon_svg(name: str, color: str = "#0b0b0b", size: int = 18, stroke_width: float = 1.8) -> str:
    path = _PATHS[name].format(color=color)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">'
        f"{path}</svg>"
    )
    return f"data:image/svg+xml,{quote(svg)}"
