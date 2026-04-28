from textual.widgets    import ListView, ListItem, Label, Static, Tabs
from textual.containers import Horizontal
from core.logger     import logger
from data.type_chart import TYPE_CHART
from core.colors     import markup

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
    """
    Derive bg, fg, and text from a base color per type.
    bg  = base color (for badge background)
    fg  = white or black depending on brightness
    text = lighter version of base (for colored text)
    """
    from textual.color import Color
    result = {}
    for type_name, hex_color in base.items():
        color      = Color.parse(hex_color)
        # lighten for text by blending with white
        lightened  = color.blend(Color.parse("#ffffff"), 0.4)
        # fg is white for dark colors, black for light ones
        brightness = (color.r * 299 + color.g * 587 + color.b * 114) / 1000
        fg         = "#111111" if brightness > 128 else "#ffffff"
        result[type_name] = {
            "bg":   hex_color,
            "fg":   fg,
            "text": lightened.hex,
        }
    return result

TYPE_COLORS = _make_type_colors(_TYPE_BASE)

class MenuUIMixin:
    """Handles action pane menu state switching."""

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        if not self._battle_ready:
            return
        event.stop()
        if event.tab is None:
            return
        match event.tab.id:
            case "tab-moves": self.show_move_menu()
            case "tab-party": self.show_party_menu()
            case "tab-items" | "tab-run" | "tab-menu":
                self._show_items()
                self.set_focus(None)

    def _show_items(self) -> None:
        self.query_one("#menu-moves").display      = False
        self.query_one("#menu-moves-rule").display = False
        self.query_one("#menu-party").display      = False
        self.query_one("#menu-items").display      = False
        self.query_one("#detail-pane").display     = False

    def show_main_menu(self) -> None:
        tabs = self.query_one("#menu-tabs", Tabs)
        match tabs.active:
            case "tab-moves": self.show_move_menu()
            case "tab-party": self.show_party_menu()
            case _:           self._show_items()

    def show_move_menu(self) -> None:
        self.query_one("#menu-party").display      = False
        self.query_one("#menu-items").display      = False
        self.query_one("#detail-pane").display     = False

        move_list = self.query_one("#menu-moves", ListView)
        move_list.clear()

        defender_types = self.npc.active().type

        for move in self.player.active().moveset:
            effectiveness = self._get_effectiveness(move, defender_types)
            eff_markup    = self._effectiveness_markup(effectiveness)
            cat_markup    = self._category_markup(move.category)

            item = ListItem(
                Label(move.name, classes="move-name"),
                Label(f"{cat_markup}  {eff_markup}", classes="move-tags", markup=True),
            )
            move_list.append(item)

        self.query_one("#menu-moves").display      = True
        self.query_one("#menu-moves-rule").display = True
        self.query_one("#action-pane").border_title = "actions"
        move_list.index = 0
        move_list.focus()

    def _type_markup(self, move_type: str) -> str:

        short_names = {
            "Normal":   "Norm",
            "Fire":     "Fire",
            "Water":    "Water",
            "Electric": "Elctr",
            "Grass":    "Grass",
            "Ice":      "Ice",
            "Fighting": "Fight",
            "Poison":   "Psn",
            "Ground":   "Grnd",
            "Flying":   "Fly",
            "Psychic":  "Psyc",
            "Bug":      "Bug",
            "Rock":     "Rock",
            "Ghost":    "Ghost",
            "Dragon":   "Drag",
            "Dark":     "Dark",
            "Steel":    "Steel",
        }

        colors = TYPE_COLORS.get(move_type, {"bg": "#555577", "fg": "#ffffff"})
        bg     = colors["bg"]
        fg     = colors["fg"]
        short  = short_names.get(move_type, move_type[:5])
        padded = f" {short:<6}"
        return f"[on {bg}][{fg}]{padded}[/{fg}][/on {bg}]"

    def _pp_markup(self, move) -> str:
        if move.pp == 0:
            return f"[#cc4444]PP:{move.pp}[/#cc4444]"
        else:
            return f"[#555577]PP:{move.pp}[/#555577]"

    def _get_effectiveness(self, move, defender_types: list[str]) -> float:
        from data.type_chart import TYPE_CHART 
        if move.category == "status":
            return 1.0
        multiplier = 1.0
        for dtype in defender_types:
            multiplier *= TYPE_CHART.get(move.type[0], {}).get(dtype, 1.0)
        return multiplier

    def _effectiveness_markup(self, effectiveness: float) -> str:
        if effectiveness == 0:
            return "[#555577]0×[/#555577]"
        elif effectiveness < 1:
            return "[#f38ba8]½×[/#f38ba8]"
        elif effectiveness > 1:
            return "[bold][#a6e3a1]2×[/#a6e3a1][/bold]"
        else:
            return "[#555577]1×[/#555577]"

    def _category_markup(self, category: str) -> str:
        labels = {
            "physical": "Phys",
            "special":  "Spec",
            "status":   "Stat",
        }
        colors = {
            "physical": "#f38ba8",
            "special":  "#89b4fa",
            "status":   "#a6e3a1",
        }
        lbl   = labels.get(category, category[:4])
        color = colors.get(category, "#888899")
        return f"[{color}]{lbl}[/{color}]"

    def show_party_menu(self) -> None:
        party_list = self.query_one("#menu-party", ListView)
        party_list.clear()

        for i, pokemon in enumerate(self.player.party):
            is_active  = i == self.player.selected_mon
            is_fainted = not pokemon.is_alive()
            hp_pct     = int((pokemon.hp / pokemon.max_hp) * 100)
            logger.debug(f"show_party_menu: {pokemon.name} active={is_active} fainted={is_fainted} major_status={pokemon.major_status}")

            # colors based on state
            if is_active or is_fainted:
                name_color = "#444466"
                hp_color   = "#444466"
                bar_char   = "#333344"
            else:
                name_color = "#ffffff"
                hp_color   = "#aaaacc"
                bar_char   = "#44cc44" if hp_pct > 50 else "#ccaa22" if hp_pct > 25 else "#cc4444"

            # status badge
            # status badges — collect all that apply and stack them
            abbrev = {
                "Burn":      "[on #441100][#ff8844] BRN [/#ff8844][/on #441100]",
                "Poison":    "[on #220044][#bb44ff] PSN [/#bb44ff][/on #220044]",
                "Paralysis": "[on #333300][#ffff44] PAR [/#ffff44][/on #333300]",
                "Sleep":     "[on #003344][#44aaff] SLP [/#44aaff][/on #003344]",
                "Freeze":    "[on #001144][#4488ff] FRZ [/#4488ff][/on #001144]",
            }
            badges = []
            if is_active:
                badges.append(" [on #002244][#4488cc] out [/#4488cc][/on #002244]")
            if is_fainted:
                badges.append(" [on #111122][#444466] FNT [/#444466][/on #111122]")
            elif pokemon.major_status:
                b = abbrev.get(pokemon.major_status.name, "")
                if b:
                    badges.append(" " + b)
            else:
                logger.debug(f"show_party_menu: {pokemon.name} fell to else: is_fainted={is_fainted}, major_status={pokemon.major_status}")
            badge = "".join(badges)
            badge_width = 6 * len(badges)

            # hp bar using block characters
            pane_width = self.query_one("#action-pane").size.width
            available  = pane_width - 2  # border(2) + action-pane padding(4) + party-item padding(2)
            bar_width  = available
            filled     = int(bar_width * hp_pct / 100)
            empty      = bar_width - filled
            bar        = f"[{bar_char}]{'─' * filled}[/{bar_char}][#222233]{'─' * empty}[/#222233]"

            # name left, level right-anchored
            lv_str  = f"Lv.{pokemon.lvl}"
            gap     = available - len(pokemon.name) - len(lv_str)
            name_lv = f"[{name_color}]{pokemon.name}[/{name_color}]" + " " * max(0, gap) + f"[#555577]{lv_str}[/#555577]"

            # hp left, badges immediately after
            hp_str  = f"{pokemon.hp} / {pokemon.max_hp}"
            hp_gap  = available - len(hp_str) - badge_width
            hp_line = (
                f"[{hp_color}]{hp_str}[/{hp_color}]"
                + " " * max(0, hp_gap)
                + badge
            )

            label = Label(
                f"{name_lv}\n{bar}\n{hp_line}",
                markup=True,
                classes="party-item"
            )
            party_list.append(ListItem(label))

        self.query_one("#menu-moves").display      = False
        self.query_one("#menu-moves-rule").display = False
        self.query_one("#menu-items").display      = False
        self.query_one("#detail-pane").display     = False
        self.query_one("#menu-party").display      = True
        self.query_one("#action-pane").border_title = "actions"
        party_list.index = 0
        party_list.focus()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        logger.debug(f"on_list_view_selected: list={event.list_view.id} idx={event.list_view.index}")
        event.stop()
        if not self._input_enabled:
            return
        idx = event.list_view.index

        if event.list_view.id == "menu-moves":
            moveset = self.player.active().moveset
            if idx >= len(moveset):
                self.show_main_menu()
            else:
                move = moveset[idx]
                # these MUST happen before run_worker
                self.controller.select_player_move(move)
                self.controller.select_npc_move()
                self.show_main_menu()
                # worker starts AFTER moves are selected
                self.run_worker(self.resolve_and_display(), thread=False)

        elif event.list_view.id == "menu-party":
            party = self.player.party
            if idx >= len(party):
                self.show_main_menu()
            else:
                pokemon = party[idx]
                if not pokemon.is_alive():
                    self.log_message(f"{pokemon.name} has fainted!")
                elif idx == self.player.selected_mon:
                    self.log_message(f"{pokemon.name} is already out!")
                else:
                    self.player.selected_mon = idx
                    self.log_message(f"Go, {pokemon.name}!")
                    self.update_display()
                    self.show_main_menu()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Update detail pane when highlighted item changes."""
        if event.list_view.id != "menu-moves":
            return
        if event.item is None:
            return

        idx     = event.list_view.index
        moveset = self.player.active().moveset
        if idx is None or idx >= len(moveset):
            return

        move = moveset[idx]
        self._show_move_detail(move)

    def _show_move_detail(self, move) -> None:
        type_key   = move.type[0].strip().capitalize()
        type_color = TYPE_COLORS.get(type_key, {}).get("text", "#aaaacc")
        acc        = "—" if move.acc is None else f"{int(move.acc * 100)}%"

        rows = [
            ("Type",     move.type[0],                          type_color),
            ("Power",    str(move.power) if move.power else "—", "#ccccee"),
            ("Accuracy", acc,                                    "#ccccee"),
            ("PP",       f"{move.pp}/{move.max_pp}",             "#ccccee"),
        ]
        if move.priority != 0:
            rows.append(("Priority", str(move.priority),        "#ccccee"))
        if move.recoil > 0:
            rows.append(("Recoil",   f"{int(move.recoil * 100)}%", "#f38ba8"))
        if move.status_effect:
            rows.append(("Effect",   move.status_effect.name,   "#f9e2af"))
        if move.multi_turn:
            rows.append(("Effect",   "Charge → invulnerable",   "#f9e2af"))
        if move.flinch_chance > 0:
            rows.append(("Flinch",   f"{int(move.flinch_chance * 100)}%", "#fab387"))

        self.query_one("#detail-name", Label).update(f"[bold]{move.name}[/bold]")

        grid = self.query_one("#detail-grid")
        grid.remove_children()
        for label, value, color in rows:
            grid.mount(Label(label, classes="detail-label"))
            grid.mount(Label(f"[{color}]{value}[/{color}]", classes="detail-value", markup=True))

        # update description label separately
        desc_label = self.query_one("#detail-description", Label)
        if move.description:
            desc_label.update(f"[#aaaacc]{move.description}[/#aaaacc]")
            desc_label.display = True
        else:
            desc_label.display = False

        self.query_one("#detail-pane").display = True