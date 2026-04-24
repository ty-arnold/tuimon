import sys
import os
import unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from helpers import make_pokemon

class TestStages(unittest.TestCase):

    def test_stage_cannot_exceed_plus_six(self):
        pokemon = make_pokemon()
        for _ in range(10):
            pokemon.apply_stage_change("stat_attk", 1)
        self.assertEqual(pokemon.stage_attk, 6)

    def test_stage_cannot_go_below_minus_six(self):
        pokemon = make_pokemon()
        for _ in range(10):
            pokemon.apply_stage_change("stat_attk", -1)
        self.assertEqual(pokemon.stage_attk, -6)

    def test_positive_stage_increases_stat(self):
        pokemon   = make_pokemon(stat_attk=100)
        base_calc = pokemon.get_stat("stat_attk")
        pokemon.apply_stage_change("stat_attk", 1)
        self.assertGreater(pokemon.get_stat("stat_attk"), base_calc)

    def test_negative_stage_decreases_stat(self):
        pokemon      = make_pokemon(stat_attk=100)
        base_calc    = pokemon.get_stat("stat_attk")  # get calculated value at stage 0
        pokemon.apply_stage_change("stat_attk", -1)
        self.assertLess(pokemon.get_stat("stat_attk"), base_calc)

    def test_zero_stage_returns_base_stat(self):
        pokemon = make_pokemon(stat_attk=100)
        # stage 0 should return the calculated stat unchanged
        self.assertEqual(pokemon.get_stat("stat_attk"), pokemon.stat_attk)

    def test_stage_reset_after_battle(self):
        pokemon = make_pokemon(stat_attk=100)
        pokemon.apply_stage_change("stat_attk", 3)
        pokemon.stage_attk = 0  # simulate end of battle reset
        self.assertEqual(pokemon.get_stat("stat_attk"), pokemon.stat_attk)