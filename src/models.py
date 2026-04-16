import random
from mult_tables import *

### Global values ###
iv = 15
ev = 85

class Pokemon:
    def __init__(self, name, lvl, type, moveset,
                 stat_hp, stat_attk, stat_def, stat_sp_attk, stat_sp_def, stat_spd):
        # identity
        self.name    = name
        self.lvl     = lvl
        self.type    = type
        self.moveset = moveset

        # base stats
        self.base_stat_hp      = stat_hp
        self.base_stat_attk    = stat_attk
        self.base_stat_def     = stat_def
        self.base_stat_sp_attk = stat_sp_attk
        self.base_stat_sp_def  = stat_sp_def
        self.base_stat_spd     = stat_spd

        # calculated stats
        self.hp           = self._calc_hp(stat_hp, iv, ev, lvl)
        self.max_hp       = self.hp
        self.stat_attk    = self._calc_stat(stat_attk,    iv, ev, lvl)
        self.stat_def     = self._calc_stat(stat_def,     iv, ev, lvl)
        self.stat_sp_attk = self._calc_stat(stat_sp_attk, iv, ev, lvl)
        self.stat_sp_def  = self._calc_stat(stat_sp_def,  iv, ev, lvl)
        self.stat_spd     = self._calc_stat(stat_spd,     iv, ev, lvl)
        self.stat_acc     = 1.0
        self.stat_eva     = 1.0

        # battle stages
        self.stage_attk    = 0
        self.stage_def     = 0
        self.stage_sp_attk = 0
        self.stage_sp_def  = 0
        self.stage_spd     = 0
        self.stage_acc     = 0
        self.stage_eva     = 0

        # status
        self.status_effect = []

    def _calc_hp(self, base, iv, ev, lvl):
        return round((((base + iv) * 2 + ev) * lvl / 100) + lvl + 10)

    def _calc_stat(self, base, iv, ev, lvl):
        return round((((base + iv) * 2 + ev) * lvl / 100) + 5)

    def active(self):
        return self

    def is_alive(self):
        return self.hp > 0
    
    def get_stat(self, stat):
        stage_map = {
            "stat_attk":    (self.stat_attk,    self.stage_attk),
            "stat_def":     (self.stat_def,     self.stage_def),
            "stat_sp_attk": (self.stat_sp_attk, self.stage_sp_attk),
            "stat_sp_def":  (self.stat_sp_def,  self.stage_sp_def),
            "stat_spd":     (self.stat_spd,     self.stage_spd),
            "stat_acc":     (self.stat_acc,     self.stage_acc),
            "stat_eva":     (self.stat_eva,     self.stage_eva),
        }
        base, stage = stage_map[stat]
        if stat in ("stat_acc", "stat_eva"):
            calculated =  base * acc_table[stage]
        else:
            calculated = round(base * stat_table[stage])

        for effect in self.status_effect:
            if stat in effect.stat_modifier:
                calculated = round(calculated * effect.stat_modifier[stat])
        
        return calculated

    def apply_stage_change(self, stat, change):
        stage_attr = {
            "stat_attk":    "stage_attk",
            "stat_def":     "stage_def",
            "stat_sp_attk": "stage_sp_attk",
            "stat_sp_def":  "stage_sp_def",
            "stat_spd":     "stage_spd",
            "stat_acc":     "stage_acc",
            "stat_eva":     "stage_eva"
        }
        attr = stage_attr[stat]
        current_stage = getattr(self, attr)
        new_stage = max(-6, min(6, current_stage + change))
        setattr(self, attr, new_stage)
        return new_stage - current_stage
    
    def apply_status_effect(self, effect):
        for stat, multiplier in effect.stat_modifier.items():
            original = getattr(self, stat)
            effect.applied_changes[stat] = original
            setattr(self, stat, int(original * multiplier))
        self.status_effect.append(effect)

    def remove_status_effect(self, effect):
        for stat, original_value in effect.applied_changes.items():
            setattr(self, stat, original_value)
        self.status_effect.remove(effect)

    def print_moves(self):
        for i, move in enumerate(self.moveset):
            print(f"{i + 1}. {move.name}")
        print(f"{len(self.moveset) + 1}. Cancel")

class Move:
    def __init__(self, name, type, category, power, acc, pp, stat_change,
                recoil            = 0.0,
                lifesteal         = 0.0,
                heal              = 0.0,
                min_hits          = None,
                max_hits          = None,
                crit_rate         = 0,
                flinch_chance     = 0.0,
                priority          = 0,
                hits_invulnerable = None,
                status_effect     = None,
                multi_turn        = None):

        self.name              = name
        self.type              = type
        self.category          = category
        self.power             = power
        self.acc               = acc
        self.pp                = pp
        self.stat_change       = stat_change
        self.recoil            = recoil
        self.lifesteal         = lifesteal
        self.heal              = heal
        self.min_hits          = min_hits
        self.max_hits          = max_hits
        self.crit_rate         = crit_rate
        self.flinch_chance     = flinch_chance
        self.priority          = priority
        self.hits_invulnerable = hits_invulnerable
        self.status_effect     = status_effect
        self.multi_turn        = multi_turn
    
    def __repr__(self):
        return self.name
    
class StatusEffect:
    def __init__(self, name, chance_to_apply, 
                 chance_to_end    = None, 
                 duration         = None, 
                 stat_modifier    = None, 
                 chance_to_act    = 1.0, 
                 damage           = None,
                 use_turn_counter = False):
        
        self.name             = name
        self.chance_to_end    = chance_to_end
        self.duration         = duration
        self.stat_modifier    = stat_modifier or {} 
        self.applied_changes  = {}               
        self.chance_to_act    = chance_to_act
        self.chance_to_apply  = chance_to_apply
        self.damage           = damage
        self.turns_active     = 0
        self.use_turn_counter = use_turn_counter
        self.turn_counter     = None

    def can_act(self):
        if self.chance_to_act < 1.0:
            if random.random() > self.chance_to_act:
                return False
        return True
        
    def check_should_end(self):
        self.turns_active += 1

        if self.turns_active < 2:
            return False

        if self.use_turn_counter and self.turn_counter is not None:
            self.turn_counter -= 1
            return self.turn_counter == 0  # returns True when counter hits 0

        if self.duration is not None:
            self.duration -= 1
            return self.duration == 0

        if self.chance_to_end is not None:
            return random.random() < self.chance_to_end

        return False

class Trainer:
    def __init__(self, name, party):
        self.name                = name
        self.party               = party
        self.selected_mon        = 0
        self.locked_move         = None
        self.locked_turns        = 0
        self.is_invulnerable     = False
        self.invulnerable_state  = None

    def print_party(self):
        print(f"{self.name}'s Party:")
        for i, pokemon in enumerate(self.party):
            print(f"{i + 1}. {pokemon.name}")
        print(f"{len(self.party) + 1}. Cancel")

    def print_hp(self):
        print(f"{self.name}'s {self.active().name}: {self.active().hp}/{self.active().max_hp}") 
    
    def active(self):
        return self.party[self.selected_mon]