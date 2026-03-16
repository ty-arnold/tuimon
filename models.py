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

    def is_alive(self):
        return self.hp > 0

    def print_moves(self):
        for i, move in enumerate(self.moveset):
            print(f"{i + 1}. {move.name}")
        print(f"{len(self.moveset) + 1}. Cancel")

class Move:
    def __init__(self, name, type, dmg_type, pp, effects):
        self.name = name
        self.type = type
        self.dmg_type = dmg_type
        self.pp = pp
        self.max_pp = pp
        self.effects = effects
    def __repr__(self):
        return self.name

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