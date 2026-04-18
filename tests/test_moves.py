import sys
import os
import random
import unittest
import unittest.mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from src.battle import apply_move, handle_multiturn, check_accuracy, apply_stat_change, apply_damage, apply_lifesteal
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

    def test_never_miss_move_always_hits(self):
        attacker = make_trainer(pokemon=[make_pokemon()])
        defender = make_trainer(pokemon=[make_pokemon()])
        move     = make_move(acc=None)  # None = never misses
        # run 100 times to ensure it never misses
        for _ in range(100):
            result = check_accuracy(move, attacker, defender)
            self.assertTrue(result)

    def test_zero_accuracy_move_always_misses(self):
        attacker = make_trainer(pokemon=[make_pokemon()])
        defender = make_trainer(pokemon=[make_pokemon()])
        move     = make_move(acc=0.0)
        for _ in range(100):
            result = check_accuracy(move, attacker, defender)
            self.assertFalse(result)

    def test_lifesteal_restores_attacker_hp(self):
        attacker          = make_trainer(pokemon=[make_pokemon(stat_attk=100, stat_hp=100)])
        defender          = make_trainer(pokemon=[make_pokemon(stat_def=50)])
        attacker.active().hp = 50  # set hp low
        move = make_move(category="physical", power=80, acc=1.0, lifesteal=0.5)
        apply_move(move, attacker, defender)
        self.assertGreater(attacker.active().hp, 50)

    def test_pp_decrements_even_on_miss(self):
        attacker  = make_trainer(pokemon=[make_pokemon()])
        defender  = make_trainer(pokemon=[make_pokemon()])
        move      = make_move(acc=0.0, pp=10)  # always misses
        pp_before = move.pp
        apply_move(move, attacker, defender)
        self.assertEqual(move.pp, pp_before - 1)  # pp still decrements on miss

    def test_multi_turn_sets_locked_move(self):
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
        self.assertEqual(attacker.locked_move, move)
        self.assertEqual(attacker.locked_turns, 1)

    def test_stat_change_chance_prevents_change(self):
        attacker = make_trainer(pokemon=[make_pokemon()])
        defender = make_trainer(pokemon=[make_pokemon()])
        move     = make_move(
            category          = "status",
            stat_change       = {"opponent": {"stat_def": -1}},
            stat_change_chance = 0.0  # never triggers
        )
        stage_before = defender.active().stage_def
        apply_stat_change(move, attacker, defender, [])
        self.assertEqual(defender.active().stage_def, stage_before)

    def test_stat_change_guaranteed_applies(self):
        attacker = make_trainer(pokemon=[make_pokemon()])
        defender = make_trainer(pokemon=[make_pokemon()])
        move     = make_move(
            category          = "status",
            stat_change       = {"opponent": {"stat_def": -1}},
            stat_change_chance = 1.0  # always triggers
        )
        stage_before = defender.active().stage_def
        apply_stat_change(move, attacker, defender, [])
        self.assertEqual(defender.active().stage_def, stage_before - 1)

class TestMultiHitMoves(unittest.TestCase):

    def test_multi_hit_move_hits_multiple_times(self):
        attacker = make_trainer(pokemon=[make_pokemon(stat_attk=100)])
        defender = make_trainer(pokemon=[make_pokemon(stat_def=50)])
        move     = make_move(
            category = "physical",
            power    = 18,
            acc      = 1.0,
            min_hits = 2,
            max_hits = 5
        )
        hp_before = defender.active().hp

        # force exactly 3 hits
        with unittest.mock.patch("battle.random.randint", return_value=3):
            damage = 0
            roll   = 3
            for i in range(roll):
                damage += apply_damage(move, attacker, defender)

        self.assertLess(defender.active().hp, hp_before)

    def test_multi_hit_deals_more_damage_than_single(self):
        attacker      = make_trainer(pokemon=[make_pokemon()])
        defender_multi  = make_trainer(pokemon=[make_pokemon()])
        defender_single = make_trainer(pokemon=[make_pokemon()])

        attacker.active().stat_attk        = 100
        defender_multi.active().stat_def   = 100
        defender_single.active().stat_def  = 100

        multi_move  = make_move(category="physical", power=18, acc=1.0, min_hits=2, max_hits=2)
        single_move = make_move(category="physical", power=18, acc=1.0)

        # force 2 hits
        with unittest.mock.patch("battle.random.randint", return_value=2):
            multi_damage = 0
            for _ in range(2):
                multi_damage += apply_damage(multi_move, attacker, defender_multi)

        single_damage = apply_damage(single_move, attacker, defender_single)

        self.assertGreater(multi_damage, single_damage)

    def test_multi_hit_stops_if_defender_faints(self):
        attacker = make_trainer(pokemon=[make_pokemon()])
        defender = make_trainer(pokemon=[make_pokemon()])

        attacker.active().stat_attk = 999  # very high attack
        defender.active().stat_def  = 1    # very low defense
        defender.active().hp        = 1    # almost fainted

        move = make_move(
            category = "physical",
            power    = 100,
            acc      = 1.0,
            min_hits = 2,
            max_hits = 5
        )

        hits_landed = 0
        with unittest.mock.patch("battle.random.randint", return_value=5):
            for i in range(5):
                apply_damage(move, attacker, defender)
                hits_landed += 1
                if not defender.active().is_alive():
                    break

        # should have stopped after first hit since defender fainted
        self.assertEqual(hits_landed, 1)
        self.assertGreaterEqual(defender.active().hp, 0)

    def test_multi_hit_minimum_hits(self):
        attacker = make_trainer(pokemon=[make_pokemon(stat_attk=100)])
        defender = make_trainer(pokemon=[make_pokemon(stat_def=100)])
        move     = make_move(
            category = "physical",
            power    = 18,
            acc      = 1.0,
            min_hits = 2,
            max_hits = 5
        )

        with unittest.mock.patch("battle.random.randint", return_value=move.min_hits):
            self.assertEqual(
                random.randint(move.min_hits, move.max_hits),
                move.min_hits
            )

    def test_multi_hit_maximum_hits(self):
        attacker = make_trainer(pokemon=[make_pokemon(stat_attk=100)])
        defender = make_trainer(pokemon=[make_pokemon(stat_def=100)])
        move     = make_move(
            category = "physical",
            power    = 18,
            acc      = 1.0,
            min_hits = 2,
            max_hits = 5
        )

        with unittest.mock.patch("battle.random.randint", return_value=move.max_hits):
            self.assertEqual(
                random.randint(move.min_hits, move.max_hits),
                move.max_hits
            )

    def test_single_hit_move_hits_once(self):
        attacker  = make_trainer(pokemon=[make_pokemon(stat_attk=100)])
        defender  = make_trainer(pokemon=[make_pokemon(stat_def=100)])
        move      = make_move(category="physical", power=50, acc=1.0)
        hp_before = defender.active().hp

        apply_damage(move, attacker, defender)
        damage = hp_before - defender.active().hp

        # apply again and verify damage is consistent
        defender.active().hp = hp_before
        apply_damage(move, attacker, defender)
        damage2 = hp_before - defender.active().hp

        self.assertEqual(damage, damage2)

    def test_multi_hit_none_min_max_is_single_hit(self):
        move = make_move(
            category = "physical",
            power    = 50,
            acc      = 1.0,
            min_hits = None,
            max_hits = None
        )
        # verify it is treated as a single hit move
        self.assertIsNone(move.min_hits)
        self.assertIsNone(move.max_hits)

    def test_multi_hit_damage_accumulates(self):
        attacker = make_trainer(pokemon=[make_pokemon()])
        defender = make_trainer(pokemon=[make_pokemon()])

        attacker.active().stat_attk = 100
        defender.active().stat_def  = 100

        move      = make_move(category="physical", power=18, acc=1.0)
        hp_before = defender.active().hp

        # manually simulate 3 hits and track total damage
        total_damage = 0
        with unittest.mock.patch("battle.random.randint", return_value=3):
            for _ in range(3):
                hit_damage    = apply_damage(move, attacker, defender)
                total_damage += hit_damage

        self.assertEqual(hp_before - defender.active().hp, total_damage)

    def test_multi_hit_lifesteal_uses_total_damage(self):
        attacker = make_trainer(pokemon=[make_pokemon()])
        defender = make_trainer(pokemon=[make_pokemon()])

        attacker.active().stat_attk = 100
        attacker.active().hp        = 50
        defender.active().stat_def  = 100

        move = make_move(
            category  = "physical",
            power     = 18,
            acc       = 1.0,
            min_hits  = 2,
            max_hits  = 2,
            lifesteal = 0.5
        )

        hp_before    = attacker.active().hp
        total_damage = 0

        with unittest.mock.patch("battle.random.randint", return_value=2):
            for _ in range(2):
                total_damage += apply_damage(move, attacker, defender)

        apply_lifesteal(move, attacker, total_damage)
        self.assertGreater(attacker.active().hp, hp_before)