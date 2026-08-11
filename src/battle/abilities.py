"""Ability hook functions called at specific points in the battle engine."""
import random
from models.turn_result import Message, HPChange


def _ability(pokemon):
    return getattr(pokemon, "ability", None)


def _name(pokemon):
    ability = _ability(pokemon)
    return ability.name if ability else ""


# ── Tier 1: Simple blockers ─────────────────────────────────────


def check_ability_prevents(pokemon, what: str) -> bool:
    """Check if the Pokemon's ability prevents a specific effect."""
    name = _name(pokemon)
    what = what.lower()
    match what:
        case "paralysis":    return name == "Limber"
        case "poison":       return name == "Immunity"
        case "sleep":        return name in ("Insomnia", "Vital Spirit")
        case "freeze":       return name in ("Magma Armor", "Water Veil")
        case "burn":         return name == "Water Veil"
        case "confusion":    return name == "Own Tempo"
        case "flinch":       return name == "Inner Focus"
        case "infatuation":  return name == "Oblivious"
        case "crit":         return name in ("Battle Armor", "Shell Armor")
        case "acc_drop":     return name == "Keen Eye"
        case "atk_drop":     return name == "Hyper Cutter"
        case "stat_drop_by_opponent": return name in ("Clear Body", "White Smoke")
    return False


# ── Tier 2: Type immunity ───────────────────────────────────────


def check_ability_type_immunity(defender, move, events=None) -> bool:
    """Return True if the defender's ability grants immunity to this move's type.
    May emit messages and heal events (Volt Absorb, Water Absorb)."""
    name = _name(defender.active())
    move_type = move.type[0]

    if name == "Levitate" and move_type == "Ground":
        if events is not None:
            events.append(Message(text=f"{defender.active().name}'s Levitate makes it immune!"))
        return True

    if name == "Volt Absorb" and move_type == "Electric":
        target = defender.active()
        heal = round(target.max_hp * 0.25)
        hp_before = target.hp
        target.hp = min(target.max_hp, target.hp + heal)
        if events is not None:
            events.append(Message(text=f"{target.name}'s Volt Absorb restored HP!"))
            events.append(HPChange(
                trainer=defender.name, pokemon_name=target.name,
                old_hp=hp_before, new_hp=target.hp, max_hp=target.max_hp,
            ))
        return True

    if name == "Water Absorb" and move_type == "Water":
        target = defender.active()
        heal = round(target.max_hp * 0.25)
        hp_before = target.hp
        target.hp = min(target.max_hp, target.hp + heal)
        if events is not None:
            events.append(Message(text=f"{target.name}'s Water Absorb restored HP!"))
            events.append(HPChange(
                trainer=defender.name, pokemon_name=target.name,
                old_hp=hp_before, new_hp=target.hp, max_hp=target.max_hp,
            ))
        return True

    if name == "Flash Fire" and move_type == "Fire":
        if events is not None:
            events.append(Message(text=f"{defender.active().name}'s Flash Fire raised its Fire power!"))
        return True

    if name == "Wonder Guard":
        from battle.damage import get_type_multiplier
        mult = get_type_multiplier(move_type, defender.active().type)
        if mult <= 1:
            if events is not None:
                events.append(Message(text=f"{defender.active().name}'s Wonder Guard blocks the attack!"))
            return True

    return False


# ── Tier 2: Damage modifiers ────────────────────────────────────


def check_ability_before_damage(defender, damage, events=None) -> int:
    """Return modified damage. Sturdy prevents OHKO from full HP."""
    name = _name(defender.active())
    target = defender.active()

    if name == "Sturdy" and target.hp == target.max_hp and damage >= target.hp:
        if events is not None:
            events.append(Message(text=f"{target.name} held on with Sturdy!"))
        return target.hp - 1

    return damage


def modify_damage_by_ability(attacker, defender, move, damage, events=None) -> float:
    """Return a multiplier (1.0 = no change) to apply to damage."""
    attacker_name = _name(attacker.active())
    move_type = move.type[0]

    # Thick Fat
    if _name(defender.active()) == "Thick Fat" and move_type in ("Fire", "Ice"):
        return 0.5

    # Low-HP type boosts
    hp_pct = attacker.active().hp / attacker.active().max_hp
    if hp_pct <= 0.33:
        match (attacker_name, move_type):
            case ("Blaze", "Fire") | ("Torrent", "Water") | ("Overgrow", "Grass") | ("Swarm", "Bug"):
                return 1.5

    return 1.0


# ── Tier 2: Stat modifiers ──────────────────────────────────────


def modify_stat_by_ability(pokemon, stat: str, value: int) -> int:
    """Return a modified stat value. Called from get_stat()."""
    name = _name(pokemon)
    is_statused = pokemon.major_status is not None

    if name == "Huge Power" and stat in ("stat_attk",):
        return value * 2
    if name == "Pure Power" and stat in ("stat_attk",):
        return value * 2
    if name == "Hustle" and stat in ("stat_attk",):
        return round(value * 1.5)
    if name == "Guts" and is_statused and stat in ("stat_attk",):
        return round(value * 1.5)
    if name == "Marvel Scale" and is_statused and stat in ("stat_def",):
        return round(value * 1.5)
    return value


# ── Tier 2: Accuracy ────────────────────────────────────────────


def check_ability_accuracy_modifier(attacker) -> float:
    """Return an accuracy multiplier (1.0 = no change)."""
    if _name(attacker.active()) == "Hustle":
        return 0.8
    return 1.0


# ── Tier 2: Misc mechanics ──────────────────────────────────────


def check_ability_recoil_prevention(attacker) -> bool:
    """Rock Head prevents recoil damage."""
    return _name(attacker.active()) == "Rock Head"


def check_ability_serene_grace(pokemon) -> bool:
    """Serene Grace doubles secondary effect chances."""
    return _name(pokemon) == "Serene Grace"


def apply_ability_pp_pressure(defender) -> bool:
    """Pressure doubles PP usage by the opponent."""
    return _name(defender.active()) == "Pressure"


# ── Tier 3: Contact abilities ───────────────────────────────────


def apply_contact_abilities(attacker, defender, move, events=None) -> None:
    """Apply abilities that trigger on contact (Static, Poison Point, etc.)."""
    if move.category != "physical":
        return

    name = _name(defender.active())

    if name == "Rough Skin":
        target = attacker.active()
        dmg = max(1, round(target.max_hp / 16))
        hp_before = target.hp
        target.hp = max(0, target.hp - dmg)
        if events is not None:
            events.append(Message(text=f"{target.name} was hurt by Rough Skin!"))
            events.append(HPChange(
                trainer=attacker.name, pokemon_name=target.name,
                old_hp=hp_before, new_hp=target.hp, max_hp=target.max_hp,
            ))
        return

    status = None
    chance = 0.0

    if name == "Static":
        status = "paralysis"
        chance = 0.3
    elif name == "Poison Point":
        status = "poison"
        chance = 0.3
    elif name == "Flame Body":
        status = "burn"
        chance = 0.3
    elif name == "Effect Spore":
        r = random.random()
        if r < 0.1:
            status = "poison"
        elif r < 0.2:
            status = "paralysis"
        elif r < 0.3:
            status = "sleep"
        chance = 1.0  # already rolled

    if status and random.random() < chance:
        from data.status_effects import poison, paralysis, sleep, burn
        from models.status_effect import StatusEffect
        effect_map = {"poison": poison, "paralysis": paralysis, "sleep": sleep, "burn": burn}
        effect = effect_map.get(status)
        if effect:
            import copy
            eff = copy.deepcopy(effect)
            target = attacker.active()
            if target.apply_status_effect(eff):
                if events is not None:
                    events.append(Message(text=f"{target.name} was {status} by {name}!"))

    # Stench: 10% flinch on contact
    if name == "Stench" and random.random() < 0.1:
        if events is not None:
            events.append(Message(
                text=f"{attacker.active().name} flinched from {defender.active().name}'s Stench!"
            ))

    # Cute Charm: 30% infatuation on contact
    if name == "Cute Charm" and random.random() < 0.3:
        if events is not None:
            events.append(Message(
                text=f"{attacker.active().name} fell in love from {defender.active().name}'s Cute Charm!"
            ))


def check_ability_prevents_switch(pokemon) -> bool:
    """Suction Cups prevents forced switching (Roar, Whirlwind)."""
    return _name(pokemon) == "Suction Cups"


# ── Tier 3: End-of-turn abilities ──────────────────────────────


def process_end_of_turn_ability(pokemon, events=None, trainer_name="") -> None:
    """Process end-of-turn ability effects (Shed Skin, Speed Boost)."""
    import random
    name = _name(pokemon)

    if name == "Shed Skin" and random.random() < 0.33:
        if pokemon.major_status is not None:
            effect_name = pokemon.major_status.name
            pokemon.remove_status_effect(pokemon.major_status)
            if events is not None:
                events.append(Message(text=f"{pokemon.name}'s Shed Skin cured its {effect_name.lower()}!"))
                from models.turn_result import StatusRemoved
                events.append(StatusRemoved(trainer=trainer_name))

    if name == "Speed Boost":
        actual = pokemon.apply_stage_change("stat_spd", 1)
        if events is not None and actual != 0:
            events.append(Message(text=f"{pokemon.name}'s Speed Boost raised its Speed!"))
            from models.turn_result import StatChange
            events.append(StatChange(
                trainer=trainer_name, pokemon_name=pokemon.name,
                stat_name="stat_spd", stage_change=actual,
            ))


# ── Tier 3: Synchronize ───────────────────────────────────────


def check_ability_synchronize(target, effect_name, events=None) -> None:
    """If the target has Synchronize and received a major status, pass it back."""
    name = _name(target)
    if name != "Synchronize":
        return
    # Called from the status application flow — the attacker parameter
    # is not available here. The caller must handle passing it back.
    # For now, this is a stub — the actual Synchronize logic needs
    # the attacker context from apply_status_effect_from_move.
    pass


# ── Tier 4: Switch-in abilities ────────────────────────────────


def apply_switch_abilities(new_trainer, opponent, events=None) -> None:
    """Apply abilities that trigger when a Pokemon switches in (Intimidate, Trace)."""
    name = _name(new_trainer.active())
    target = opponent.active()

    if name == "Intimidate" and target.is_alive():
        if check_ability_prevents(target, "stat_drop_by_opponent"):
            if events is not None:
                events.append(Message(
                    text=f"{target.name}'s {_name(target)} prevented Intimidate!"
                ))
        else:
            actual = target.apply_stage_change("stat_attk", -1)
            if events is not None:
                events.append(Message(
                    text=f"{new_trainer.active().name}'s Intimidate lowered {target.name}'s Attack!"
                ))
                if actual != 0:
                    from models.turn_result import StatChange
                    events.append(StatChange(
                        trainer=opponent.name, pokemon_name=target.name,
                        stat_name="stat_attk", stage_change=actual,
                    ))

    if name == "Trace":
        opponent_ability = _name(target)
        if opponent_ability and opponent_ability != "Trace":
            from data.abilities import Ability
            new_trainer.active().ability = Ability(
                opponent_ability,
                f"Traced from {target.name}",
            )
            if events is not None:
                events.append(Message(
                    text=f"{new_trainer.active().name}'s Trace copied {target.name}'s {opponent_ability}!"
                ))


def apply_switch_out_abilities(trainer, events=None) -> None:
    """Apply abilities that trigger when a Pokemon switches out (Natural Cure)."""
    old_mon = trainer.active()
    if _name(old_mon) == "Natural Cure" and old_mon.major_status is not None:
        old_mon.remove_status_effect(old_mon.major_status)
        if events is not None:
            events.append(Message(text=f"{old_mon.name} was cured by Natural Cure!"))


# ── Quick wins ──────────────────────────────────────────────────


def check_ability_accuracy_modifier(attacker) -> float:
    """Return an accuracy multiplier (1.0 = no change)."""
    name = _name(attacker.active())
    if name == "Hustle":
        return 0.8
    if name == "Compound Eyes":
        return 1.3
    return 1.0


def check_ability_halves_sleep_turns(pokemon) -> bool:
    """Early Bird halves sleep duration."""
    return _name(pokemon) == "Early Bird"


def check_ability_shield_dust(pokemon) -> bool:
    """Shield Dust prevents all secondary effects from moves."""
    return _name(pokemon) == "Shield Dust"


_SOUND_MOVES = {
    "heal-bell", "hyper-voice", "metal-sound", "perish-song",
    "roar", "screech", "sing", "supersonic", "uproar",
    "grasswhistle", "snore", "spark", "bug-buzz", "chatter",
}


def check_ability_blocks_sound(pokemon) -> bool:
    """Soundproof blocks sound-based moves."""
    return _name(pokemon) == "Soundproof"


def is_sound_move(move_name: str) -> bool:
    """Check if a move is sound-based."""
    return move_name.lower().replace(" ", "-") in _SOUND_MOVES


def check_ability_blocks_explosion(pokemon) -> bool:
    """Damp blocks Self-Destruct and Explosion."""
    return _name(pokemon) == "Damp"


def is_explosion_move(move_name: str) -> bool:
    """Check if a move is Self-Destruct or Explosion."""
    return move_name.lower() in ("self-destruct", "selfdestruct", "explosion")


def check_ability_liquid_ooze_defender(defender, attacker, damage, move) -> bool:
    """Liquid Ooze: drain moves deal damage instead of healing."""
    if _name(defender.active()) == "Liquid Ooze" and move.lifesteal > 0:
        target = attacker.active()
        target.hp = max(0, target.hp - damage)
        return True
    return False


_STENCH_FLINCH_CHANCE = 0.1


def check_ability_stench(pokemon) -> bool:
    """Stench may cause flinch on contact."""
    return _name(pokemon) == "Stench" and random.random() < _STENCH_FLINCH_CHANCE


# ── Weather system ──────────────────────────────────────────────


_WEATHER_SETTERS = {"Drizzle": "rain", "Drought": "sun", "Sand Stream": "sandstorm"}


def check_weather_setter(pokemon) -> str | None:
    """Return the weather type if this Pokemon sets weather on switch-in."""
    return _WEATHER_SETTERS.get(_name(pokemon))


def is_weather_active(weather: str | None, trainer1, trainer2) -> bool:
    """Check if weather is active (Cloud Nine / Air Lock negate)."""
    if not weather:
        return False
    for t in (trainer1, trainer2):
        if _name(t.active()) in ("Cloud Nine", "Air Lock"):
            return False
    return True


def modify_speed_by_weather(pokemon, speed: int, weather: str | None) -> int:
    """Apply weather-based speed modifiers (Swift Swim, Chlorophyll)."""
    if not weather:
        return speed
    name = _name(pokemon)
    if weather == "rain" and name == "Swift Swim":
        return speed * 2
    if weather == "sun" and name == "Chlorophyll":
        return speed * 2
    return speed


def modify_evasion_by_weather(pokemon, eva: int, weather: str | None) -> int:
    """Sand Veil: +1 evasion stage in sandstorm."""
    if weather == "sandstorm" and _name(pokemon) == "Sand Veil":
        return eva + 1
    return eva


_SANDSTORM_IMMUNE = {"Rock", "Steel", "Ground"}


def apply_weather_damage(pokemon, weather: str | None, events=None, trainer_name="") -> None:
    """Apply end-of-turn weather damage (sandstorm) or heal (Rain Dish)."""
    if not weather:
        return

    name = _name(pokemon)
    target = pokemon

    # Sandstorm damage
    if weather == "sandstorm":
        if not any(t in _SANDSTORM_IMMUNE for t in target.type):
            dmg = max(1, round(target.max_hp / 16))
            hp_before = target.hp
            target.hp = max(0, target.hp - dmg)
            if events is not None and dmg > 0:
                events.append(Message(text=f"{target.name} was buffeted by sandstorm!"))
                events.append(HPChange(
                    trainer=trainer_name, pokemon_name=target.name,
                    old_hp=hp_before, new_hp=target.hp, max_hp=target.max_hp,
                ))

    # Rain Dish heal
    if weather == "rain" and name == "Rain Dish":
        heal = max(1, round(target.max_hp / 16))
        hp_before = target.hp
        target.hp = min(target.max_hp, target.hp + heal)
        if events is not None:
            events.append(Message(text=f"{target.name} was healed by Rain Dish!"))
            events.append(HPChange(
                trainer=trainer_name, pokemon_name=target.name,
                old_hp=hp_before, new_hp=target.hp, max_hp=target.max_hp,
            ))

    # Hail damage
    if weather == "hail" and "Ice" not in target.type:
        dmg = max(1, round(target.max_hp / 16))
        hp_before = target.hp
        target.hp = max(0, target.hp - dmg)
        if events is not None and dmg > 0:
            events.append(Message(text=f"{target.name} was buffeted by hail!"))
            events.append(HPChange(
                trainer=trainer_name, pokemon_name=target.name,
                old_hp=hp_before, new_hp=target.hp, max_hp=target.max_hp,
            ))


def modify_damage_by_weather(move_type: str, weather: str | None) -> float:
    """Return a damage multiplier based on weather.
    Rain: Water +50%, Fire -50%. Sun: Fire +50%, Water -50%."""
    if not weather:
        return 1.0
    if weather == "rain":
        if move_type == "Water":
            return 1.5
        if move_type == "Fire":
            return 0.5
    if weather == "sun":
        if move_type == "Fire":
            return 1.5
        if move_type == "Water":
            return 0.5
    return 1.0




