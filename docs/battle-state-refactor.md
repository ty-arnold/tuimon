# BattleState Refactor Plan

Consolidating scattered battle state into a single `BattleState` object with
encapsulated mutators.

**Design decision:** mutable state + encapsulated mutators + `clone()`.
Not a functional/immutable core — see "Why not immutable" at the bottom.

---

## The problem

Battle state currently lives in six places with no owner:

| State | Lives on | Problem |
|---|---|---|
| `turn` | `BattleController` | threaded as `current_turn` param through 5 modules |
| `weather` | `BattleController` | **never passed back into `resolve_turn`** → resets every turn |
| `phase` | `BattleController` | UI writes to it directly |
| `locked_move`, `locked_turns`, `invulnerable_state` | `Trainer` | belongs to the active *Pokémon* |
| `active_effects`, `consecutive_protect` | `Trainer` | screens store absolute expiry turn |
| `modifiers`, `accumulator`, `truant_skip`, statuses, stages | `Pokemon` | mixed permanent + transient |
| `hp`, `stat_*` | `Pokemon` | status effects destructively overwrite base stats |
| `events` | out-param `list` | 22 signatures, 73 `if events is not None:` guards |
| RNG | `random` module global | not seedable |

### Known bugs this fixes

1. **Weather evaporates every turn** — `battle.py:63` hard-codes `weather = None`;
   `controller.weather` is write-only.
2. **Weather applied too late** — weather-setting moves are scanned at `battle.py:78`,
   *after* `_resolve_moves`. Swift Swim / Chlorophyll never fire.
3. **Status stat modifiers applied twice** — `Pokemon.apply_status_effect` writes
   `setattr(self, stat, base * mult)` **and** `get_stat()` multiplies again.
   Verified: base speed 162 → paralysed `get_stat()` returns 91, should be 121.
4. **Accumulator damage emits no `HPChange`** — `accumulator.py:39` subtracts HP with
   zero event. Bide/Rollout damage doesn't animate the HP bar.
5. **Three `HPChange` events have `trainer=""`** — `status_effects.py:70,82`,
   `initiative.py:80`. Only a `Pokemon` is in scope, so the owner is unknown.
6. **HP bar routing breaks in mirror matches** — `battle_ui._get_hp_widget_id` matches
   by species name and checks the NPC party first. Both sides running Pidgeot → all
   HP animation hits the NPC bar. (Fixed by #5 giving events a real trainer.)
7. **Four package-level import cycles**, three of them top-level in both directions —
   see Phase 0. They survive only by luck of import ordering.
8. **`TurnResult.winner` is always `None`** — `resolve_turn` returns `bool | None`,
   but `controller.py:86` tests `isinstance(winner, Trainer)`. The
   "You won!"/"You lost!" log line has never displayed. See Step 11.
9. **Unbounded queue growth in the TUI** — `battle_screen.message_queue` has no
   consumer, and `_start_battle` is rescheduled ~6.7x/sec forever by
   `_animate_sprites`. See Step 12.

### Root cause of #4, #5, #6

HP mutation and event emission are **two independent steps duplicated at 16 sites**:

```
file                     hp mutations   HPChange emitted
battle/accumulator.py          1                 0     ← bug
battle/damage.py               3                 1
battle/abilities.py            7                 6     ← suspect
battle/move_handler.py         2                 4
battle/status_effects.py       2                 2
battle/initiative.py           1                 1
```

Encapsulated mutators make the mismatch structurally impossible.

---

## Target architecture

```
BattleState                 (src/core/battle_context.py)
├── turn: int
├── weather: Weather | None      (name + turns_remaining)
├── rng: random.Random
├── player / npc: Trainer        (references, never copies)
├── _events: list[TurnEvent]     (private)
│
├── emit(e) / emit_all(es) / drain_events()
├── clone()                      → speculative AI, replay, undo
├── owner_of(pokemon) -> Trainer (fixes trainer="" events)
└── mutators (see Step 6)
```

Every engine function converges on:

```python
# before
def apply_move(move, attacker, defender, current_turn, events=None, weather=None)
# after
def apply_move(state, move, attacker, defender)
```

`state` goes **first** and is **required** — no default. Required-ness is what makes
the test suite find every call site for you.

**Two hard rules:**
- Hold *references* to `Pokemon`/`Trainer`. Never copy them into state — two sources
  of truth for HP is worse than the bug you're fixing.
- Never import `BattleState` into `src/models/`. That's a new import cycle, and you
  already have 38 function-local imports working around cycles.

---

## Steps

Two phases, fifteen steps. **Each ends with tests green and is one commit.**

**Phase 0 (A–D)** untangles the import graph. Do it first — threading `state`
through a clean graph is far easier than fighting deferred imports at every call site.
All four steps are mechanical and near-zero risk.

**Phase 1 (0–11)** is the `BattleState` work. Steps 0–7 are behaviour-preserving;
steps 8+ are the actual bug fixes, deliberately last so that when regression numbers
move, you know it was intentional.

| Step | Change | Risk | Behaviour changes? |
|---|---|---|---|
| A | Thin the `__init__.py` files | none | no |
| B | Re-home `core/` by layer | low | no |
| C | Delete presentation methods on models | none | no |
| D | Architecture test | none | no |
| 0 | Characterization tests | none | — |
| 1 | Create `BattleState` + `clone()` | none | no |
| 2 | Instantiate in controller | none | no |
| 3 | Thread `state` everywhere | low | no |
| 4 | Retire `current_turn` | low | no |
| 5 | Retire `events` out-param | medium | no |
| 6 | Add mutator API (unused) | none | no |
| 7 | Migrate 59 mutation sites | **medium** | **yes** — fixes #4, #5, #6 |
| 8 | Fix weather | medium | **yes** — fixes #1, #2 |
| 9 | Inject RNG | low | no (if seeded) |
| 10 | Fix double stat modifier | medium | **yes** — fixes #3 |
| 11 | NPC AI out of UI + fix `winner` | low | **yes** — fixes #8 |
| 12 | Drain/delete the message queue | low | **yes** — fixes #9 |

## Before you start

- **Commit or stash first.** 15 files are currently modified, including 6 that Phase 1
  rewrites (`battle/{abilities,battle,controller,damage,initiative,move_handler,
  status_effects}.py`, `models/{move,pokemon}.py`). Land or shelve that work before
  Step A — you do not want an unrelated diff tangled into a 15-step refactor.
- **`git add docs/`.** This file is currently untracked.
- **Mind the coverage gaps.** `move_effects.py`, `modifiers.py`, `accumulator.py`, and
  `controller.py` have **zero direct tests**, yet Step 7 migrates mutation sites in
  three of them and Step 0 drives everything through `controller.py`. Write targeted
  unit tests for those four modules as part of Step 0, before touching them.
- **`Move.__init__` has shared mutable defaults.** `immune_types: list[str] = []` and
  `immune_moves` are assigned straight to `self`, so *every* Move built without those
  args shares one list object — verified: appending to one leaks into all others.
  Nothing appends today, so it is latent, but fix it (`= None` + `or []`) during
  Phase 0 while you are already in `models/`.

---

# Phase 0 — Untangle imports

## The cycles

AST analysis of `src/` finds four package-level cycles:

```
battle  <->  models      (models->battle deferred)
core    <->  models      <- both top-level
core    <->  pokemon     <- both top-level
models  <->  data        <- both top-level
```

Three are top-level in **both** directions. They work today only because of import
ordering; one reordered line yields
`ImportError: cannot import name 'X' from partially initialized module`.

There are **38 function-local (deferred) imports** across `src/`, and **26 of them
(68%) are `from battle.abilities`**. One module causes two-thirds of the problem.

## Why the cycles exist

### Cause 1 — fat `__init__.py` re-exports coarsen the graph

`models/pokemon.py` needs two lookup tables:

```python
from data import acc_table, stat_table
```

`data/mult_tables.py`, where those live, has **zero imports** — a pure leaf. There is
no real dependency. But `from data import ...` executes `data/__init__.py`, which
imports `data.status_effects`, which imports `models`. The cycle is created entirely
by the re-export.

**Submodule imports do not save you** — Python initializes parent packages first.
Verified in this tree:

```python
import core.config
# core.msg loaded as side effect?  True
# models loaded as side effect?    True
# data loaded as side effect?      True
```

So `models/pokemon.py: from core.config import DEFAULT_IV` — apparently a dependency
on an 8-line constants file — actually drags in `core/__init__` -> `core.msg` ->
`models.turn_result` -> the whole `models` package. That is the `core <-> models`
cycle, manufactured by `core/__init__.py`.

### Cause 2 — `core/` is a junk drawer spanning four layers

| Module | Real dependencies | Actual layer |
|---|---|---|
| `config.py` | none | leaf |
| `logger.py` | none | leaf |
| `battle_state.py` (`BattlePhase`) | none | leaf |
| `msg.py` | `data.messages`, `models.turn_result` | engine |
| `game_print.py` | `core.config`, queue global | presentation |
| `colors.py` | — | presentation |
| `presets.py` | `pokemon`, `models` | app wiring |

`core` is not a layer — it is four layers in a trench coat, welded together by its
`__init__.py`. `models` legitimately depends on `core.config` (a leaf), but gets
`core.msg` (engine layer) forced on it.

`core/presets.py` pulls `pokemon` into `core` single-handedly, causing the
`core <-> pokemon` cycle. It is DEBUG fixture data imported only by `main.py` and
`title_screen.py`.

### Cause 3 — models reach into the engine

- `Pokemon.print_moves()` / `Trainer.print_party()` defer-import `core.game_print`.
  Only `cli/input.py` calls them, at 3 sites.
- `Pokemon.get_stat()` calls `battle.abilities` **four times** — a data model
  computing ability-modified stats. This is the `battle <-> models` cycle.

### Cause 4 — `battle.abilities` is a hub with a back-edge

`abilities.py:84` imports `battle.damage`; `damage.py` imports `battle.abilities`
three times. A genuine module-level 2-cycle, worked around by deferring on both sides.

## Target layering

```
Layer 0   data/           pure tables, zero imports
          core/           config, logger, battle_state ONLY
Layer 1   models/         -> data, core
Layer 2   battle/         -> models, data, core
          pokemon/ saves/
Layer 3   ui/, cli/       -> everything
```

---

### Step A — Thin the `__init__.py` files

Biggest leverage, near-zero risk. Kills cycles #2, #3, and #4 with no architectural
change.

1. Empty `data/__init__.py` and `core/__init__.py` (the two urgent ones — both sit
   below `models` in the layering and both currently import upward).
2. Replace every `from data import X` / `from core import X` with the concrete module:
   `from data.mult_tables import acc_table, stat_table`,
   `from data.type_chart import TYPE_CHART`, `from core.msg import msg`, etc.
3. Then thin `models/__init__.py`, `battle/__init__.py`, `pokemon/__init__.py` the
   same way. These are less urgent (they sit at or above their dependencies) but the
   re-exports still hide the true graph.
4. `battle/__init__.py` is also a stale API surface — it re-exports `get_npc_move`
   and `execute_switch`, which move in Step 11. Emptying it now avoids churn later.

**Verify:** `uv run python -m unittest discover tests -v` green; app launches.
Re-run the cycle detector — `models <-> data` and `core <-> models` should be gone.

---

### Step B — Re-home `core/` by layer

Pure file moves. Do them while the engine is still stable.

| Move | To | Why |
|---|---|---|
| `core/msg.py` | `battle/messages.py` | it is engine output; depends on `models` |
| `core/game_print.py` | `ui/game_print.py` | presentation + the async queue global |
| `core/colors.py` | `ui/colors.py` | presentation |
| `core/presets.py` | `app/fixtures.py` (new) or `scripts/` | DEBUG fixtures; kills `core <-> pokemon` |

Keep in `core/`: `config.py`, `logger.py`, `battle_state.py`. All three are leaves
with no first-party imports — which is what makes `core` safe for `models` to depend on.

⚠️ `models/turn_result.py` imports `core.battle_state` for `BattlePhase`. That stays
valid (leaf -> leaf). Do not move `battle_state.py` into `battle/`, or you recreate
`models <-> battle`.

⚠️ `battle/move_handler.py:272` defer-imports `core.game_print` inside
`check_immunity` but never uses the result — dead line. Delete it rather than
updating the path.

**Verify:** all four cycles reduced to `battle <-> models` only. App launches; CLI
mode (`TUI_MODE = False`) still runs.

---

### Step C — Delete presentation methods on models

1. Move the loops in `Pokemon.print_moves()` and `Trainer.print_party()` into
   `cli/input.py` (3 call sites: lines 18, 23, 72).
2. Delete both methods.

This removes the last `models -> core.game_print` edge. After this, the only remaining
`models -> battle` edge is `Pokemon.get_stat()` calling `battle.abilities`.

**Verify:** `grep -rn "game_print" src/models/` -> empty.

---

### Step D — Lock it in with an architecture test

Without this it regresses within a month. Add `tests/test_architecture.py` that walks
the AST of every file under `src/` and asserts:

```python
LAYERS = {"data": 0, "core": 0, "models": 1, "battle": 2,
          "pokemon": 2, "saves": 2, "assets": 2, "ui": 3, "cli": 3}

# 1. no module may import from a strictly higher layer
# 2. no function-local import of a first-party package  <- the important one
```

Assertion 2 is what matters: deferred imports are how cycles hide. Make them fail
loudly and every future cycle surfaces as a red test instead of a workaround.

**Seed it with the known exceptions** so it passes today:

```python
KNOWN_VIOLATIONS = {
    ("models.pokemon", "battle.abilities"),   # removed in Step 10
    ("battle.damage", "battle.abilities"),    # removed by the hook registry
    # ... the remaining battle.abilities deferrals
}
```

Delete entries from `KNOWN_VIOLATIONS` as later steps remove them. The set shrinking
to empty is the completion signal for the whole refactor.

**Verify:** test passes with the exception list; fails if you add a new deferred
first-party import anywhere.

---

# Phase 1 — BattleState

### Step 0 — Build a safety net

Your tests are the only thing making this safe, and today they can't detect
ordering or RNG changes.

1. Add `tests/test_regression_battle.py`.
2. ~5 tests running **full battles** through `BattleController`: `random.seed(1234)`
   in `setUp`, two fixed 2-Pokémon teams from `tests/helpers.py`, loop
   `select_player_move` → `select_npc_move` → `execute_turn` until `BATTLE_OVER`.
3. Assert on **final HP, turn count, and the event type sequence**
   (`[type(e).__name__ for e in result.events]`). The event sequence is what protects
   Steps 5 and 7.
4. Record whatever the current code produces — **including wrong values**. This is a
   characterization test, not a correctness test. Mark known-bad expectations:
   `# FIXME: wrong due to double-applied paralysis; changes in Step 10`

**Verify:** 224 tests green. Run twice — differing results mean an RNG path escaped
seeding. Find it before continuing.

---

### Step 1 — Create the class, wire it to nothing

Create `src/core/battle_context.py`. Put it in `core/`, not `battle/` — both
`battle/` and `controller` need it and `core/` avoids a new cycle.

- `@dataclass class Weather:` — `name: str`, `turns_remaining: int`
- `class BattleState:` — `__init__(self, player, npc, rng=None)` setting `turn=0`,
  `weather=None`, `rng = rng or random.Random()`, `_events=[]`
- `emit(event)`, `emit_all(events)`, `drain_events()` (return copy, clear)
- `opponent_of(trainer)`, `both_trainers()`
- `owner_of(pokemon) -> Trainer` — scan both parties by identity (`is`), not name.
  This is what kills the `trainer=""` events in Step 7.
- `clone() -> BattleState` — `deepcopy` the parties + weather, fresh event list,
  share the rng (or re-seed). Unlocks lookahead AI, replay, and undo for ~30 lines.

Add `tests/test_battle_state.py` for `emit`/`drain_events`/`owner_of`/`clone`
(assert clone mutation doesn't touch the original).

**Do not import it anywhere else yet.**

---

### Step 2 — Instantiate in the controller, still unused

In `src/battle/controller.py`:
- `__init__`: `self.state = BattleState(player, npc)`
- Keep `self.turn` and `self.weather` as **properties** proxying to `self.state.*`.
  This preserves `controller.turn` reads in `phase_handler.py` and `battle_ui.py`
  with zero UI changes.
- `execute_turn` still calls `resolve_turn` the old way.

**Verify:** tests green; `uv run python src/main.py` still plays.

---

### Step 3 — Thread `state` alongside the old params

Largest mechanical step. Go in **dependency order** so you never edit a caller
before its callee is ready:

```
1. modifiers.py       5. status_effects.py    9. battle.py (root)
2. move_effects.py    6. initiative.py
3. accumulator.py     7. move_handler.py
4. damage.py          8. abilities.py
```

Per module: add `state: BattleState` as the **first** parameter of every public
function, **leave `current_turn` / `events` / `weather` in place**, update callers,
run tests.

**Verify after each module.** One commit is fine; per-module test runs are not.

---

### Step 4 — Retire `current_turn`

1. Replace body uses of `current_turn` with `state.turn` in the 5 modules that take it.
2. Delete the param from signatures and all call sites.

Leave `Modifier.is_active(current_turn)`, `Modifier.is_expired(current_turn)`, and
`Pokemon.get_active_modifiers(current_turn)` alone — model methods taking a plain
int are correct. Callers pass `state.turn`.

**Verify:** `grep -rn "current_turn" src/battle/` → empty. Tests green.

---

### Step 5 — Retire the `events` out-param

Deletes 73 guards and 22 signature params.

**Do this before Step 6.** If mutators emitted into `state._events` while call sites
still appended to a separate `events` list, the two streams would interleave wrongly
and scramble event ordering in `TurnResult`.

Per module:
1. `events.append(x)` → `state.emit(x)`
2. Delete the enclosing `if events is not None:` guard, dedent the body
3. Delete the `events` param from signature and call sites
4. In `resolve_turn`, delete the `if events is None: events = []` prelude
5. In `controller.execute_turn`, replace the local `events = []` with
   `events = self.state.drain_events()` **after** `resolve_turn` returns

⚠️ Before starting, `grep -rn "events\[\|len(events)" src/battle/` — any site that
*reads* the list needs restructuring or a `peek_events()` accessor.

**Verify:** `grep -rc "if events is not None" src/battle/*.py` → all zeros.
Step 0's event-sequence assertions must still pass exactly.

---

### Step 6 — Add the mutator API (no call sites yet)

Add to `BattleState`. Each mutator **clamps, mutates, and emits its own event**.
Each returns the *actual* amount applied, which is what callers need for recoil,
drain, and "won't go any further" messages.

```
damage(pokemon, amount)          -> int    clamp ≥0,      emit HPChange
heal(pokemon, amount)            -> int    clamp ≤max_hp, emit HPChange
set_hp(pokemon, value)           -> int    clamp,         emit HPChange
change_stage(pokemon, stat, d)   -> int    clamp ±6,      emit StatChange
apply_status(pokemon, effect)    -> bool                  emit StatusApplied
remove_status(pokemon, effect)   -> None                  emit StatusRemoved
add_effect(trainer, effect)      -> None                  emit EffectChange
remove_effect(trainer, effect)   -> None                  emit EffectChange
add_modifier(pokemon, modifier)  -> None
remove_modifier(pokemon, mod)    -> None
switch(trainer, slot)            -> None                  emit Switch
set_weather(name, turns)         -> None                  emit Message
```

All event `trainer=` fields are filled via `self.owner_of(pokemon).name` — never `""`.

**Ordering convention — decide now and document it in the docstring:**
`HPChange` is emitted **first**, then the descriptive `Message`. That matches the
majority of existing sites (`damage.py`, `move_handler.py` recoil/heal). The minority
that emit message-first will shift in Step 7; expect Step 0 sequence diffs there.

These are pure additions. Unit-test each in `tests/test_battle_state.py`
(clamping at 0 / max_hp / ±6, event emitted exactly once, correct trainer name).

**Verify:** tests green, nothing else changed.

---

### Step 7 — Migrate the 59 mutation sites

The payoff step. Work file by file, and for each site do **both halves atomically**:
replace the raw mutation *and* delete the now-redundant manual event append.

Order by risk, easiest first:

1. **`accumulator.py`** (1 site) — `defender.active().hp = max(0, ...)` →
   `state.damage(...)`. **This adds the missing `HPChange`** → new event in the
   stream, HP bar now animates for Bide/Rollout. Expected Step 0 diff.
2. **`status_effects.py`** (2 sites) — poison/burn tick. **`trainer=""` becomes a real
   name.** Expected diff.
3. **`initiative.py`** (1 site) — confusion self-hit. Same `trainer=""` fix.
4. **`damage.py`** (3 sites) — main damage path, plus the dead `apply_recoil` /
   `apply_lifesteal` helpers. Check whether those two are called anywhere
   (`move_handler` re-implements recoil inline); if dead, **delete them**.
5. **`move_handler.py`** (2 HP sites + stat changes) — recoil, lifesteal, heal.
   Then collapse `apply_stat_change` + `_emit_stat_events` into `state.change_stage()`:
   the `old_stats` accumulator list, the `actual_change == 0` "won't go any further"
   branch, and the `seen` dedup set all move inside the mutator. This is the biggest
   single readability win in the refactor.
6. **`abilities.py`** (7 sites) — Volt Absorb, Water Absorb, Rough Skin, Liquid Ooze,
   etc. The 7-vs-6 count mismatch means **one ability mutates HP without an event**;
   find it and note which in the commit message.
7. **`move_effects.py`** (3 `active_effects.append` + 1 `remove`) →
   `state.add_effect` / `state.remove_effect`.
8. **`models/pokemon.py`** — `add_modifier` / `remove_modifier` / `minor_status`
   append+remove stay as-is (they're model-internal), but the **engine** must call
   `state.add_modifier(...)` rather than `pokemon.add_modifier(...)` so events fire.

After migrating, make the raw fields private-by-convention (`Pokemon._hp` with a
read-only `hp` property) so accidental writes are visible in review.

**Verify:** `grep -rn "\.hp = \|\.hp -= \|\.hp += " src/battle/` → **zero**.
That grep is your permanent invariant — add it to the Makefile as a lint target.
Step 0 numbers will shift for the sites flagged above; re-record and justify each.

---

### Step 8 — Make weather persistent

1. Delete `weather = None` at `battle.py:63` and the `weather_container` param entirely.
2. Replace local `weather` reads with `state.weather.name if state.weather else None`.
3. **Move the weather-setting scan** from `battle.py:78` (after `_resolve_moves`) into
   `apply_move`, right after accuracy/immunity pass and before damage. That's correct
   Gen 3 timing — weather is up for the rest of the turn.
4. Setting weather → `state.set_weather(name, turns=5)`.
5. In `resolve_turn`'s end-of-turn block, **after** weather damage, decrement
   `state.weather.turns_remaining`; at 0 set `state.weather = None` and emit a
   "weather returned to normal" message.
6. Add `weather_cleared` templates to `src/data/messages.py`.
7. Delete `weather_container` handling from `controller.execute_turn`.

Add `tests/test_weather.py`: rain persists 3 turns and still boosts Water; clears
after 5; Swift Swim actually fires (this exercises the reordering in #3).

---

### Step 9 — Inject the RNG

19 call sites across 8 files.

1. `random.random()` → `state.rng.random()`, `.choice()`, `.randint()` throughout
   `src/battle/`. Delete the now-unused `import random`.
2. Three model sites also call `random`: `StatusEffect.can_act()` /
   `check_should_end()` (`status_effect.py:34,53`) and `Pokemon.apply_status_effect`
   (`pokemon.py:130`). Give them an optional `rng=None` param defaulting to the
   module `random`; pass `state.rng` from the engine. **Do not** import `BattleState`
   into `models/`.
3. `BattleController.__init__` gains `seed: int | None = None` →
   `BattleState(player, npc, rng=random.Random(seed))`.
4. Rewrite tests: replace `patch("battle.damage.random.random", ...)` with a fake rng
   injected into `BattleState`.
5. **Update `AGENTS.md` and `CLAUDE.md`** — the "patch random at submodule level"
   gotcha is now obsolete, and both docs still reference `battle.turn_order`, which
   was renamed to `battle.initiative`.

**Verify:** `grep -rn "random\." src/battle/` → empty. Same seed → identical battles.

---

### Step 10 — Fix the double-applied stat modifier

Also the moment to close the last `models -> battle` cycle. `Pokemon.get_stat()`
currently calls `battle.abilities` four times; stat calculation belongs in the engine.
Move it to `state.effective_stat(pokemon, stat)` and reduce `Pokemon.get_stat()` to
base × stage with no ability awareness. Then drop
`("models.pokemon", "battle.abilities")` from `KNOWN_VIOLATIONS` in Step D's test.

1. `models/pokemon.py::apply_status_effect` — delete the
   `setattr(self, stat, int(original * multiplier))` block and the
   `effect.applied_changes[stat] = original` bookkeeping.
2. `remove_status_effect` — delete the `applied_changes` restore loop.
3. `get_stat()` already applies `major_status.stat_modifier` and becomes the single
   source of truth.
4. Delete `applied_changes` from `StatusEffect.__init__`.
5. Test: paralysed base-162 Pokémon → `get_stat("stat_spd") == 121` and
   `pokemon.stat_spd` stays `162`.

⚠️ `tests/test_status_effects.py:149::test_major_status_stat_modifier_applied` will
likely fail — read it first and confirm it was asserting the doubled value.

---

### Step 11 — Move NPC AI out of the UI

`PhaseHandlerMixin._do_npc_switch()` in `src/ui/mixins/phase_handler.py` is game logic
living in the view, and it mutates `locked_move` / `invulnerable_state` / `selected_mon`.

1. Create `src/battle/ai.py` with `choose_switch(state, trainer) -> int | None`;
   move `get_npc_move` there from `battle.py`.
2. Add `BattleController.execute_npc_switch()` calling it via `state.switch(...)`.
3. `battle_ui.py` replaces `self._do_npc_switch()` with
   `self.controller.execute_npc_switch()` and renders the `Switch` event normally.
4. Delete `_do_npc_switch` from the mixin.
5. **Fix `TurnResult.winner` first — it is currently always `None`.**
   `resolve_turn` is typed `-> bool | None` and returns `True`/`None`, but
   `controller.py:86` guards on `if isinstance(winner, Trainer)`, which can never be
   true. So `winner_id` is always `None`, and `battle_ui._handle_winner`'s
   "You won!" / "You lost!" has **never once displayed**.

   `check_winner` already returns `Trainer | None` — the information is thrown away at
   `battle.py:108` (`return True if check_winner(...) else None`). Fix by propagating
   the trainer:
   - `battle.py:108` -> `return check_winner(state, player, npc)`
   - the four intermediate `return True` sites in `_resolve_moves` / `resolve_turn`
     -> return the winning `Trainer` instead
   - retype `resolve_turn` and `_resolve_moves` as `-> Trainer | None`
   - `controller.execute_turn`'s `if winner:` truthiness check still works unchanged

   Only *then* switch `phase_handler`'s EndScreen from `any(p.is_alive() ...)` to
   `result.winner`. Doing it in the other order silently breaks the end screen.

**Verify:** headless test that a fainted NPC auto-switches with no UI involved, plus
a test asserting `TurnResult.winner == "player"` on a win.

---

### Step 12 — Drain or delete the message queue (TUI)

Independent of the engine, but it is a live memory leak and the plan touches
`battle_screen.py` anyway.

1. `battle_screen.on_mount` creates `self.message_queue` and registers it via
   `set_async_queue()`, but **nothing ever consumes it**. Every `game_print()` in TUI
   mode does `put_nowait` into a queue that is never drained.
2. `_animate_sprites` — running on `set_interval(0.15, ...)` — ends with
   `self.set_timer(0.2, self._start_battle)`. That reschedules `_start_battle`
   **~6.7 times per second, forever**, each firing
   `game_print(msg("battle_start"))` into the undrained queue. Move that
   `set_timer` call into `on_mount` where it belongs.
3. `game_print` is typed `(message: str)` but is being handed a `Message` object here
   — this is one of the 44 pyright errors (`battle_screen.py:161`).
4. Decide: either add a consumer task that pumps the queue into the `RichLog`, or
   delete the queue entirely. Since `TurnResult.events` already carries everything to
   the UI, **deleting is the better option** — along with `set_async_queue` and the
   `_async_message_queue` global in `game_print.py`.

**Verify:** run the app for 60s; memory flat. `grep -rn "set_async_queue" src/` empty
if you deleted it.

---

## Follow-ups (not in this refactor)

- Move `locked_move` / `locked_turns` / `invulnerable_state` from `Trainer` → `Pokemon`.
  Today, switching out mid-Fly carries invulnerability to the incoming Pokémon.
  Deliberately separate so a regression can be bisected.
- Fix `battle_ui._get_hp_widget_id` to route by `event.trainer` instead of species
  name (Step 7 supplies the real trainer; this consumes it).
- Fix the 44 `pyright` errors and add CI. A gate that's never green protects nothing.
- **Ability hook registry** — replaces `abilities.py`'s name-matching chains *and*
  removes the remaining ~26 deferred imports. Instead of every engine module importing
  `abilities`, abilities register into a table the engine reads:

  ```
  battle/hooks.py      registry: dict[HookName, list[callable]]  — zero imports
  battle/abilities.py  imports hooks + damage, registers handlers
  battle/damage.py     imports hooks only; hooks.fire("on_damage", state, ...)
  ```

  `abilities -> damage` becomes the only edge; the back-edge is gone. Best done
  **after Step 7**, since it touches the same call sites the mutator migration does.
  Empties the rest of `KNOWN_VIOLATIONS`.

## What this unlocks

Adding a field mechanic becomes **one field on `BattleState` plus the code that reads
it** — no signature churn. Terrain, entry hazards, Trick Room, Encore/Taunt counters,
and eventually double battles all become additive. `clone()` gives you lookahead AI
and replays whenever you want them.

## Why not immutable

A frozen `BattleState` wrapping mutable `Pokemon` objects is decorative — the state
that matters lives in the models. Real immutability means the whole object graph:
59 mutation sites, 7 model classes converted to frozen dataclasses, and every Pokémon
re-addressed **by path** (`state.side("npc").party[slot]`) instead of by reference,
because snapshots break the 3 identity comparisons in `move_handler.py:374`,
`battle.py:84`, and `controller.py:86`.

The killer is the failure mode: every function returns a new state the caller **must**
rebind. Miss one `state = ` and the update silently vanishes — no exception, no crash,
just an intermittently no-op move. `apply_move` alone has ~15 sequential mutation
points. Estimate: 2–4 weeks, with a window where the engine is broken in ways the
current tests can't see (they address Pokémon by reference too).

The one genuine payoff — speculative evaluation for lookahead AI, replay, undo — is
available from `clone()` for ~30 lines. Pokémon Showdown, far more complex than this
engine, is fully mutable and does exactly that. Chess engines use make/unmake on a
mutable board for the same reason.

And critically: **immutability would not fix bugs #4, #5, or #6.** You'd write
`state.with_hp(target, n)` and forget the event just as easily. Encapsulation fixes
those; immutability doesn't. Controlled mutation is the right target here.
