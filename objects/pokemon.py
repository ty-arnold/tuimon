from models import Pokemon
from objects.moves import *

nidorino = Pokemon(
    name = "Nidorino",
    lvl = 50, 
    type = ["Normal"], 
    moveset = [scratch, toxic, test],
    stat_hp = 66, 
    stat_attk = 65,
    stat_def = 60,
    stat_sp_attk = 130,
    stat_sp_def = 75,
    stat_spd = 110
)

gengar = Pokemon(
    name = "Gengar",
    lvl = 50, 
    type = ["Fire"], 
    moveset = [scratch, growl, agility],
    stat_hp = 61, 
    stat_attk = 72,
    stat_def = 57,
    stat_sp_attk = 55,
    stat_sp_def = 55,
    stat_spd = 65
)