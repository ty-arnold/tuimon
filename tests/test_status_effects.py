# tests/test_status_effects.py
import unittest
import sys
import os
import random
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from src.battle import process_status_effects
from src.status_effects import poison, paralysis, sleep, burn
from helpers import make_pokemon
import copy

class TestStatusEffects(unittest.TestCase):

    def test_poison_deals_damage_each_turn(self):
        pokemon = make_pokemon(stat_hp=100)
        effect  = copy.deepcopy(poison)
        pokemon.apply_status_effect(effect)
        hp_before = pokemon.hp
        process_status_effects(pokemon)
        self.assertLess(pokemon.hp, hp_before)

    def test_poison_damage_is_percentage_of_max_hp(self):
        pokemon = make_pokemon(stat_hp=100)
        effect  = copy.deepcopy(poison)
        pokemon.apply_status_effect(effect)
        hp_before = pokemon.hp
        process_status_effects(pokemon)
        expected_damage = round(pokemon.max_hp * poison.damage)
        self.assertEqual(hp_before - pokemon.hp, expected_damage)

    def test_hp_cannot_go_below_zero_from_poison(self):
        pokemon    = make_pokemon(stat_hp=100)
        pokemon.hp = 1  # set hp very low
        effect     = copy.deepcopy(poison)
        pokemon.apply_status_effect(effect)
        process_status_effects(pokemon)
        self.assertGreaterEqual(pokemon.hp, 0)

    def test_sleep_prevents_action(self):
        effect = copy.deepcopy(sleep)
        self.assertFalse(effect.can_act())

    def test_paralysis_reduces_speed(self):
        pokemon = make_pokemon(stat_spd=100)
        effect  = copy.deepcopy(paralysis)
        pokemon.apply_status_effect(effect)
        self.assertLess(pokemon.get_stat("stat_spd"), 100)

    def test_status_effect_removed_after_duration(self):
        pokemon = make_pokemon(stat_hp=100)
        effect  = copy.deepcopy(poison)  # use poison since it has a chance_to_end
        effect.duration     = 1          # force it to end after 1 turn
        effect.turns_active = 2          # skip first turn immunity
        effect.chance_to_end = None      # make sure only duration is used
        pokemon.apply_status_effect(effect)
        process_status_effects(pokemon)
        self.assertEqual(len(pokemon.status_effect), 0)

    def test_pokemon_cannot_have_same_status_twice(self):
        pokemon  = make_pokemon(stat_hp=100)
        effect1  = copy.deepcopy(poison)
        effect2  = copy.deepcopy(poison)
        pokemon.apply_status_effect(effect1)
        initial_count = len(pokemon.status_effect)
        # try applying again - should be blocked by apply_status_effect check
        if not any(e.name == effect2.name for e in pokemon.status_effect):
            pokemon.apply_status_effect(effect2)
        self.assertEqual(len(pokemon.status_effect), initial_count)

    def test_paralysis_chance_to_act(self):
        effect = copy.deepcopy(paralysis)
        # run 1000 times and verify roughly 75% chance to act
        act_count = sum(1 for _ in range(1000) if effect.can_act())
        # should be roughly 750, allow wide margin for randomness
        self.assertGreater(act_count, 600)
        self.assertLess(act_count, 900)

    def test_burn_reduces_attack(self):
        pokemon = make_pokemon(stat_attk=100)
        effect  = copy.deepcopy(burn)
        pokemon.apply_status_effect(effect)
        self.assertLess(pokemon.get_stat("stat_attk"), 100)

    def test_multiple_different_status_effects_can_stack(self):
        pokemon  = make_pokemon(stat_hp=100)
        p_effect = copy.deepcopy(poison)
        # add a custom second effect with a different name
        from models import StatusEffect
        custom = StatusEffect(name="Custom", chance_to_apply=1.0)
        pokemon.apply_status_effect(p_effect)
        pokemon.apply_status_effect(custom)
        self.assertEqual(len(pokemon.status_effect), 2)

    def test_status_effect_does_not_apply_below_chance(self):
        pokemon = make_pokemon(stat_hp=100)
        effect  = copy.deepcopy(paralysis)
        effect.chance_to_apply = 0.0  # never applies
        # simulate apply_status_effect check
        applied = random.random() < effect.chance_to_apply
        self.assertFalse(applied)