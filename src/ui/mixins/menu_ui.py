from textual.widgets import ListView, ListItem, Label
from core.logger     import logger

class MenuUIMixin:
    """Handles action pane menu state switching."""

    def show_main_menu(self) -> None:
        self.query_one("#menu-main").display  = True
        self.query_one("#menu-moves").display = False
        self.query_one("#menu-party").display = False
        self.query_one("#menu-items").display = False
        self.query_one("#action-pane").border_title = "actions"

    def show_move_menu(self) -> None:
        move_list = self.query_one("#menu-moves", ListView)
        move_list.clear()
        for move in self.player.active().moveset:
            move_list.append(ListItem(Label(f"{move.name}  PP: {move.pp}")))
        move_list.append(ListItem(Label("Cancel")))
        self.query_one("#menu-main").display  = False
        self.query_one("#menu-moves").display = True
        self.query_one("#action-pane").border_title = "moves"

    def show_party_menu(self) -> None:
        party_list = self.query_one("#menu-party", ListView)
        party_list.clear()
        for pokemon in self.player.party:
            status = "FNT" if not pokemon.is_alive() else f"{pokemon.hp}/{pokemon.max_hp}"
            party_list.append(ListItem(Label(f"{pokemon.name}  {status}")))
        party_list.append(ListItem(Label("Cancel")))
        self.query_one("#menu-main").display  = False
        self.query_one("#menu-party").display = True
        self.query_one("#action-pane").border_title = "party"

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        logger.debug(f"on_list_view_selected: list={event.list_view.id} idx={event.list_view.index}")
        event.stop()
        idx = event.list_view.index

        if event.list_view.id == "menu-main":
            match idx:
                case 0:
                    # check lock before showing move menu
                    if self.player.locked_move is not None:
                        move = self.player.locked_move
                        self.player.locked_turns -= 1
                        self.controller.select_player_move(move)
                        self.controller.select_npc_move()
                        self.show_main_menu()
                        self.run_worker(self.resolve_and_display())
                    else:
                        self.show_move_menu()
                case 1: self.show_party_menu()
                case 2: pass
                case 3: self.action_quit()

        elif event.list_view.id == "menu-moves":
            moveset = self.player.active().moveset
            if idx >= len(moveset):
                self.show_main_menu()
            else:
                move = moveset[idx]
                self.controller.select_player_move(move)
                self.controller.select_npc_move()
                self.show_main_menu()
                self.run_worker(self.resolve_and_display())

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