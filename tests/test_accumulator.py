import sys
import os
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from battle.accumulator  import release_accumulator
from models.move         import Accumulator
from models.turn_result  import HPChange
from helpers import make_pokemon, make_move, make_trainer


class AccumulatorTestBase(unittest.TestCase):
    """Crits are disabled for every test here — `random.random()` returning 1.0
    is never < the 1/16 crit chance, so damage is deterministic."""

    def setUp(self):
        self.attacker = make_trainer(name="A", pokemon=[make_pokemon(name="Atk")])
        self.defender = make_trainer(name="B", pokemon=[make_pokemon(name="Def")])
        self.events   = []
        patcher = patch("battle.damage.random.random", return_value=1.0)
        patcher.start()
        self.addCleanup(patcher.stop)


# ─────────────────────────────────────────────────────────────
# release formulas — one test per (type, formula) branch
# ─────────────────────────────────────────────────────────────

class TestReleaseFormulas(AccumulatorTestBase):

    def test_damage_taken_double_returns_twice_the_stored_damage(self):
        self.attacker.active().accumulator = 50
        config = Accumulator(type="damage_taken", release_formula="double", ignore_type=True)
        damage = release_accumulator(make_move(), self.attacker, self.defender, config,
                                     events=self.events)
        self.assertEqual(damage, 100)

    def test_turn_count_double_scales_linearly(self):
        config = Accumulator(type="turn_count", release_formula="double", ignore_type=True)
        move   = make_move(power=1)

        self.attacker.active().accumulator = 0
        first = release_accumulator(move, self.attacker, self.defender, config, events=self.events)
        self.defender.active().hp = self.defender.active().max_hp

        self.attacker.active().accumulator = 1
        second = release_accumulator(move, self.attacker, self.defender, config, events=self.events)

        self.assertEqual(second, first * 2)

    def test_turn_count_exponential_doubles_each_stack(self):
        config = Accumulator(type="turn_count", release_formula="exponential", ignore_type=True)
        move   = make_move(power=1)

        self.attacker.active().accumulator = 1
        one = release_accumulator(move, self.attacker, self.defender, config, events=self.events)
        self.defender.active().hp = self.defender.active().max_hp

        self.attacker.active().accumulator = 3
        three = release_accumulator(move, self.attacker, self.defender, config, events=self.events)

        self.assertEqual(three, one * 4)   # 2**3 / 2**1

    def test_unknown_formula_deals_no_damage(self):
        self.attacker.active().accumulator = 50
        config = Accumulator(type="damage_taken", release_formula="nonsense", ignore_type=True)
        damage = release_accumulator(make_move(), self.attacker, self.defender, config,
                                     events=self.events)
        self.assertEqual(damage, 0)

    def test_unknown_type_deals_no_damage(self):
        self.attacker.active().accumulator = 50
        config = Accumulator(type="nonsense", release_formula="double", ignore_type=True)
        damage = release_accumulator(make_move(), self.attacker, self.defender, config,
                                     events=self.events)
        self.assertEqual(damage, 0)

    def test_zero_stored_damage_releases_nothing(self):
        self.attacker.active().accumulator = 0
        config = Accumulator(type="damage_taken", release_formula="double", ignore_type=True)
        damage = release_accumulator(make_move(), self.attacker, self.defender, config,
                                     events=self.events)
        self.assertEqual(damage, 0)


# ─────────────────────────────────────────────────────────────
# type effectiveness — the ignore_type flag, both branches
# ─────────────────────────────────────────────────────────────

class TestAccumulatorTyping(AccumulatorTestBase):

    def test_ignore_type_skips_the_effectiveness_multiplier(self):
        self.defender.party[0] = make_pokemon(name="Rock", type=["Rock"])
        self.attacker.active().accumulator = 50
        config = Accumulator(type="damage_taken", release_formula="double", ignore_type=True)
        damage = release_accumulator(make_move(type=["Water"]), self.attacker, self.defender,
                                     config, events=self.events)
        self.assertEqual(damage, 100)

    def test_super_effective_doubles_the_release(self):
        self.defender.party[0] = make_pokemon(name="Rock", type=["Rock"])
        self.attacker.active().accumulator = 50
        config = Accumulator(type="damage_taken", release_formula="double", ignore_type=False)
        damage = release_accumulator(make_move(type=["Water"]), self.attacker, self.defender,
                                     config, events=self.events)
        self.assertEqual(damage, 200)

    def test_immune_defender_takes_nothing(self):
        self.defender.party[0] = make_pokemon(name="Ghost", type=["Ghost"])
        self.attacker.active().accumulator = 50
        config = Accumulator(type="damage_taken", release_formula="double", ignore_type=False)
        damage = release_accumulator(make_move(type=["Normal"]), self.attacker, self.defender,
                                     config, events=self.events)
        self.assertEqual(damage, 0)


# ─────────────────────────────────────────────────────────────
# side effects — HP, reset, events
# ─────────────────────────────────────────────────────────────

class TestAccumulatorSideEffects(AccumulatorTestBase):

    def _release(self, stored=50, **kwargs):
        self.attacker.active().accumulator = stored
        config = Accumulator(type="damage_taken", release_formula="double",
                             ignore_type=True, **kwargs)
        return release_accumulator(make_move(), self.attacker, self.defender, config,
                                   events=self.events)

    def test_defender_loses_hp(self):
        before = self.defender.active().hp
        damage = self._release(stored=20)
        self.assertEqual(self.defender.active().hp, before - damage)

    def test_hp_is_clamped_at_zero(self):
        self._release(stored=99999)
        self.assertEqual(self.defender.active().hp, 0)

    def test_accumulator_resets_after_release(self):
        self._release(stored=50)
        self.assertEqual(self.attacker.active().accumulator, 0)

    def test_release_message_is_emitted_when_configured(self):
        self._release(stored=50, release_message="unleashed its energy")
        texts = [getattr(e, "text", "") for e in self.events]
        self.assertTrue(any("unleashed its energy" in t for t in texts))

    def test_no_release_message_when_not_configured(self):
        self._release(stored=50)
        texts = [getattr(e, "text", "") for e in self.events]
        self.assertFalse(any("unleashed" in t for t in texts))

    @unittest.expectedFailure
    def test_release_emits_an_hpchange_event(self):
        """FIXME: accumulator.py mutates HP without emitting HPChange, so the
        TUI never animates the bar for Bide/Rollout-style releases.
        Fixed in Step 7 of the BattleState refactor — remove the decorator then."""
        self._release(stored=20)
        self.assertTrue(any(isinstance(e, HPChange) for e in self.events))


if __name__ == "__main__":
    unittest.main()
