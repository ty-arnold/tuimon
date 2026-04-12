from models import Move
from objects.status_effects import paralysis, poison, burn, freeze, sleep

scratch = Move(
    name = "Scratch",
    type = ["Normal"],
    category = "physical",
    power = 40,
    acc = 0.80,
    pp = 20,
    effects = {}
)

test = Move(
    name = "Test",
    type = ["Normal"],
    category = "physical",
    power = 60,
    acc = 1.0,
    pp = 20,
    effects = {
        "self":     {"stat_spd": +1},  
        "opponent": {"stat_spd": -2}
    }
)

thunder = Move(
    name = "Thunder",
    type = ["Normal"],
    category = "special",
    power = 60,
    acc = 0.85,
    pp = 20,
    effects = {}
)

growl = Move(
    name = "Growl",
    type = ["Normal"],
    category = "status",
    power = 0,
    acc = 0.85,
    pp = 20,
    effects = {
        "opponent" : {"stat_def": -1},
    }
)

agility = Move(
    name = "Agility",
    type = ["Normal"],
    category = "status",
    power = 0,
    acc = 0.75,
    pp = 20,
    effects = {
        "opponent" : {"stat_spd": +2},
    }
)

doubleedge = Move(
    name="Double Edge",
    type = ["Normal"],
    category="physical",
    power = 80,
    recoil = 30,
    acc = 0.75,
    pp = 20,
    effects={}
)

toxic = Move(
    name = "Toxic",
    type = ["Poison"],
    category = "physical",
    power = 20,
    acc = 0.85,
    pp = 20,
    effects = {},
    status_effect = poison
)

sand_attack = Move(
    name = "Sand Attack",
    type = ["Normal"],
    category = "status",
    power = 0,
    acc = 0.85,
    pp = 20,
    effects = {
        "opponent" : {"stat_acc": -1},
    },
)