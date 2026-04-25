# ui/app.py
from textual.app import App
from textual.theme import Theme

TUIMON_DARK = Theme(
    name        = "tuimon-dark",
    primary     = "#6655dd",    # $primary     — ui chrome, title, selected icons
    secondary   = "#4444aa",    # $secondary   — borders, dim keys
    accent      = "#aa44ff",    # $accent      — super effective
    background  = "#0d0d1a",    # $background  — screen bg
    surface     = "#111122",    # $surface     — footer, detail boxes
    panel       = "#1a1a33",    # $panel       — hover, selected bg
    success     = "#44cc44",    # $success     — hp bar healthy, player title
    warning     = "#ccaa22",    # $warning     — hp bar mid, status
    error       = "#cc4444",    # $error       — hp bar low, damage
    dark        = True,
    variables   = {
        # these are accessible via app.get_css_variables()
        # but NOT via $ in CSS — keep for Python-side color access only
        "npc-border":       "#773388",
        "npc-title":        "#cc88dd",
        "player-border":    "#336633",
        "player-title":     "#66cc66",
        "log-bg":           "#080810",
        "sprite-npc":       "#884499",
        "sprite-player":    "#336633",
        "log-bg":           "#080810",
    }
)

CATPPUCCIN_MOCHA = Theme(
    name        = "catppuccin-mocha",
    primary     = "#cba6f7",    # mauve
    secondary   = "#89b4fa",    # blue
    accent      = "#f5c2e7",    # pink
    background  = "#1e1e2e",    # base
    surface     = "#181825",    # mantle
    panel       = "#313244",    # surface0
    success     = "#a6e3a1",    # green
    warning     = "#f9e2af",    # yellow
    error       = "#f38ba8",    # red
    dark        = True,
    variables   = {
        # npc/player panels — keep semantic meaning
        "npc-border":       "#f5c2e7",    # pink
        "npc-title":        "#f5c2e7",    # pink
        "player-border":    "#a6e3a1",    # green
        "player-title":     "#a6e3a1",    # green
        "log-bg":           "#11111b",    # crust
        "sprite-npc":       "#eba0ac",    # maroon
        "sprite-player":    "#a6e3a1",    # green
        "log-bg":           "#181825"
    }
)