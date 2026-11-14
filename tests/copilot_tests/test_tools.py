import copilot.__main__ as main
from copilot.agent import Agent
from copilot.tools import LocalTools
from fakes import TOOLS, FakeGame, FakeModel


def item(name, made_by):
    return {"kind": "item", "name": name, "made_by_recipes": made_by}


def recipe(name, seconds, ingredients, products, made_in, available=True):
    return {"kind": "recipe", "name": name, "seconds": seconds, "available_now": available, "made_in": made_in,
            "ingredients": [{"name": n, "type": "item", "amount": a} for n, a in ingredients],
            "products": [{"name": n, "type": "item", "amount": a} for n, a in products]}


ASSEMBLERS = ["assembling-machine-1", "assembling-machine-2"]
BOOK = {
    ("automation-science-pack", "item"): item("automation-science-pack", ["automation-science-pack"]),
    ("automation-science-pack", "recipe"): recipe("automation-science-pack", 5, [("copper-plate", 1), ("iron-gear-wheel", 1)], [("automation-science-pack", 1)], ASSEMBLERS),
    ("iron-gear-wheel", "item"): item("iron-gear-wheel", ["iron-gear-wheel"]),
    ("iron-gear-wheel", "recipe"): recipe("iron-gear-wheel", 0.5, [("iron-plate", 2)], [("iron-gear-wheel", 1)], ASSEMBLERS),
    ("iron-plate", "item"): item("iron-plate", ["casting-iron", "iron-plate"]),
    ("iron-plate", "recipe"): recipe("iron-plate", 3.2, [("iron-ore", 1)], [("iron-plate", 1)], ["stone-furnace"]),
    ("copper-plate", "item"): item("copper-plate", ["copper-plate"]),
    ("copper-plate", "recipe"): recipe("copper-plate", 3.2, [("copper-ore", 1)], [("copper-plate", 1)], ["stone-furnace"], available=False),
    ("iron-ore", "item"): item("iron-ore", None),
    ("copper-ore", "item"): item("copper-ore", None),
    ("assembling-machine-1", "entity"): {"kind": "entity", "name": "assembling-machine-1", "tiles_wide": 3, "tiles_high": 3, "crafting_speed": 0.5},
    ("assembling-machine-2", "entity"): {"kind": "entity", "name": "assembling-machine-2", "tiles_wide": 3, "tiles_high": 3, "crafting_speed": 0.75},
    ("stone-furnace", "entity"): {"kind": "entity", "name": "stone-furnace", "tiles_wide": 2, "tiles_high": 2, "crafting_speed": 1},
}


def lookup(args):
    hit = BOOK.get((args["name"], args.get("kind")))
    return {"ok": True, "result": [hit]} if hit else {"ok": False, "error": "nothing is named '%s'" % args["name"], "hint": "try search"}


def game(rows=None, build=None):
    results = {"lookup": lookup}
    if rows is not None:
        results["occupancy"] = {"ok": True, "result": {"rows": rows}}
    results["build"] = build or (lambda a: {"ok": True, "result": {"placed": 0 if a["dry_run"] else len(a["entities"]), "would_place": len(a["entities"]), "failed": []}})
    return FakeGame(results)


def test_production_plan_for_red_science():
    r = LocalTools(game()).call("plan_production", {"item": "automation-science-pack", "per_minute": 60})
    assert r["ok"], r
    steps = {s["make"]: s for s in r["result"]["steps"]}
    assert steps["automation-science-pack"]["machines"] == 10 and steps["automation-science-pack"]["machine"] == "assembling-machine-1"
    assert steps["iron-gear-wheel"]["machines"] == 1 and steps["iron-plate"]["machine"] == "stone-furnace"
    assert steps["iron-plate"]["machines"] == 7                               # 2 plates a second at 3.2 s each
    assert r["result"]["supplied_per_minute"] == {"copper-ore": 60, "iron-ore": 120}
    assert r["result"]["not_yet_researched"] == ["copper-plate"]


def test_production_plan_with_a_faster_machine_and_supplied_plates():
    r = LocalTools(game()).call("plan_production", {"item": "automation-science-pack", "per_minute": 60, "machine": "assembling-machine-2", "stop_at": "iron-plate, copper-plate"})
    steps = {s["make"]: s for s in r["result"]["steps"]}
    assert steps["automation-science-pack"]["machines"] == 7 and set(steps) == {"automation-science-pack", "iron-gear-wheel"}
    assert r["result"]["supplied_per_minute"] == {"copper-plate": 60, "iron-plate": 120}
    assert r["result"]["basic_belts_needed"]["iron-plate"] == round(2 / 15, 2)


def test_production_plan_refusals():
    t = LocalTools(game())
    assert "raw input" in t.call("plan_production", {"item": "iron-ore", "per_minute": 10})["error"]
    assert "above zero" in t.call("plan_production", {"item": "iron-gear-wheel", "per_minute": 0})["error"]
    assert "needs the parameter 'per_minute'" in t.call("plan_production", {"item": "iron-gear-wheel"})["error"]
    r = t.call("plan_production", {"item": "iron-gear-wheel", "per_minut": 5})
    assert "no parameter 'per_minut'" in r["error"] and r["tool"]["name"] == "plan_production"


def test_plan_row_makes_a_picture_and_keeps_the_plan():
    t = LocalTools(game())
    r = t.call("plan_row", {"machine": "assembling-machine-1", "count": 3, "x": 10, "y": 20, "recipe": "iron-gear-wheel"})["result"]
    assert r["picture"].split("\n") == ["bbbbbbbbb", ".i..i..i.", "MMMMMMMMM", "MMMMMMMMM", "MMMMMMMMM", ".i..i..i.", "bbbbbbbbb"]
    assert r["covers"] == {"from_x": 10, "from_y": 20, "to_x": 18, "to_y": 26} and r["pieces"]["assembling-machine-1"] == 3
    ents = t.plans[r["plan_id"]]["entities"]
    m = [e for e in ents if e["name"] == "assembling-machine-1"][0]
    assert (m["x"], m["y"], m["recipe"]) == (11.5, 23.5, "iron-gear-wheel")


def test_plan_row_turned_east_and_fed_by_robots():
    t = LocalTools(game())
    r = t.call("plan_row", {"machine": "stone-furnace", "count": 2, "x": 0, "y": 0, "feed": "robots", "facing": "east"})["result"]
    assert r["covers"] == {"from_x": 0, "from_y": 0, "to_x": 5, "to_y": 3}          # 2-tile furnaces, chests east and west
    assert r["pieces"] == {"requester-chest": 2, "inserter": 4, "stone-furnace": 2, "passive-provider-chest": 2}
    req = [e for e in t.plans[r["plan_id"]]["entities"] if e["name"] == "requester-chest"]
    assert all(e["x"] == 5.5 for e in req)                                         # the requesters are on the east side


def test_plan_row_refusals():
    t = LocalTools(game())
    assert "cannot run the recipe" in t.call("plan_row", {"machine": "stone-furnace", "count": 2, "x": 0, "y": 0, "recipe": "iron-gear-wheel"})["error"]
    assert "between 1 and 50" in t.call("plan_row", {"machine": "stone-furnace", "count": 0, "x": 0, "y": 0})["error"]
    assert "facing" in t.call("plan_row", {"machine": "stone-furnace", "count": 1, "x": 0, "y": 0, "facing": "up"})["error"]
    assert "nothing is named" in t.call("plan_row", {"machine": "assembler", "count": 1, "x": 0, "y": 0})["error"]


def open_rows(width, height, wall_x=None, pipes=()):
    rows = []
    for j in range(height):
        rows.append("".join("p" if (i, j) in pipes else ("#" if wall_x is not None and i == wall_x else ".") for i in range(width)))
    return rows


def test_plan_route_reads_the_map_and_dives_under_a_wall():
    # window: left = 0-12 = -12, so the wall at window column 14 is map x = 2
    g = game(open_rows(29, 25, wall_x=14))
    t = LocalTools(g)
    r = t.call("plan_route", {"kind": "belt", "from_x": 0, "from_y": 0, "to_x": 4, "to_y": 0})
    assert r["ok"], r
    assert g.named("occupancy") == [{"x": -12, "y": -12, "width": 29, "height": 25}]
    assert r["result"]["tiles"] == 5 and r["result"]["underground_pairs"] == 1
    ents = t.plans[r["result"]["plan_id"]]["entities"]
    assert [(e["x"], e["name"], e.get("type")) for e in ents] == [(0.5, "transport-belt", None), (1.5, "underground-belt", "input"),
                                                                 (3.5, "underground-belt", "output"), (4.5, "transport-belt", None)]


def test_plan_route_for_a_pipe_keeps_clear_of_other_pipes():
    pipes = {(i, 14) for i in range(29)}                                           # an old pipe line along map y = 2
    t = LocalTools(game(open_rows(29, 29, pipes=pipes)))
    r = t.call("plan_route", {"kind": "pipe", "from_x": 0, "from_y": 0, "to_x": 0, "to_y": 4})
    assert r["ok"], r
    names = [(e["y"], e["name"]) for e in t.plans[r["result"]["plan_id"]]["entities"]]
    assert names == [(0.5, "pipe-to-ground"), (4.5, "pipe-to-ground")]             # nothing plain beside the old line


def test_plan_route_refusals():
    t = LocalTools(game(open_rows(29, 25)))
    assert "too far apart" in t.call("plan_route", {"kind": "belt", "from_x": 0, "from_y": 0, "to_x": 200, "to_y": 0})["error"]
    assert "'belt' or 'pipe'" in t.call("plan_route", {"kind": "rail", "from_x": 0, "from_y": 0, "to_x": 2, "to_y": 0})["error"]
    assert "no underground piece" in t.call("plan_route", {"kind": "belt", "from_x": 0, "from_y": 0, "to_x": 2, "to_y": 0, "item": "wooden-belt"})["error"]
    g = FakeGame({"occupancy": {"ok": False, "error": "there is no surface named 'mars'"}})
    assert "no surface" in LocalTools(g).call("plan_route", {"kind": "belt", "from_x": 0, "from_y": 0, "to_x": 2, "to_y": 0, "surface": "mars"})["error"]


def test_a_plan_must_pass_a_dry_run_before_it_is_built_and_is_built_once():
    g = game()
    t = LocalTools(g)
    pid = t.call("plan_row", {"machine": "assembling-machine-1", "count": 1, "x": 0, "y": 0})["result"]["plan_id"]
    assert "not passed a dry run" in t.call("build_plan", {"plan_id": pid, "dry_run": False})["error"]
    assert g.named("build") == []
    dry = t.call("build_plan", {"plan_id": pid})
    assert dry["ok"] and dry["result"]["dry_run"] is True and g.named("build")[0]["dry_run"] is True
    real = t.call("build_plan", {"plan_id": pid, "dry_run": False})
    assert real["ok"] and real["result"]["placed"] == len(t.plans[pid]["entities"])
    assert "not passed a dry run" in t.call("build_plan", {"plan_id": pid, "dry_run": False})["error"]     # not twice
    assert "no plan with the id" in t.call("build_plan", {"plan_id": "plan-99"})["error"]


def test_a_failed_dry_run_does_not_unlock_building():
    g = game(build=lambda a: {"ok": True, "result": {"would_place": 3, "failed": [{"name": "inserter", "x": 1.5, "y": 1.5, "why": "something is in the way"}]}})
    t = LocalTools(g)
    pid = t.call("plan_row", {"machine": "assembling-machine-1", "count": 1, "x": 0, "y": 0})["result"]["plan_id"]
    assert t.call("build_plan", {"plan_id": pid})["result"]["failed"]
    assert "not passed a dry run" in t.call("build_plan", {"plan_id": pid, "dry_run": False})["error"]


ALERT_TOOL = {"name": "alerts", "description": "alerts", "parameters": {}}
RAW = [{"name": "build", "description": "b", "parameters": {}}, {"name": "occupancy", "description": "o", "parameters": {}}]


class GameWithAlerts(FakeGame):
    def tools(self):
        return TOOLS + [ALERT_TOOL] + RAW


def test_the_model_gets_planning_tools_but_not_the_raw_build_call():
    g = GameWithAlerts({"lookup": lookup})
    agent = Agent(g, FakeModel(["ok"]), local=LocalTools(g))
    assert {"plan_production", "plan_row", "plan_route", "build_plan", "lookup", "alerts"} <= agent.names
    assert not {"build", "occupancy", "say"} & agent.names


def test_a_planning_call_is_answered_by_the_bridge_not_the_game():
    g = GameWithAlerts({"lookup": lookup})
    agent = Agent(g, FakeModel([[("plan_production", {"item": "iron-gear-wheel", "per_minute": 60})], "One machine."]), local=LocalTools(g))
    answer, outcome, stats = agent.handle("how many gear machines for 60 a minute?", light=False)
    assert answer == "One machine." and stats["misses"] == 0 and g.named("plan_production") == []
    assert '"machines": 1' in agent.model.seen[1][-1]["content"]


def test_every_turn_starts_with_the_alerts_showing():
    alerts = {"ok": True, "result": {"alerts": [{"surface": "nauvis", "kind": "no_material_for_construction", "count": 4, "means": "robots lack the item"},
                                              {"surface": "gleba", "kind": "entity_destroyed", "count": 1}]}}
    g = GameWithAlerts({"alerts": alerts})
    agent = Agent(g, FakeModel(["ok"]))
    agent.handle("hello", light=False)
    first = agent.model.seen[0][1]["content"]
    assert first.startswith("hello") and "no_material_for_construction x4 on nauvis (robots lack the item)" in first and "entity_destroyed x1 on gleba" in first
    text, kinds = agent.alerts()
    assert kinds == {("nauvis", "no_material_for_construction"), ("gleba", "entity_destroyed")}


def test_no_alerts_adds_nothing_and_a_mod_without_the_tool_is_fine():
    g = GameWithAlerts({"alerts": {"ok": True, "result": {"alerts": {}}}})
    agent = Agent(g, FakeModel(["ok"]))
    agent.handle("hello", light=False)
    assert agent.model.seen[0][1]["content"] == "hello"
    plain = Agent(FakeGame(), FakeModel(["ok"]))
    assert plain.alerts() == ("", set()) and FakeGame().named("alerts") == []


def test_an_alert_is_raised_once_and_again_only_after_it_cleared():
    w = main.AlertWatch()
    a, b = ("nauvis", "no_power"), ("nauvis", "turret_out_of_ammo")
    assert w.new({a}) == {a}
    assert w.new({a}) == set()
    assert w.new({a, b}) == {b}
    assert w.new(set()) == set()
    assert w.new({a}) == {a}                                                       # it went away and came back


def test_alert_prompt_names_the_new_kinds():
    p = main.alert_prompt({("nauvis", "no_power")}, "Alerts showing in the game right now: no_power x3 on nauvis.")
    assert "no_power on nauvis" in p and "x3" in p and "nothing" in p


def test_locate_turns_words_into_tiles_from_the_frames_the_game_gives():
    frames = {"ok": True, "result": {"surface": "nauvis", "view": [-40, -22, 39, 22], "base": [-300, -200, 299, 199], "map": [-1000, -1000, 999, 999], "player": [-3, -22, 27, 8]}}
    t = LocalTools(FakeGame({"frames": frames}))
    r = t.call("locate", {"frame": "base", "part": "east"})["result"]
    assert (r["from_x"], r["to_x"], r["surface"]) == (100, 299, "nauvis")
    r = t.call("locate", {"frame": "view", "part": "upper right corner"})["result"]
    assert r["to_x"] == 39 and r["from_y"] == -22
    assert t.call("locate", {"frame": "view"})["result"]["part"] == "middle"
    assert "not a part I know" in t.call("locate", {"frame": "view", "part": "yonder"})["error"]
    assert "frame must be one of" in t.call("locate", {"frame": "screen"})["error"]
    assert "no player" in LocalTools(FakeGame({"frames": {"ok": False, "error": "no player is in the game"}})).call("locate", {"frame": "view"})["error"]
