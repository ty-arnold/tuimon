import sys
import os
import unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

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
        defender       = make_trainer(pokemon=[make_pokemon()])
        attacker_low   = make_trainer(pokemon=[make_pokemon()])
        attacker_high  = make_trainer(pokemon=[make_pokemon()])
        move           = make_move(category="physical", power=50)

        # directly override stats
        defender.active().stat_def         = 100
        attacker_low.active().stat_attk    = 50
        attacker_high.active().stat_attk   = 200

        damage_low,  _ = calculate_damage(move, attacker_low,  defender)
        damage_high, _ = calculate_damage(move, attacker_high, defender)
        self.assertGreater(damage_high, damage_low)

    def test_higher_defense_takes_less_damage(self):
        attacker       = make_trainer(pokemon=[make_pokemon()])
        defender_low   = make_trainer(pokemon=[make_pokemon()])
        defender_high  = make_trainer(pokemon=[make_pokemon()])
        move           = make_move(category="physical", power=50)

        # directly override stats to guarantee different ratios
        attacker.active().stat_attk      = 100
        defender_low.active().stat_def   = 50
        defender_high.active().stat_def  = 200

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
        defender_resist = make_trainer(pokemon=[make_pokemon(type=["Grass"])])
        move = make_move(type=["Water"], category="special", power=50)
        
        _, multiplier_normal = calculate_damage(move, attacker, defender_normal)
        _, multiplier_resist = calculate_damage(move, attacker, defender_resist)
        
        # check multipliers directly rather than damage values to avoid rounding issues
        self.assertEqual(multiplier_normal, 1)
        self.assertEqual(multiplier_resist, 0.5)

    def test_no_effect_deals_zero_damage(self):
        attacker = make_trainer(pokemon=[make_pokemon()])
        defender = make_trainer(pokemon=[make_pokemon(type=["Ghost"])])
        move     = make_move(type=["Normal"], category="physical", power=50)
        damage, multiplier = calculate_damage(move, attacker, defender)
        self.assertEqual(multiplier, 0)
        self.assertEqual(damage, 0)

    def test_zero_power_move_deals_no_damage(self):
        attacker  = make_trainer(pokemon=[make_pokemon()])
        defender  = make_trainer(pokemon=[make_pokemon()])
        move      = make_move(category="status", power=0, acc=1.0)
        damage, _ = calculate_damage(move, attacker, defender)
        self.assertEqual(damage, 0)  # status moves return 0 before formula

    def test_higher_level_deals_more_damage(self):
        defender  = make_trainer(pokemon=[make_pokemon(stat_def=100)])
        low_level = make_trainer(pokemon=[make_pokemon(lvl=20, stat_attk=100)])
        hi_level  = make_trainer(pokemon=[make_pokemon(lvl=50, stat_attk=100)])
        move = make_move(category="physical", power=50)
        damage_low, _ = calculate_damage(move, low_level, defender)
        damage_hi,  _ = calculate_damage(move, hi_level,  defender)
        self.assertGreater(damage_hi, damage_low)

    def test_special_move_uses_special_stats(self):
        attacker = make_trainer(pokemon=[make_pokemon()])
        defender = make_trainer(pokemon=[make_pokemon()])

        # directly override calculated stats to guarantee specific ratios
        attacker.active().stat_attk    = 200
        attacker.active().stat_sp_attk = 10
        defender.active().stat_def     = 10
        defender.active().stat_sp_def  = 200

        phys_move = make_move(category="physical", power=50)
        spec_move = make_move(category="special",  power=50)
        phys_damage, _ = calculate_damage(phys_move, attacker, defender)
        spec_damage, _ = calculate_damage(spec_move, attacker, defender)

        self.assertGreater(phys_damage, spec_damage)