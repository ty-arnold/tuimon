import sys
import os
import unittest
import copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from helpers import make_pokemon, make_move, make_trainer
from data import poison, paralysis, sleep, burn, freeze, confusion
from data.abilities import Ability
from battle.abilities import check_ability_prevents
from battle.damage import calculate_damage


class TestStatusImmunityAbilities(unittest.TestCase):
    """Tier 1 ability tests — status/stat drop/crit prevention."""

    def test_limber_prevents_paralysis(self):
        poke = make_pokemon()
        poke.ability = Ability("Limber")
        self.assertFalse(poke.apply_status_effect(copy.deepcopy(paralysis)))

    def test_immunity_prevents_poison(self):
        poke = make_pokemon()
        poke.ability = Ability("Immunity")
        self.assertFalse(poke.apply_status_effect(copy.deepcopy(poison)))

    def test_insomnia_prevents_sleep(self):
        poke = make_pokemon()
        poke.ability = Ability("Insomnia")
        self.assertFalse(poke.apply_status_effect(copy.deepcopy(sleep)))

    def test_vital_spirit_prevents_sleep(self):
        poke = make_pokemon()
        poke.ability = Ability("Vital Spirit")
        self.assertFalse(poke.apply_status_effect(copy.deepcopy(sleep)))

    def test_magma_armor_prevents_freeze(self):
        poke = make_pokemon()
        poke.ability = Ability("Magma Armor")
        self.assertFalse(poke.apply_status_effect(copy.deepcopy(freeze)))

    def test_water_veil_prevents_burn(self):
        poke = make_pokemon()
        poke.ability = Ability("Water Veil")
        self.assertFalse(poke.apply_status_effect(copy.deepcopy(burn)))

    def test_own_tempo_prevents_confusion(self):
        poke = make_pokemon()
        poke.ability = Ability("Own Tempo")
        self.assertFalse(poke.apply_status_effect(copy.deepcopy(confusion)))

    def test_limber_does_not_block_poison(self):
        """Limber should only block paralysis, not other statuses."""
        poke = make_pokemon()
        poke.ability = Ability("Limber")
        self.assertTrue(poke.apply_status_effect(copy.deepcopy(poison)))

    def test_water_veil_does_not_block_poison(self):
        poke = make_pokemon()
        poke.ability = Ability("Water Veil")
        self.assertTrue(poke.apply_status_effect(copy.deepcopy(poison)))

    def test_no_ability_allows_status(self):
        poke = make_pokemon()
        self.assertTrue(poke.apply_status_effect(copy.deepcopy(paralysis)))


class TestStatDropPreventionAbilities(unittest.TestCase):
    """Clear Body, White Smoke, Keen Eye, Hyper Cutter."""

    def test_clear_body_prevents_stat_drop(self):
        poke = make_pokemon()
        poke.ability = Ability("Clear Body")
        self.assertTrue(check_ability_prevents(poke, "stat_drop_by_opponent"))

    def test_white_smoke_prevents_stat_drop(self):
        poke = make_pokemon()
        poke.ability = Ability("White Smoke")
        self.assertTrue(check_ability_prevents(poke, "stat_drop_by_opponent"))

    def test_keen_eye_prevents_acc_drop(self):
        poke = make_pokemon()
        poke.ability = Ability("Keen Eye")
        self.assertTrue(check_ability_prevents(poke, "acc_drop"))

    def test_hyper_cutter_prevents_atk_drop(self):
        poke = make_pokemon()
        poke.ability = Ability("Hyper Cutter")
        self.assertTrue(check_ability_prevents(poke, "atk_drop"))

    def test_keen_eye_does_not_block_other_drops(self):
        poke = make_pokemon()
        poke.ability = Ability("Keen Eye")
        self.assertFalse(check_ability_prevents(poke, "stat_drop_by_opponent"))


class TestCritImmunityAbilities(unittest.TestCase):
    """Battle Armor and Shell Armor prevent critical hits."""

    def test_battle_armor_prevents_crit(self):
        poke = make_pokemon()
        poke.ability = Ability("Battle Armor")
        self.assertTrue(check_ability_prevents(poke, "crit"))

    def test_shell_armor_prevents_crit(self):
        poke = make_pokemon()
        poke.ability = Ability("Shell Armor")
        self.assertTrue(check_ability_prevents(poke, "crit"))

    def test_regular_pokemon_does_not_prevent_crit(self):
        poke = make_pokemon()
        self.assertFalse(check_ability_prevents(poke, "crit"))


class TestInnerFocus(unittest.TestCase):
    """Inner Focus prevents flinching."""

    def test_inner_focus_prevents_flinch(self):
        poke = make_pokemon()
        poke.ability = Ability("Inner Focus")
        self.assertTrue(check_ability_prevents(poke, "flinch"))


if __name__ == "__main__":
    unittest.main()
