from battle import resolve_turn, get_turn
from print import *
from objects.moves import *
from objects.trainers import *
from pokemon_factory import create_pokemon_from_api
from presets import get_test_player, get_test_npc

DEBUG = True

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

print(f"DEBUG player party: {[p.name if p is not None else 'None' for p in player.party]}")
print(f"DEBUG npc party: {[p.name if p is not None else 'None' for p in npc.party]}")
print(f"DEBUG player selected_mon: {player.selected_mon}")
print(f"DEBUG npc selected_mon: {npc.selected_mon}")

turn = 1
print("Battle Start!")
while True:
    player_move = get_turn(player)
    npc_move = get_turn(npc)
    winner = resolve_turn(player, player_move, npc, npc_move)
    if winner:
        print(winner)
        break  
    # player.print_hp()
    debug_print_stats(player.active())
    print(f"DEBUG status effects: {[e.name for e in player.active().status_effect]}")
    for move in player.active().moveset:
        debug_print_move(move)
    # npc.print_hp()
    debug_print_stats(npc.active())
    print(f"DEBUG status effects: {[e.name for e in npc.active().status_effect]}")
    for move in npc.active().moveset:
        debug_print_move(move)
    turn += 1
