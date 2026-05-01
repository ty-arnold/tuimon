import os
from enum import Enum, auto

from textual.app        import ComposeResult
from textual.screen     import Screen, ModalScreen
from textual.widgets    import Footer, ListView, ListItem, Label, Static, Input, Rule, Tabs, Tab
from textual.containers import Horizontal, Vertical, Container, ScrollableContainer
from textual.worker     import Worker, WorkerState
from textual.message    import Message
from textual.events     import Key

from pokemon.cache_manager  import (
    get_pokemon_cache, get_move_cache,
    dict_to_pokemon, dict_to_move, move_to_dict, save_move_cache,
    save_pokemon_cache,
)
from pokemon.gen3_names    import get_gen3_names
from saves.teams_save      import load_teams, save_teams
from saves.inventory_save  import load_inventory
from data.icon_cache       import get_icon
from ui.palette            import Colors
from ui.mixins.menu_ui     import TYPE_COLORS
from core.logger           import logger


MAX_PARTY = 6
MAX_MOVES = 4


class State(Enum):
    PARTY       = auto()   # left panel focused
    INVENTORY   = auto()   # middle grid focused
    POKEMON     = auto()   # right detail focused (move slots active)
    MOVE_SEARCH = auto()   # move search pane visible


class RenameTeamModal(Screen):
    """Modal for renaming a team."""

    CSS = """
    RenameTeamModal {
        align: center middle;
    }
    #rename-container {
        width: 36;
        height: auto;
        padding: 1 2;
        border: thick $primary;
        background: $surface;
    }
    #rename-label {
        margin-bottom: 1;
    }
    #rename-input {
        margin-bottom: 1;
    }
    """

    def __init__(self, current_name: str) -> None:
        super().__init__()
        self._current = current_name

    def compose(self) -> ComposeResult:
        with Container(id="rename-container"):
            yield Label(f"Rename '{self._current}':", id="rename-label")
            yield Input(value=self._current, id="rename-input")
            yield Label("Enter to confirm, Esc to cancel")

    def on_input_submitted(self) -> None:
        name = self.query_one("#rename-input", Input).value.strip()
        self.dismiss(name if name else None)

    def on_key(self, event: Key) -> None:
        if event.key == "escape":
            self.dismiss(None)


class PokemonCell(Static):
    """A clickable inventory cell showing a 12×6 icon sprite."""

    class Highlighted(Message):
        def __init__(self, name: str) -> None:
            super().__init__()
            self.name = name

    class Chosen(Message):
        def __init__(self, name: str) -> None:
            super().__init__()
            self.name = name

    class Navigate(Message):
        def __init__(self, direction: str) -> None:
            super().__init__()
            self.direction = direction

    class Escaped(Message):
        pass

    def __init__(self, name: str, **kwargs) -> None:
        self.poke_name = name
        super().__init__("\n".join(get_icon(name)), **kwargs)
        self.can_focus = True

    def on_mount(self) -> None:
        self.border_title = self.poke_name.replace("-", " ").title()

    def on_focus(self) -> None:
        self.post_message(self.Highlighted(self.poke_name))

    def on_click(self) -> None:
        self.post_message(self.Chosen(self.poke_name))

    def on_key(self, event: Key) -> None:
        if event.key in ("up", "down", "left", "right"):
            self.post_message(self.Navigate(event.key))
            event.prevent_default()
        elif event.key == "escape":
            self.post_message(self.Escaped())
            event.stop()


class PartyBuilderScreen(Screen):

    CSS_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "styles", "party_builder.tcss"
    )

    BINDINGS = [
        ("escape",     "back",        "Back"),
        ("d",          "delete",      "Delete"),
        ("shift+up",   "move_up",     "Move Up"),
        ("shift+down", "move_down",   "Move Down"),
        ("r",          "rename_team", "Rename"),
        ("q",          "quit_screen", "Quit"),
    ]

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def __init__(self) -> None:
        super().__init__()
        self._teams:        list[dict] = load_teams()
        self._inventory:    list[dict] = load_inventory()
        self._active_team:  int        = 0
        self._party:        list[dict] = self._teams[0]["party"]
        self._state:        State      = State.PARTY
        self._selected_slot: int       = 0
        self._selected_move: int       = 0
        self._fetching:     bool       = False
        self._detail_name:  str | None = None  # Pokémon currently shown in right pane

    def compose(self) -> ComposeResult:
        with Horizontal(id="pb-main"):
            # ── Left: team tabs + party slots ──────────────────────────────
            with Container(id="party-panel"):
                yield Tabs(
                    *[Tab(t["name"], id=f"team-{i}") for i, t in enumerate(self._teams)],
                    id="team-tabs",
                )
                for i in range(MAX_PARTY):
                    yield ListItem(Label("", id=f"slot-label-{i}"), id=f"slot-{i}")

            # ── Middle: search + scrollable icon grid ──────────────────────
            with Container(id="inventory-panel"):
                yield Label("search", id="inv-search-label")
                yield Input(placeholder="", id="inv-search")
                with ScrollableContainer(id="inv-scroll"):
                    yield Container(id="inv-grid")

            # ── Right: detail + move search ─────────────────────────────────
            with Container(id="detail-panel"):
                with Horizontal(id="poke-header"):
                    yield Label("", id="poke-name")
                    yield Label("", id="poke-level")
                yield Label("", id="poke-types")
                yield Static("", id="poke-stats")
                yield Rule()
                yield Label("moves", id="moves-header")
                for i in range(MAX_MOVES):
                    yield ListItem(Label("", id=f"move-label-{i}"), id=f"move-slot-{i}")
                with Container(id="move-search-pane"):
                    yield Input(placeholder="Search moves…", id="move-input")
                    yield Label("", id="move-loading")
                    yield ListView(id="move-results")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#party-panel").border_title   = "party"
        self.query_one("#inventory-panel").border_title = "inventory"
        self.query_one("#detail-panel").border_title  = "detail"
        for i in range(MAX_PARTY):
            self.query_one(f"#slot-{i}").can_focus = True
        for i in range(MAX_MOVES):
            self.query_one(f"#move-slot-{i}").can_focus = True
        self._refresh_party_list()
        self._mount_inventory()
        self._set_state(State.PARTY)

    # ── State machine ──────────────────────────────────────────────────────────

    def _set_state(self, state: State) -> None:
        self._state = state

        self.query_one("#move-search-pane").display = state == State.MOVE_SEARCH

        if state == State.PARTY:
            self.query_one(f"#slot-{self._selected_slot}").focus()

        elif state == State.INVENTORY:
            cells = [c for c in self.query(".pokemon-cell") if c.display]
            if cells:
                cells[0].focus()

        elif state == State.POKEMON:
            self._refresh_poke_detail()
            self.query_one(f"#move-slot-{self._selected_move}").focus()

        elif state == State.MOVE_SEARCH:
            inp = self.query_one("#move-input", Input)
            inp.value = ""
            inp.focus()
            self._filter_moves("")

    # ── Party list ─────────────────────────────────────────────────────────────

    def _refresh_party_list(self) -> None:
        c = Colors(self.app)
        for i in range(MAX_PARTY):
            label = self.query_one(f"#slot-label-{i}", Label)
            item  = self.query_one(f"#slot-{i}",       ListItem)

            if i < len(self._party):
                slot  = self._party[i]
                name  = slot["name"].capitalize()
                types = self._poke_type_markup(slot["name"], c)
                label.update(f"[bold]{name}[/bold]  {types}")
            else:
                label.update(f"[{c.text_dim}](empty)[/{c.text_dim}]")

            if i == self._selected_slot:
                item.add_class("selected")
            else:
                item.remove_class("selected")

    # ── Inventory grid ─────────────────────────────────────────────────────────

    def _mount_inventory(self) -> None:
        """Mount all cells once. Use _filter_inventory() to show/hide by query."""
        grid  = self.query_one("#inv-grid", Container)
        cells = [
            PokemonCell(entry["name"], classes="pokemon-cell", id=f"cell-{entry['name']}")
            for entry in self._inventory
        ]
        grid.mount(*cells)

    def _filter_inventory(self, query: str = "") -> None:
        """Show/hide existing cells without re-mounting (avoids duplicate ID errors)."""
        q = query.lower().strip()
        for cell in self.query(".pokemon-cell"):
            cell.display = not q or q in cell.poke_name

    # ── Detail pane ────────────────────────────────────────────────────────────

    def _show_detail(self, name: str) -> None:
        self._detail_name = name
        c    = Colors(self.app)
        data = get_pokemon_cache().get(name.lower(), {})
        lvl  = next(
            (e.get("level", 50) for e in self._inventory if e["name"] == name.lower()),
            50,
        )

        self.query_one("#poke-name",  Label).update(f"[bold]{name.capitalize()}[/bold]")
        self.query_one("#poke-level", Label).update(f"[{c.text_muted_ui}]Lv.{lvl}[/{c.text_muted_ui}]")
        self.query_one("#poke-types", Label).update(self._poke_type_markup(name, c))
        self.query_one("#poke-stats", Static).update(self._format_stats(data, c))

        # Show moves from the party slot if this Pokémon is in the active party
        party_slot = next(
            (s for s in self._party if s["name"].lower() == name.lower()), None
        )
        move_cache = get_move_cache()
        for i in range(MAX_MOVES):
            label = self.query_one(f"#move-label-{i}", Label)
            item  = self.query_one(f"#move-slot-{i}",  ListItem)
            slugs = party_slot.get("moves", []) if party_slot else []

            if i < len(slugs):
                slug       = slugs[i]
                move_data  = move_cache.get(slug, {})
                move_name  = move_data.get("name", slug.replace("-", " ").title())
                move_type  = (move_data.get("type") or ["?"])[0]
                type_color = TYPE_COLORS.get(move_type, {}).get("text", c.text_ui)
                cat_markup = self._cat_markup(move_data.get("category", ""), c)
                label.update(f"[{c.text_ui}]{move_name}[/{c.text_ui}]  [{type_color}]{move_type}[/{type_color}]  {cat_markup}")
            else:
                label.update(f"[{c.text_dim}](empty)[/{c.text_dim}]")

            if i == self._selected_move:
                item.add_class("selected")
            else:
                item.remove_class("selected")

    def _refresh_poke_detail(self) -> None:
        if self._detail_name:
            self._show_detail(self._detail_name)

    # ── Event handlers ─────────────────────────────────────────────────────────

    def on_pokemon_cell_escaped(self, event: PokemonCell.Escaped) -> None:
        self.action_back()

    def on_pokemon_cell_navigate(self, event: PokemonCell.Navigate) -> None:
        if self._state != State.INVENTORY:
            return
        cells = [c for c in self.query(".pokemon-cell") if c.display]
        if not cells:
            return
        try:
            idx = cells.index(self.focused)
        except ValueError:
            idx = 0
        cols = 4
        if event.direction == "right":
            idx = min(idx + 1, len(cells) - 1)
        elif event.direction == "left":
            idx = max(idx - 1, 0)
        elif event.direction == "down":
            idx = min(idx + cols, len(cells) - 1)
        elif event.direction == "up":
            idx = max(idx - cols, 0)
        cells[idx].focus(scroll_visible=True)

    def on_pokemon_cell_highlighted(self, event: PokemonCell.Highlighted) -> None:
        if self._state != State.INVENTORY:
            return
        self._show_detail(event.name)

    def on_pokemon_cell_chosen(self, event: PokemonCell.Chosen) -> None:
        if self._state != State.INVENTORY:
            return
        """Fill the selected party slot with this Pokémon."""
        name      = event.name
        slot_data = {"name": name, "level": 50, "moves": []}

        if self._selected_slot < len(self._party):
            self._party[self._selected_slot] = slot_data
        else:
            while len(self._party) < self._selected_slot:
                self._party.append(None)
            self._party.append(slot_data)

        self._teams[self._active_team]["party"] = self._party
        save_teams(self._teams)
        self._refresh_party_list()

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        if event.tab is None:
            return
        tab_id = event.tab.id  # "team-0", "team-1", ...
        try:
            idx = int(tab_id.split("-")[1])
        except (IndexError, ValueError):
            return
        self._active_team   = idx
        self._party         = self._teams[idx]["party"]
        self._selected_slot = 0
        self._refresh_party_list()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "inv-search":
            self._filter_inventory(event.value)
        elif event.input.id == "move-input":
            self._filter_moves(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "inv-search":
            cells = self.query(".pokemon-cell")
            if cells:
                self._set_state(State.INVENTORY)

    def on_key(self, event: Key) -> None:
        key = event.key

        if self._state == State.PARTY:
            if key == "up":
                self._selected_slot = max(0, self._selected_slot - 1)
                self._refresh_party_list()
                event.prevent_default()
            elif key == "down":
                self._selected_slot = min(MAX_PARTY - 1, self._selected_slot + 1)
                self._refresh_party_list()
                event.prevent_default()
            elif key == "enter":
                self._set_state(State.INVENTORY)
                event.prevent_default()
            elif key == "tab":
                self._set_state(State.INVENTORY)
                event.prevent_default()
            elif key == "left":
                self.query_one("#team-tabs", Tabs).action_previous_tab()
                event.prevent_default()
            elif key == "right":
                self.query_one("#team-tabs", Tabs).action_next_tab()
                event.prevent_default()

        elif self._state == State.INVENTORY:
            if key == "tab":
                self._set_state(State.PARTY)
                event.prevent_default()
            elif key == "enter":
                if self._detail_name:
                    self.on_pokemon_cell_chosen(PokemonCell.Chosen(self._detail_name))
                self._set_state(State.PARTY)
                event.prevent_default()

        elif self._state == State.POKEMON:
            if key == "up":
                self._selected_move = max(0, self._selected_move - 1)
                self._refresh_poke_detail()
                event.prevent_default()
            elif key == "down":
                self._selected_move = min(MAX_MOVES - 1, self._selected_move + 1)
                self._refresh_poke_detail()
                event.prevent_default()
            elif key == "enter":
                self._set_state(State.MOVE_SEARCH)
                event.prevent_default()

        elif self._state == State.MOVE_SEARCH:
            move_results = self.query_one("#move-results", ListView)
            if self.focused is self.query_one("#move-input", Input) and key == "down":
                move_results.focus()
                event.prevent_default()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        event.stop()
        slug = getattr(event.item, "data", None)
        if slug is None or event.list_view.id != "move-results":
            return
        move_cache = get_move_cache()
        if slug in move_cache:
            self._add_move(slug)
        else:
            self._fetch_move(slug)

    # ── Move search ────────────────────────────────────────────────────────────

    def _filter_moves(self, query: str) -> None:
        results = self.query_one("#move-results", ListView)
        results.clear()

        # Get learnset from the Pokémon currently shown in detail pane
        name       = self._detail_name
        if not name:
            return
        all_slugs  = get_pokemon_cache().get(name.lower(), {}).get("moves", [])
        q          = query.lower().strip().replace(" ", "-")
        matches    = [s for s in all_slugs if q in s][:20]
        move_cache = get_move_cache()
        c          = Colors(self.app)

        for slug in matches:
            cached = move_cache.get(slug)
            if cached:
                move_name  = cached.get("name", slug.replace("-", " ").title())
                move_type  = (cached.get("type") or ["?"])[0]
                type_color = TYPE_COLORS.get(move_type, {}).get("text", c.text_ui)
                cat        = self._cat_markup(cached.get("category", ""), c)
                text       = f"[{c.text_ui}]{move_name}[/{c.text_ui}]  [{type_color}]{move_type}[/{type_color}]  {cat}"
            else:
                text = f"[{c.text_muted_ui}]{slug.replace('-', ' ').title()}[/{c.text_muted_ui}]"
            item      = ListItem(Label(text, markup=True))
            item.data = slug  # type: ignore[attr-defined]
            results.append(item)

    def _add_move(self, slug: str) -> None:
        name = self._detail_name
        if not name:
            return
        party_slot = next(
            (s for s in self._party if s["name"].lower() == name.lower()), None
        )
        if party_slot is None:
            return
        moves = party_slot.setdefault("moves", [])
        if slug not in moves:
            if len(moves) >= MAX_MOVES:
                moves[self._selected_move] = slug
            else:
                moves.append(slug)
        self._teams[self._active_team]["party"] = self._party
        save_teams(self._teams)
        self._set_state(State.POKEMON)

    def _fetch_move(self, slug: str) -> None:
        if self._fetching:
            return
        self._fetching = True
        loading = self.query_one("#move-loading", Label)
        c       = Colors(self.app)
        loading.update(f"[{c.warning}]Loading…[/{c.warning}]")
        loading.display = True

        def _do_fetch() -> str | None:
            from pokemon.pokemon_factory import fetch_move_data
            from pokemon.cache_manager  import move_to_dict, get_move_cache, save_move_cache
            move = fetch_move_data(slug)
            if move is not None:
                cache       = get_move_cache()
                cache[slug] = move_to_dict(move)
                save_move_cache(cache)
            return slug if move is not None else None

        self.run_worker(_do_fetch, thread=True, name="fetch_move")

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state != WorkerState.SUCCESS:
            return
        self._fetching = False
        if event.worker.name == "fetch_move":
            self.query_one("#move-loading").display = False
            slug = event.worker.result
            if slug:
                self._add_move(slug)
            else:
                c = Colors(self.app)
                self.query_one("#move-loading", Label).update(f"[{c.error}]Move not found.[/{c.error}]")
                self.query_one("#move-loading").display = True

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _poke_type_markup(self, name: str, c: Colors) -> str:
        data  = get_pokemon_cache().get(name.lower(), {})
        types = data.get("type", [])
        parts = []
        for t in types:
            color = TYPE_COLORS.get(t, {}).get("text", c.text_ui)
            parts.append(f"[{color}]{t}[/{color}]")
        return " / ".join(parts)

    def _format_stats(self, data: dict, c: Colors) -> str:
        if not data:
            return ""
        stats = [
            ("HP",  data.get("hp",           0)),
            ("ATK", data.get("stat_attk",     0)),
            ("DEF", data.get("stat_def",      0)),
            ("SpA", data.get("stat_sp_attk",  0)),
            ("SpD", data.get("stat_sp_def",   0)),
            ("SPD", data.get("stat_spd",      0)),
        ]
        parts = [f"[{c.text_label}]{lbl}[/{c.text_label}] [{c.text_ui}]{val}[/{c.text_ui}]"
                 for lbl, val in stats]
        return "  ".join(parts)

    def _cat_markup(self, category: str, c: Colors) -> str:
        labels = {"physical": "Phys", "special": "Spec", "status": "Stat"}
        colors = {"physical": c.error, "special": c.secondary, "status": c.success}
        return f"[{colors.get(category, c.text_muted_ui)}]{labels.get(category, '')}[/{colors.get(category, c.text_muted_ui)}]"

    # ── Actions ────────────────────────────────────────────────────────────────

    def action_back(self) -> None:
        if self._state == State.MOVE_SEARCH:
            move_results = self.query_one("#move-results", ListView)
            if self.focused is move_results:
                self.query_one("#move-input", Input).focus()
                return
            self._set_state(State.POKEMON)
        elif self._state == State.POKEMON:
            self._set_state(State.INVENTORY)
        elif self._state == State.INVENTORY:
            self._set_state(State.PARTY)
        elif self._state == State.PARTY:
            self.app.pop_screen()

    def action_delete(self) -> None:
        if self._state == State.PARTY and self._selected_slot < len(self._party):
            self._party.pop(self._selected_slot)
            self._selected_slot = min(self._selected_slot, max(0, len(self._party) - 1))
            self._teams[self._active_team]["party"] = self._party
            save_teams(self._teams)
            self._refresh_party_list()

        elif self._state == State.POKEMON:
            name = self._detail_name
            if not name:
                return
            party_slot = next(
                (s for s in self._party if s["name"].lower() == name.lower()), None
            )
            if party_slot is None:
                return
            moves = party_slot.get("moves", [])
            if self._selected_move < len(moves):
                moves.pop(self._selected_move)
                self._selected_move = min(self._selected_move, max(0, len(moves) - 1))
                self._teams[self._active_team]["party"] = self._party
                save_teams(self._teams)
                self._refresh_poke_detail()

    def action_move_up(self) -> None:
        i = self._selected_slot
        if self._state == State.PARTY and i > 0 and i < len(self._party):
            self._party[i], self._party[i - 1] = self._party[i - 1], self._party[i]
            self._selected_slot -= 1
            self._teams[self._active_team]["party"] = self._party
            save_teams(self._teams)
            self._refresh_party_list()

    def action_move_down(self) -> None:
        i = self._selected_slot
        if self._state == State.PARTY and i < len(self._party) - 1:
            self._party[i], self._party[i + 1] = self._party[i + 1], self._party[i]
            self._selected_slot += 1
            self._teams[self._active_team]["party"] = self._party
            save_teams(self._teams)
            self._refresh_party_list()

    def action_rename_team(self) -> None:
        if self._state != State.PARTY:
            return
        current = self._teams[self._active_team]["name"]

        def _on_result(new_name: str | None) -> None:
            if new_name and new_name != current:
                self._teams[self._active_team]["name"] = new_name
                save_teams(self._teams)
                self.query_one(f"#team-{self._active_team}", Tab).label = new_name

        self.app.push_screen(RenameTeamModal(current), callback=_on_result)

    def action_quit_screen(self) -> None:
        self.app.pop_screen()
