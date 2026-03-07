from models import Move

scratch = Move(
    name = "Scratch",
    type = ["Water"],
    dmg_type = "physical",
    pp = 20,
    target = "opponent",
    stat_hp = -50,
    stat_max_hp = 0, 
    stat_attk = 0,
    stat_def = 0,
    stat_sp_attk = 0,
    stat_sp_def = 0,
    stat_spd = 0
)

thunder = Move(
    name = "Thunder",
    type = ["Normal"],
    dmg_type = "physical",
    pp = 20,
    target = "opponent",
    stat_hp = -50,
    stat_max_hp = 0, 
    stat_attk = 0,
    stat_def = 0,
    stat_sp_attk = 0,
    stat_sp_def = 0,
    stat_spd = 0
)

growl = Move(
    name = "Growl",
    type = ["Normal"],
    dmg_type = "physical",
    pp = 20,
    target = "opponent",
    stat_hp = 0,
    stat_max_hp = 0,
    stat_attk = -20,
    stat_def = 0,
    stat_sp_attk = 0,
    stat_sp_def = 0,
    stat_spd = 0
)

agility = Move(
    name = "Agility",
    type = ["Normal"],
    dmg_type = "physical",
    pp = 20,
    target = "self",
    stat_hp = 0, 
    stat_max_hp = 0,
    stat_attk = 0,
    stat_def = 0,
    stat_sp_attk = 0,
    stat_sp_def = 0,
    stat_spd = 50
)