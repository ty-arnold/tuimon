from src.models import StatusEffect

poison = StatusEffect(
    name = "Poison",
    chance_to_apply = 1.0,
    chance_to_end = 0.5,
    damage = (1/16),
    is_major = True
)

paralysis = StatusEffect(
    name = "Paralysis",
    stat_modifier = {"stat_spd" : 0.75},
    chance_to_act = 0.75,
    chance_to_apply = 0.30,
    is_major = True
)

sleep = StatusEffect(
    name = "Sleep",
    chance_to_end = 0.25,
    chance_to_act = 0.0,
    chance_to_apply = 0.10,
    is_major = True
)

burn = StatusEffect(
    name = "Burn",
    stat_modifier = {"stat_attk" : 0.5},
    chance_to_apply = 0.10,
    damage = (1/8),
    is_major = True
)

freeze = StatusEffect(
    name = "Freeze",
    chance_to_act = 0.0,
    chance_to_apply = 0.10,
    is_major = True
)

confusion = StatusEffect(
    name            = "Confusion",
    chance_to_apply = 1.0,
    chance_to_end   = 0.25,
    chance_to_act   = 1.0,  # always acts, but may hurt itself via process_effect
)

curse = StatusEffect(
    name            = "Curse",
    chance_to_apply = 1.0,
    chance_to_end   = None,    # curse never ends on its own
    damage          = 0.25,    # deals 25% max hp per turn
)