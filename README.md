# TuiMon

A command-line Pokemon battle simulator built in Python, featuring real Pokemon data from the PokeAPI.

---

## Features

- Turn-based battle system with speed-based turn order
- Real Pokemon and move data fetched from the PokeAPI
- Full damage formula implementation including critical hits and type effectiveness
- Stat stage system (+6 to -6) for buffs and debuffs
- Status effects including poison, paralysis, sleep, burn, and freeze
- Multi-turn moves including charge moves (Fly, Dig) and recharge moves (Hyper Beam)
- Move PP tracking
- Local JSON caching for Pokemon and move data
- Logging system with configurable debug output

---

## Project Structure

```
tuimon/
├── src/
│   ├── main.py               # entry point and battle loop
│   ├── battle.py             # battle logic (apply_move, resolve_turn, check_winner)
│   ├── models.py             # Pokemon, Move, Trainer, StatusEffect classes
│   ├── print.py              # UI and input handling
│   ├── logger.py             # logging setup
│   ├── debug.py              # debug dump functions
│   ├── presets.py            # preset teams for testing
│   └── pokemon/
│       ├── __init__.py
│       ├── pokemon_factory.py  # PokeAPI integration and pokemon creation
│       └── cache_manager.py    # JSON cache read/write and serialization
├── objects/
│   ├── __init__.py
│   ├── moves.py              # manually defined moves
│   └── status_effects.py     # status effect definitions
├── scripts/
│   └── fetch_gen3_moves.py   # script to bulk fetch and cache gen 1-3 moves
├── cache/
│   ├── pokemon_cache.json    # cached pokemon data
│   └── move_cache.json       # cached move data
├── logs/                     # battle log files
└── README.md
```

---

## Installation

**Requirements:** Python 3.10+

1. Clone the repository:
```bash
git clone https://github.com/ty-arnold/tuimon.git
cd tuimon
```

2. Install dependencies:
```bash
pip install requests
```

3. Fetch move data for generations 1-3:
```bash
python scripts/fetch_gen3_moves.py
```

---

## Usage

**Normal mode** — prompts you to choose your pokemon and moves interactively:
```bash
python src/main.py
```

**Debug mode** — loads preset teams instantly for testing. Set `DEBUG = True` in `main.py`:
```python
DEBUG = True
```

---

## How It Works

### Battle Flow
```
1. Both trainers select an action (move, swap pokemon, item)
2. Speed stats determine turn order
3. Status effects are checked — paralysis/sleep may prevent action
4. Moves are applied in order
5. Damage is calculated using the official Gen 3 formula
6. Status effects are processed at end of turn
7. Fainted pokemon are swapped out
8. Battle ends when one trainer has no pokemon remaining
```

### Damage Formula
The damage formula follows the official Generation 3 calculation:

```
Damage = (((2 * Level * Critical / 5) + 2) * Power * Atk/Def / 50 + 2) * STAB * Type1 * Type2
```

### Stat Stages
Stats can be modified in battle between -6 and +6 stages using the following multipliers:

| Stage | Multiplier |
|-------|------------|
| -6    | 2/8        |
| -3    | 2/5        |
| 0     | 2/2 (1.0)  |
| +3    | 5/2        |
| +6    | 8/2        |

### Type Chart
Full 18-type chart implemented including all generation 1-3 types. Type effectiveness multipliers:
- Super effective: 2x
- Not very effective: 0.5x
- No effect: 0x

---

## Pokemon & Move Data

Pokemon and move data is fetched from the [PokeAPI](https://pokeapi.co) and cached locally in JSON format. Only Generation 1-3 Pokemon are supported.

### Fetching Move Data
Run the fetch script to populate your move cache before playing:
```bash
python scripts/fetch_gen3_moves.py
```

This fetches all moves from generations 1-3 and caches them locally. Subsequent runs skip already cached moves so the script is safe to run multiple times.

### Fetching Pokemon Data
Pokemon are fetched on demand when selected by the player and cached automatically. To pre-fetch specific pokemon:
```bash
python scripts/fetch_pokemon.py
```

---

## Classes

### Pokemon
Represents a single Pokemon with base stats, calculated stats, stage modifiers, and status effects.

| Attribute | Description |
|-----------|-------------|
| `name` | Pokemon name |
| `lvl` | Current level |
| `type` | List of types |
| `hp` / `max_hp` | Current and maximum HP |
| `stat_attk` | Calculated attack stat |
| `stat_def` | Calculated defense stat |
| `stat_sp_attk` | Calculated special attack stat |
| `stat_sp_def` | Calculated special defense stat |
| `stat_spd` | Calculated speed stat |
| `stage_*` | Battle stage modifiers (-6 to +6) |
| `status_effect` | List of active status effects |
| `moveset` | List of Move objects |

### Move
Represents a single move with all battle attributes.

| Attribute | Description |
|-----------|-------------|
| `name` | Move name |
| `type` | Move type |
| `category` | physical, special, or status |
| `power` | Base power |
| `acc` | Accuracy (0.0 to 1.0) |
| `pp` | Power points remaining |
| `stat_change` | Stat stage changes per target |
| `recoil` | Recoil damage as percentage of damage dealt |
| `lifesteal` | HP drained as percentage of damage dealt |
| `heal` | HP restored as percentage of max HP |
| `crit_rate` | Critical hit rate stage bonus |
| `flinch_chance` | Chance to cause flinch |
| `priority` | Move priority (-8 to +8) |
| `multi_turn` | Multi-turn move configuration |
| `hits_invulnerable` | Invulnerable states this move can hit through |
| `status_effect` | Status effect applied by this move |

### Trainer
Represents a player or NPC with a party of Pokemon.

| Attribute | Description |
|-----------|-------------|
| `name` | Trainer name |
| `party` | List of Pokemon objects |
| `selected_mon` | Index of active Pokemon |
| `locked_move` | Currently locked multi-turn move |
| `locked_turns` | Turns remaining on locked move |
| `is_invulnerable` | Whether trainer's active Pokemon is invulnerable |
| `invulnerable_state` | Current invulnerability state (flying, underground, etc.) |

### StatusEffect
Represents a status condition that can be applied to a Pokemon.

| Attribute | Description |
|-----------|-------------|
| `name` | Effect name |
| `chance_to_apply` | Probability of being applied (0.0 to 1.0) |
| `chance_to_act` | Probability of acting each turn (0.0 to 1.0) |
| `chance_to_end` | Probability of ending each turn (0.0 to 1.0) |
| `stat_modifier` | Stat multipliers applied for duration of effect |
| `damage` | Percentage of max HP dealt per turn |

---

## Status Effects

| Effect | Behavior |
|--------|----------|
| Poison | Deals 10% max HP per turn |
| Burn | Deals 6.25% max HP per turn, reduces attack |
| Paralysis | 25% chance to be unable to act, reduces speed |
| Sleep | Unable to act until effect ends |
| Freeze | Unable to act until effect ends |

---

## Multi-Turn Moves

| Move | Behavior |
|------|----------|
| Fly | Charge turn 1 (invulnerable), attack turn 2 |
| Dig | Charge turn 1 (invulnerable), attack turn 2 |
| Bounce | Charge turn 1 (invulnerable), attack turn 2 |
| Dive | Charge turn 1 (invulnerable), attack turn 2 |
| Solar Beam | Charge turn 1, attack turn 2 |
| Skull Bash | Charge turn 1, attack turn 2 |
| Hyper Beam | Attack turn 1, recharge turn 2 |
| Blast Burn | Attack turn 1, recharge turn 2 |

---

## Debug & Logging

Set `DEBUG = True` in `main.py` to enable verbose logging. All battle logs are saved to the `logs/` directory with a timestamp.

```python
DEBUG = True  # enables preset teams and verbose logging
```

Log levels:
- `INFO` — normal battle messages shown in console
- `DEBUG` — detailed state dumps written to log file

---

## Acknowledgements

- Pokemon data provided by [PokeAPI](https://pokeapi.co)
- Damage formula based on [Bulbapedia](https://bulbapedia.bulbagarden.net/wiki/Damage)
- Type chart based on [Bulbapedia](https://bulbapedia.bulbagarden.net/wiki/Type)

---

## TODO

- test the following functionality:
  - for fly:
    - invulnerable state set to "flying"
    - opponent cant hit user
    - hits_invlunerable "flying" work on flyer
    - flys up into air on first turn, damage is dealt on second turn
    - pokemon is locked into move until 2nd turn resolves
  - repeat for underground invuln move
  - repeat for underwater invlun move
- add weather system
- add ability system
- add test cases
- add type checking for functions
- modify multiplier calculation for second typing
- modify stab calculation for second typing
- finish fleshing out status moves
- set correct values for status moves
- flesh out move application
  - moves like confusion
  - [x] add turn sensitive status moves
  - add moves that trigger multiple times (ex: bullet seed)
  - [x] order of operations for applying stats + dealing damage
  - [x] allow application of moves to both attacker and defender
  - logic for moves like fly and substitute
- get player name/selected pokemon
- flesh out item system
  - add item class
  - logic to apply an item and skip move phase
- add tui
  - textual?

### Completed

- [x] add scraper or method to get stats of selected pokemon
- [x] add scraper or method to dynamically get stats of moves of selected pokemon
- [x] add handling for flat percentage changes to stats from things like paralysis
- [x] implement stat changes as stages (instead of fixed +/- values it increments or deincrements a staged amount)
- [x] add logic for multiple pokemon per trainer
  - [x] swap to next pokemon when active one dies
  - [x] check all pokemon of specific trainer when checking for winner
- [x] add battle menu
  - [x] moves
  - [x] items
  - [x] swap pokemon
- [x] add physical/special split
