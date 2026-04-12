from battle import resolve_turn, get_turn
from print import *
from objects.pokemon import *
from objects.moves import *
from objects.trainers import *

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
    # npc.print_hp()
    debug_print_stats(npc.active())
    print(f"DEBUG status effects: {[e.name for e in npc.active().status_effect]}")
    turn += 1
