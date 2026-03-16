from models import Move

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

DoubleEdge = Move(
    name="Double Edge",
    type = ["Normal"],
    dmg_type=["physical"],
    pp = 20,
    effects={
        "opponent": {"hp": -100},
        "self":     {"hp": -30}
    }
)