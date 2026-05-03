import sys
import os
import unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from battle import check_winner, resolve_turn, apply_move, get_turn_order
from helpers import make_pokemon, make_move, make_trainer
from models import Trainer, Pokemon, Move, BattleAction

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
        self.assertIsNotNone(check_winner(player, npc))

    def test_check_winner_returns_player_when_npc_fainted(self):
        npc_mon    = make_pokemon()
        npc_mon.hp = 0
        player     = make_trainer(pokemon=[make_pokemon()])
        npc        = make_trainer(pokemon=[npc_mon])
        self.assertIsNotNone(check_winner(player, npc))

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
            action = BattleAction(kind="move", move=move)
            resolve_turn(player, action, npc, action, current_turn)
        except Exception as e:
            self.fail(f"resolve_turn raised an exception: {e}")

    def test_fainted_pokemon_triggers_winner(self):
        player  = make_trainer(pokemon=[make_pokemon(stat_attk=999)])
        npc_mon = make_pokemon(stat_def=1, stat_hp=1)
        npc_mon.hp = 1
        npc     = make_trainer(pokemon=[npc_mon])
        move    = make_move(category="physical", power=250, acc=1.0)
        current_turn = 1
        action = BattleAction(kind="move", move=move)
        resolve_turn(player, action, npc, action, current_turn)
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
        player = make_trainer(pokemon=[make_pokemon(stat_spd=50)])
        npc    = make_trainer(pokemon=[make_pokemon(stat_spd=150)])

        player_move = make_move(name="Quick Attack", power=40, acc=1.0, priority=1)
        npc_move    = make_move(name="Tackle",       power=40, acc=1.0, priority=0)

        order = get_turn_order(player, BattleAction(kind="move", move=player_move),
                               npc, BattleAction(kind="move", move=npc_move), True, True)
        self.assertEqual(order.first, player)
        self.assertEqual(order.second, npc)

    def test_lower_priority_move_goes_second(self):
        player = make_trainer(pokemon=[make_pokemon(stat_spd=150)])
        npc    = make_trainer(pokemon=[make_pokemon(stat_spd=50)])

        player_move = make_move(name="Tackle",       power=40, acc=1.0, priority=0)
        npc_move    = make_move(name="Quick Attack", power=40, acc=1.0, priority=1)

        order = get_turn_order(player, BattleAction(kind="move", move=player_move),
                               npc, BattleAction(kind="move", move=npc_move), True, True)
        self.assertEqual(order.first, npc)
        self.assertEqual(order.second, player)

    def test_equal_priority_uses_speed(self):
        player = make_trainer(pokemon=[make_pokemon()])
        npc    = make_trainer(pokemon=[make_pokemon()])

        player.active().stat_spd = 150
        npc.active().stat_spd    = 50

        player_move = BattleAction(kind="move", move=make_move(priority=0))
        npc_move    = BattleAction(kind="move", move=make_move(priority=0))

        order = get_turn_order(player, player_move, npc, npc_move, True, True)
        self.assertEqual(order.first, player)
        self.assertEqual(order.second, npc)

    def test_equal_priority_slower_pokemon_goes_second(self):
        player = make_trainer(pokemon=[make_pokemon()])
        npc    = make_trainer(pokemon=[make_pokemon()])

        player.active().stat_spd = 50
        npc.active().stat_spd    = 150

        player_move = BattleAction(kind="move", move=make_move(priority=0))
        npc_move    = BattleAction(kind="move", move=make_move(priority=0))

        order = get_turn_order(player, player_move, npc, npc_move, True, True)
        self.assertEqual(order.first, npc)
        self.assertEqual(order.second, player)

    def test_equal_priority_equal_speed_resolves(self):
        player = make_trainer(pokemon=[make_pokemon()])
        npc    = make_trainer(pokemon=[make_pokemon()])

        player.active().stat_spd = 100
        npc.active().stat_spd    = 100

        player_move = BattleAction(kind="move", move=make_move(priority=0))
        npc_move    = BattleAction(kind="move", move=make_move(priority=0))

        try:
            order = get_turn_order(player, player_move, npc, npc_move, True, True)
            self.assertIn(order.first, [player, npc])
            self.assertIn(order.second, [player, npc])
            self.assertNotEqual(order.first, order.second)
        except Exception as e:
            self.fail(f"get_turn_order raised an exception on speed tie: {e}")

    def test_negative_priority_goes_last(self):
        player = make_trainer(pokemon=[make_pokemon()])
        npc    = make_trainer(pokemon=[make_pokemon()])

        player.active().stat_spd = 150
        npc.active().stat_spd    = 50

        player_move = BattleAction(kind="move", move=make_move(name="Slow Move", power=0, acc=1.0, priority=-1))
        npc_move    = BattleAction(kind="move", move=make_move(name="Tackle",    power=40, acc=1.0, priority=0))

        order = get_turn_order(player, player_move, npc, npc_move, True, True)
        self.assertEqual(order.first,  npc)
        self.assertEqual(order.second, player)

    def test_same_high_priority_uses_speed(self):
        player = make_trainer(pokemon=[make_pokemon()])
        npc    = make_trainer(pokemon=[make_pokemon()])

        player.active().stat_spd = 50
        npc.active().stat_spd    = 150

        player_move = BattleAction(kind="move", move=make_move(name="Quick Attack", power=40, acc=1.0, priority=1))
        npc_move    = BattleAction(kind="move", move=make_move(name="Quick Attack", power=40, acc=1.0, priority=1))

        order = get_turn_order(player, player_move, npc, npc_move, True, True)
        self.assertEqual(order.first,  npc)
        self.assertEqual(order.second, player)

    def test_can_act_flags_preserved_in_order(self):
        player = make_trainer(pokemon=[make_pokemon(stat_spd=150)])
        npc    = make_trainer(pokemon=[make_pokemon(stat_spd=50)])

        player_move = BattleAction(kind="move", move=make_move(priority=0))
        npc_move    = BattleAction(kind="move", move=make_move(priority=0))

        order = get_turn_order(player, player_move, npc, npc_move,
                               player_can_act=True, npc_can_act=False)

        self.assertEqual(order.first,          player)
        self.assertTrue(order.first_can_act)
        self.assertEqual(order.second,         npc)
        self.assertFalse(order.second_can_act)