import sys
import logging

DEBUG       = True
ENABLE_LOGS = True

from logger import setup_logger
if ENABLE_LOGS:
    setup_logger(debug=DEBUG)

logger = logging.getLogger("tuimon")

from battle          import resolve_turn, get_turn
from print           import build_party, print_actions
from presets         import get_test_player, get_test_npc
from debug           import dump_battle_state, dump_move
from models          import Trainer
from game_print      import game_print
from pokemon_factory import create_pokemon_from_api

try:
    if DEBUG:
        player = get_test_player()
        npc    = get_test_npc()
    else:
        player_party = build_party("Ash", party_size=2)
        player       = Trainer(name="Ash", party=player_party)
        npc_party    = [
            create_pokemon_from_api("gengar",   lvl=55),
            create_pokemon_from_api("alakazam", lvl=55)
        ]
        npc = Trainer(name="Gary", party=npc_party)

    turn = 1

    game_print("Battle Start!")
    while True:
        dump_battle_state(player, npc, turn=turn)

        player_move = get_turn(player)
        npc_move = get_turn(npc)

        logger.debug(f"Player chose: {player_move.name if player_move else 'charge/recharge turn'}")
        logger.debug(f"NPC chose: {npc_move.name if npc_move else 'charge/recharge turn'}")

        if player_move:
            dump_move(player_move)
        if npc_move:
            dump_move(npc_move)

        winner = resolve_turn(player, player_move, npc, npc_move)
        if winner:
            game_print(winner)
            break  
        turn += 1

except KeyboardInterrupt:
    game_print("\nThanks for playing!")
    sys.exit(0)