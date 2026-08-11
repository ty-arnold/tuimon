import sys
import os
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from battle.move_effects import (
    apply_move_effect, clear_switch_effects, is_protected,
    get_screen_modifier, blocks_stat_changes,
)
from helpers import make_pokemon, make_move, make_trainer, make_move_effect


# ─────────────────────────────────────────────────────────────
# is_protected  — predicate, 4 branches
# ─────────────────────────────────────────────────────────────

class TestIsProtected(unittest.TestCase):

    def test_no_effects_means_not_protected(self):
        trainer = make_trainer()
        self.assertFalse(is_protected(trainer, make_move()))

    def test_non_protect_effect_is_ignored(self):
        trainer = make_trainer()
        trainer.active_effects.append(make_move_effect(effect_type="screen"))
        self.assertFalse(is_protected(trainer, make_move()))

    def test_protect_blocks_a_normal_move(self):
        trainer = make_trainer()
        trainer.active_effects.append(make_move_effect(effect_type="protect"))
        self.assertTrue(is_protected(trainer, make_move(name="Tackle")))

    def test_bypass_move_ignores_protect(self):
        trainer = make_trainer()
        trainer.active_effects.append(
            make_move_effect(effect_type="protect", bypass_moves=["feint"])
        )
        self.assertFalse(is_protected(trainer, make_move(name="Feint")))

    def test_move_name_is_slugified_before_bypass_lookup(self):
        """'Hyper Beam' must match the 'hyper-beam' slug in bypass_moves."""
        trainer = make_trainer()
        trainer.active_effects.append(
            make_move_effect(effect_type="protect", bypass_moves=["hyper-beam"])
        )
        self.assertFalse(is_protected(trainer, make_move(name="Hyper Beam")))


# ─────────────────────────────────────────────────────────────
# clear_switch_effects  — mutator, 2 branches
# ─────────────────────────────────────────────────────────────

class TestClearSwitchEffects(unittest.TestCase):

    def test_effects_clear_on_switch_by_default(self):
        trainer = make_trainer()
        trainer.active_effects.append(make_move_effect(effect_type="protect"))
        clear_switch_effects(trainer)
        self.assertEqual(trainer.active_effects, [])

    def test_effects_marked_persistent_survive_a_switch(self):
        trainer = make_trainer()
        trainer.active_effects.append(
            make_move_effect(effect_type="screen",
                             properties={"clears_on_switch": False})
        )
        clear_switch_effects(trainer)
        self.assertEqual(len(trainer.active_effects), 1)

    def test_clears_only_the_transient_effects(self):
        trainer = make_trainer()
        trainer.active_effects.append(make_move_effect(effect_type="protect"))
        trainer.active_effects.append(
            make_move_effect(effect_type="screen",
                             properties={"clears_on_switch": False})
        )
        clear_switch_effects(trainer)
        self.assertEqual([e.effect_type for e in trainer.active_effects], ["screen"])


# ─────────────────────────────────────────────────────────────
# get_screen_modifier  — calculation + mutation, 5 branches
# ─────────────────────────────────────────────────────────────

class TestScreenModifier(unittest.TestCase):

    def _screen(self, category, mult=0.5, expires_on=5):
        effect = make_move_effect(
            effect_type="screen",
            properties={"category_condition": category, "damage_modifier": mult},
        )
        effect.turns = expires_on   # absolute expiry turn
        return effect

    def test_no_screens_gives_neutral_modifier(self):
        defender = make_trainer()
        modifier = get_screen_modifier(make_move(category="physical"), defender, 1)
        self.assertEqual(modifier, 1.0)

    def test_matching_category_applies_the_reduction(self):
        defender = make_trainer()
        defender.active_effects.append(self._screen("physical"))
        modifier = get_screen_modifier(make_move(category="physical"), defender, 1)
        self.assertEqual(modifier, 0.5)

    def test_non_matching_category_is_ignored(self):
        defender = make_trainer()
        defender.active_effects.append(self._screen("physical"))
        modifier = get_screen_modifier(make_move(category="special"), defender, 1)
        self.assertEqual(modifier, 1.0)

    def test_two_screens_stack_multiplicatively(self):
        defender = make_trainer()
        defender.active_effects.append(self._screen("physical"))
        defender.active_effects.append(self._screen("physical", mult=0.5))
        modifier = get_screen_modifier(make_move(category="physical"), defender, 1)
        self.assertEqual(modifier, 0.25)

    def test_expired_screen_is_removed_from_the_trainer(self):
        defender = make_trainer()
        defender.active_effects.append(self._screen("physical", expires_on=3))
        get_screen_modifier(make_move(category="physical"), defender, current_turn=4)
        self.assertEqual(defender.active_effects, [])

    def test_screen_still_applies_on_its_final_turn(self):
        """Boundary: expiry is `turns <= current_turn`, and the modifier is
        multiplied in *before* the expiry check — so the last turn still benefits."""
        defender = make_trainer()
        defender.active_effects.append(self._screen("physical", expires_on=3))
        modifier = get_screen_modifier(make_move(category="physical"), defender, current_turn=3)
        self.assertEqual(modifier, 0.5)
        self.assertEqual(defender.active_effects, [])  # ...and is gone afterwards


# ─────────────────────────────────────────────────────────────
# blocks_stat_changes  — predicate, 2 branches
# ─────────────────────────────────────────────────────────────

class TestBlocksStatChanges(unittest.TestCase):

    def test_no_mist_allows_stat_changes(self):
        self.assertFalse(blocks_stat_changes(make_trainer()))

    def test_mist_blocks_stat_changes(self):
        trainer = make_trainer()
        trainer.active_effects.append(
            make_move_effect(effect_type="mist", properties={"blocks_stat_changes": True})
        )
        self.assertTrue(blocks_stat_changes(trainer))

    def test_mist_without_the_property_does_not_block(self):
        trainer = make_trainer()
        trainer.active_effects.append(make_move_effect(effect_type="mist"))
        self.assertFalse(blocks_stat_changes(trainer))


# ─────────────────────────────────────────────────────────────
# apply_move_effect  — dispatcher, 4 branches
# ─────────────────────────────────────────────────────────────

class TestApplyMoveEffectDispatch(unittest.TestCase):

    def setUp(self):
        self.attacker = make_trainer(name="A")
        self.defender = make_trainer(name="B")
        self.events   = []

    def test_move_without_an_effect_does_nothing(self):
        move = make_move()
        self.assertFalse(apply_move_effect(move, self.attacker, self.defender, 1, events=self.events))
        self.assertEqual(self.events, [])

    def test_unknown_effect_type_is_a_no_op(self):
        move = make_move(move_effect=make_move_effect(effect_type="nonsense"))
        self.assertFalse(apply_move_effect(move, self.attacker, self.defender, 1, events=self.events))

    def test_protect_targets_the_attacker(self):
        move = make_move(move_effect=make_move_effect(effect_type="protect", target="self"))
        apply_move_effect(move, self.attacker, self.defender, 1, events=self.events)
        self.assertEqual(len(self.attacker.active_effects), 1)
        self.assertEqual(self.defender.active_effects, [])

    def test_opponent_targeted_effect_lands_on_the_defender(self):
        move = make_move(move_effect=make_move_effect(
            effect_type="screen", target="opponent",
            properties={"category_condition": "physical", "damage_modifier": 0.5},
        ))
        apply_move_effect(move, self.attacker, self.defender, 1, events=self.events)
        self.assertEqual(len(self.defender.active_effects), 1)


# ─────────────────────────────────────────────────────────────
# protect  — 3 branches incl. the consecutive-use reduction
# ─────────────────────────────────────────────────────────────

class TestProtectEffect(unittest.TestCase):

    def setUp(self):
        self.trainer = make_trainer()
        self.other   = make_trainer(name="B")
        self.events  = []
        self.move    = make_move(move_effect=make_move_effect(
            effect_type="protect",
            properties={"consecutive_reduction": True},
        ))

    def test_first_protect_succeeds(self):
        apply_move_effect(self.move, self.trainer, self.other, 1, events=self.events)
        self.assertEqual(len(self.trainer.active_effects), 1)
        self.assertEqual(self.trainer.consecutive_protect, 1)

    def test_consecutive_protects_increment_the_counter(self):
        with patch("battle.move_effects.random.random", return_value=0.0):
            apply_move_effect(self.move, self.trainer, self.other, 1, events=self.events)
            apply_move_effect(self.move, self.trainer, self.other, 2, events=self.events)
        self.assertEqual(self.trainer.consecutive_protect, 2)

    @unittest.expectedFailure
    def test_failed_consecutive_protect_resets_the_counter(self):
        """FIXME: crashes with KeyError('target').

        `move_effects.py:60` calls msg("target_effect", pokemon=..., message=...)
        but the template is "{target} {message}". This branch has never run.
        Remove the decorator once fixed."""
        self.trainer.consecutive_protect = 1
        with patch("battle.move_effects.random.random", return_value=1.0):
            apply_move_effect(self.move, self.trainer, self.other, 2, events=self.events)
        self.assertEqual(self.trainer.consecutive_protect, 0)
        self.assertEqual(self.trainer.active_effects, [])


# ─────────────────────────────────────────────────────────────
# screen / mist  — "already active" guard, 2 branches each
# ─────────────────────────────────────────────────────────────

class TestScreenAndMistGuards(unittest.TestCase):

    def setUp(self):
        self.trainer = make_trainer()
        self.other   = make_trainer(name="B")
        self.events  = []

    def test_screen_expiry_is_stored_as_an_absolute_turn(self):
        move = make_move(move_effect=make_move_effect(
            effect_type="screen", turns=5,
            properties={"category_condition": "physical", "damage_modifier": 0.5},
        ))
        apply_move_effect(move, self.trainer, self.other, current_turn=3, events=self.events)
        self.assertEqual(self.trainer.active_effects[0].turns, 8)   # 3 + 5

    def test_duplicate_screen_of_same_category_fails(self):
        move = make_move(move_effect=make_move_effect(
            effect_type="screen",
            properties={"category_condition": "physical", "damage_modifier": 0.5},
        ))
        apply_move_effect(move, self.trainer, self.other, 1, events=self.events)
        apply_move_effect(move, self.trainer, self.other, 2, events=self.events)
        self.assertEqual(len(self.trainer.active_effects), 1)
        self.assertIn("But it failed!", [getattr(e, "text", "") for e in self.events])

    def test_screens_of_different_categories_coexist(self):
        physical = make_move(move_effect=make_move_effect(
            effect_type="screen",
            properties={"category_condition": "physical", "damage_modifier": 0.5}))
        special = make_move(move_effect=make_move_effect(
            effect_type="screen",
            properties={"category_condition": "special", "damage_modifier": 0.5}))
        apply_move_effect(physical, self.trainer, self.other, 1, events=self.events)
        apply_move_effect(special,  self.trainer, self.other, 1, events=self.events)
        self.assertEqual(len(self.trainer.active_effects), 2)

    def test_duplicate_mist_fails(self):
        move = make_move(move_effect=make_move_effect(
            effect_type="mist", properties={"blocks_stat_changes": True}))
        apply_move_effect(move, self.trainer, self.other, 1, events=self.events)
        apply_move_effect(move, self.trainer, self.other, 2, events=self.events)
        self.assertEqual(len(self.trainer.active_effects), 1)

    def test_applied_effect_is_a_copy_not_the_move_template(self):
        """Regression guard: the move's own MoveEffect must not be mutated,
        or every Pokémon sharing that move inherits the expiry turn."""
        effect = make_move_effect(
            effect_type="screen", turns=5,
            properties={"category_condition": "physical", "damage_modifier": 0.5})
        move = make_move(move_effect=effect)
        apply_move_effect(move, self.trainer, self.other, current_turn=3, events=self.events)
        self.assertEqual(effect.turns, 5)                      # template untouched
        self.assertIsNot(self.trainer.active_effects[0], effect)


if __name__ == "__main__":
    unittest.main()
