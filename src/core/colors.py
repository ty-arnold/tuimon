"""
Centralized color definitions for Rich markup used in game messages
and display formatting. Update these to change colors app-wide.
"""

# combat log message colors
LOG = {
    "move":       "#8888aa",    # "{pokemon} used {move}!"
    "damage":     "#f38ba8",    # "{pokemon} took {damage} damage!"
    "healing":    "#a6e3a1",    # "{pokemon} restored {amount} HP!"
    "status":     "#f9e2af",    # status effect messages
    "super":      "#cba6f7",    # "It's super effective!"
    "weak":       "#6c7086",    # "It's not very effective..."
    "miss":       "#585b70",    # "attack missed!"
    "crit":       "#fab387",    # "Critical hit!"
    "info":       "#89b4fa",    # charge turns, invulnerability
    "turn":       "#313244",    # turn dividers
    "fainted":    "#f38ba8",    # "{pokemon} fainted!"
    "win":        "#a6e3a1",    # "You won!"
    "lose":       "#f38ba8",    # "You lost!"
}

# stat stage colors
STAGES = {
    "positive_bg":   "#112211",
    "positive_text": "#a6e3a1",
    "negative_bg":   "#221111",
    "negative_text": "#f38ba8",
    "neutral":       "#585b70",
}

# status badge colors
STATUS = {
    "BRN": {"bg": "#441100", "text": "#ff8844"},
    "PSN": {"bg": "#220044", "text": "#bb44ff"},
    "PAR": {"bg": "#333300", "text": "#ffff44"},
    "SLP": {"bg": "#003344", "text": "#44aaff"},
    "FRZ": {"bg": "#001144", "text": "#4488ff"},
    "CFZ": {"bg": "#222200", "text": "#aaaa44"},
}

def markup(text: str, color: str) -> str:
    """Wrap text in Rich color markup."""
    return f"[{color}]{text}[/{color}]"

def log_color(key: str, text: str) -> str:
    """Apply a log color to text."""
    return markup(text, LOG[key])

def stage_markup(name: str, val: int) -> str:
    """Format a stat stage with appropriate color."""
    if val > 0:
        return (
            f"[on {STAGES['positive_bg']}]"
            f"[{STAGES['positive_text']}] {name}+{val} "
            f"[/{STAGES['positive_text']}]"
            f"[/on {STAGES['positive_bg']}]"
        )
    elif val < 0:
        return (
            f"[on {STAGES['negative_bg']}]"
            f"[{STAGES['negative_text']}] {name}{val} "
            f"[/{STAGES['negative_text']}]"
            f"[/on {STAGES['negative_bg']}]"
        )
    else:
        return f"[{STAGES['neutral']}]{name} 0[/{STAGES['neutral']}]"

def status_markup(status_name: str) -> str:
    """Format a status badge with appropriate color."""
    colors = STATUS.get(status_name, {"bg": "#333333", "text": "#ffffff"})
    return (
        f"[on {colors['bg']}]"
        f"[{colors['text']}] {status_name} "
        f"[/{colors['text']}]"
        f"[/on {colors['bg']}]"
    )