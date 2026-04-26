from models import MultiTurn, Accumulator, Modifier, MoveEffect

MULTI_TURN_OVERRIDES = {

    # ── CHARGE TURN 1 - INVULNERABLE ──────────────────────────────────────

    "fly": MultiTurn(
        turns                = 2,
        charge_turn          = 1,
        invulnerable         = True,
        invulnerable_state   = "flying",
        charge_message       = "flew up high!",
        invulnerable_message = "is high up in the air!"
    ),
    "dig": MultiTurn(
        turns                = 2,
        charge_turn          = 1,
        invulnerable         = True,
        invulnerable_state   = "underground",
        charge_message       = "dug a hole!",
        invulnerable_message = "is underground!"
    ),
    "dive": MultiTurn(
        turns                = 2,
        charge_turn          = 1,
        invulnerable         = True,
        invulnerable_state   = "underwater",
        charge_message       = "hid underwater!",
        invulnerable_message = "is hiding underwater!"
    ),
    "bounce": MultiTurn(
        turns                = 2,
        charge_turn          = 1,
        invulnerable         = True,
        invulnerable_state   = "flying",
        charge_message       = "sprang up!",
        invulnerable_message = "is high up in the air!"
    ),

    # ── CHARGE TURN 1 - NOT INVULNERABLE ──────────────────────────────────

    "skull-bash": MultiTurn(
        turns          = 2,
        charge_turn    = 1,
        invulnerable   = False,
        charge_message = "lowered its head and charged!"
        # raises defense on charge turn - handled via stat_change in apply_move
    ),
    "solar-beam": MultiTurn(
        turns          = 2,
        charge_turn    = 1,
        invulnerable   = False,
        charge_message = "absorbed light!"
    ),
    "razor-wind": MultiTurn(
        turns          = 2,
        charge_turn    = 1,
        invulnerable   = False,
        charge_message = "whipped up a whirlwind!"
    ),
    "sky-attack": MultiTurn(
        turns          = 2,
        charge_turn    = 1,
        invulnerable   = False,
        charge_message = "is glowing!"
    ),

    # ── CHARGE TURN 2 - RECHARGE ───────────────────────────────────────────

    "hyper-beam": MultiTurn(
        turns          = 2,
        charge_turn    = 2,
        invulnerable   = False,
        charge_message = "must recharge!"
    ),
    "blast-burn": MultiTurn(
        turns          = 2,
        charge_turn    = 2,
        invulnerable   = False,
        charge_message = "must recharge!"
    ),
    "frenzy-plant": MultiTurn(
        turns          = 2,
        charge_turn    = 2,
        invulnerable   = False,
        charge_message = "must recharge!"
    ),
    "hydro-cannon": MultiTurn(
        turns          = 2,
        charge_turn    = 2,
        invulnerable   = False,
        charge_message = "must recharge!"
    ),

    # ── ACCUMULATOR MOVES ─────────────────────────────────────────────────

    "bide": MultiTurn(
        turns          = 2,
        charge_turn    = 1,
        invulnerable   = False,
        charge_message = "is storing energy!",
        accumulator    = Accumulator(
            type            = "damage_taken",
            release_formula = "double",
            ignore_type     = True,
            release_message = "unleashed energy!"
        )
    ),
    "rollout": MultiTurn(
        turns          = 5,
        charge_turn    = 1,
        invulnerable   = False,
        charge_message = "began rolling!",
        accumulator    = Accumulator(
            type            = "turn_count",
            release_formula = "exponential",
            release_message = ""
        )
    ),
    "ice-ball": MultiTurn(
        turns          = 5,
        charge_turn    = 1,
        invulnerable   = False,
        charge_message = "began rolling!",
        accumulator    = Accumulator(
            type            = "turn_count",
            release_formula = "exponential",
            release_message = ""
        )
    ),
    "fury-cutter": MultiTurn(
        turns          = 5,
        charge_turn    = 1,
        invulnerable   = False,
        charge_message = "used Fury Cutter!",
        accumulator    = Accumulator(
            type            = "turn_count",
            release_formula = "double",
            release_message = ""
        )
    ),
}

MODIFIER_OVERRIDES = {
    "charge": {
        "name":            "Charge",
        "expires_turn":    0,          # set dynamically when applied
        "turns":           1,
        "power_modifier":  2.0,
        "type_condition":  "Electric",
        "clears_on_switch": True,
        "consume_message": "The charge wore off!"
    },
    "focus-energy": {
        "name":            "Focus Energy",
        "expires_turn":    -1,         # permanent until switched out
        "turns":           -1,
        "power_modifier":  1.0,
        "damage_modifier": 1.0,        # actually raises crit rate in games
        "clears_on_switch": True,
        "consume_message": ""
    },
    "defense-curl": {
        "name":            "Defense Curl",
        "expires_turn":    -1,
        "turns":           -1,
        "power_modifier":  2.0,
        "type_condition":  "Normal",   # doubles rollout/ice ball power
        "clears_on_switch": True,
        "consume_message": ""
    },
}

MODIFIER_OVERRIDES = {

    # doubles power of next electric type move
    "charge": Modifier(
        name             = "Charge",
        expires_turn     = 0,          # set dynamically when applied
        turns            = 1,
        target           = "self",
        power_modifier   = 2.0,
        type_condition   = "Electric",
        clears_on_switch = True,
        consume_message  = "The charge wore off!"
    ),

    # raises crit rate - in gen 3 this raises crit stage by 1
    "focus-energy": Modifier(
        name             = "Focus Energy",
        expires_turn     = -1,         # permanent until switched out
        turns            = -1,
        target           = "self",
        clears_on_switch = True,
        consume_message  = ""
        # note: crit rate boost handled separately via crit_rate stage
    ),

    # doubles rollout and ice ball power if used before those moves
    "defense-curl": Modifier(
        name             = "Defense Curl",
        expires_turn     = -1,
        turns            = -1,
        target           = "self",
        power_modifier   = 2.0,
        clears_on_switch = True,
        consume_message  = ""
        # note: only applies to rollout and ice-ball
        # requires move_condition check not just type_condition
    ),

    # weakens electric type moves for 5 turns - field effect
    "mud-sport": Modifier(
        name             = "Mud Sport",
        expires_turn     = 0,
        turns            = 5,
        target           = "both",
        power_modifier   = 0.5,
        type_condition   = "Electric",
        clears_on_switch = False,      # field effect persists
        consume_message  = "The mud dried up!"
    ),

    # weakens fire type moves for 5 turns - field effect
    "water-sport": Modifier(
        name             = "Water Sport",
        expires_turn     = 0,
        turns            = 5,
        target           = "both",
        power_modifier   = 0.5,
        type_condition   = "Fire",
        clears_on_switch = False,      # field effect persists
        consume_message  = "The water dried up!"
    ),

    # boosts allies next move by 1.5x - doubles only
    "helping-hand": Modifier(
        name             = "Helping Hand",
        expires_turn     = 0,
        turns            = 1,
        target           = "self",
        power_modifier   = 1.5,
        clears_on_switch = True,
        consume_message  = ""
    ),
}

# ── IMMUNE TYPE OVERRIDES ─────────────────────────────────────────────────────
# moves that are blocked by specific types despite type chart
# (separate from type chart 0x immunity which is handled automatically)

IMMUNE_TYPE_OVERRIDES = {
    # bide ignores type effectiveness but is still blocked by ghost
    "bide":          ["Ghost"],

    # thunder wave is a status move but ground types are immune
    "thunder-wave":  ["Ground"],

    # glare is blocked by ghost types in gen 2-3 specifically
    "glare":         ["Ghost"],

    # odor sleuth and foresight are move effects not immunities
    # they're better handled as MoveEffect overrides that remove
    # ghost immunity for the remainder of the battle, not here
}

# ── HITS INVULNERABLE OVERRIDES ───────────────────────────────────────────────
# moves that can hit pokemon in semi-invulnerable states
# and any damage modifiers that apply in those states

HITS_INVULNERABLE = {

    # hits flying pokemon (fly/bounce)
    "thunder": {
        "states":          ["flying"],
        "damage_modifier": {}           # no bonus damage
    },
    "hurricane": {
        "states":          ["flying"],
        "damage_modifier": {}
    },

    # hits flying and deals double damage
    "gust": {
        "states":          ["flying"],
        "damage_modifier": {"flying": 2.0}
    },
    "twister": {
        "states":          ["flying"],
        "damage_modifier": {"flying": 2.0}
    },
    "sky-uppercut": {
        "states":          ["flying"],
        "damage_modifier": {}
    },
    "smack-down": {
        "states":          ["flying"],
        "damage_modifier": {}
    },

    # hits underground pokemon (dig) and deals double damage
    "earthquake": {
        "states":          ["underground"],
        "damage_modifier": {"underground": 2.0}
    },
    "magnitude": {
        "states":          ["underground"],
        "damage_modifier": {"underground": 2.0}
    },
    "fissure": {
        "states":          ["underground"],
        "damage_modifier": {}           # ohko move - no damage modifier needed
    },

    # hits underwater pokemon (dive) and deals double damage
    "surf": {
        "states":          ["underwater"],
        "damage_modifier": {"underwater": 2.0}
    },
    "whirlpool": {
        "states":          ["underwater"],
        "damage_modifier": {"underwater": 2.0}
    },
}

MOVE_EFFECT_OVERRIDES = {
    "light-screen": MoveEffect(
        effect_type = "screen",
        target      = "self",
        turns       = 5,
        message     = "put up a Light Screen!",
        properties  = {
            "damage_modifier":     0.5,
            "category_condition":  "special"
        }
    ),
    "reflect": MoveEffect(
        effect_type = "screen",
        target      = "self",
        turns       = 5,
        message     = "put up a Reflect!",
        properties  = {
            "damage_modifier":     0.5,
            "category_condition":  "physical"
        }
    ),
    "protect": MoveEffect(
        effect_type  = "protect",
        target       = "self",
        turns        = 1,
        message      = "protected itself!",
        fail_message = "tried to protect itself but failed!",
        properties   = {
            "consecutive_reduction": True
        },
        bypass_moves = ["feint"]
    ),
    "detect": MoveEffect(
        effect_type  = "protect",
        target       = "self",
        turns        = 1,
        message      = "protected itself!",
        fail_message = "tried to protect itself but failed!",
        properties   = {
            "consecutive_reduction": True
        },
        bypass_moves = ["feint"]
    ),
    "mist": MoveEffect(
        effect_type = "mist",
        target      = "self",
        turns       = 5,
        message     = "shrouded itself in mist!",
        properties  = {
            "blocks_stat_changes": True
        }
    ),
    "safeguard": MoveEffect(
        effect_type = "safeguard",
        target      = "self",
        turns       = 5,
        message     = "became cloaked in a mystical veil!",
        properties  = {
            "blocks_status_effects": True
        }
    ),
}