import sys
import os
import unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from src.battle import check_winner, resolve_turn, apply_move
from helpers import make_pokemon, make_move, make_trainer
from models import Trainer, Pokemon, Move
from src.battle import resolve_turn, get_turn_order

class TestBattle(unittest.TestCase):

    def test_check_winner_returns_none_when_both_alive(self):
        player = make_trainer(pokemon=[make_pokemon()])
        npc    = make_trainer(pokemon=[make_pokemon()])
        self.assertIsNone(check_winner(player, npc))

    def test_check_winner_returns_npc_when_player_fainted(self):
        player_mon    = make_pokemon()
        player_mon.hp = 0
        player        = make_trainer(pokemon=[player_mon])
        npc           = make_trainer(pokemon=[make_pokemon()])
        self.assertTrue(check_winner(player, npc))

    def test_check_winner_returns_player_when_npc_fainted(self):
        npc_mon    = make_pokemon()
        npc_mon.hp = 0
        player     = make_trainer(pokemon=[make_pokemon()])
        npc        = make_trainer(pokemon=[npc_mon])
        self.assertTrue(check_winner(player, npc))

    def test_faster_pokemon_attacks_first(self):
        attack_order = []
        fast_mon  = make_pokemon(name="Fast",  stat_spd=100)
        slow_mon  = make_pokemon(name="Slow",  stat_spd=50)
        player    = make_trainer(pokemon=[fast_mon])
        npc       = make_trainer(pokemon=[slow_mon])
        # fast pokemon should attack first
        self.assertGreater(
            player.active().get_stat("stat_spd"),
            npc.active().get_stat("stat_spd")
        )

    def test_hp_cannot_go_negative(self):
        attacker = make_trainer(pokemon=[make_pokemon(stat_attk=999)])
        defender = make_trainer(pokemon=[make_pokemon(stat_def=1)])
        move     = make_move(category="physical", power=250, acc=1.0)
        current_turn = 1
        apply_move(move, attacker, defender, current_turn)
        self.assertGreaterEqual(defender.active().hp, 0)

    def test_speed_tie_still_resolves(self):
        # equal speed should not crash
        player = make_trainer(pokemon=[make_pokemon(stat_spd=100)])
        npc    = make_trainer(pokemon=[make_pokemon(stat_spd=100)])
        move   = make_move(category="physical", power=50, acc=1.0)
        current_turn = 1
        # should not raise any exceptions
        try:
            resolve_turn(player, move, npc, move, current_turn)
        except Exception as e:
            self.fail(f"resolve_turn raised an exception: {e}")

    def test_fainted_pokemon_triggers_winner(self):
        player  = make_trainer(pokemon=[make_pokemon(stat_attk=999)])
        npc_mon = make_pokemon(stat_def=1, stat_hp=1)
        npc_mon.hp = 1
        npc     = make_trainer(pokemon=[npc_mon])
        move    = make_move(category="physical", power=250, acc=1.0)
        current_turn = 1
        resolve_turn(player, move, npc, move, current_turn)
        self.assertIsNotNone(check_winner(player, npc))

    def test_switching_pokemon_updates_selected_mon(self):
        mon1    = make_pokemon(name="Mon1")
        mon2    = make_pokemon(name="Mon2")
        trainer = make_trainer(pokemon=[mon1, mon2])
        self.assertEqual(trainer.selected_mon, 0)
        trainer.selected_mon = 1
        self.assertEqual(trainer.active(), mon2)

    def test_all_pokemon_fainted_ends_battle(self):
        player_mon    = make_pokemon()
        player_mon.hp = 0
        npc_mon       = make_pokemon()
        npc_mon.hp    = 0
        player        = make_trainer(pokemon=[player_mon])
        npc           = make_trainer(pokemon=[npc_mon])
        # both fainted - check_winner should return something
        self.assertIsNotNone(check_winner(player, npc))

class TestMovePriority(unittest.TestCase):

    def test_higher_priority_move_goes_first(self):
        # player has slower pokemon but higher priority move
        player = make_trainer(pokemon=[make_pokemon(stat_spd=50)])
        npc    = make_trainer(pokemon=[make_pokemon(stat_spd=150)])

        # high priority move like quick attack
        player_move = make_move(name="Quick Attack", power=40, acc=1.0, priority=1)
        npc_move    = make_move(name="Tackle",       power=40, acc=1.0, priority=0)

        order = get_turn_order(player, player_move, npc, npc_move, True, True)
        self.assertEqual(order.first, player)
        self.assertEqual(order.second, npc)

    def test_lower_priority_move_goes_second(self):
        # player has faster pokemon but lower priority move
        player = make_trainer(pokemon=[make_pokemon(stat_spd=150)])
        npc    = make_trainer(pokemon=[make_pokemon(stat_spd=50)])

        player_move = make_move(name="Tackle",       power=40, acc=1.0, priority=0)
        npc_move    = make_move(name="Quick Attack", power=40, acc=1.0, priority=1)

        order = get_turn_order(player, player_move, npc, npc_move, True, True)
        self.assertEqual(order.first, npc)
        self.assertEqual(order.second, player)

    def test_equal_priority_uses_speed(self):
        # both moves have same priority, faster pokemon goes first
        player = make_trainer(pokemon=[make_pokemon()])
        npc    = make_trainer(pokemon=[make_pokemon()])

        player.active().stat_spd = 150
        npc.active().stat_spd    = 50

        player_move = make_move(priority=0)
        npc_move    = make_move(priority=0)

        order = get_turn_order(player, player_move, npc, npc_move, True, True)
        self.assertEqual(order.first, player)
        self.assertEqual(order.second, npc)

    def test_equal_priority_slower_pokemon_goes_second(self):
        player = make_trainer(pokemon=[make_pokemon()])
        npc    = make_trainer(pokemon=[make_pokemon()])

        player.active().stat_spd = 50
        npc.active().stat_spd    = 150

        player_move = make_move(priority=0)
        npc_move    = make_move(priority=0)

        order = get_turn_order(player, player_move, npc, npc_move, True, True)
        self.assertEqual(order.first, npc)
        self.assertEqual(order.second, player)

    def test_equal_priority_equal_speed_resolves(self):
        # speed tie should not crash and should return a valid order
        player = make_trainer(pokemon=[make_pokemon()])
        npc    = make_trainer(pokemon=[make_pokemon()])

        player.active().stat_spd = 100
        npc.active().stat_spd    = 100

        player_move = make_move(priority=0)
        npc_move    = make_move(priority=0)

        try:
            order = get_turn_order(player, player_move, npc, npc_move, True, True)
            # result should be one of two valid orderings
            self.assertIn(order.first, [player, npc])
            self.assertIn(order.second, [player, npc])
            self.assertNotEqual(order.first, order.second)
        except Exception as e:
            self.fail(f"get_turn_order raised an exception on speed tie: {e}")

    def test_negative_priority_goes_last(self):
        # negative priority moves like trick room go last
        player = make_trainer(pokemon=[make_pokemon()])
        npc    = make_trainer(pokemon=[make_pokemon()])

        player.active().stat_spd = 150  # faster pokemon
        npc.active().stat_spd    = 50

        player_move = make_move(name="Slow Move", power=0,  acc=1.0, priority=-1)
        npc_move    = make_move(name="Tackle",    power=40, acc=1.0, priority=0)

        order = get_turn_order(player, player_move, npc, npc_move, True, True)
        # despite being faster, player's negative priority move goes second
        self.assertEqual(order.first,  npc)
        self.assertEqual(order.second, player)

    def test_same_high_priority_uses_speed(self):
        # if both moves have the same high priority, speed still decides
        player = make_trainer(pokemon=[make_pokemon()])
        npc    = make_trainer(pokemon=[make_pokemon()])

        player.active().stat_spd = 50
        npc.active().stat_spd    = 150

        player_move = make_move(name="Quick Attack", power=40, acc=1.0, priority=1)
        npc_move    = make_move(name="Quick Attack", power=40, acc=1.0, priority=1)

        order = get_turn_order(player, player_move, npc, npc_move, True, True)
        # both have priority 1, npc is faster so goes first
        self.assertEqual(order.first,  npc)
        self.assertEqual(order.second, player)

    def test_can_act_flags_preserved_in_order(self):
        # verify can_act flags are correctly assigned to first and second
        player = make_trainer(pokemon=[make_pokemon(stat_spd=150)])
        npc    = make_trainer(pokemon=[make_pokemon(stat_spd=50)])

        player_move = make_move(priority=0)
        npc_move    = make_move(priority=0)

        order = get_turn_order(player, player_move, npc, npc_move,
                               player_can_act=True, npc_can_act=False)

        # player is faster so goes first
        self.assertEqual(order.first,          player)
        self.assertTrue(order.first_can_act)   # player can act
        self.assertEqual(order.second,         npc)
        self.assertFalse(order.second_can_act) # npc cannot act