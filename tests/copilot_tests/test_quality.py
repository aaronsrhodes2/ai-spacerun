"""Quality that builds (the Captain, 2026-11-21): with the mod skippy-quality, one quality module makes a machine's output
the best quality researched, slowly. The runtime half: extra quality modules are taken out and spilled for the robots,
and the assistant's ghosts are placed at the best quality, so the requests ask for it. Without skippy-quality nothing
changes. The data half is read from the mod's own file."""
import pathlib
import re

import pytest

from luamod import LuaMod

ROOT = pathlib.Path(__file__).resolve().parents[2]
ROW = [{"name": "assembling-machine-2", "x": 1.5, "y": 1.5, "recipe": "iron-gear-wheel"},
       {"name": "transport-belt", "x": 1.5, "y": 4.5, "direction": "east"}]


@pytest.fixture
def mod():
    m = LuaMod()
    m.run("prototypes.item['quality-module'] = { name = 'quality-module', type = 'module', category = 'quality', stack_size = 50 } "
          "prototypes.item['speed-module'] = { name = 'speed-module', type = 'module', category = 'speed', stack_size = 50 }")
    return m


def quality_on(mod, *unlocked):
    mod.run("script.active_mods['skippy-quality'] = '0.2.0'")
    for q in unlocked:
        mod.run("fake.unlocked['%s'] = true" % q)


def machine(mod, modules):
    lit = "{" + ",".join("{name='%s', quality='%s', count=%d}" % m for m in modules) + "}"
    mod.run("M = game.surfaces.nauvis.create_entity{name='assembling-machine-2', position={10.5, 10.5}, force='player', modules=%s}" % lit)


def check_all(mod):
    mod.run("storage.quality_scan = nil")
    mod.tick(60)


def test_a_second_quality_module_is_taken_out_and_spilled_for_the_robots(mod):
    quality_on(mod)
    machine(mod, [("quality-module", "normal", 1), ("quality-module", "rare", 1), ("speed-module", "normal", 1)])
    check_all(mod)
    left = mod.lua.eval("(function() local n = 0 for _, m in ipairs(M.modules) do if m.name == 'quality-module' then n = n + m.count end end return n end)()")
    assert left == 1 and mod.lua.eval("M.modules[3].count") == 1                      # other modules stay
    assert mod.lua.eval("#fake.spilled") == 1 and mod.lua.eval("fake.spilled[1].marked") and mod.lua.eval("fake.spilled[1].stack.quality") == "rare"
    assert any(e["kind"] == "quality_module" and "one is enough" in e["text"] for e in mod.result("events_read")["events"])


def test_without_skippy_quality_nothing_is_touched(mod):
    machine(mod, [("quality-module", "normal", 2)])
    check_all(mod)
    assert mod.lua.eval("M.modules[1].count") == 2 and mod.lua.eval("#fake.spilled") == 0


def test_the_assistants_ghosts_are_placed_at_the_best_quality_researched(mod):
    quality_on(mod, "uncommon", "rare")
    assert mod.result("design_save", {"name": "cell", "description": "a gear cell", "pieces": ROW, "note": "first"})["version"] == 1
    mod.result("design_deploy", {"name": "cell", "x": 20, "y": 20, "dry_run": False})
    qualities = mod.lua.eval("(function() local t = {} for _, e in ipairs(game.surfaces.nauvis.entities) do if e.valid and e.type == 'entity-ghost' then t[#t + 1] = e.quality.name end end return t end)()")
    assert sorted(qualities.values()) == ["rare", "rare"]
    saved = mod.lua.eval("storage.design_inventory[1].ents[1].quality")                   # the design itself is unchanged
    assert saved is None


def test_without_skippy_quality_ghosts_stay_normal(mod):
    mod.run("fake.unlocked['legendary'] = true")
    mod.result("design_save", {"name": "cell", "description": "a gear cell", "pieces": ROW, "note": "first"})
    mod.result("design_deploy", {"name": "cell", "x": 20, "y": 20, "dry_run": False})
    qualities = mod.lua.eval("(function() local t = {} for _, e in ipairs(game.surfaces.nauvis.entities) do if e.valid and e.type == 'entity-ghost' then t[#t + 1] = e.quality.name end end return t end)()")
    assert set(qualities.values()) == {"normal"}


def test_the_data_half_makes_one_module_reach_the_top_slowly():
    text = (ROOT / "mods" / "skippy-quality" / "data-final-fixes.lua").read_text(encoding="utf-8")
    assert "m.effect.quality = 1.0" in text and "q.chain_probability = 1" in text and "q.next_probability = 1" in text
    speeds = dict(re.findall(r"\[(\d)\] = (-[\d.]+)", text))
    assert speeds == {"1": "-0.667", "2": "-0.5", "3": "-0.333"}                       # 3x, 2x and 1.5x the time
