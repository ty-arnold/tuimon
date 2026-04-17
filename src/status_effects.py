from src.models import StatusEffect

poison = StatusEffect(
    name = "Poison",
    chance_to_apply = 1.0,
    chance_to_end = 0.5,
    damage = (1/16)
)

paralysis = StatusEffect(
    name = "Paralysis",
    stat_modifier = {"stat_spd" : 0.75},
    chance_to_act = 0.75,
    chance_to_apply = 0.30
)

sleep = StatusEffect(
    name = "Sleep",
    chance_to_end = 0.25,
    chance_to_act = 0.0,
    chance_to_apply = 0.10
)

burn = StatusEffect(
    name = "Burn",
    stat_modifier = {"stat_attack" : 0.5},
    chance_to_apply = 0.10,
    damage = (1/8)
)

freeze = StatusEffect(
    name = "Freeze",
    chance_to_act = 0.0,
    chance_to_apply = 0.10
)