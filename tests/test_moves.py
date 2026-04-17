# tests/test_moves.py
import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from src.battle import apply_move, handle_multiturn
from helpers import make_pokemon, make_move, make_trainer

class TestMoves(unittest.TestCase):

    def test_move_pp_decrements_on_use(self):
        attacker = make_trainer(pokemon=[make_pokemon()])
        defender = make_trainer(pokemon=[make_pokemon()])
        move     = make_move(pp=10)
        pp_before = move.pp
        apply_move(move, attacker, defender)
        self.assertEqual(move.pp, pp_before - 1)

    def test_move_deals_damage_to_defender(self):
        attacker = make_trainer(pokemon=[make_pokemon(stat_attk=100)])
        defender = make_trainer(pokemon=[make_pokemon(stat_def=100)])
        move     = make_move(category="physical", power=50, acc=1.0)
        hp_before = defender.active().hp
        apply_move(move, attacker, defender)
        self.assertLess(defender.active().hp, hp_before)

    def test_recoil_damages_attacker(self):
        attacker = make_trainer(pokemon=[make_pokemon(stat_attk=100)])
        defender = make_trainer(pokemon=[make_pokemon(stat_def=100)])
        move     = make_move(category="physical", power=100, acc=1.0, recoil=0.33)
        hp_before = attacker.active().hp
        apply_move(move, attacker, defender)
        self.assertLess(attacker.active().hp, hp_before)

    def test_fly_sets_invulnerable_on_charge_turn(self):
        attacker = make_trainer(pokemon=[make_pokemon()])
        move     = make_move(multi_turn={
            "turns":                2,
            "charge_turn":          1,
            "invulnerable":         True,
            "invulnerable_state":   "flying",
            "charge_message":       "flew up high!",
            "invulnerable_message": "is high up in the air!"
        })
        handle_multiturn(move, attacker)
        self.assertEqual(attacker.invulnerable_state, "flying")

    def test_status_move_does_not_deal_damage(self):
        attacker  = make_trainer(pokemon=[make_pokemon()])
        defender  = make_trainer(pokemon=[make_pokemon()])
        move      = make_move(category="status", power=0, acc=1.0)
        hp_before = defender.active().hp
        apply_move(move, attacker, defender)
        self.assertEqual(defender.active().hp, hp_before)

    def test_heal_move_restores_hp(self):
        attacker          = make_trainer(pokemon=[make_pokemon(stat_hp=100)])
        defender          = make_trainer(pokemon=[make_pokemon()])
        attacker.active().hp = 10  # set hp very low so heal is obvious
        move = make_move(category="status", power=0, acc=1.0, heal=0.5)
        apply_move(move, attacker, defender)
        self.assertGreater(attacker.active().hp, 10)

    def test_regular_move_cannot_hit_invulnerable_pokemon(self):
        attacker = make_trainer(pokemon=[make_pokemon()])
        defender = make_trainer(pokemon=[make_pokemon()])

        # set defender to be invulnerable via fly
        defender.invulnerable_state = "flying"

        tackle   = make_move(name="Tackle", category="physical", power=40, acc=1.0)
        hp_before = defender.active().hp

        apply_move(tackle, attacker, defender)

        # hp should be unchanged since tackle cant hit a flying pokemon
        self.assertEqual(defender.active().hp, hp_before)

    def test_hits_invulnerable_move_can_hit_invulnerable_pokemon(self):
        attacker = make_trainer(pokemon=[make_pokemon(stat_sp_attk=100)])
        defender = make_trainer(pokemon=[make_pokemon(stat_sp_def=100)])

        # set defender to be invulnerable via fly
        defender.invulnerable_state = "flying"

        # lock the defender into fly so handle_invulnerability can read the state
        fly = make_move(
            name  = "Fly",
            multi_turn = {
                "turns":                2,
                "charge_turn":          1,
                "invulnerable":         True,
                "invulnerable_state":   "flying",
                "charge_message":       "flew up high!",
                "invulnerable_message": "is high up in the air!"
            }
        )
        defender.locked_move = fly

        gust = make_move(
            name              = "Gust",
            type              = ["Flying"],
            category          = "special",
            power             = 40,
            acc               = 1.0,
            hits_invulnerable = ["flying"]
        )
        hp_before = defender.active().hp

        apply_move(gust, attacker, defender)

        # hp should be reduced since gust can hit flying pokemon
        self.assertLess(defender.active().hp, hp_before)

    def test_hits_invulnerable_move_cannot_hit_different_invulnerable_state(self):
        attacker = make_trainer(pokemon=[make_pokemon(stat_sp_attk=100)])
        defender = make_trainer(pokemon=[make_pokemon(stat_sp_def=100)])

        # set defender to be invulnerable via fly
        defender.invulnerable_state = "flying"

        # lock the defender into fly
        fly = make_move(
            name       = "Fly",
            multi_turn = {
                "turns":                2,
                "charge_turn":          1,
                "invulnerable":         True,
                "invulnerable_state":   "flying",
                "charge_message":       "flew up high!",
                "invulnerable_message": "is high up in the air!"
            }
        )
        defender.locked_move = fly

        # surf can hit underwater pokemon but NOT flying pokemon
        surf = make_move(
            name              = "Surf",
            type              = ["Water"],
            category          = "special",
            power             = 90,
            acc               = 1.0,
            hits_invulnerable = ["underwater"]  # only hits underwater, not flying
        )
        hp_before = defender.active().hp

        apply_move(surf, attacker, defender)

        # hp should be unchanged since surf cannot hit a flying pokemon
        self.assertEqual(defender.active().hp, hp_before)