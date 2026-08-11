import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from battle.modifiers import apply_modifier, get_modifier_value, clear_expired_modifiers
from helpers import make_pokemon, make_move, make_modifier


# ─────────────────────────────────────────────────────────────
# apply_modifier  — mutator, 4 branches
# ─────────────────────────────────────────────────────────────

class TestApplyModifier(unittest.TestCase):

    def setUp(self):
        self.pokemon = make_pokemon()
        self.events  = []

    def test_move_without_a_modifier_adds_nothing(self):
        apply_modifier(make_move(), self.pokemon, 1, events=self.events)
        self.assertEqual(self.pokemon.modifiers, [])

    def test_timed_modifier_gets_an_absolute_expiry_turn(self):
        move = make_move(modifier=make_modifier(turns=3))
        apply_modifier(move, self.pokemon, current_turn=5, events=self.events)
        self.assertEqual(self.pokemon.modifiers[0].expires_turn, 8)   # 5 + 3

    def test_zero_turn_modifier_is_permanent(self):
        move = make_move(modifier=make_modifier(turns=0))
        apply_modifier(move, self.pokemon, current_turn=5, events=self.events)
        self.assertEqual(self.pokemon.modifiers[0].expires_turn, -1)

    def test_applied_modifier_is_a_copy_not_the_move_template(self):
        """Regression guard: without the deepcopy, two Pokémon using the same
        move would share one Modifier object and clobber each other's expiry."""
        modifier = make_modifier(turns=3)
        move     = make_move(modifier=modifier)
        apply_modifier(move, self.pokemon, current_turn=5, events=self.events)
        self.assertEqual(modifier.expires_turn, -1)                 # template untouched
        self.assertIsNot(self.pokemon.modifiers[0], modifier)

    def test_same_move_used_by_two_pokemon_does_not_share_state(self):
        other = make_pokemon(name="Other")
        move  = make_move(modifier=make_modifier(turns=3))
        apply_modifier(move, self.pokemon, current_turn=1, events=self.events)
        apply_modifier(move, other,        current_turn=9, events=self.events)
        self.assertEqual(self.pokemon.modifiers[0].expires_turn, 4)
        self.assertEqual(other.modifiers[0].expires_turn, 12)


# ─────────────────────────────────────────────────────────────
# get_modifier_value  — calculation + consumption
# ─────────────────────────────────────────────────────────────

class TestGetModifierValue(unittest.TestCase):

    def setUp(self):
        self.pokemon = make_pokemon()
        self.move    = make_move(type=["Fire"], category="physical")

    def test_no_modifiers_is_neutral(self):
        value = get_modifier_value("power_modifier", self.move, self.pokemon, 1)
        self.assertEqual(value, 1.0)

    def test_matching_modifier_is_applied(self):
        self.pokemon.add_modifier(make_modifier(power_modifier=2.0, turns=-1))
        value = get_modifier_value("power_modifier", self.move, self.pokemon, 1)
        self.assertEqual(value, 2.0)

    def test_modifiers_multiply_together(self):
        self.pokemon.add_modifier(make_modifier(power_modifier=2.0))
        self.pokemon.add_modifier(make_modifier(power_modifier=1.5))
        value = get_modifier_value("power_modifier", self.move, self.pokemon, 1)
        self.assertEqual(value, 3.0)

    def test_type_condition_filters_out_non_matching_moves(self):
        self.pokemon.add_modifier(make_modifier(power_modifier=2.0, type_condition="Water"))
        value = get_modifier_value("power_modifier", self.move, self.pokemon, 1)
        self.assertEqual(value, 1.0)

    def test_type_condition_applies_to_matching_moves(self):
        self.pokemon.add_modifier(make_modifier(power_modifier=2.0, type_condition="Fire"))
        value = get_modifier_value("power_modifier", self.move, self.pokemon, 1)
        self.assertEqual(value, 2.0)

    def test_category_condition_filters_out_non_matching_moves(self):
        self.pokemon.add_modifier(make_modifier(power_modifier=2.0, category_condition="special"))
        value = get_modifier_value("power_modifier", self.move, self.pokemon, 1)
        self.assertEqual(value, 1.0)

    def test_requesting_an_unset_attribute_is_neutral(self):
        self.pokemon.add_modifier(make_modifier(power_modifier=2.0))
        value = get_modifier_value("damage_modifier", self.move, self.pokemon, 1)
        self.assertEqual(value, 1.0)

    def test_different_attributes_are_read_independently(self):
        self.pokemon.add_modifier(make_modifier(power_modifier=2.0, accuracy_modifier=0.5))
        self.assertEqual(get_modifier_value("power_modifier",    self.move, self.pokemon, 1), 2.0)
        self.assertEqual(get_modifier_value("accuracy_modifier", self.move, self.pokemon, 1), 0.5)


class TestModifierLifecycle(unittest.TestCase):
    """Boundary behaviour around expiry — `is_active` uses `<=` while the
    consumption check uses `>=`, so the expiry turn is both active and final."""

    def setUp(self):
        self.pokemon = make_pokemon()
        self.move    = make_move()
        apply_modifier(make_move(modifier=make_modifier(power_modifier=2.0, turns=2)),
                       self.pokemon, current_turn=1)
        # expires_turn == 3

    def test_modifier_applies_before_expiry(self):
        self.assertEqual(get_modifier_value("power_modifier", self.move, self.pokemon, 2), 2.0)
        self.assertEqual(len(self.pokemon.modifiers), 1)

    def test_modifier_still_applies_on_its_expiry_turn(self):
        self.assertEqual(get_modifier_value("power_modifier", self.move, self.pokemon, 3), 2.0)

    def test_modifier_is_consumed_on_its_expiry_turn(self):
        get_modifier_value("power_modifier", self.move, self.pokemon, 3)
        self.assertEqual(self.pokemon.modifiers, [])

    def test_modifier_read_after_expiry_is_inert_but_lingers(self):
        """Documents current behaviour: past the expiry turn `is_active` is False,
        so the modifier is never visited and never consumed by this function.
        It only disappears via clear_expired_modifiers()."""
        value = get_modifier_value("power_modifier", self.move, self.pokemon, 4)
        self.assertEqual(value, 1.0)
        self.assertEqual(len(self.pokemon.modifiers), 1)   # still there
        clear_expired_modifiers(self.pokemon, 4)
        self.assertEqual(self.pokemon.modifiers, [])

    def test_permanent_modifier_is_never_consumed(self):
        pokemon = make_pokemon()
        apply_modifier(make_move(modifier=make_modifier(power_modifier=2.0, turns=0)),
                       pokemon, current_turn=1)
        for turn in range(1, 20):
            get_modifier_value("power_modifier", self.move, pokemon, turn)
        self.assertEqual(len(pokemon.modifiers), 1)

    @unittest.expectedFailure
    def test_consume_message_is_emitted_when_modifier_expires(self):
        """FIXME: crashes with TypeError.

        `modifiers.py:37` calls msg(message=...) with no message key —
        msg() requires a positional `key`. This branch has never run.
        Remove the decorator once fixed."""
        pokemon = make_pokemon()
        apply_modifier(
            make_move(modifier=make_modifier(power_modifier=2.0, turns=1,
                                             consume_message="The effect faded!")),
            pokemon, current_turn=1)
        events = []
        get_modifier_value("power_modifier", self.move, pokemon, 2, events=events)
        self.assertEqual(len(events), 1)


# ─────────────────────────────────────────────────────────────
# clears_on_switch  — interaction with Pokemon.clear_all_modifiers
# ─────────────────────────────────────────────────────────────

class TestClearOnSwitch(unittest.TestCase):

    def test_switch_clears_transient_modifiers(self):
        pokemon = make_pokemon()
        pokemon.add_modifier(make_modifier(clears_on_switch=True))
        pokemon.clear_all_modifiers()
        self.assertEqual(pokemon.modifiers, [])

    def test_switch_keeps_persistent_modifiers(self):
        pokemon = make_pokemon()
        pokemon.add_modifier(make_modifier(clears_on_switch=False))
        pokemon.clear_all_modifiers()
        self.assertEqual(len(pokemon.modifiers), 1)

    def test_force_clears_everything(self):
        pokemon = make_pokemon()
        pokemon.add_modifier(make_modifier(clears_on_switch=False))
        pokemon.clear_all_modifiers(force=True)
        self.assertEqual(pokemon.modifiers, [])


if __name__ == "__main__":
    unittest.main()
