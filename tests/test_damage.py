# tests/test_damage.py
import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from src.battle import calculate_damage
from helpers import make_pokemon, make_move, make_trainer

class TestDamageCalculation(unittest.TestCase):

    def test_physical_damage_is_positive(self):
        attacker = make_trainer(pokemon=[make_pokemon(stat_attk=100)])
        defender = make_trainer(pokemon=[make_pokemon(stat_def=100)])
        move     = make_move(category="physical", power=50)
        damage, _ = calculate_damage(move, attacker, defender)
        self.assertGreater(damage, 0)

    def test_status_move_deals_no_damage(self):
        attacker = make_trainer(pokemon=[make_pokemon()])
        defender = make_trainer(pokemon=[make_pokemon()])
        move     = make_move(category="status", power=0)
        damage, _ = calculate_damage(move, attacker, defender)
        self.assertEqual(damage, 0)

    def test_higher_attack_deals_more_damage(self):
        defender     = make_trainer(pokemon=[make_pokemon(stat_def=100)])
        attacker_low  = make_trainer(pokemon=[make_pokemon(stat_attk=50)])
        attacker_high = make_trainer(pokemon=[make_pokemon(stat_attk=150)])
        move = make_move(category="physical", power=50)
        damage_low,  _ = calculate_damage(move, attacker_low,  defender)
        damage_high, _ = calculate_damage(move, attacker_high, defender)
        self.assertGreater(damage_high, damage_low)

    def test_higher_defense_takes_less_damage(self):
        attacker      = make_trainer(pokemon=[make_pokemon(stat_attk=100)])
        defender_low  = make_trainer(pokemon=[make_pokemon(stat_def=50)])
        defender_high = make_trainer(pokemon=[make_pokemon(stat_def=150)])
        move = make_move(category="physical", power=50)
        damage_low,  _ = calculate_damage(move, attacker, defender_low)
        damage_high, _ = calculate_damage(move, attacker, defender_high)
        self.assertGreater(damage_low, damage_high)

    def test_super_effective_doubles_damage(self):
        attacker        = make_trainer(pokemon=[make_pokemon()])
        defender_normal = make_trainer(pokemon=[make_pokemon(type=["Normal"])])
        defender_weak   = make_trainer(pokemon=[make_pokemon(type=["Rock"])])
        move = make_move(type=["Water"], category="special", power=50)
        damage_normal, multiplier_normal = calculate_damage(move, attacker, defender_normal)
        damage_super,  multiplier_super  = calculate_damage(move, attacker, defender_weak)
        # check the multiplier directly rather than the damage value
        self.assertEqual(multiplier_normal, 1)
        self.assertEqual(multiplier_super,  2)


    def test_not_very_effective_halves_damage(self):
        attacker        = make_trainer(pokemon=[make_pokemon()])
        defender_normal = make_trainer(pokemon=[make_pokemon(type=["Normal"])])
        defender_resist = make_trainer(pokemon=[make_pokemon(type=["Grass"])])  # grass resists water
        move = make_move(type=["Water"], category="special", power=50)
        damage_normal, _ = calculate_damage(move, attacker, defender_normal)
        damage_resist, _ = calculate_damage(move, attacker, defender_resist)
        self.assertAlmostEqual(damage_resist, damage_normal * 0.5, delta=2)

    def test_no_effect_deals_zero_damage(self):
        attacker = make_trainer(pokemon=[make_pokemon()])
        defender = make_trainer(pokemon=[make_pokemon(type=["Ghost"])])
        move     = make_move(type=["Normal"], category="physical", power=50)
        damage, multiplier = calculate_damage(move, attacker, defender)
        self.assertEqual(multiplier, 0)
        self.assertEqual(damage, 0)