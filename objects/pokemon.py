from models import Pokemon
from objects.moves import *

nidorino = Pokemon(
    name = "Nidorino",
    lvl = 50, 
    type = ["Normal"], 
    moveset = [scratch, growl, toxic, sand_attack],
    stat_hp = 61, 
    stat_attk = 72,
    stat_def = 57,
    stat_sp_attk = 55,
    stat_sp_def = 55,
    stat_spd = 65
)

gengar = Pokemon(
    name = "Gengar",
    lvl = 50, 
    type = ["Fire"], 
    moveset = [scratch, growl, agility, test],
    stat_hp = 60, 
    stat_attk = 65,
    stat_def = 60,
    stat_sp_attk = 130,
    stat_sp_def = 76,
    stat_spd = 110
)