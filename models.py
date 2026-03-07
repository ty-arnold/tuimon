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

class Move:
    def __init__(self, name, type, pp, target, stat_hp, stat_max_hp, dmg_type,
                 stat_attk, stat_def, stat_sp_attk, stat_sp_def, stat_spd):
        self.name = name
        self.type = type
        self.pp = pp
        self.max_pp = pp
        self.target = target
        self.stat_hp = stat_hp
        self.stat_max_hp = stat_max_hp
        self.stat_attk = stat_attk
        self.stat_def = stat_def
        self.stat_sp_attk =stat_sp_attk
        self.stat_sp_def = stat_sp_def
        self.stat_spd = stat_spd
        self.dmg_type = dmg_type

    def __repr__(self):
        return self.name

class Trainer:
    def __init__(self, name, party, selected_mon):
        self.name = name
        self.party = party
        self.selected_mon = selected_mon