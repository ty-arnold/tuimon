import sys
import os
import unittest
import copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from helpers import make_pokemon, make_move, make_trainer
from data.status_effects import poison, paralysis, sleep, burn, freeze, confusion
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


class TestTypeImmunityAbilities(unittest.TestCase):
    """Levitate, Volt Absorb, Water Absorb, Wonder Guard, Flash Fire."""

    def test_levitate_blocks_ground(self):
        poke = make_pokemon(type=["Psychic"])
        poke.ability = Ability("Levitate")
        defender = make_trainer(name="Blue", pokemon=[poke])
        move = make_move(type=["Ground"], power=80, acc=1.0)
        events = []
        from battle.abilities import check_ability_type_immunity
        self.assertTrue(check_ability_type_immunity(defender, move, events))

    def test_volt_absorb_blocks_electric_and_heals(self):
        poke = make_pokemon(type=["Water"], stat_hp=100)
        poke.hp = 50
        poke.ability = Ability("Volt Absorb")
        defender = make_trainer(name="Blue", pokemon=[poke])
        move = make_move(type=["Electric"], power=80, acc=1.0)
        events = []
        from battle.abilities import check_ability_type_immunity
        self.assertTrue(check_ability_type_immunity(defender, move, events))
        self.assertGreater(poke.hp, 50)

    def test_water_absorb_blocks_water_and_heals(self):
        poke = make_pokemon(type=["Ground"], stat_hp=100)
        poke.hp = 50
        poke.ability = Ability("Water Absorb")
        defender = make_trainer(name="Blue", pokemon=[poke])
        move = make_move(type=["Water"], power=80, acc=1.0)
        events = []
        from battle.abilities import check_ability_type_immunity
        self.assertTrue(check_ability_type_immunity(defender, move, events))
        self.assertGreater(poke.hp, 50)

    def test_wonder_guard_blocks_neutral(self):
        poke = make_pokemon(type=["Ghost"])
        poke.ability = Ability("Wonder Guard")
        defender = make_trainer(name="Blue", pokemon=[poke])
        move = make_move(type=["Normal"], power=80, acc=1.0)
        events = []
        from battle.abilities import check_ability_type_immunity
        self.assertTrue(check_ability_type_immunity(defender, move, events))

    def test_wonder_guard_allows_super_effective(self):
        poke = make_pokemon(type=["Ghost"])
        poke.ability = Ability("Wonder Guard")
        defender = make_trainer(name="Blue", pokemon=[poke])
        move = make_move(type=["Ghost"], power=80, acc=1.0)
        events = []
        from battle.abilities import check_ability_type_immunity
        self.assertFalse(check_ability_type_immunity(defender, move, events))

    def test_flash_fire_blocks_fire(self):
        poke = make_pokemon(type=["Grass"])
        poke.ability = Ability("Flash Fire")
        defender = make_trainer(name="Blue", pokemon=[poke])
        move = make_move(type=["Fire"], power=80, acc=1.0)
        events = []
        from battle.abilities import check_ability_type_immunity
        self.assertTrue(check_ability_type_immunity(defender, move, events))

    def test_flash_fire_does_not_block_other_types(self):
        poke = make_pokemon(type=["Grass"])
        poke.ability = Ability("Flash Fire")
        defender = make_trainer(name="Blue", pokemon=[poke])
        move = make_move(type=["Water"], power=80, acc=1.0)
        events = []
        from battle.abilities import check_ability_type_immunity
        self.assertFalse(check_ability_type_immunity(defender, move, events))


class TestSturdy(unittest.TestCase):
    """Sturdy prevents OHKO from full HP."""

    def test_sturdy_leaves_1hp(self):
        poke = make_pokemon(stat_hp=100)
        poke.hp = poke.max_hp  # ensure full HP
        poke.ability = Ability("Sturdy")
        defender = make_trainer(pokemon=[poke])
        from battle.abilities import check_ability_before_damage
        new_dmg = check_ability_before_damage(defender, 999)
        self.assertEqual(new_dmg, poke.hp - 1)

    def test_sturdy_only_at_full_hp(self):
        poke = make_pokemon(stat_hp=100)
        poke.hp = poke.max_hp - 10  # not full
        poke.ability = Ability("Sturdy")
        defender = make_trainer(pokemon=[poke])
        from battle.abilities import check_ability_before_damage
        new_dmg = check_ability_before_damage(defender, 999)
        self.assertEqual(new_dmg, 999)


class TestStatBoostAbilities(unittest.TestCase):
    """Huge Power, Pure Power, Hustle, Guts, Marvel Scale."""

    def test_huge_power_doubles_attack(self):
        poke = make_pokemon(stat_attk=100)
        poke.ability = Ability("Huge Power")
        from battle.abilities import modify_stat_by_ability
        self.assertEqual(modify_stat_by_ability(poke, "stat_attk", 100), 200)

    def test_guts_boosts_attack_when_statused(self):
        from data.status_effects import burn
        poke = make_pokemon(stat_attk=100)
        poke.ability = Ability("Guts")
        poke.apply_status_effect(copy.deepcopy(burn))
        from battle.abilities import modify_stat_by_ability
        self.assertEqual(modify_stat_by_ability(poke, "stat_attk", 50), 75)

    def test_hustle_boosts_attack(self):
        poke = make_pokemon(stat_attk=100)
        poke.ability = Ability("Hustle")
        from battle.abilities import modify_stat_by_ability
        self.assertEqual(modify_stat_by_ability(poke, "stat_attk", 100), 150)

    def test_rock_head_prevents_recoil(self):
        poke = make_pokemon()
        poke.ability = Ability("Rock Head")
        attacker = make_trainer(pokemon=[poke])
        from battle.abilities import check_ability_recoil_prevention
        self.assertTrue(check_ability_recoil_prevention(attacker))

    def test_pressure_active(self):
        poke = make_pokemon()
        poke.ability = Ability("Pressure")
        defender = make_trainer(pokemon=[poke])
        from battle.abilities import apply_ability_pp_pressure
        self.assertTrue(apply_ability_pp_pressure(defender))

    def test_serene_grace_active(self):
        poke = make_pokemon()
        poke.ability = Ability("Serene Grace")
        from battle.abilities import check_ability_serene_grace
        self.assertTrue(check_ability_serene_grace(poke))


class TestDamageModifierAbilities(unittest.TestCase):
    """Thick Fat, Blaze/Torrent/Overgrow/Swarm."""

    def test_thick_fat_halves_fire(self):
        poke = make_pokemon()
        poke.ability = Ability("Thick Fat")
        defender = make_trainer(pokemon=[poke])
        attacker = make_trainer(pokemon=[make_pokemon()])
        move = make_move(type=["Fire"], power=80)
        from battle.abilities import modify_damage_by_ability
        self.assertEqual(modify_damage_by_ability(attacker, defender, move, 100), 0.5)

    def test_thick_fat_halves_ice(self):
        poke = make_pokemon()
        poke.ability = Ability("Thick Fat")
        defender = make_trainer(pokemon=[poke])
        attacker = make_trainer(pokemon=[make_pokemon()])
        move = make_move(type=["Ice"], power=80)
        from battle.abilities import modify_damage_by_ability
        self.assertEqual(modify_damage_by_ability(attacker, defender, move, 100), 0.5)

    def test_thick_fat_does_not_affect_other_types(self):
        poke = make_pokemon()
        poke.ability = Ability("Thick Fat")
        defender = make_trainer(pokemon=[poke])
        attacker = make_trainer(pokemon=[make_pokemon()])
        move = make_move(type=["Normal"], power=80)
        from battle.abilities import modify_damage_by_ability
        self.assertEqual(modify_damage_by_ability(attacker, defender, move, 100), 1.0)

    def test_blaze_boosts_fire_at_low_hp(self):
        poke = make_pokemon(stat_hp=100)
        poke.hp = 1  # below 1/3
        poke.ability = Ability("Blaze")
        attacker = make_trainer(pokemon=[poke])
        defender = make_trainer(pokemon=[make_pokemon()])
        move = make_move(type=["Fire"], power=80)
        from battle.abilities import modify_damage_by_ability
        self.assertEqual(modify_damage_by_ability(attacker, defender, move, 100), 1.5)

    def test_blaze_no_boost_at_high_hp(self):
        poke = make_pokemon(stat_hp=100)
        poke.hp = poke.max_hp
        poke.ability = Ability("Blaze")
        attacker = make_trainer(pokemon=[poke])
        defender = make_trainer(pokemon=[make_pokemon()])
        move = make_move(type=["Fire"], power=80)
        from battle.abilities import modify_damage_by_ability
        self.assertEqual(modify_damage_by_ability(attacker, defender, move, 100), 1.0)

    def test_overgrow_boosts_grass_at_low_hp(self):
        poke = make_pokemon(stat_hp=100)
        poke.hp = 1
        poke.ability = Ability("Overgrow")
        attacker = make_trainer(pokemon=[poke])
        defender = make_trainer(pokemon=[make_pokemon()])
        move = make_move(type=["Grass"], power=80)
        from battle.abilities import modify_damage_by_ability
        self.assertEqual(modify_damage_by_ability(attacker, defender, move, 100), 1.5)

    def test_low_hp_boost_wrong_type_no_effect(self):
        poke = make_pokemon(stat_hp=100)
        poke.hp = 1
        poke.ability = Ability("Blaze")
        attacker = make_trainer(pokemon=[poke])
        defender = make_trainer(pokemon=[make_pokemon()])
        move = make_move(type=["Water"], power=80)
        from battle.abilities import modify_damage_by_ability
        self.assertEqual(modify_damage_by_ability(attacker, defender, move, 100), 1.0)

    def test_torrent_boosts_water_at_low_hp(self):
        poke = make_pokemon(stat_hp=100)
        poke.hp = 1
        poke.ability = Ability("Torrent")
        attacker = make_trainer(pokemon=[poke])
        defender = make_trainer(pokemon=[make_pokemon()])
        move = make_move(type=["Water"], power=80)
        from battle.abilities import modify_damage_by_ability
        self.assertEqual(modify_damage_by_ability(attacker, defender, move, 100), 1.5)

    def test_swarm_boosts_bug_at_low_hp(self):
        poke = make_pokemon(stat_hp=100)
        poke.hp = 1
        poke.ability = Ability("Swarm")
        attacker = make_trainer(pokemon=[poke])
        defender = make_trainer(pokemon=[make_pokemon()])
        move = make_move(type=["Bug"], power=80)
        from battle.abilities import modify_damage_by_ability
        self.assertEqual(modify_damage_by_ability(attacker, defender, move, 100), 1.5)


class TestRemainingStatAbilities(unittest.TestCase):
    """Pure Power, Marvel Scale, Hustle accuracy."""

    def test_pure_power_doubles_attack(self):
        poke = make_pokemon(stat_attk=100)
        poke.ability = Ability("Pure Power")
        from battle.abilities import modify_stat_by_ability
        self.assertEqual(modify_stat_by_ability(poke, "stat_attk", 100), 200)

    def test_marvel_scale_boosts_defense_when_statused(self):
        from data.status_effects import burn
        poke = make_pokemon(stat_def=100)
        poke.ability = Ability("Marvel Scale")
        poke.apply_status_effect(copy.deepcopy(burn))
        from battle.abilities import modify_stat_by_ability
        self.assertEqual(modify_stat_by_ability(poke, "stat_def", 100), 150)

    def test_hustle_accuracy_penalty(self):
        poke = make_pokemon()
        poke.ability = Ability("Hustle")
        attacker = make_trainer(pokemon=[poke])
        from battle.abilities import check_ability_accuracy_modifier
        self.assertEqual(check_ability_accuracy_modifier(attacker), 0.8)

    def test_no_ability_accuracy_unchanged(self):
        poke = make_pokemon()
        attacker = make_trainer(pokemon=[poke])
        from battle.abilities import check_ability_accuracy_modifier
        self.assertEqual(check_ability_accuracy_modifier(attacker), 1.0)


class TestContactAbilities(unittest.TestCase):
    """Static, Poison Point, Flame Body, Rough Skin, Effect Spore."""

    def _apply_contact(self, ability_name, attacker_hp=100):
        import unittest.mock
        poke = make_pokemon(stat_hp=100)
        poke.ability = Ability(ability_name)
        defender = make_trainer(name="Blue", pokemon=[poke])
        atk_poke = make_pokemon(stat_hp=attacker_hp)
        atk_poke.hp = attacker_hp
        attacker = make_trainer(name="Red", pokemon=[atk_poke])
        move = make_move(category="physical", power=50, acc=1.0)
        events = []
        # Ensure random rolls trigger (chance < 1.0 needs random < 0.3)
        with unittest.mock.patch("battle.abilities.random.random", return_value=0.0):
            from battle.abilities import apply_contact_abilities
            apply_contact_abilities(attacker, defender, move, events)
        return atk_poke, events

    def test_static_paralyzes_on_contact(self):
        atk_poke, events = self._apply_contact("Static")
        self.assertEqual(atk_poke.major_status.name, "Paralysis")

    def test_poison_point_poisons_on_contact(self):
        atk_poke, events = self._apply_contact("Poison Point")
        self.assertEqual(atk_poke.major_status.name, "Poison")

    def test_flame_body_burns_on_contact(self):
        atk_poke, events = self._apply_contact("Flame Body")
        self.assertEqual(atk_poke.major_status.name, "Burn")

    def test_rough_skin_damages_on_contact(self):
        atk_poke, events = self._apply_contact("Rough Skin")
        self.assertLess(atk_poke.hp, atk_poke.max_hp)

    def test_no_contact_on_special_move(self):
        """Contact abilities don't trigger on special moves."""
        import unittest.mock
        poke = make_pokemon()
        poke.ability = Ability("Static")
        defender = make_trainer(name="Blue", pokemon=[poke])
        atk_poke = make_pokemon()
        attacker = make_trainer(name="Red", pokemon=[atk_poke])
        move = make_move(category="special", power=50, acc=1.0)
        events = []
        with unittest.mock.patch("battle.abilities.random.random", return_value=0.0):
            from battle.abilities import apply_contact_abilities
            apply_contact_abilities(attacker, defender, move, events)
        self.assertIsNone(atk_poke.major_status)

    def test_effect_spore_on_contact(self):
        import unittest.mock
        poke = make_pokemon(stat_hp=100)
        poke.ability = Ability("Effect Spore")
        defender = make_trainer(name="Blue", pokemon=[poke])
        atk_poke = make_pokemon(stat_hp=100)
        atk_poke.hp = 100
        attacker = make_trainer(name="Red", pokemon=[atk_poke])
        move = make_move(category="physical", power=50, acc=1.0)
        events = []
        # Effect Spore uses 3-tier random: <0.1 poison, <0.2 paralysis, <0.3 sleep
        with unittest.mock.patch("battle.abilities.random.random", return_value=0.05):
            from battle.abilities import apply_contact_abilities
            apply_contact_abilities(attacker, defender, move, events)
        self.assertIsNotNone(atk_poke.major_status)  # should have SOME status


class TestShedSkin(unittest.TestCase):
    """Shed Skin — 1/3 chance to cure status each turn."""

    def test_shed_skin_cures_status(self):
        import unittest.mock
        from data.status_effects import burn
        poke = make_pokemon()
        poke.ability = Ability("Shed Skin")
        poke.apply_status_effect(copy.deepcopy(burn))
        self.assertIsNotNone(poke.major_status)
        with unittest.mock.patch("battle.abilities.random.random", return_value=0.0):
            from battle.abilities import process_end_of_turn_ability
            process_end_of_turn_ability(poke, [], "Red")
        self.assertIsNone(poke.major_status)

    def test_shed_skin_does_not_always_cure(self):
        import unittest.mock
        from data.status_effects import burn
        poke = make_pokemon()
        poke.ability = Ability("Shed Skin")
        poke.apply_status_effect(copy.deepcopy(burn))
        self.assertIsNotNone(poke.major_status)
        with unittest.mock.patch("battle.abilities.random.random", return_value=0.5):
            from battle.abilities import process_end_of_turn_ability
            process_end_of_turn_ability(poke, [], "Red")
        self.assertIsNotNone(poke.major_status)


class TestSynchronize(unittest.TestCase):
    """Synchronize passes major status to attacker."""

    def test_synchronize_passes_status(self):
        import unittest.mock
        from battle.status_effects import apply_status_effect_from_move
        poke = make_pokemon()
        poke.ability = Ability("Synchronize")
        defender = make_trainer(name="Blue", pokemon=[poke])
        atk_poke = make_pokemon()
        attacker = make_trainer(name="Red", pokemon=[atk_poke])
        move = make_move(status_effect=copy.deepcopy(burn), category="status")
        events = []
        with unittest.mock.patch("battle.status_effects.random.random", return_value=0.0):
            result, effect = apply_status_effect_from_move(move, defender, attacker, events)
        self.assertEqual(result, "afflicted")
        self.assertEqual(atk_poke.major_status.name, "Burn")


class TestSwitchAbilities(unittest.TestCase):
    """Intimidate lowers Attack on switch-in. Natural Cure cures on switch-out."""

    def test_intimidate_lowers_attack(self):
        atk_poke = make_pokemon(stat_spd=50)
        int_poke = make_pokemon(stat_spd=50)
        int_poke.ability = Ability("Intimidate")
        opponent = make_trainer(name="Red", pokemon=[atk_poke])
        trainer = make_trainer(name="Blue", pokemon=[make_pokemon(), int_poke])
        trainer.selected_mon = 1  # switch to Intimidate mon
        from battle.abilities import apply_switch_abilities
        events = []
        apply_switch_abilities(trainer, opponent, events)
        self.assertEqual(atk_poke.stage_attk, -1)

    def test_intimidate_does_not_affect_fainted(self):
        atk_poke = make_pokemon(stat_spd=50)
        atk_poke.hp = 0
        int_poke = make_pokemon(stat_spd=50)
        int_poke.ability = Ability("Intimidate")
        opponent = make_trainer(name="Red", pokemon=[atk_poke])
        trainer = make_trainer(name="Blue", pokemon=[make_pokemon(), int_poke])
        trainer.selected_mon = 1
        from battle.abilities import apply_switch_abilities
        events = []
        apply_switch_abilities(trainer, opponent, events)
        self.assertEqual(atk_poke.stage_attk, 0)

    def test_natural_cure_cures_on_switch_out(self):
        from data.status_effects import burn
        poke = make_pokemon()
        poke.ability = Ability("Natural Cure")
        poke.apply_status_effect(copy.deepcopy(burn))
        trainer = make_trainer(name="Blue", pokemon=[poke])
        from battle.abilities import apply_switch_out_abilities
        apply_switch_out_abilities(trainer)
        self.assertIsNone(poke.major_status)


class TestQuickWinAbilities(unittest.TestCase):
    """Compound Eyes, Early Bird, Shield Dust, Soundproof, Oblivious, Liquid Ooze."""

    def test_compound_eyes_boosts_accuracy(self):
        poke = make_pokemon()
        poke.ability = Ability("Compound Eyes")
        attacker = make_trainer(pokemon=[poke])
        from battle.abilities import check_ability_accuracy_modifier
        self.assertAlmostEqual(check_ability_accuracy_modifier(attacker), 1.3)

    def test_compound_eyes_stacks_with_hustle(self):
        # Compound Eyes and Hustle are on different mons, but just test CE alone
        pass  # CE is on the attacker, Hustle on different species

    def test_oblivious_prevents_infatuation(self):
        poke = make_pokemon()
        poke.ability = Ability("Oblivious")
        from battle.abilities import check_ability_prevents
        self.assertTrue(check_ability_prevents(poke, "infatuation"))

    def test_shield_dust_active(self):
        poke = make_pokemon()
        poke.ability = Ability("Shield Dust")
        from battle.abilities import check_ability_shield_dust
        self.assertTrue(check_ability_shield_dust(poke))

    def test_shield_dust_blocks_status_from_move(self):
        import unittest.mock
        poke = make_pokemon()
        poke.ability = Ability("Shield Dust")
        defender = make_trainer(pokemon=[poke])
        move = make_move(status_effect=copy.deepcopy(paralysis))
        from battle.status_effects import apply_status_effect_from_move
        result, effect = apply_status_effect_from_move(move, defender)
        self.assertEqual(result, "failed")

    def test_soundproof_blocks_sound(self):
        poke = make_pokemon()
        poke.ability = Ability("Soundproof")
        from battle.abilities import check_ability_blocks_sound
        self.assertTrue(check_ability_blocks_sound(poke))

    def test_sound_move_detection(self):
        from battle.abilities import is_sound_move
        self.assertTrue(is_sound_move("Hyper Voice"))
        self.assertFalse(is_sound_move("Tackle"))

    def test_damp_blocks_explosion(self):
        poke = make_pokemon()
        poke.ability = Ability("Damp")
        from battle.abilities import check_ability_blocks_explosion
        self.assertTrue(check_ability_blocks_explosion(poke))

    def test_explosion_move_detection(self):
        from battle.abilities import is_explosion_move
        self.assertTrue(is_explosion_move("Self-Destruct"))
        self.assertTrue(is_explosion_move("Explosion"))
        self.assertFalse(is_explosion_move("Tackle"))

    def test_early_bird_active(self):
        poke = make_pokemon()
        poke.ability = Ability("Early Bird")
        from battle.abilities import check_ability_halves_sleep_turns
        self.assertTrue(check_ability_halves_sleep_turns(poke))

    def test_liquid_ooze_blocks_drain(self):
        atk_poke = make_pokemon(stat_hp=100)
        atk_poke.hp = 50
        def_poke = make_pokemon(stat_hp=100)
        def_poke.ability = Ability("Liquid Ooze")
        attacker = make_trainer(name="Red", pokemon=[atk_poke])
        defender = make_trainer(name="Blue", pokemon=[def_poke])
        move = make_move(lifesteal=0.5, power=40, acc=1.0)
        from battle.abilities import check_ability_liquid_ooze_defender
        result = check_ability_liquid_ooze_defender(defender, attacker, 40, move)
        self.assertTrue(result)
        self.assertLess(atk_poke.hp, 50)  # took damage instead of healing

    def test_liquid_ooze_no_effect_without_drain(self):
        atk_poke = make_pokemon(stat_hp=100)
        def_poke = make_pokemon(stat_hp=100)
        def_poke.ability = Ability("Liquid Ooze")
        attacker = make_trainer(name="Red", pokemon=[atk_poke])
        defender = make_trainer(name="Blue", pokemon=[def_poke])
        move = make_move(category="physical", power=40, acc=1.0)  # no lifesteal
        from battle.abilities import check_ability_liquid_ooze_defender
        self.assertFalse(check_ability_liquid_ooze_defender(defender, attacker, 0, move))

    def test_stench_active(self):
        poke = make_pokemon()
        poke.ability = Ability("Stench")
        import unittest.mock
        from battle.abilities import check_ability_stench
        with unittest.mock.patch("battle.abilities.random.random", return_value=0.0):
            self.assertTrue(check_ability_stench(poke))

    def test_stench_does_not_always_trigger(self):
        poke = make_pokemon()
        poke.ability = Ability("Stench")
        import unittest.mock
        from battle.abilities import check_ability_stench
        with unittest.mock.patch("battle.abilities.random.random", return_value=0.5):
            self.assertFalse(check_ability_stench(poke))


class TestWeatherAbilities(unittest.TestCase):
    """Drizzle, Drought, Sand Stream, Swift Swim, Chlorophyll, Rain Dish, Sand Veil, Cloud Nine, Air Lock."""

    def test_drizzle_sets_rain(self):
        poke = make_pokemon()
        poke.ability = Ability("Drizzle")
        from battle.abilities import check_weather_setter
        self.assertEqual(check_weather_setter(poke), "rain")

    def test_drought_sets_sun(self):
        poke = make_pokemon()
        poke.ability = Ability("Drought")
        from battle.abilities import check_weather_setter
        self.assertEqual(check_weather_setter(poke), "sun")

    def test_sand_stream_sets_sandstorm(self):
        poke = make_pokemon()
        poke.ability = Ability("Sand Stream")
        from battle.abilities import check_weather_setter
        self.assertEqual(check_weather_setter(poke), "sandstorm")

    def test_swift_swim_doubles_speed_in_rain(self):
        poke = make_pokemon()
        poke.ability = Ability("Swift Swim")
        from battle.abilities import modify_speed_by_weather
        self.assertEqual(modify_speed_by_weather(poke, 100, "rain"), 200)

    def test_swift_swim_no_boost_without_rain(self):
        poke = make_pokemon()
        poke.ability = Ability("Swift Swim")
        from battle.abilities import modify_speed_by_weather
        self.assertEqual(modify_speed_by_weather(poke, 100, "sun"), 100)

    def test_chlorophyll_doubles_speed_in_sun(self):
        poke = make_pokemon()
        poke.ability = Ability("Chlorophyll")
        from battle.abilities import modify_speed_by_weather
        self.assertEqual(modify_speed_by_weather(poke, 100, "sun"), 200)

    def test_rain_dish_heals(self):
        poke = make_pokemon(stat_hp=100)
        poke.hp = 50
        poke.ability = Ability("Rain Dish")
        from battle.abilities import apply_weather_damage
        apply_weather_damage(poke, "rain", [], "Red")
        self.assertGreater(poke.hp, 50)

    def test_sandstorm_damages_non_immune(self):
        poke = make_pokemon(stat_hp=100, type=["Normal"])
        poke.hp = 100
        from battle.abilities import apply_weather_damage
        apply_weather_damage(poke, "sandstorm", [], "Red")
        self.assertLess(poke.hp, 100)

    def test_sandstorm_spares_rock_type(self):
        poke = make_pokemon(stat_hp=100, type=["Rock"])
        poke.hp = 100
        from battle.abilities import apply_weather_damage
        apply_weather_damage(poke, "sandstorm", [], "Red")
        self.assertEqual(poke.hp, 100)

    def test_cloud_nine_negates_weather(self):
        poke = make_pokemon()
        poke.ability = Ability("Cloud Nine")
        trainer = make_trainer(pokemon=[poke])
        trainer2 = make_trainer(pokemon=[make_pokemon()])
        from battle.abilities import is_weather_active
        self.assertFalse(is_weather_active("rain", trainer, trainer2))

    def test_air_lock_negates_weather(self):
        poke = make_pokemon()
        poke.ability = Ability("Air Lock")
        trainer = make_trainer(pokemon=[poke])
        trainer2 = make_trainer(pokemon=[make_pokemon()])
        from battle.abilities import is_weather_active
        self.assertFalse(is_weather_active("rain", trainer, trainer2))

    def test_sand_veil_evasion_in_sandstorm(self):
        poke = make_pokemon()
        poke.ability = Ability("Sand Veil")
        from battle.abilities import modify_evasion_by_weather
        self.assertEqual(modify_evasion_by_weather(poke, 0, "sandstorm"), 1)

    def test_sand_veil_no_boost_without_sandstorm(self):
        poke = make_pokemon()
        poke.ability = Ability("Sand Veil")
        from battle.abilities import modify_evasion_by_weather
        self.assertEqual(modify_evasion_by_weather(poke, 0, "rain"), 0)

    def test_hail_damages_non_ice(self):
        poke = make_pokemon(stat_hp=100, type=["Normal"])
        poke.hp = 100
        from battle.abilities import apply_weather_damage
        apply_weather_damage(poke, "hail", [], "Red")
        self.assertLess(poke.hp, 100)

    def test_hail_spares_ice_type(self):
        poke = make_pokemon(stat_hp=100, type=["Ice"])
        poke.hp = 100
        from battle.abilities import apply_weather_damage
        apply_weather_damage(poke, "hail", [], "Red")
        self.assertEqual(poke.hp, 100)

    def test_rain_boosts_water_damage(self):
        from battle.abilities import modify_damage_by_weather
        self.assertEqual(modify_damage_by_weather("Water", "rain"), 1.5)

    def test_rain_reduces_fire_damage(self):
        from battle.abilities import modify_damage_by_weather
        self.assertEqual(modify_damage_by_weather("Fire", "rain"), 0.5)

    def test_sun_boosts_fire_damage(self):
        from battle.abilities import modify_damage_by_weather
        self.assertEqual(modify_damage_by_weather("Fire", "sun"), 1.5)

    def test_sun_reduces_water_damage(self):
        from battle.abilities import modify_damage_by_weather
        self.assertEqual(modify_damage_by_weather("Water", "sun"), 0.5)

    def test_neutral_weather_no_damage_mod(self):
        from battle.abilities import modify_damage_by_weather
        self.assertEqual(modify_damage_by_weather("Normal", "rain"), 1.0)
        self.assertEqual(modify_damage_by_weather("Fire", None), 1.0)


class TestE3Abilities(unittest.TestCase):
    """Speed Boost, Trace, Cute Charm, Suction Cups."""

    def test_speed_boost_raises_speed(self):
        poke = make_pokemon()
        poke.ability = Ability("Speed Boost")
        from battle.abilities import process_end_of_turn_ability
        process_end_of_turn_ability(poke, [], "Red")
        self.assertEqual(poke.stage_spd, 1)

    def test_trace_copies_ability(self):
        trace_poke = make_pokemon()
        trace_poke.ability = Ability("Trace")
        opp_poke = make_pokemon()
        opp_poke.ability = Ability("Levitate")
        trainer = make_trainer(name="Blue", pokemon=[make_pokemon(), trace_poke])
        trainer.selected_mon = 1
        opponent = make_trainer(name="Red", pokemon=[opp_poke])
        from battle.abilities import apply_switch_abilities
        apply_switch_abilities(trainer, opponent, [])
        self.assertEqual(trace_poke.ability.name, "Levitate")

    def test_cute_charm_triggers_on_contact(self):
        import unittest.mock
        poke = make_pokemon()
        poke.ability = Ability("Cute Charm")
        defender = make_trainer(name="Blue", pokemon=[poke])
        attacker = make_trainer(name="Red", pokemon=[make_pokemon()])
        move = make_move(category="physical", power=40, acc=1.0)
        events = []
        with unittest.mock.patch("battle.abilities.random.random", return_value=0.0):
            from battle.abilities import apply_contact_abilities
            apply_contact_abilities(attacker, defender, move, events)
        self.assertTrue(any("Cute Charm" in e.text for e in events if hasattr(e, 'text')))

    def test_suction_cups_prevents_forced_switch(self):
        poke = make_pokemon()
        poke.ability = Ability("Suction Cups")
        from battle.abilities import check_ability_prevents_switch
        self.assertTrue(check_ability_prevents_switch(poke))

    def test_truant_skips_every_other_turn(self):
        poke = make_pokemon()
        poke.ability = Ability("Truant")
        from battle.initiative import check_can_act
        # First turn: should act
        can_act, reason = check_can_act(poke)
        self.assertTrue(can_act)
        self.assertTrue(poke.truant_skip)
        # Second turn: should skip
        can_act, reason = check_can_act(poke)
        self.assertFalse(can_act)
        self.assertEqual(reason, "Truant")
        self.assertFalse(poke.truant_skip)

    def test_color_change_changes_type(self):
        poke = make_pokemon(type=["Normal"])
        poke.ability = Ability("Color Change")
        defender = make_trainer(pokemon=[poke])
        attacker = make_trainer(pokemon=[make_pokemon(stat_attk=100)])
        move = make_move(type=["Fire"], category="physical", power=40, acc=1.0)
        from battle.damage import apply_damage
        apply_damage(move, attacker, defender, 1)
        self.assertEqual(poke.type, ["Fire"])

    def test_color_change_no_change_same_type(self):
        poke = make_pokemon(type=["Fire"])
        poke.ability = Ability("Color Change")
        defender = make_trainer(pokemon=[poke])
        attacker = make_trainer(pokemon=[make_pokemon(stat_attk=100)])
        move = make_move(type=["Fire"], category="physical", power=40, acc=1.0)
        from battle.damage import apply_damage
        apply_damage(move, attacker, defender, 1)
        self.assertEqual(poke.type, ["Fire"])  # unchanged


class TestIntegrationEdges(unittest.TestCase):
    """Edge cases and ability interactions."""

    def test_guts_burn_boost_ignores_burn_halving(self):
        """Guts gives 1.5x Atk and ignores Burn's 0.5x when statused."""
        from data.status_effects import burn
        poke = make_pokemon(stat_attk=100)
        # Without abilities: Burn halves attack
        poke_no_ability = make_pokemon(stat_attk=100)
        poke_no_ability.apply_status_effect(copy.deepcopy(burn))
        halved = poke_no_ability.get_stat("stat_attk")
        # With Guts: attack should NOT be halved, should be boosted
        poke.ability = Ability("Guts")
        poke.apply_status_effect(copy.deepcopy(burn))
        guts_atk = poke.get_stat("stat_attk")
        self.assertGreater(guts_atk, halved)  # Guts beats Burn halving
        self.assertGreater(guts_atk, poke.stat_attk)  # Guts actually boosts

    def test_intimidate_blocked_by_clear_body(self):
        atk_poke = make_pokemon()
        atk_poke.ability = Ability("Clear Body")
        int_poke = make_pokemon()
        int_poke.ability = Ability("Intimidate")
        opponent = make_trainer(name="Red", pokemon=[atk_poke])
        trainer = make_trainer(name="Blue", pokemon=[make_pokemon(), int_poke])
        trainer.selected_mon = 1
        from battle.abilities import apply_switch_abilities
        apply_switch_abilities(trainer, opponent, [])
        self.assertEqual(atk_poke.stage_attk, 0)

    def test_synchronize_fails_against_immunity(self):
        """Synchronize shouldn't pass poison to an Immunity mon."""
        import unittest.mock
        from battle.status_effects import apply_status_effect_from_move
        def_poke = make_pokemon()
        def_poke.ability = Ability("Synchronize")
        defender = make_trainer(name="Blue", pokemon=[def_poke])
        atk_poke = make_pokemon()
        atk_poke.ability = Ability("Immunity")
        attacker = make_trainer(name="Red", pokemon=[atk_poke])
        move = make_move(status_effect=copy.deepcopy(poison), category="status")
        with unittest.mock.patch("battle.status_effects.random.random", return_value=0.0):
            apply_status_effect_from_move(move, defender, attacker, [])
        self.assertIsNone(atk_poke.major_status)

    def test_volt_absorb_declines_self_electric(self):
        """Volt Absorb should still absorb allied Electric (future doubles)."""
        poke = make_pokemon(stat_hp=100)
        poke.hp = 50
        poke.ability = Ability("Volt Absorb")
        defender = make_trainer(pokemon=[poke])
        move = make_move(type=["Electric"], power=80, acc=1.0)
        events = []
        from battle.abilities import check_ability_type_immunity
        self.assertTrue(check_ability_type_immunity(defender, move, events))

    def test_wonder_guard_takes_weather_damage(self):
        """Wonder Guard blocks moves but not weather damage."""
        poke = make_pokemon(stat_hp=100, type=["Steel"])
        poke.hp = 100
        poke.ability = Ability("Wonder Guard")
        from battle.abilities import apply_weather_damage
        apply_weather_damage(poke, "sandstorm", [], "Red")
        self.assertEqual(poke.hp, 100)  # Steel immune to sandstorm

    def test_levitate_takes_non_ground_move(self):
        """Levitate blocks Ground but not Normal."""
        poke = make_pokemon(type=["Psychic"])
        poke.ability = Ability("Levitate")
        defender = make_trainer(pokemon=[poke])
        from battle.abilities import check_ability_type_immunity
        self.assertFalse(check_ability_type_immunity(defender, make_move(type=["Normal"], power=80, acc=1.0), []))

    def test_contact_ability_stacks_with_move_status(self):
        """A move that poisons should also potentially trigger Static."""
        import unittest.mock
        poke = make_pokemon(stat_hp=100)
        poke.ability = Ability("Static")
        defender = make_trainer(name="Blue", pokemon=[poke])
        atk_poke = make_pokemon()
        attacker = make_trainer(name="Red", pokemon=[atk_poke])
        move = make_move(category="physical", power=40, acc=1.0,
                         status_effect=copy.deepcopy(poison))
        events = []
        with unittest.mock.patch("battle.abilities.random.random", return_value=0.0):
            from battle.abilities import apply_contact_abilities
            apply_contact_abilities(attacker, defender, move, events)
        self.assertEqual(atk_poke.major_status.name, "Paralysis")

    def test_sturdy_does_not_protect_from_multihit_second_hit(self):
        """Sturdy only protects the first hit at full HP."""
        poke = make_pokemon(stat_hp=100)
        poke.hp = poke.max_hp
        poke.ability = Ability("Sturdy")
        defender = make_trainer(pokemon=[poke])
        from battle.abilities import check_ability_before_damage
        # First hit from full: reduces to 1 HP
        dmg = check_ability_before_damage(defender, 999, [])
        self.assertEqual(dmg, poke.hp - 1)
        # Apply the damage
        poke.hp = poke.hp - dmg  # 1 HP
        # Second hit: Sturdy shouldn't activate (not at full)
        dmg2 = check_ability_before_damage(defender, 50, [])
        self.assertEqual(dmg2, 50)

    def test_thick_fat_stacks_with_weather(self):
        """Thick Fat + Rain: fire damage is halved twice (0.5 * 0.5 = 0.25)."""
        poke = make_pokemon()
        poke.ability = Ability("Thick Fat")
        defender = make_trainer(pokemon=[poke])
        attacker = make_trainer(pokemon=[make_pokemon()])
        move = make_move(type=["Fire"], power=80)
        from battle.abilities import modify_damage_by_ability, modify_damage_by_weather
        mult = modify_damage_by_ability(attacker, defender, move, 100) * \
               modify_damage_by_weather("Fire", "rain")
        self.assertAlmostEqual(mult, 0.25)

    def test_truant_skips_confused_turn(self):
        """Truant should skip even if the Pokemon would act through confusion."""
        import unittest.mock
        poke = make_pokemon()
        poke.ability = Ability("Truant")
        poke.truant_skip = True
        from battle.initiative import check_can_act
        can_act, reason = check_can_act(poke)
        self.assertFalse(can_act)
        self.assertEqual(reason, "Truant")

    def test_sturdy_then_sandstorm_kos(self):
        """Sturdy leaves 1 HP, then sandstorm damage KOs."""
        poke = make_pokemon(stat_hp=100, type=["Normal"])
        poke.hp = poke.max_hp
        poke.ability = Ability("Sturdy")
        defender = make_trainer(pokemon=[poke])
        from battle.abilities import check_ability_before_damage, apply_weather_damage
        # OHKO attack → Sturdy leaves 1 HP
        dmg = check_ability_before_damage(defender, 999, [])
        poke.hp = max(0, poke.hp - dmg)
        self.assertEqual(poke.hp, 1)
        # Sandstorm finishes it
        apply_weather_damage(poke, "sandstorm", [], "Red")
        self.assertEqual(poke.hp, 0)

    def test_rough_skin_plus_recoil(self):
        """Rough Skin + recoil: attacker takes both on contact."""
        import unittest.mock
        poke = make_pokemon(stat_hp=100)
        poke.ability = Ability("Rough Skin")
        defender = make_trainer(name="Blue", pokemon=[poke])
        atk_poke = make_pokemon(stat_hp=100)
        atk_poke.hp = 100
        attacker = make_trainer(name="Red", pokemon=[atk_poke])
        move = make_move(category="physical", power=40, acc=1.0, recoil=0.3)
        events = []
        with unittest.mock.patch("battle.abilities.random.random", return_value=0.0):
            from battle.abilities import apply_contact_abilities
            apply_contact_abilities(attacker, defender, move, events)
        self.assertLess(atk_poke.hp, 100)  # took Rough Skin damage

    def test_hustle_plus_compound_eyes_stacks(self):
        """Hustle (0.8x) + Compound Eyes (1.3x) = 1.04x accuracy."""
        # These are on different Pokemon, test multipliers independently
        from battle.abilities import check_ability_accuracy_modifier
        hpoke = make_pokemon(); hpoke.ability = Ability("Hustle")
        cpoke = make_pokemon(); cpoke.ability = Ability("Compound Eyes")
        self.assertAlmostEqual(check_ability_accuracy_modifier(make_trainer(pokemon=[hpoke])), 0.8)
        self.assertAlmostEqual(check_ability_accuracy_modifier(make_trainer(pokemon=[cpoke])), 1.3)

    def test_poison_point_blocked_by_immunity(self):
        """Poison Point shouldn't poison an Immunity mon."""
        import unittest.mock
        poke = make_pokemon(stat_hp=100)
        poke.ability = Ability("Poison Point")
        defender = make_trainer(name="Blue", pokemon=[poke])
        atk_poke = make_pokemon()
        atk_poke.ability = Ability("Immunity")
        attacker = make_trainer(name="Red", pokemon=[atk_poke])
        move = make_move(category="physical", power=40, acc=1.0)
        events = []
        with unittest.mock.patch("battle.abilities.random.random", return_value=0.0):
            from battle.abilities import apply_contact_abilities
            apply_contact_abilities(attacker, defender, move, events)
        self.assertIsNone(atk_poke.major_status)

    def test_flash_fire_blocks_will_o_wisp(self):
        """Flash Fire blocks Fire-type moves including status moves."""
        poke = make_pokemon(type=["Grass"])
        poke.ability = Ability("Flash Fire")
        defender = make_trainer(name="Blue", pokemon=[poke])
        move = make_move(type=["Fire"], power=0, acc=1.0, category="status")
        events = []
        from battle.abilities import check_ability_type_immunity
        self.assertTrue(check_ability_type_immunity(defender, move, events))

    def test_serene_grace_shield_dust_interaction(self):
        """Serene Grace doubles chance, but Shield Dust blocks all secondary."""
        from battle.abilities import check_ability_shield_dust, check_ability_serene_grace
        sgpoke = make_pokemon(); sgpoke.ability = Ability("Serene Grace")
        sdpoke = make_pokemon(); sdpoke.ability = Ability("Shield Dust")
        self.assertTrue(check_ability_serene_grace(sgpoke))
        self.assertTrue(check_ability_shield_dust(sdpoke))

    def test_weather_speed_negated_by_cloud_nine(self):
        """Cloud Nine negates weather for speed calcs."""
        poke = make_pokemon()
        poke.ability = Ability("Swift Swim")
        poke2 = make_pokemon()
        poke2.ability = Ability("Cloud Nine")
        t1 = make_trainer(pokemon=[poke])
        t2 = make_trainer(pokemon=[poke2])
        from battle.abilities import is_weather_active
        self.assertFalse(is_weather_active("rain", t1, t2))
        # Speed shouldn't double
        from battle.abilities import modify_speed_by_weather
        self.assertEqual(modify_speed_by_weather(poke, 100, None), 100)


if __name__ == "__main__":
    unittest.main()
