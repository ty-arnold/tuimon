import random
from mult_tables import *

### Global values ###
iv = 15
ev = 85

class Pokemon:
    def __init__(self, name, lvl, type, moveset, stat_hp, 
                 stat_attk, stat_def, stat_sp_attk, stat_sp_def, stat_spd):

        self.name    = name
        self.lvl     = lvl
        self.type    = type
        self.moveset = moveset

        self.base_stat_hp      = stat_hp
        self.base_stat_attk    = stat_attk
        self.base_stat_def     = stat_def
        self.base_stat_sp_attk = stat_sp_attk
        self.base_stat_sp_def  = stat_sp_def
        self.base_stat_spd     = stat_spd

        self.hp           = round((((((self.base_stat_hp      + iv) * 2) + ev) * self.lvl) / 100 ) + lvl + 10)
        self.stat_attk    = round((((((self.base_stat_attk    + iv) * 2) + ev) * self.lvl) / 100 ) + 5)
        self.stat_def     = round((((((self.base_stat_def     + iv) * 2) + ev) * self.lvl) / 100 ) + 5)
        self.stat_sp_attk = round((((((self.base_stat_sp_attk + iv) * 2) + ev) * self.lvl) / 100 ) + 5)
        self.stat_sp_def  = round((((((self.base_stat_sp_def  + iv) * 2) + ev) * self.lvl) / 100 ) + 5)
        self.stat_spd     = round((((((self.base_stat_spd     + iv) * 2) + ev) * self.lvl) / 100 ) + 5)
        self.stat_acc     = 1
        self.stat_eva     = 1
        self.max_hp  = self.hp

        self.stage_attk    = 0
        self.stage_def     = 0
        self.stage_sp_attk = 0
        self.stage_sp_def  = 0
        self.stage_spd     = 0
        self.stage_acc     = 0
        self.stage_eva     = 0 

        self.status_effect = []
        
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
        if stat == "stat_acc":
            return round(base * acc_table[stage])
        else:
            return round(base * stat_table[stage])

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
        for stat, multiplier in effect.stat_changes.items():
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
    def __init__(self, name, type, category, power, acc, pp, effects, status_effect=None, recoil=0.0):
        self.name = name
        self.type = type
        self.category = category
        self.power = power
        self.recoil = recoil
        self.acc = acc
        self.pp = pp
        self.max_pp = pp
        self.effects = effects
        self.status_effect = status_effect
    def __repr__(self):
        return self.name
    
class StatusEffect:
    def __init__(self, name, chance_to_apply, chance_to_end=None, duration=None, stat_changes=None, chance_to_act=1.0):
        self.name = name
        self.chance_to_end = chance_to_end
        self.duration = duration
        self.stat_changes = stat_changes or {} 
        self.applied_changes = {}               
        self.chance_to_act = chance_to_act
        self.chance_to_apply = chance_to_apply
        self.turns_active = 0 

    def can_act(self):
        if self.chance_to_act < 1.0:
            if random.random() > self.chance_to_act:
                return False
        return True
        
    def check_should_end(self):
        self.turns_active += 1

        if self.turns_active < 2:
            return False
        
        if self.duration is not None:
            self.duration -= 1
            return self.duration == 0 
        elif self.chance_to_end is not None:
            return random.random() < self.chance_to_end
        return False

class Trainer:
    def __init__(self, name, party, selected_mon):
        self.name = name
        self.party = party
        self.selected_mon = selected_mon

    def print_party(self):
        print(f"{self.name}'s Party:")
        for i, pokemon in enumerate(self.party):
            print(f"{i + 1}. {pokemon.name}")
        print(f"{len(self.party) + 1}. Cancel")

    def print_hp(self):
        print(f"{self.name}'s {self.active().name}: {self.active().hp}/{self.active().max_hp}") 
    
    def active(self):
        return self.party[self.selected_mon]