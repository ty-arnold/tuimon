# tuimon

A command-line Pokemon battle simulator built in Python, featuring real Pokemon data from the PokeAPI. Supports Generation 1-3 Pokemon and moves with accurate battle mechanics.

---

## Features

- Turn-based battle system with priority and speed-based turn order
- Real Pokemon and move data fetched from the PokeAPI with local JSON caching
- Official Generation 3 damage formula with critical hits and type effectiveness
- Stat stage system (+6 to -6) for buffs and debuffs
- Major status effects (Poison, Burn, Paralysis, Sleep, Freeze) — only one at a time
- Minor status effects (Confusion, Curse) — multiple can stack
- Multi-turn moves: charge moves (Fly, Dig, Dive, Bounce), recharge moves (Hyper Beam), and accumulator moves (Bide, Rollout, Fury Cutter)
- Move priority system — higher priority moves always go first regardless of speed
- Never-miss moves (Swift, Aerial Ace)
- Multi-hit moves (Bullet Seed, Double Slap)
- Recoil, lifesteal, and healing moves
- Modifier system for turn-based power and damage buffs (Charge, Mud Sport)
- Screen effects (Light Screen, Reflect) and protection moves (Protect, Detect)
- Invulnerability states (flying, underground, underwater)
- Type immunity overrides (Thunder Wave vs Ground, Bide vs Ghost)
- Move PP tracking — PP only consumed on successful execution
- Configurable debug mode with preset teams
- Timestamped battle logs with configurable verbosity

---

## Project Structure

```
pokemongame/
├── src/
│   ├── main.py                     # entry point and battle loop
│   ├── battle/
│   │   ├── __init__.py
│   │   ├── battle.py               # resolve_turn, next_mon, check_winner
│   │   ├── turn_order.py           # get_turn_order, check_can_act
│   │   ├── move_handler.py         # apply_move, handle_charge_turn, check_accuracy
│   │   ├── damage.py               # calculate_damage, apply_damage, get_type_multiplier
│   │   ├── effects.py              # process_status_effects, apply_status_effect_from_move
│   │   ├── modifiers.py            # apply_modifier, get_modifier_value
│   │   ├── move_effects.py         # apply_move_effect, handle_protect, handle_screen
│   │   └── accumulator.py          # handle_accumulator, release_accumulator
│   ├── models/
│   │   ├── __init__.py
│   │   ├── pokemon.py              # Pokemon class
│   │   ├── move.py                 # Move class
│   │   ├── trainer.py              # Trainer class
│   │   ├── status_effect.py        # StatusEffect class
│   │   ├── modifier.py             # Modifier, MoveEffect dataclasses
│   │   ├── multi_turn.py           # MultiTurn, Accumulator dataclasses
│   │   └── turn_order.py           # TurnOrder NamedTuple
│   ├── pokemon/
│   │   ├── __init__.py
│   │   ├── pokemon_factory.py      # PokeAPI integration, create_pokemon_from_api
│   │   └── cache_manager.py        # JSON cache read/write and serialization
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── print.py                # print_actions, print_status_effect, display_party
│   │   ├── input.py                # get_turn, get_party, get_move
│   │   └── debug.py                # dump_pokemon, dump_move, dump_battle_state
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # global constants (DEFAULT_IV, DEFAULT_EV, DEBUG)
│   │   ├── game_print.py           # game_print() — prints to terminal and logs
│   │   ├── logger.py               # setup_logger, logger object
│   │   └── presets.py              # get_test_player, get_test_npc for debug mode
│   └── data/
│       ├── __init__.py
│       ├── mult_tables.py          # stat_table, acc_table, crit_table
│       ├── type_chart.py           # full gen 1-3 type chart
│       └── status_effects.py       # poison, burn, paralysis, sleep, freeze, confusion, curse
├── scripts/
│   ├── fetch_gen3_moves.py         # bulk fetch and cache gen 1-3 moves from PokeAPI
│   └── fetch_pokemon.py            # pre-fetch specific pokemon
├── tests/
│   ├── conftest.py
│   ├── helpers.py                  # make_pokemon, make_move, make_trainer
│   ├── test_battle.py
│   ├── test_damage.py
│   ├── test_moves.py
│   ├── test_stages.py
│   └── test_status_effects.py
├── cache/
│   ├── pokemon_cache.json          # cached pokemon data (auto-generated)
│   └── move_cache.json             # cached move data (auto-generated)
├── logs/                           # timestamped battle logs (auto-generated)
├── pyproject.toml
├── Makefile
└── README.md
```

---

## Installation

**Requirements:** Python 3.12+

1. Clone the repository:
```bash
git clone https://github.com/yourname/tuimon.git
cd tuimon
```

2. Install dependencies:
```bash
uv sync
```
or
```bash
pip install requests
```

3. Fetch move data for generations 1-3:
```bash
python scripts/fetch_gen3_moves.py
```

---

## Usage

**Normal mode** — prompts you to choose your Pokemon and moves interactively:
```bash
python src/main.py
```

**Debug mode** — loads preset teams instantly for testing. Set `DEBUG = True` in `core/config.py`:
```python
DEBUG = True
```

---

## Common Commands

```bash
# run the game
python src/main.py

# run all tests
python -m unittest discover tests -v

# run a single test file
python -m unittest tests.test_damage -v

# run a single test
python -m unittest tests.test_moves.TestMultiHitMoves.test_multi_hit_stops_if_defender_faints -v

# fetch move data
python scripts/fetch_gen3_moves.py

# type check
pyright src/
```

Or using the Makefile:
```bash
make run
make test
make fetch
make typecheck
```

---

## How It Works

### Battle Flow
```
1. Both trainers select an action (move, swap pokemon, items)
2. Status effects checked — paralysis/sleep/confusion may prevent action
3. Move priority determines who goes first
4. If equal priority, speed determines order (ties randomized)
5. Moves are applied — accuracy checked, type immunity checked
6. Damage calculated using the official gen 3 formula
7. Secondary effects applied (stat changes, status effects, recoil)
8. End of turn: status effects deal damage and may expire
9. Fainted pokemon are swapped out
10. Battle ends when one trainer has no pokemon remaining
```

### Damage Formula
Follows the official Generation 3 calculation:

```
damage = round(
    (((2 * level * critical / 5) + 2) * power * (attack / defense) / 50 + 2)
    * type_multiplier
)
```

Where:
- `critical` = 2 on a crit, 1 otherwise
- `power` = effective power after modifier adjustments (e.g. Charge doubling Electric moves)
- `attack / defense` = stat_attk/stat_def for physical, stat_sp_attk/stat_sp_def for special

### Turn Order
1. Higher priority moves always go first (e.g. Quick Attack +1 beats Tackle 0)
2. Equal priority — faster Pokemon goes first
3. Speed tie — randomized

### Stat Stages
Stats can be modified in battle between -6 and +6:

| Stage | Multiplier |
|-------|------------|
| -6    | 0.25x      |
| -3    | 0.4x       |
| 0     | 1.0x       |
| +3    | 2.5x       |
| +6    | 4.0x       |

---

## Data Models

### Pokemon
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
| `major_status` | Active major status effect (only one at a time) |
| `minor_status` | Active minor status effects (multiple allowed) |
| `modifiers` | Active turn-based move modifiers |
| `accumulator` | Accumulated value for Bide/Rollout type moves |
| `moveset` | List of Move objects |

### Move
| Attribute | Description |
|-----------|-------------|
| `name` | Move name |
| `type` | Move type |
| `category` | physical, special, or status |
| `power` | Base power |
| `acc` | Accuracy (0.0–1.0, None = never misses) |
| `pp` | Power points remaining |
| `stat_change` | Stat stage changes per target |
| `stat_change_chance` | Probability stat changes trigger (e.g. 0.1 for Acid) |
| `recoil` | Recoil as percentage of damage dealt |
| `lifesteal` | HP drained as percentage of damage dealt |
| `heal` | HP restored as percentage of max HP |
| `crit_rate` | Critical hit rate stage bonus |
| `flinch_chance` | Chance to cause flinch |
| `priority` | Move priority |
| `min_hits` / `max_hits` | Multi-hit range (None = single hit) |
| `multi_turn` | MultiTurn dataclass for charge/recharge/accumulator moves |
| `hits_invulnerable` | Invulnerable states this move can hit |
| `immune_types` | Types that are immune to this move |
| `status_effect` | Status effect applied on hit |
| `modifier` | Modifier applied when this move is used |
| `move_effect` | Field effect (protect, screen, mist, safeguard) |

### Trainer
| Attribute | Description |
|-----------|-------------|
| `name` | Trainer name |
| `party` | List of Pokemon |
| `selected_mon` | Index of active Pokemon |
| `locked_move` | Currently locked multi-turn move |
| `locked_turns` | Turns remaining on locked move |
| `invulnerable_state` | Current state (flying, underground, underwater) |
| `active_effects` | Active field effects (screens, protect) |
| `consecutive_protect` | Counter for consecutive protect accuracy reduction |

### StatusEffect
| Attribute | Description |
|-----------|-------------|
| `name` | Effect name |
| `is_major` | True for Poison/Burn/Paralysis/Sleep/Freeze |
| `chance_to_apply` | Probability of being applied |
| `chance_to_act` | Probability of acting each turn |
| `chance_to_end` | Probability of ending each turn |
| `use_turn_counter` | True for Sleep — uses random 1-3 turn counter |
| `stat_modifier` | Stat multipliers for duration of effect |
| `damage` | Percentage of max HP dealt per turn |

### Modifier
| Attribute | Description |
|-----------|-------------|
| `name` | Identifier e.g. "Charge" |
| `turns` | Duration in turns (-1 = permanent until switched out) |
| `target` | "self", "opponent", or "both" |
| `power_modifier` | Multiplies move power |
| `accuracy_modifier` | Multiplies accuracy |
| `damage_modifier` | Multiplies final damage |
| `type_condition` | Only applies to moves of this type |
| `category_condition` | Only applies to physical/special/status |
| `clears_on_switch` | Whether modifier is lost on switch |

### MultiTurn
| Attribute | Description |
|-----------|-------------|
| `turns` | Total number of turns |
| `charge_turn` | 1 = charge first, 2 = recharge after |
| `charge_message` | Message shown on charge/recharge turn |
| `invulnerable` | Whether user is invulnerable during charge |
| `invulnerable_state` | State name (flying, underground, underwater) |
| `invulnerable_message` | Message shown when opponent tries to hit |
| `accumulator` | Optional Accumulator config for Bide/Rollout type moves |

---

## Status Effects

### Major (only one at a time)
| Effect | Behavior |
|--------|----------|
| Poison | Deals 10% max HP per turn |
| Burn | Deals 6.25% max HP per turn, halves attack stat |
| Paralysis | 25% chance to be unable to act, halves speed |
| Sleep | Unable to act for 1-3 turns (random counter) |
| Freeze | Unable to act until randomly thawed |

### Minor (multiple can stack)
| Effect | Behavior |
|--------|----------|
| Confusion | 50% chance to deal 10% max HP self-damage instead of attacking |
| Curse | Deals 25% max HP per turn |

---

## Multi-Turn Moves

### Charge then Attack
| Move | Invulnerable | Notes |
|------|-------------|-------|
| Fly | Yes (flying) | Hit by Thunder, Gust (2x) |
| Dig | Yes (underground) | Hit by Earthquake (2x) |
| Dive | Yes (underwater) | Hit by Surf (2x) |
| Bounce | Yes (flying) | Hit by Thunder, Gust (2x) |
| Solar Beam | No | Skips charge in sunny weather (future) |
| Skull Bash | No | |
| Razor Wind | No | |
| Sky Attack | No | |

### Attack then Recharge
| Move |
|------|
| Hyper Beam |
| Blast Burn |
| Frenzy Plant |
| Hydro Cannon |

### Accumulator Moves
| Move | Accumulates | Releases |
|------|-------------|---------|
| Bide | Damage taken | 2x accumulated damage, ignores type, blocked by Ghost |
| Rollout | Turn count | Exponentially increasing damage each hit |
| Ice Ball | Turn count | Exponentially increasing damage each hit |
| Fury Cutter | Turn count | Doubles each successive hit |

---

## Move Override System

Since the PokeAPI doesn't expose structured data for every mechanic, several override dictionaries in `fetch_gen3_moves.py` define behavior manually:

- `MULTI_TURN_OVERRIDES` — charge/recharge/accumulator move configs
- `MODIFIER_OVERRIDES` — power/damage modifiers (Charge, Mud Sport, Water Sport)
- `MOVE_EFFECT_OVERRIDES` — field effects (Light Screen, Reflect, Protect, Mist, Safeguard)
- `HITS_INVULNERABLE` — moves that hit through invulnerability states
- `IMMUNE_TYPE_OVERRIDES` — type-based immunity exceptions (Thunder Wave vs Ground)

---

## Pokemon & Move Data

Pokemon and move data is fetched from the [PokeAPI](https://pokeapi.co) and cached locally in `cache/`. Only Generation 1-3 Pokemon and moves are supported.

### Fetching Move Data
Run the fetch script before playing to populate the move cache:
```bash
python scripts/fetch_gen3_moves.py
```

This fetches all moves from generations 1-3 and caches them. Already cached moves are skipped so the script is safe to re-run. Progress is saved every 10 moves in case of interruption.

### Fetching Pokemon Data
Pokemon are fetched and cached on demand when selected during gameplay.

---

## Testing

Tests are written using `unittest` and cover damage calculation, move mechanics, status effects, stat stages, and battle resolution.

```bash
# run all tests
python -m unittest discover tests -v

# run specific file
python -m unittest tests.test_status_effects -v

# run specific test
python -m unittest tests.test_damage.TestDamageCalculation.test_critical_hit_deals_more_damage -v
```

When mocking random values always patch the submodule where random is used:
```python
# correct — patch where it's used
unittest.mock.patch("battle.damage.random.random", return_value=1.0)
unittest.mock.patch("battle.turn_order.random.random", return_value=0.0)

# incorrect — battle is a package not a module
unittest.mock.patch("battle.random.random", return_value=1.0)
```

---

## Debug & Logging

Set `DEBUG = True` in `core/config.py` to load preset teams and enable verbose output. All battle logs are saved to `logs/` with a timestamp.

Log levels:
- `INFO` — normal battle messages shown in console and saved to log
- `DEBUG` — detailed state information (stats, damage calc, stage changes) saved to log file only

---

## Acknowledgements

- Pokemon data provided by [PokeAPI](https://pokeapi.co)
- Damage formula based on [Bulbapedia — Damage](https://bulbapedia.bulbagarden.net/wiki/Damage)
- Type chart based on [Bulbapedia — Type](https://bulbapedia.bulbagarden.net/wiki/Type)
- Move data verified against [Bulbapedia — List of Moves](https://bulbapedia.bulbagarden.net/wiki/List_of_moves)
- Move effect categories from [Bulbapedia — Moves by Effect](https://bulbapedia.bulbagarden.net/wiki/Category:Moves_by_effect)


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
