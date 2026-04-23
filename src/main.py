import sys
import logging

from core.config import DEBUG, ENABLE_LOGS

from core.logger import setup_logger
if ENABLE_LOGS:
    setup_logger(debug=DEBUG)

logger = logging.getLogger("tuimon")

from models       import Trainer
from battle       import resolve_turn, get_turn
from ui           import build_party, dump_battle_state, dump_move
from core         import game_print
from core.presets import get_test_player, get_test_npc
from pokemon      import create_pokemon_from_api

try:
    if DEBUG:
        player = get_test_player()
        npc    = get_test_npc()
    else:
        player_party_raw = build_party("Ash", party_size=2)
        player_party     = [p for p in player_party_raw if p is not None]
        assert len(player_party) > 0, "Failed to create player party!"
        player = Trainer(name="Ash", party=player_party)

        npc_party_raw = [
            create_pokemon_from_api("gengar",   lvl=55),
            create_pokemon_from_api("alakazam", lvl=55)
        ]
        npc_party = [p for p in npc_party_raw if p is not None]
        assert len(npc_party) > 0, "Failed to create NPC party!"
        npc = Trainer(name="Gary", party=npc_party)

    current_turn = 1

    game_print("Battle Start!")
    while True:
        dump_battle_state(player, npc, current_turn)

        player_move = get_turn(player)
        npc_move = get_turn(npc)

        logger.debug(f"Player chose: {player_move.name if player_move else 'charge/recharge turn'}")
        logger.debug(f"NPC chose: {npc_move.name if npc_move else 'charge/recharge turn'}")

        if player_move:
            dump_move(player_move)
        if npc_move:
            dump_move(npc_move)

        if player_move is not None and npc_move is not None:
            winner = resolve_turn(player, player_move, npc, npc_move, current_turn)
            if winner:
                game_print(winner)
                break  
        game_print(f"{player.name}'s {player.active().name}: HP - {player.active().hp}/{player.active().max_hp}")
        game_print(f"{npc.name}'s {npc.active().name}: HP - {npc.active().hp}/{npc.active().max_hp}")
        current_turn += 1

except KeyboardInterrupt:
    game_print("\nThanks for playing!")
    sys.exit(0)