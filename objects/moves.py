from models import Move
from objects.status_effects import paralysis, poison, burn, freeze, sleep

scratch = Move(
    name = "Scratch",
    type = ["Water"],
    dmg_type = "physical",
    pp = 20,
    effects = {
        "opponent" : {"hp": -20},
    }
)

thunder = Move(
    name = "Thunder",
    type = ["Normal"],
    dmg_type = "special",
    pp = 20,
    effects = {
        "opponent" : {"hp": -20},
    }
)

growl = Move(
    name = "Growl",
    type = ["Normal"],
    dmg_type = "physical",
    pp = 20,
    effects = {
        "opponent" : {"stat_def": -20},
    }
)

agility = Move(
    name = "Agility",
    type = ["Normal"],
    dmg_type = "physical",
    pp = 20,
    effects = {
        "opponent" : {"stat_spd": +20},
    }
)

doubleedge = Move(
    name="Double Edge",
    type = ["Normal"],
    dmg_type=["physical"],
    pp = 20,
    effects={
        "opponent": {"hp": -100},
        "self":     {"hp": -30}
    }
)

toxic = Move(
    name = "Toxic",
    type = ["Poison"],
    dmg_type = ["physical"],
    pp = 20,
    effects = {
        "opponent": {"hp": -20},
    },
    status_effect = poison
)