import random

class Pokemon:
    def __init__(self, name, lvl, type, moveset, stat_hp, 
                 stat_attk, stat_def, stat_sp_attk, stat_sp_def, stat_spd):
        self.name = name
        self.lvl = lvl
        self.type = type
        self.hp = ((((2 * stat_hp) * lvl))/100) + lvl + 10
        self.max_hp = self.hp
        self.moveset = moveset
        self.stat_attk = stat_attk
        self.stat_def = stat_def
        self.stat_sp_attk = stat_sp_attk
        self.stat_sp_def = stat_sp_def
        self.stat_spd = stat_spd
        self.status_effect = []

    def is_alive(self):
        return self.hp > 0
    
    def apply_status_effects(self, effect):
        for stat, multiplier in effect.stat_changes.items():
            original = getattr(self, stat)
            effect.applied_changes[stat] = original
            setattr(self, stat, int(original * multiplier))
        self.status_effect.append(effect)

    def remove_status_effects(self, effect):
        for stat, original_value in effect.applied_changes.items():
            setattr(self, stat, original_value)
            self.status_effect.remove(effect)

    def print_moves(self):
        for i, move in enumerate(self.moveset):
            print(f"{i + 1}. {move.name}")
        print(f"{len(self.moveset) + 1}. Cancel")

class Move:
    def __init__(self, name, type, dmg_type, pp, effects, status_effect=None):
        self.name = name
        self.type = type
        self.dmg_type = dmg_type
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

    def can_act(self):
        if self.chance_to_act < 1.0:
            if random.random() > self.chance_to_act:
                return False
            return True
        
    def check_should_end(self):
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