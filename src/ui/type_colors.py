"""
Pokemon type → color mapping for Textual UI elements.
Used by menu_ui, display_ui, and party_builder_screen.
"""

_TYPE_BASE = {
    "Normal":   "#888888",
    "Fire":     "#dd4400",
    "Water":    "#2288cc",
    "Electric": "#ccaa00",
    "Grass":    "#228833",
    "Ice":      "#44aacc",
    "Fighting": "#882200",
    "Poison":   "#882288",
    "Ground":   "#aa8833",
    "Flying":   "#6688cc",
    "Psychic":  "#cc2266",
    "Bug":      "#668822",
    "Rock":     "#888844",
    "Ghost":    "#554488",
    "Dragon":   "#4422cc",
    "Dark":     "#443322",
    "Steel":    "#888899",
}


def _make_type_colors(base: dict) -> dict:
    from textual.color import Color
    result = {}
    for type_name, hex_color in base.items():
        color      = Color.parse(hex_color)
        lightened  = color.blend(Color.parse("#ffffff"), 0.4)
        brightness = (color.r * 299 + color.g * 587 + color.b * 114) / 1000
        fg         = "#111111" if brightness > 128 else "#ffffff"
        result[type_name] = {
            "bg":   hex_color,
            "fg":   fg,
            "text": lightened.hex,
        }
    return result


TYPE_COLORS = _make_type_colors(_TYPE_BASE)
