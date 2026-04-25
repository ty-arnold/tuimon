# ui/screens/title_screen.py
import os
from textual.screen     import Screen
from textual.app        import ComposeResult
from textual.widgets    import Static, Footer, ListView, ListItem, Label
from textual.containers import Vertical, Horizontal, Center
from textual.binding    import Binding

ASCII_ART = """████████╗██╗   ██╗██╗███╗   ███╗ ██████╗ ███╗   ██╗
╚══██╔══╝██║   ██║██║████╗ ████║██╔═══██╗████╗  ██║
   ██║   ██║   ██║██║██╔████╔██║██║   ██║██╔██╗ ██║
   ██║   ██║   ██║██║██║╚██╔╝██║██║   ██║██║╚██╗██║
   ██║   ╚██████╔╝██║██║ ╚═╝ ██║╚██████╔╝██║ ╚████║
   ╚═╝    ╚═════╝ ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝"""

class TitleScreen(Screen):

    CSS_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "styles", "title.tcss"
    )

    BINDINGS = [
        Binding("a",     "vs_ai",     "vs. AI"),
        Binding("o",     "vs_online", "vs. Online"),
        Binding("t",     "team",      "Team Builder"),
        Binding("s",     "shop",      "Shop"),
        Binding("q",     "quit",      "Quit"),
        Binding("enter", "select",    "Select"),
        Binding("up",    "cursor_up",   show=False),
        Binding("down",  "cursor_down", show=False),
    ]

    # track selected index for keyboard navigation
    _selected: int = 0
    _items = [
        ("vs. AI",       "⚔",  "a",  "menu-vs-ai"),     # swords
        ("vs. Online",   "⊹",  "o",  "menu-vs-online"),  # network/star
        ("Team Builder", "⊞",  "t",  "menu-team"),       # grid/team
        ("Shop",         "◈",  "s",  "menu-shop"),       # diamond
        ("Quit",         "⊗",  "q",  "menu-quit"),       # close/exit
    ]

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="title-container"):
                yield Static(ASCII_ART, id="ascii-art")
                yield Static("POKEMON BATTLE SIMULATOR", id="subtitle")
                with Vertical(id="title-menu"):
                    for i, (label, icon, key, item_id) in enumerate(self._items):
                        with Horizontal(id=item_id, classes="menu-item"):
                            yield Static(icon,  classes="menu-icon")
                            yield Static(label, classes="menu-label")
                            yield Static(key,   classes="menu-key")
                yield Static("v0.1.0", id="version")
        yield Footer()

    def on_mount(self) -> None:
        self._update_selection()

    def _update_selection(self) -> None:
        for i, (_, _, _,item_id) in enumerate(self._items):
            widget = self.query_one(f"#{item_id}", Horizontal)
            if i == self._selected:
                widget.add_class("selected")
            else:
                widget.remove_class("selected")

    def action_cursor_up(self) -> None:
        self._selected = (self._selected - 1) % len(self._items)
        self._update_selection()

    def action_cursor_down(self) -> None:
        self._selected = (self._selected + 1) % len(self._items)
        self._update_selection()

    def action_select(self) -> None:
        match self._selected:
            case 0: self.action_vs_ai()
            case 1: self.action_vs_online()
            case 2: self.action_team()
            case 3: self.action_shop()
            case 4: self.action_quit()

    def on_click(self, event) -> None:
        # check the clicked widget and its parent for a menu item id
        widget    = event.widget
        widget_id = widget.id or (widget.parent.id if widget.parent else None)

        for i, (_, _, item_id) in enumerate(self._items):
            if widget_id == item_id:
                self._selected = i
                self._update_selection()
                self.action_select()
                return

    def action_vs_ai(self) -> None:
        from core.presets import get_test_player, get_test_npc
        from ui.screens.battle_screen import BattleScreen
        player = get_test_player()
        npc    = get_test_npc()
        self.app.push_screen(BattleScreen(player, npc))

    def action_vs_online(self) -> None:
        self.notify("Coming soon!", severity="warning")

    def action_team(self) -> None:
        self.notify("Coming soon!", severity="warning")

    def action_shop(self) -> None:
        self.notify("Coming soon!", severity="warning")

    def action_quit(self) -> None:
        self.app.exit()