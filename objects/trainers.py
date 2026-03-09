from models import Trainer
from objects.pokemon import *
import copy

player = Trainer(
    name = "Ash",
    party = [copy.deepcopy(nidorino), copy.deepcopy(gengar)],
    selected_mon = 0
)

npc = Trainer(
    name = "Gary",
    party = [copy.deepcopy(gengar), copy.deepcopy(nidorino)],
    selected_mon = 0
)