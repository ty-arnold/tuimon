import sys
import os
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from battle.controller   import BattleController
from core.battle_state   import BattlePhase
from models.turn_result  import TurnResult, Faint, Switch
from helpers import make_pokemon, make_move, make_trainer


class ControllerTestBase(unittest.TestCase):
    """Determinism recipe for anything that runs a full turn:

      * acc=None            -> check_accuracy() short-circuits, moves never miss
      * patch damage.random -> 1.0 is never < the 1/16 crit chance, so no crits
      * distinct speeds     -> no speed tie, so turn_order.random is never reached
    """

    PLAYER_SPD = 100
    NPC_SPD    = 50     # player moves first by default

    def setUp(self):
        self.move = make_move(name="Tackle", power=40, acc=None)

        player_mon = make_pokemon(name="Pika", stat_spd=self.PLAYER_SPD)
        npc_mon    = make_pokemon(name="Gengar", stat_spd=self.NPC_SPD)
        player_mon.moveset = [self.move]
        npc_mon.moveset    = [make_move(name="Bite", power=40, acc=None)]

        self.player = make_trainer(name="Ash",  pokemon=[player_mon])
        self.npc    = make_trainer(name="Gary", pokemon=[npc_mon])
        self.controller = BattleController(self.player, self.npc)

        patcher = patch("battle.damage.random.random", return_value=1.0)
        patcher.start()
        self.addCleanup(patcher.stop)

    def add_backup(self, trainer, name="Backup"):
        mon = make_pokemon(name=name)
        mon.moveset = [make_move(name="Scratch", power=40, acc=None)]
        trainer.party.append(mon)
        return mon

    def run_turn(self):
        self.controller.select_player_move(self.move)
        self.controller.select_npc_move()
        return self.controller.execute_turn()


# ─────────────────────────────────────────────────────────────
# action selection — phase transitions before resolution
# ─────────────────────────────────────────────────────────────

class TestActionSelection(ControllerTestBase):

    def test_starts_waiting_for_the_player(self):
        self.assertEqual(self.controller.phase, BattlePhase.PLAYER_ACTION)

    def test_selecting_a_move_advances_to_npc_action(self):
        self.controller.select_player_move(self.move)
        self.assertEqual(self.controller.phase, BattlePhase.NPC_ACTION)
        self.assertEqual(self.controller.player_action.kind, "move")
        self.assertIs(self.controller.player_action.move, self.move)

    def test_selecting_a_switch_advances_to_npc_action(self):
        self.add_backup(self.player)
        self.controller.select_player_switch(1)
        self.assertEqual(self.controller.phase, BattlePhase.NPC_ACTION)
        self.assertEqual(self.controller.player_action.kind, "switch")
        self.assertEqual(self.controller.player_action.switch_slot, 1)

    def test_npc_selection_advances_to_resolving(self):
        self.controller.select_player_move(self.move)
        self.controller.select_npc_move()
        self.assertEqual(self.controller.phase, BattlePhase.RESOLVING)
        self.assertIsNotNone(self.controller.npc_action)

    def test_npc_only_picks_moves_with_pp_remaining(self):
        out_of_pp = make_move(name="Empty", pp=0, acc=None)
        usable    = make_move(name="Usable", pp=5, acc=None)
        self.npc.active().moveset = [out_of_pp, usable]
        self.controller.select_npc_move()
        self.assertIs(self.controller.npc_action.move, usable)


# ─────────────────────────────────────────────────────────────
# execute_turn guards — the two ValueError branches
# ─────────────────────────────────────────────────────────────

class TestExecuteTurnGuards(ControllerTestBase):

    def test_raises_if_the_player_has_not_chosen(self):
        with self.assertRaises(ValueError):
            self.controller.execute_turn()

    def test_raises_if_the_npc_has_not_chosen(self):
        self.controller.select_player_move(self.move)
        with self.assertRaises(ValueError):
            self.controller.execute_turn()


# ─────────────────────────────────────────────────────────────
# turn bookkeeping
# ─────────────────────────────────────────────────────────────

class TestTurnBookkeeping(ControllerTestBase):

    def test_turn_counter_increments(self):
        self.assertEqual(self.controller.turn, 0)
        self.run_turn()
        self.assertEqual(self.controller.turn, 1)

    def test_actions_are_cleared_after_resolution(self):
        self.run_turn()
        self.assertIsNone(self.controller.player_action)
        self.assertIsNone(self.controller.npc_action)

    def test_result_is_appended_to_the_battle_log(self):
        self.run_turn()
        self.run_turn()
        self.assertEqual(len(self.controller.battle_log), 2)
        self.assertIsInstance(self.controller.battle_log[0], TurnResult)

    def test_returns_to_player_action_after_an_ordinary_turn(self):
        result = self.run_turn()
        self.assertEqual(result.phase, BattlePhase.PLAYER_ACTION)
        self.assertEqual(self.controller.phase, BattlePhase.PLAYER_ACTION)

    def test_both_sides_take_damage_on_an_ordinary_turn(self):
        self.run_turn()
        self.assertLess(self.player.active().hp, self.player.active().max_hp)
        self.assertLess(self.npc.active().hp,    self.npc.active().max_hp)

    def test_locked_turns_decrement_once_per_turn(self):
        self.player.locked_move  = self.move
        self.player.locked_turns = 2
        self.run_turn()
        self.assertEqual(self.player.locked_turns, 1)

    def test_locked_turns_untouched_when_no_move_is_locked(self):
        self.player.locked_turns = 5      # stale value, no locked_move
        self.run_turn()
        self.assertEqual(self.player.locked_turns, 5)


# ─────────────────────────────────────────────────────────────
# faint handling — the three post-turn phase branches
# ─────────────────────────────────────────────────────────────

class TestFaintPhases(ControllerTestBase):

    def test_npc_faint_with_backup_requests_an_npc_switch(self):
        self.add_backup(self.npc, name="NpcBackup")
        self.npc.active().hp = 1
        result = self.run_turn()
        self.assertEqual(result.phase, BattlePhase.NPC_SWITCH)
        self.assertTrue(any(isinstance(e, Faint) for e in result.events))

    def test_player_faint_with_backup_prompts_a_switch(self):
        self.add_backup(self.player, name="PlayerBackup")
        self.player.active().hp = 1
        result = self.run_turn()
        self.assertEqual(result.phase, BattlePhase.SWITCH_PROMPT)
        self.assertTrue(any(isinstance(e, Faint) for e in result.events))

    def test_faint_event_names_the_correct_trainer(self):
        self.add_backup(self.npc, name="NpcBackup")
        self.npc.active().hp = 1
        result = self.run_turn()
        faint = next(e for e in result.events if isinstance(e, Faint))
        self.assertEqual(faint.trainer, "Gary")

    def test_last_pokemon_fainting_ends_the_battle(self):
        self.npc.active().hp = 1
        result = self.run_turn()
        self.assertEqual(result.phase, BattlePhase.BATTLE_OVER)

    def test_player_wipe_ends_the_battle(self):
        self.player.active().hp = 1
        result = self.run_turn()
        self.assertEqual(result.phase, BattlePhase.BATTLE_OVER)


# ─────────────────────────────────────────────────────────────
# switching
# ─────────────────────────────────────────────────────────────

class TestSwitching(ControllerTestBase):

    def test_switch_changes_the_active_pokemon(self):
        self.add_backup(self.player, name="PlayerBackup")
        self.controller.select_player_switch(1)
        self.controller.select_npc_move()
        result = self.controller.execute_turn()
        self.assertEqual(self.player.active().name, "PlayerBackup")
        self.assertTrue(any(isinstance(e, Switch) for e in result.events))

    def test_switching_clears_stat_stages(self):
        self.add_backup(self.player, name="PlayerBackup")
        self.player.active().stage_attk = 2
        outgoing = self.player.active()
        self.controller.select_player_switch(1)
        self.controller.select_npc_move()
        self.controller.execute_turn()
        self.assertEqual(self.player.party[0].stage_attk, 2,
                         "stage stays on the model; only modifiers are cleared")
        self.assertIsNot(self.player.active(), outgoing)


# ─────────────────────────────────────────────────────────────
# known-bad behaviour — pinned so the fixes are visible
# ─────────────────────────────────────────────────────────────

class TestKnownIssues(ControllerTestBase):

    @unittest.expectedFailure
    def test_turn_result_reports_the_winner(self):
        """FIXME: TurnResult.winner is always None.

        resolve_turn() is typed `-> bool | None` and returns True/None, but
        controller.py:86 guards on `isinstance(winner, Trainer)`, which can
        never be true. battle_ui._handle_winner has therefore never displayed
        'You won!'. Fixed in Step 11 — remove the decorator then."""
        self.npc.active().hp = 1
        result = self.run_turn()
        self.assertEqual(result.winner, "player")

    def test_winner_is_currently_always_none(self):
        """Characterization: pins the bug above so a fix is a visible diff."""
        self.npc.active().hp = 1
        result = self.run_turn()
        self.assertEqual(result.phase, BattlePhase.BATTLE_OVER)
        self.assertIsNone(result.winner)

    def test_weather_is_recorded_on_the_turn_it_is_set(self):
        self.move.weather = "rain"
        self.run_turn()
        self.assertEqual(self.controller.weather, "rain")

    @unittest.expectedFailure
    def test_weather_persists_to_the_following_turn(self):
        """FIXME: resolve_turn() starts each turn with `weather = None` and never
        reads controller.weather, so weather lasts exactly one turn.
        Fixed in Step 8 — remove the decorator then."""
        self.move.weather = "rain"
        self.run_turn()
        self.move.weather = None
        self.run_turn()
        self.assertEqual(self.controller.weather, "rain")

    def test_weather_currently_clears_after_one_turn(self):
        """Characterization: pins the bug above."""
        self.move.weather = "rain"
        self.run_turn()
        self.move.weather = None
        self.run_turn()
        self.assertIsNone(self.controller.weather)


if __name__ == "__main__":
    unittest.main()
