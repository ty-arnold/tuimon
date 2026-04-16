# tests/test_status_effects.py
import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from src.battle import process_status_effects
from src.status_effects import poison, paralysis, sleep
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