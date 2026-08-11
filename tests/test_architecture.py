"""Locks in the import layering from docs/battle-state-refactor.md (Phase 0).

Two assertions, both AST-based (no imports actually executed):

1. No module may import, at module scope, from a package in a strictly
   higher layer than its own.
2. No function/method body may contain a first-party import (deferred
   imports are how import cycles hide).

Both assertions are seeded with the violations that exist in the codebase
today via KNOWN_* sets below. As later refactor steps remove a deferred
import or a layering violation, delete its entry here — the sets shrinking
to empty is the completion signal for the whole import-graph cleanup.

Do NOT add new entries to either set without a comment explaining why, and
prefer fixing the import instead.
"""
import ast
import os
import unittest

SRC_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")

# Layer 0 is the bottom (zero first-party deps allowed above it); higher
# numbers may depend on lower numbers but not the reverse.
LAYERS = {
    "data":    0,
    "core":    0,
    "models":  1,
    "battle":  2,
    "pokemon": 2,
    "saves":   2,
    "assets":  2,
    "ui":      3,
    "cli":     3,
    "app":     4,
}

FIRST_PARTY_PACKAGES = set(LAYERS)

# (importer_module, imported_module) pairs where importer_module contains a
# module-scope `from imported_module import ...` reaching into a strictly
# higher layer. Both known offenders predate the architecture test.
KNOWN_LAYER_VIOLATIONS = {
    # data/ is documented as "pure tables, zero imports" but this file
    # builds StatusEffect instances, so it reaches up into models/.
    ("data.status_effects", "models.status_effect"),
    # pokemon_factory does interactive CLI-style status printing via
    # game_print, which moved to ui/ in Step B. Pre-existing coupling,
    # surfaced (not introduced) by that move.
    ("pokemon.pokemon_factory", "ui.game_print"),
}

# (importer_module, imported_module) pairs where importer_module contains a
# function/method-local `from imported_module import ...`. This is the
# "deferred imports hide cycles" list from the refactor doc's Step D.
KNOWN_DEFERRED_IMPORTS = {
    # battle.abilities <-> battle.damage: a genuine module-level 2-cycle,
    # worked around by deferring on both sides. Fixed by the ability hook
    # registry described in the refactor doc's follow-ups.
    ("battle.abilities", "battle.damage"),
    ("battle.damage", "battle.abilities"),

    # battle.abilities is a hub imported by nearly every other battle/
    # module; each of these is deferred purely to avoid battle.abilities
    # itself being imported before the module that needs it is ready.
    # Removed by the ability hook registry (see refactor doc follow-ups).
    ("battle.abilities", "data.abilities"),
    ("battle.abilities", "data.status_effects"),
    ("battle.abilities", "models.status_effect"),
    ("battle.abilities", "models.turn_result"),
    ("battle.battle", "battle.abilities"),
    ("battle.initiative", "battle.abilities"),
    ("battle.move_handler", "battle.abilities"),
    ("battle.status_effects", "battle.abilities"),

    # models.pokemon -> battle.abilities: the last models -> battle edge.
    # Removed in Step 10 when stat calc moves to BattleState.effective_stat.
    ("models.pokemon", "battle.abilities"),

    # pokemon.cache_manager defers these to avoid import-time cost / to
    # keep dict_to_move / dict_to_pokemon lazy at module load.
    ("pokemon.cache_manager", "data.abilities"),
    ("pokemon.cache_manager", "data.status_effects"),
    ("pokemon.cache_manager", "models.modifier"),
    ("pokemon.cache_manager", "models.move"),
    ("pokemon.cache_manager", "models.pokemon"),

    # saves/ modules defer their pokemon/ imports.
    ("saves.inventory_save", "pokemon.gen3_names"),
    ("saves.party_save", "pokemon.cache_manager"),

    # ui/ deferrals are mostly Textual screen-push cycles (screen A pushes
    # screen B which could push screen A) and lazy heavy imports
    # (sprite_cache, cache_manager) — not part of the battle/models cycle
    # work, but still first-party deferrals per the doc's rule.
    ("ui.app", "ui.screens.title_screen"),
    ("ui.mixins.battle_ui", "ui.widgets.hp_bar"),
    ("ui.mixins.menu_ui", "data.type_chart"),
    ("ui.mixins.phase_handler", "ui.screens.end_screen"),
    ("ui.screens.battle_screen", "assets.sprite_cache"),
    ("ui.screens.party_builder_screen", "pokemon.cache_manager"),
    ("ui.screens.party_builder_screen", "pokemon.pokemon_factory"),
    ("ui.screens.title_screen", "app.fixtures"),
    ("ui.screens.title_screen", "ui.screens.battle_screen"),
    ("ui.screens.title_screen", "ui.screens.party_builder_screen"),
}


def _module_name(filepath: str) -> str:
    rel = os.path.relpath(filepath, SRC_ROOT)
    rel = rel[:-3] if rel.endswith(".py") else rel
    parts = rel.split(os.sep)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _iter_src_files():
    for dirpath, _dirnames, filenames in os.walk(SRC_ROOT):
        if "__pycache__" in dirpath:
            continue
        for fn in filenames:
            if fn.endswith(".py"):
                yield os.path.join(dirpath, fn)


class _ImportCollector(ast.NodeVisitor):
    """Collects first-party `from X import ...` targets, split into
    module-scope vs function/method-scope."""

    def __init__(self):
        self._func_depth = 0
        self.module_scope: list[tuple[int, str]] = []
        self.func_scope: list[tuple[int, str]] = []

    def visit_FunctionDef(self, node):
        self._func_depth += 1
        self.generic_visit(node)
        self._func_depth -= 1

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            top = node.module.split(".")[0]
            if top in FIRST_PARTY_PACKAGES:
                bucket = self.func_scope if self._func_depth > 0 else self.module_scope
                bucket.append((node.lineno, node.module))
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            top = alias.name.split(".")[0]
            if top in FIRST_PARTY_PACKAGES:
                bucket = self.func_scope if self._func_depth > 0 else self.module_scope
                bucket.append((node.lineno, alias.name))
        self.generic_visit(node)


def _collect() -> dict[str, _ImportCollector]:
    results = {}
    for path in _iter_src_files():
        mod = _module_name(path)
        with open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=path)
        collector = _ImportCollector()
        collector.visit(tree)
        results[mod] = collector
    return results


class TestImportLayering(unittest.TestCase):
    """Assertion 1: no module-scope import reaches into a strictly higher
    layer than its own package."""

    @classmethod
    def setUpClass(cls):
        cls.collected = _collect()

    def test_no_module_scope_import_from_higher_layer(self):
        violations = []
        for mod, collector in self.collected.items():
            top = mod.split(".")[0]
            if top not in LAYERS:
                continue  # not a layered package (e.g. top-level main.py)
            my_layer = LAYERS[top]
            for lineno, imported in collector.module_scope:
                itop = imported.split(".")[0]
                if itop not in LAYERS:
                    continue
                if LAYERS[itop] <= my_layer:
                    continue
                if (mod, imported) in KNOWN_LAYER_VIOLATIONS:
                    continue
                violations.append(f"{mod}:{lineno} imports {imported} "
                                   f"(layer {LAYERS[itop]} > {my_layer})")

        self.assertEqual(
            violations, [],
            "New module-scope layering violation(s) found. Either fix the "
            "import or add a justified entry to KNOWN_LAYER_VIOLATIONS in "
            "tests/test_architecture.py:\n" + "\n".join(violations),
        )

    def test_known_layer_violations_are_still_present(self):
        """Guards against a stale allow-list — if a violation is fixed,
        its entry must be deleted from KNOWN_LAYER_VIOLATIONS (that removal
        is itself the signal the refactor step is complete)."""
        seen = set()
        for mod, collector in self.collected.items():
            for _lineno, imported in collector.module_scope:
                seen.add((mod, imported))

        stale = KNOWN_LAYER_VIOLATIONS - seen
        self.assertEqual(
            stale, set(),
            f"KNOWN_LAYER_VIOLATIONS contains entries that no longer exist "
            f"in the codebase — delete them: {stale}",
        )


class TestNoDeferredFirstPartyImports(unittest.TestCase):
    """Assertion 2: no function/method body may contain a first-party
    import. Deferred imports are how import cycles hide."""

    @classmethod
    def setUpClass(cls):
        cls.collected = _collect()

    def test_no_new_function_local_first_party_imports(self):
        violations = []
        for mod, collector in self.collected.items():
            for lineno, imported in collector.func_scope:
                if (mod, imported) in KNOWN_DEFERRED_IMPORTS:
                    continue
                violations.append(f"{mod}:{lineno} defers import of {imported}")

        self.assertEqual(
            violations, [],
            "New function-local first-party import(s) found. Either import "
            "at module scope or add a justified entry to "
            "KNOWN_DEFERRED_IMPORTS in tests/test_architecture.py:\n"
            + "\n".join(violations),
        )

    def test_known_deferred_imports_are_still_present(self):
        """Same staleness guard as above, for the deferred-import list.
        A shrinking KNOWN_DEFERRED_IMPORTS is the completion signal for
        untangling the import graph (see docs/battle-state-refactor.md)."""
        seen = set()
        for mod, collector in self.collected.items():
            for _lineno, imported in collector.func_scope:
                seen.add((mod, imported))

        stale = KNOWN_DEFERRED_IMPORTS - seen
        self.assertEqual(
            stale, set(),
            f"KNOWN_DEFERRED_IMPORTS contains entries that no longer exist "
            f"in the codebase — delete them: {stale}",
        )


if __name__ == "__main__":
    unittest.main()
