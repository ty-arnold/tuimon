import sys
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
        break






    
    
    