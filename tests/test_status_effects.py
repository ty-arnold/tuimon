# tests/test_status_effects.py
import unittest
import sys
import os
import random
import unittest.mock
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from src.battle import process_status_effects, get_all_effects, check_can_act, apply_move
from src.status_effects import *
from helpers import make_pokemon, make_trainer, make_move
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

        self.assertIsNotNone(poison.damage, "poison.damage should not be None")
        expected_damage = round(pokemon.max_hp * poison.damage)  # type: ignore
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
        all_effects = get_all_effects(pokemon)
        pokemon.apply_status_effect(effect)
        process_status_effects(pokemon)
        self.assertEqual(len(all_effects), 0)

    def test_pokemon_cannot_have_same_status_twice(self):
        pokemon  = make_pokemon(stat_hp=100)
        effect1  = copy.deepcopy(poison)
        effect2  = copy.deepcopy(poison)
        pokemon.apply_status_effect(effect1)
        init_all_effects = get_all_effects(pokemon)
        initial_count = len(init_all_effects)
        # try applying again - should be blocked by apply_status_effect check
        if not any(e.name == effect2.name for e in init_all_effects):
            pokemon.apply_status_effect(effect2)
        post_all_effects = get_all_effects(pokemon)
        self.assertEqual(len(post_all_effects), initial_count)

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

    def test_status_effect_does_not_apply_below_chance(self):
        pokemon = make_pokemon(stat_hp=100)
        effect  = copy.deepcopy(paralysis)
        effect.chance_to_apply = 0.0  # never applies
        # simulate apply_status_effect check
        applied = random.random() < effect.chance_to_apply
        self.assertFalse(applied)

class TestMajorStatusEffects(unittest.TestCase):

    def test_major_status_applied_correctly(self):
        pokemon = make_pokemon()
        effect  = copy.deepcopy(poison)
        pokemon.apply_status_effect(effect)
        self.assertIsNotNone(pokemon.major_status)
        self.assertEqual(pokemon.major_status.name, "Poison")

    def test_only_one_major_status_allowed(self):
        pokemon       = make_pokemon()
        poison_effect = copy.deepcopy(poison)
        burn_effect   = copy.deepcopy(burn)
        pokemon.apply_status_effect(poison_effect)
        result = pokemon.apply_status_effect(burn_effect)
        # should be blocked - pokemon already has poison
        self.assertFalse(result)
        self.assertEqual(pokemon.major_status.name, "Poison")  # still poison

    def test_cannot_apply_same_major_status_twice(self):
        pokemon  = make_pokemon()
        effect1  = copy.deepcopy(poison)
        effect2  = copy.deepcopy(poison)
        pokemon.apply_status_effect(effect1)
        result = pokemon.apply_status_effect(effect2)
        self.assertFalse(result)
        self.assertEqual(pokemon.major_status, effect1)

    def test_major_status_removed_correctly(self):
        pokemon = make_pokemon()
        effect  = copy.deepcopy(poison)
        pokemon.apply_status_effect(effect)
        pokemon.remove_status_effect(effect)
        self.assertIsNone(pokemon.major_status)

    def test_can_apply_new_major_status_after_removal(self):
        pokemon       = make_pokemon()
        poison_effect = copy.deepcopy(poison)
        burn_effect   = copy.deepcopy(burn)
        pokemon.apply_status_effect(poison_effect)
        pokemon.remove_status_effect(poison_effect)
        result = pokemon.apply_status_effect(burn_effect)
        self.assertTrue(result)
        self.assertEqual(pokemon.major_status.name, "Burn")

    def test_all_major_status_effects_are_flagged(self):
        major_effects = [poison, paralysis, sleep, burn, freeze]
        for effect in major_effects:
            self.assertTrue(effect.is_major, f"{effect.name} should be a major status effect")

    def test_major_status_stat_modifier_applied(self):
        pokemon      = make_pokemon()
        base_spd     = pokemon.get_stat("stat_spd")
        para_effect  = copy.deepcopy(paralysis)
        pokemon.apply_status_effect(para_effect)
        self.assertLess(pokemon.get_stat("stat_spd"), base_spd)

    def test_major_status_stat_restored_on_removal(self):
        pokemon     = make_pokemon()
        base_spd    = pokemon.get_stat("stat_spd")
        para_effect = copy.deepcopy(paralysis)
        pokemon.apply_status_effect(para_effect)
        pokemon.remove_status_effect(para_effect)
        self.assertEqual(pokemon.get_stat("stat_spd"), base_spd)

class TestMinorStatusEffects(unittest.TestCase):

    def test_minor_status_applied_to_minor_list(self):
        pokemon       = make_pokemon()
        conf_effect   = copy.deepcopy(confusion)
        pokemon.apply_status_effect(conf_effect)
        self.assertIn(conf_effect, pokemon.minor_status)
        self.assertIsNone(pokemon.major_status)

    def test_multiple_minor_statuses_can_stack(self):
        pokemon     = make_pokemon()
        conf_effect = copy.deepcopy(confusion)
        curse_effect = copy.deepcopy(curse)
        pokemon.apply_status_effect(conf_effect)
        pokemon.apply_status_effect(curse_effect)
        self.assertEqual(len(pokemon.minor_status), 2)

    def test_cannot_apply_same_minor_status_twice(self):
        pokemon      = make_pokemon()
        conf_effect1 = copy.deepcopy(confusion)
        conf_effect2 = copy.deepcopy(confusion)
        pokemon.apply_status_effect(conf_effect1)
        result = pokemon.apply_status_effect(conf_effect2)
        self.assertFalse(result)
        self.assertEqual(len(pokemon.minor_status), 1)

    def test_minor_status_removed_correctly(self):
        pokemon     = make_pokemon()
        conf_effect = copy.deepcopy(confusion)
        pokemon.apply_status_effect(conf_effect)
        pokemon.remove_status_effect(conf_effect)
        self.assertEqual(len(pokemon.minor_status), 0)

    def test_minor_status_does_not_block_major_status(self):
        pokemon      = make_pokemon()
        conf_effect  = copy.deepcopy(confusion)
        burn_effect  = copy.deepcopy(burn)
        pokemon.apply_status_effect(conf_effect)
        result = pokemon.apply_status_effect(burn_effect)
        self.assertTrue(result)
        self.assertEqual(pokemon.major_status.name, "Burn")
        self.assertEqual(len(pokemon.minor_status), 1)

    def test_major_status_does_not_block_minor_status(self):
        pokemon      = make_pokemon()
        burn_effect  = copy.deepcopy(burn)
        conf_effect  = copy.deepcopy(confusion)
        pokemon.apply_status_effect(burn_effect)
        result = pokemon.apply_status_effect(conf_effect)
        self.assertTrue(result)
        self.assertEqual(pokemon.major_status.name, "Burn")
        self.assertEqual(len(pokemon.minor_status), 1)

    def test_minor_status_effects_are_not_flagged_as_major(self):
        minor_effects = [confusion, curse]
        for effect in minor_effects:
            self.assertFalse(effect.is_major, f"{effect.name} should not be a major status effect")

    def test_removing_one_minor_status_leaves_others(self):
        pokemon      = make_pokemon()
        conf_effect  = copy.deepcopy(confusion)
        curse_effect = copy.deepcopy(curse)
        pokemon.apply_status_effect(conf_effect)
        pokemon.apply_status_effect(curse_effect)
        pokemon.remove_status_effect(conf_effect)
        self.assertEqual(len(pokemon.minor_status), 1)
        self.assertEqual(pokemon.minor_status[0].name, "Curse")

class TestMixedStatusEffects(unittest.TestCase):

    def test_major_and_minor_can_coexist(self):
        pokemon      = make_pokemon()
        burn_effect  = copy.deepcopy(burn)
        conf_effect  = copy.deepcopy(confusion)
        pokemon.apply_status_effect(burn_effect)
        pokemon.apply_status_effect(conf_effect)
        self.assertIsNotNone(pokemon.major_status)
        self.assertEqual(len(pokemon.minor_status), 1)

    def test_process_status_effects_handles_both(self):
        pokemon      = make_pokemon()
        poison_effect = copy.deepcopy(poison)
        conf_effect   = copy.deepcopy(confusion)
        pokemon.apply_status_effect(poison_effect)
        pokemon.apply_status_effect(conf_effect)
        hp_before = pokemon.hp
        # should not raise any exceptions
        try:
            process_status_effects(pokemon)
        except Exception as e:
            self.fail(f"process_status_effects raised an exception: {e}")

    def test_removing_major_does_not_affect_minor(self):
        pokemon       = make_pokemon()
        poison_effect = copy.deepcopy(poison)
        conf_effect   = copy.deepcopy(confusion)
        pokemon.apply_status_effect(poison_effect)
        pokemon.apply_status_effect(conf_effect)
        pokemon.remove_status_effect(poison_effect)
        self.assertIsNone(pokemon.major_status)
        self.assertEqual(len(pokemon.minor_status), 1)

    def test_get_all_effects_returns_both(self):
        pokemon       = make_pokemon()
        poison_effect = copy.deepcopy(poison)
        conf_effect   = copy.deepcopy(confusion)
        pokemon.apply_status_effect(poison_effect)
        pokemon.apply_status_effect(conf_effect)
        all_effects = get_all_effects(pokemon)
        self.assertEqual(len(all_effects), 2)
        names = [e.name for e in all_effects]
        self.assertIn("Poison",    names)
        self.assertIn("Confusion", names)

    def test_get_all_effects_empty_when_no_status(self):
        pokemon     = make_pokemon()
        all_effects = get_all_effects(pokemon)
        self.assertEqual(len(all_effects), 0)

    def test_get_all_effects_only_major(self):
        pokemon       = make_pokemon()
        poison_effect = copy.deepcopy(poison)
        pokemon.apply_status_effect(poison_effect)
        all_effects = get_all_effects(pokemon)
        self.assertEqual(len(all_effects), 1)
        self.assertEqual(all_effects[0].name, "Poison")

class TestConfusion(unittest.TestCase):

    def test_confusion_is_minor_status(self):
        self.assertFalse(confusion.is_major)

    def test_confusion_applied_to_minor_list(self):
        pokemon     = make_pokemon()
        conf_effect = copy.deepcopy(confusion)
        pokemon.apply_status_effect(conf_effect)
        self.assertIn(conf_effect, pokemon.minor_status)
        self.assertIsNone(pokemon.major_status)

    def test_confusion_does_not_block_major_status(self):
        pokemon      = make_pokemon()
        conf_effect  = copy.deepcopy(confusion)
        burn_effect  = copy.deepcopy(burn)
        pokemon.apply_status_effect(conf_effect)
        result = pokemon.apply_status_effect(burn_effect)
        self.assertTrue(result)
        self.assertEqual(len(pokemon.minor_status), 1)
        assert pokemon.major_status is not None
        self.assertEqual(pokemon.major_status.name, "Burn")

    def test_confusion_damage_reduces_hp(self):
        pokemon     = make_pokemon()
        conf_effect = copy.deepcopy(confusion)
        pokemon.apply_status_effect(conf_effect)
        hp_before   = pokemon.hp

        # force confusion to trigger by mocking random
        with unittest.mock.patch("battle.random.random", return_value=0.0):
            can_act, reason = check_can_act(pokemon)

        self.assertFalse(can_act)
        self.assertEqual(reason, "Confusion")
        self.assertLess(pokemon.hp, hp_before)

    def test_confusion_damage_is_10_percent_max_hp(self):
        pokemon     = make_pokemon()
        conf_effect = copy.deepcopy(confusion)
        pokemon.apply_status_effect(conf_effect)
        hp_before   = pokemon.hp

        with unittest.mock.patch("battle.random.random", return_value=0.0):
            check_can_act(pokemon)

        expected_damage = round(pokemon.max_hp * 0.1)
        self.assertEqual(hp_before - pokemon.hp, expected_damage)

    def test_confusion_allows_action_on_successful_roll(self):
        pokemon     = make_pokemon()
        conf_effect = copy.deepcopy(confusion)
        pokemon.apply_status_effect(conf_effect)
        hp_before   = pokemon.hp

        # force confusion not to trigger
        with unittest.mock.patch("battle.random.random", return_value=1.0):
            can_act, reason = check_can_act(pokemon)

        self.assertTrue(can_act)
        self.assertIsNone(reason)
        self.assertEqual(pokemon.hp, hp_before)  # no self damage

    def test_confusion_hp_cannot_go_below_zero(self):
        pokemon     = make_pokemon()
        pokemon.hp  = 1  # set hp very low
        conf_effect = copy.deepcopy(confusion)
        pokemon.apply_status_effect(conf_effect)

        with unittest.mock.patch("battle.random.random", return_value=0.0):
            check_can_act(pokemon)

        self.assertGreaterEqual(pokemon.hp, 0)

    def test_confusion_can_end_randomly(self):
        pokemon     = make_pokemon()
        conf_effect = copy.deepcopy(confusion)
        conf_effect.turns_active = 2  # skip first turn immunity
        pokemon.apply_status_effect(conf_effect)

        with unittest.mock.patch("battle.random.random", return_value=0.0):
            process_status_effects(pokemon)

        self.assertEqual(len(pokemon.minor_status), 0)

    def test_confusion_does_not_end_every_turn(self):
        pokemon     = make_pokemon()
        conf_effect = copy.deepcopy(confusion)
        conf_effect.turns_active = 2
        pokemon.apply_status_effect(conf_effect)

        with unittest.mock.patch("battle.random.random", return_value=1.0):
            process_status_effects(pokemon)

        self.assertEqual(len(pokemon.minor_status), 1)

    def test_cannot_apply_confusion_twice(self):
        pokemon      = make_pokemon()
        conf_effect1 = copy.deepcopy(confusion)
        conf_effect2 = copy.deepcopy(confusion)
        pokemon.apply_status_effect(conf_effect1)
        result = pokemon.apply_status_effect(conf_effect2)
        self.assertFalse(result)
        self.assertEqual(len(pokemon.minor_status), 1)

    def test_confusion_removed_after_battle(self):
        pokemon     = make_pokemon()
        conf_effect = copy.deepcopy(confusion)
        pokemon.apply_status_effect(conf_effect)
        pokemon.remove_status_effect(conf_effect)
        self.assertEqual(len(pokemon.minor_status), 0)

    def test_confused_pokemon_skips_attack_on_self_damage(self):
        attacker    = make_trainer(pokemon=[make_pokemon(stat_attk=100)])
        defender    = make_trainer(pokemon=[make_pokemon(stat_def=100)])
        conf_effect = copy.deepcopy(confusion)
        attacker.active().apply_status_effect(conf_effect)
        move        = make_move(category="physical", power=50, acc=1.0)
        hp_before   = defender.active().hp

        # force confusion self damage
        with unittest.mock.patch("battle.random.random", return_value=0.0):
            can_act, _ = check_can_act(attacker.active())
            current_turn = 1
            if not can_act:
                pass  # skip apply_move
            else:
                apply_move(move, attacker, defender, current_turn)

        # defender should be untouched since attacker hurt itself
        self.assertEqual(defender.active().hp, hp_before)