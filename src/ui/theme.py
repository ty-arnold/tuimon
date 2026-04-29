# ui/app.py
from textual.app import App
from textual.theme import Theme

TUIMON_DARK = Theme(
    name        = "tuimon-dark",
    primary     = "#6655dd",    # $primary     — ui chrome, title, selected icons
    secondary   = "#4444aa",    # $secondary   — borders, dim keys
    accent      = "#aa44ff",    # $accent      — highlights, flinch
    background  = "#0d0d1a",    # $background  — screen bg
    surface     = "#111122",    # $surface     — footer, detail boxes
    panel       = "#1a1a33",    # $panel       — hover, selected bg
    success     = "#44cc44",    # $success     — hp healthy, 2× effective, stat up
    warning     = "#ccaa22",    # $warning     — hp mid, field effects
    error       = "#cc4444",    # $error       — hp low, ½× effective, stat down
    dark        = True,
    variables   = {
        "npc-border":       "#773388",
        "npc-title":        "#cc88dd",
        "player-border":    "#336633",
        "player-title":     "#66cc66",
        "log-bg":           "#080810",
        # ── Python-side Rich markup colors ──────────────────────────
        "text-ui":          "#aaaacc",    # general value text
        "text-muted-ui":    "#555577",    # muted / secondary text
        "text-dim":         "#333344",    # disabled / fainted
        "text-bright":      "#ccccee",    # bright numbers (move detail)
        "text-label":       "#888899",    # stat/field headers
        "hp-empty":         "#222233",    # empty portion of hp bar
        "party-disabled":   "#444466",    # active or fainted pokemon row
        "fainted-bg":       "#111122",    # fainted badge background
        "effect-lock":      "#4488cc",    # locked move / flying / invulnerable
    }
)

CATPPUCCIN_MOCHA = Theme(
    name        = "catppuccin-mocha",
    primary     = "#cba6f7",    # mauve
    secondary   = "#89b4fa",    # blue
    accent      = "#fab387",    # peach
    background  = "#1e1e2e",    # base
    surface     = "#181825",    # mantle
    panel       = "#313244",    # surface0
    success     = "#a6e3a1",    # green
    warning     = "#f9e2af",    # yellow
    error       = "#f38ba8",    # red
    dark        = True,
    variables   = {
        "npc-border":       "#f5c2e7",    # pink
        "npc-title":        "#f5c2e7",    # pink
        "player-border":    "#a6e3a1",    # green
        "player-title":     "#a6e3a1",    # green
        "log-bg":           "#181825",    # mantle
        # ── Python-side Rich markup colors ──────────────────────────
        "text-ui":          "#cdd6f4",    # text
        "text-muted-ui":    "#6c7086",    # subtext0
        "text-dim":         "#45475a",    # surface1
        "text-bright":      "#cdd6f4",    # text
        "text-label":       "#9399b2",    # overlay2
        "hp-empty":         "#313244",    # surface0
        "party-disabled":   "#585b70",    # surface2
        "fainted-bg":       "#181825",    # mantle
        "effect-lock":      "#89b4fa",    # blue
    }
)