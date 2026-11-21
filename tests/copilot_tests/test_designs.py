"""Designs: the blueprint library as the source of what stands on the map. Versions are saved and edited in the library;
the map only receives a version, by deployment (ghosts), and is moved to a later one by upgrade orders or by a clear and
rebuild. The blueprint stacks, ghosts and orders are the stand-ins in fake_game.lua."""
import pytest

from luamod import LuaMod

ROW = [{"name": "assembling-machine-2", "x": 1.5, "y": 1.5, "recipe": "iron-gear-wheel"},
       {"name": "inserter", "x": 1.5, "y": 3.5},
       {"name": "transport-belt", "x": 1.5, "y": 4.5, "direction": "east"}]


@pytest.fixture
def mod():
    m = LuaMod()
    m.run("fake.add_player('captain', 0, 0) "
          "prototypes.entity['fast-inserter'] = { name = 'fast-inserter', type = 'inserter', tile_width = 1, tile_height = 1, items_to_place_this = { { name = 'inserter', count = 1 } } } "
          "prototypes.entity['wooden-chest'].tile_width = 1")
    return m


def save_row(mod, name="gear-cell"):
    return mod.result("design_save", {"name": name, "description": "one gear machine fed from a belt", "pieces": ROW, "note": "first"})


def ghosts(mod):
    return mod.run("local n = 0 for _, e in ipairs(game.surfaces.nauvis.entities) do if e.valid and e.type == 'entity-ghost' then n = n + 1 end end return n")


def test_a_design_written_from_pieces_is_listed_with_its_cost(mod):
    r = save_row(mod)
    assert (r["version"], r["kind"], r["pieces"]) == (1, "written", 3)
    d = mod.result("designs")["designs"][0]
    assert d["name"] == "gear-cell" and d["version"] == 1 and d["deployments"] == 0
    assert {c["item"] for c in d["cost"]} == {"assembling-machine-2", "inserter", "transport-belt"}
    assert "needs a description" in mod.call("design_save", {"name": "new", "pieces": ROW})["error"]
    assert "library is empty" not in str(mod.result("designs"))


def test_capture_from_the_map_and_import_export_round_trip(mod):
    mod.place("assembling-machine-2", 10.5, 10.5, recipe="iron-gear-wheel")
    mod.place("inserter", 10.5, 12.5)
    r = mod.result("design_save", {"name": "captured", "description": "taken off the map", "x": 9, "y": 9, "width": 4, "height": 5})
    assert r["kind"] == "capture" and r["pieces"] == 2
    text = mod.result("design_export", {"name": "captured"})["string"]
    r = mod.result("design_save", {"name": "imported", "description": "the same, by string", "string": text})
    assert r["kind"] == "import" and r["pieces"] == 2
    assert "not a blueprint" in mod.call("design_save", {"name": "bad", "description": "x", "string": "nonsense"})["error"]
    assert "nothing of ours" in mod.call("design_save", {"name": "empty", "description": "x", "x": 50, "y": 50, "width": 3, "height": 3})["error"]


def test_deploy_is_a_dry_run_first_then_ghosts_tagged_with_their_deployment(mod):
    save_row(mod)
    r = mod.result("design_deploy", {"name": "gear-cell", "x": 20, "y": 20})
    assert r["would_place"] == 3 and "failed" not in r and ghosts(mod) == 0
    r = mod.result("design_deploy", {"name": "gear-cell", "x": 20, "y": 20, "dry_run": False})
    assert r["deployment"] == 1 and r["ghosts"] == 3 and ghosts(mod) == 3
    w = mod.result("what_is", {"x": 20, "y": 20})                                     # the inserter's tile
    assert w["name"] == "inserter" and w["ghost"] and w["design"]["name"] == "gear-cell" and w["design"]["deployment"] == 1
    assert mod.result("deployments")["deployments"][0]["behind"] is False


def test_a_blocked_spot_places_nothing(mod):
    save_row(mod)
    mod.place("steel-chest", 20.5, 20.5)                                               # where the inserter would go
    r = mod.result("design_deploy", {"name": "gear-cell", "x": 20, "y": 20, "dry_run": False})
    assert r["failed"][0]["name"] == "inserter" and ghosts(mod) == 0 and not mod.result("deployments")["deployments"]


def test_facing_turns_the_whole_design(mod):
    save_row(mod)
    mod.result("design_deploy", {"name": "gear-cell", "x": 0, "y": 0, "facing": "south", "dry_run": False})
    belt = mod.run("for _, e in ipairs(game.surfaces.nauvis.entities) do if e.ghost_name == 'transport-belt' then return e.position.x .. ',' .. e.position.y .. ',' .. e.direction end end")
    assert belt == "-0.5,-1.5,12"                                                     # offset turned half round, east turned to west


def test_build_now_over_water_says_landfill_comes_first(mod):
    """Found live 2026-11-21: on a fresh map the site was a lake, and the note blamed trees that were not there."""
    save_row(mod)
    mod.run("fake.water = true")
    r = mod.result("design_deploy", {"name": "gear-cell", "x": 20, "y": 20, "dry_run": False, "build_now": True})
    assert r["ghosts"] == 3 and "landfill" in r["waiting"] and "trees" not in r["waiting"], r


def test_an_edit_makes_a_version_and_redeploy_rolls_it_out_by_upgrade_orders(mod):
    save_row(mod)
    mod.result("design_deploy", {"name": "gear-cell", "x": 20, "y": 20, "dry_run": False, "build_now": True})
    r = mod.result("design_edit", {"name": "gear-cell", "replace": {"inserter": "fast-inserter"}, "note": "faster feed"})
    assert r["version"] == 2 and r["buildings_swapped"] == 1 and r["deployments_behind"] == 1
    assert mod.result("designs", {"name": "gear-cell"})["designs"][0]["versions"][0]["note"] == "faster feed"
    plan = mod.result("design_redeploy", {"deployment": 1})
    assert plan["how"] == "upgrade" and plan["upgrade_orders"] == 1
    r = mod.result("design_redeploy", {"deployment": 1, "dry_run": False})
    assert r["planner"].startswith("0fake:")
    assert mod.run("for _, e in ipairs(game.surfaces.nauvis.entities) do if e.valid and e.name == 'inserter' then return e.upgrade_target end end") == "fast-inserter"
    assert mod.result("deployments")["deployments"][0]["version"] == 2
    assert "not the same size" in mod.call("design_edit", {"name": "gear-cell", "replace": {"inserter": "assembling-machine-2"}, "note": "x"})["error"]


def test_a_new_layout_clears_the_whole_footprint_and_rebuilds(mod):
    save_row(mod)
    mod.result("design_deploy", {"name": "gear-cell", "x": 20, "y": 20, "dry_run": False, "build_now": True})
    mod.place("pipe", 19.5, 20.5)                                                      # something left inside the footprint
    mod.place("pipe", 30.5, 30.5)                                                      # and something well outside it
    smaller = [p for p in ROW if p["name"] != "inserter"]
    assert mod.result("design_save", {"name": "gear-cell", "pieces": smaller, "note": "robots feed it"})["version"] == 2
    plan = mod.result("design_redeploy", {"deployment": 1})
    assert plan["how"] == "rebuild" and plan["deconstruct"] == 4 and plan["cleared"]["pipe"] == 1
    mod.result("design_redeploy", {"deployment": 1, "dry_run": False})
    marked = mod.run("local n = {} for _, e in ipairs(game.surfaces.nauvis.entities) do if e.to_be_deconstructed then n[#n + 1] = e.name end end table.sort(n) return table.concat(n, ',')")
    assert marked == "assembling-machine-2,inserter,pipe,transport-belt"               # the old inserter goes too: no leftovers
    assert ghosts(mod) == 2 and mod.result("deployments")["deployments"][0]["version"] == 2


def test_rollback_and_undeploy(mod):
    save_row(mod)
    mod.result("design_deploy", {"name": "gear-cell", "x": 20, "y": 20, "dry_run": False})
    mod.result("design_edit", {"name": "gear-cell", "recipes": {"iron-gear-wheel": "copper-cable"}, "note": "cable instead"})
    mod.result("design_redeploy", {"deployment": 1, "dry_run": False})
    back = mod.result("design_redeploy", {"deployment": 1, "version": 1})
    assert back["how"] == "rebuild"                                                    # going back is a rebuild
    r = mod.result("design_undeploy", {"deployment": 1, "dry_run": False})
    assert r["ghosts_removed"] == 3 and ghosts(mod) == 0 and not mod.result("deployments")["deployments"]


def test_tiling_makes_a_grid_fixed_to_the_map_and_skips_what_collides(mod):
    mod.result("design_save", {"name": "pole", "description": "one pole", "pieces": [{"name": "medium-electric-pole", "x": 0.5, "y": 0.5}]})
    r = mod.result("design_tile", {"name": "pole", "x": 0, "y": 0, "width": 30, "height": 1, "step_x": 7})
    assert r["copies"] == 5 and r["would_place"] == 5                                   # at x 0, 7, 14, 21, 28
    mod.place("steel-chest", 14.5, 0.5)
    r = mod.result("design_tile", {"name": "pole", "x": 0, "y": 0, "width": 30, "height": 1, "step_x": 7, "dry_run": False})
    assert r["placed"] == 4 and r["skipped_count"] == 1 and r["skipped"][0]["x"] == 14
    assert len(mod.result("deployments", {"name": "pole"})["deployments"]) == 4


def test_advise_mode_allows_only_dry_runs_and_build_now_needs_the_allowance(mod):
    save_row(mod)
    mod.result("set_allowance", {"id": "free-placement", "on": False})
    assert "build_now" in mod.call("design_deploy", {"name": "gear-cell", "x": 20, "y": 20, "dry_run": False, "build_now": True})["error"]
    mod.result("set_mode", {"mode": "advise"})
    assert "advise mode" in mod.call("design_deploy", {"name": "gear-cell", "x": 20, "y": 20, "dry_run": False})["error"]
    assert mod.result("design_deploy", {"name": "gear-cell", "x": 20, "y": 20})["would_place"] == 3


def test_deploy_at_a_named_place(mod):
    save_row(mod)
    mod.result("mark_place", {"name": "gear site", "x": 40, "y": 40})
    r = mod.result("design_deploy", {"name": "gear-cell", "at": "gear site", "dry_run": False})
    assert r["x"] == 40 and mod.result("deployments")["deployments"][0]["at"] == "gear site"
    assert mod.result("what_is", {"x": 40, "y": 40})["nearest_place"]["name"] == "gear site"


def test_a_piece_built_by_robots_keeps_its_deployment(mod):
    save_row(mod)
    mod.result("design_deploy", {"name": "gear-cell", "x": 20, "y": 20, "dry_run": False})
    mod.run("local g for _, e in ipairs(game.surfaces.nauvis.entities) do if e.ghost_name == 'inserter' then g = e end end "
            "local tags = g.tags local _, built = g.revive() "
            "fake.handlers[defines.events.on_robot_built_entity] { entity = built, tags = tags }")
    w = mod.result("what_is", {"x": 20, "y": 20})
    assert w["name"] == "inserter" and not w.get("ghost") and w["design"]["deployment"] == 1
