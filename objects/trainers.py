from models import Trainer
from objects.pokemon import *

player = Trainer(
    name = "Ash",
    party = [nidorino, gengar],
    selected_mon = 0
)

npc = Trainer(
    name = "Gary",
    party = [gengar, nidorino],
    selected_mon = 0
)