#!/usr/bin/env python3
"""Checks the Skippy Copilot mod against the local test server: builds a small known scene and asserts what each tool says
about it. The first piece of the scoring harness: a tool that answers wrongly fails here, before a model ever sees it.
Start the server first (scripts/modserver.sh start). Usage: modcheck.py"""
import sys

from modtest import call, client

SCENE = ("local s=game.surfaces.nauvis local f='player' for _,e in pairs(s.find_entities_filtered{area={{-20,-12},{20,12}}}) do e.destroy() end "
         "s.create_entity{name='assembling-machine-2',position={3.5,1.5},force=f,recipe='iron-gear-wheel'} "
         "for x=0,10 do s.create_entity{name='transport-belt',position={x+0.5,4.5},direction=defines.direction.east,force=f} end "
         "s.create_entity{name='inserter',position={3.5,3.5},direction=defines.direction.south,force=f} "
         "s.create_entity{name='electric-mining-drill',position={-8.5,-3.5},force=f} "
         "for x=-10,-6 do for y=-6,-2 do s.create_entity{name='iron-ore',position={x+0.5,y+0.5},amount=500} end end "
         "local t={} for x=12,16 do for y=-8,-5 do t[#t+1]={name='water',position={x,y}} end end s.set_tiles(t) "
         "s.create_entity{name='entity-ghost',inner_name='lab',position={0.5,-6.5},force=f} rcon.print('scene')")
fails = []


def check(name, cond, detail=""):
    print("ok  " if cond else "FAIL", name, "" if cond else detail)
    if not cond:
        fails.append(name)


def main():
    c = client()
    c.send_command("/sc game.forces.player.research_all_technologies()")      # the first /sc on a server only warns; this one is spent on it
    c.send_command("/sc game.forces.player.research_all_technologies()")
    check("scene built", (c.send_command("/sc " + SCENE) or "").strip() == "scene")
    t = call("tools", None, c)
    names = [x["name"] for x in t["result"]]
    check("tool list", all(n in names for n in ["lookup", "search", "map", "tile", "find_free", "diagnose", "chat_read", "say", "set_state", "events_read", "design_note", "alerts", "player", "bottlenecks", "occupancy", "build", "frames", "reveal_map", "avatar", "avatar_walk", "avatar_mine", "avatar_stop", "avatar_craft", "avatar_carry", "set_mode", "lock_mode", "avatar_travel", "progress"]), names)
    check("every tool is described", all(x["description"] and isinstance(x["parameters"], (dict, list)) for x in t["result"]))

    r = call("lookup", {"name": "electronic-circuit", "kind": "recipe"}, c)["result"][0]
    check("recipe ingredients", {i["name"]: i["amount"] for i in r["ingredients"]} == {"iron-plate": 1, "copper-cable": 3}, r["ingredients"])
    check("recipe made in", "assembling-machine-1" in r["made_in"] and "electromagnetic-plant" in r["made_in"], r["made_in"])
    r = call("lookup", {"name": "assembling-machine-2", "kind": "entity"}, c)["result"][0]
    check("entity size and speed", (r["tiles_wide"], r["tiles_high"], r["crafting_speed"]) == (3, 3, 0.75), r)
    r = call("lookup", {"name": "heating-tower", "kind": "entity"}, c)["result"][0]
    check("heat connections", len(r["heat"]["connections"]) == 4, r.get("heat"))
    r = call("lookup", {"name": "cryogenic-science-pack", "kind": "technology"}, c)["result"][0]
    check("trigger technology", r["earned_by"]["item"] == "cryogenic-plant", r)
    r = call("lookup", {"name": "circut"}, c)
    check("misspelt name gives similar names", not r["ok"] and any(s["name"] == "electronic-circuit" for s in r.get("similar", [])), r)
    r = call("nope", None, c)
    check("unknown tool lists the tools", not r["ok"] and "lookup" in r["tools"], r)
    r = call("lookup", {"nam": "x"}, c)
    check("unknown parameter shows the tool", not r["ok"] and r["tool"]["name"] == "lookup", r)
    r = call("lookup", {"name": 5}, c)
    check("wrong type is refused", not r["ok"] and "must be a string" in r["error"], r)

    m = call("map", {"x": -16, "y": -10, "width": 36, "height": 18}, c)["result"]
    rows = {int(line[:4]): line[5:] for line in m["picture"].split("\n")[2:]}
    def at(x, y):
        return rows[y][x - m["left_x"]]
    check("map: machine", at(2, 0) == "A" and at(4, 2) == "A" and at(5, 0) == ".", rows[0])
    check("map: belt and inserter", at(0, 4) == "b" and at(10, 4) == "b" and at(11, 4) == "." and at(3, 3) == "i", rows[4])
    check("map: drill over ore", at(-9, -4) == "M" and at(-6, -6) == ":", rows[-4])
    check("map: water and ghost", at(12, -8) == "~" and at(0, -7) == "?", rows[-8])
    check("map: legend names what is here", any(e["char"] == "A" and e["here"] == ["assembling-machine-2 x1"] for e in m["legend"]), m["legend"])
    check("map: window is capped", call("map", {"x": 0, "y": 0, "width": 500, "height": 500}, c)["result"]["width"] == 60)

    r = call("tile", {"x": 3, "y": 1}, c)["result"]
    check("tile: machine with recipe and state", r["things"][0]["recipe"] == "iron-gear-wheel" and r["things"][0]["state"] == "no_power" and not r["free"], r)
    check("tile: free ground", call("tile", {"x": 15, "y": 8}, c)["result"]["free"] is True)
    check("tile: water is not free", call("tile", {"x": 13, "y": -6}, c)["result"]["free"] is False)
    r = call("find_free", {"x": 3, "y": 1, "width": 6, "height": 4}, c)["result"]
    ok = r["found"]
    if ok:
        for x in range(r["left_x"], r["left_x"] + 6):
            for y in range(r["top_y"], r["top_y"] + 4):
                ok = ok and call("tile", {"x": x, "y": y}, c)["result"]["free"]
    check("find_free: every tile of the answer is free", ok, r)
    r = call("diagnose", None, c)["result"]
    states = {p["state"]: p["count"] for p in r["problems"]}
    check("diagnose: unpowered machines", states.get("no_power") == 2, states)

    before = call("events_read", None, c)["result"]["last_id"]
    c.send_command("/sc local t=game.forces.player.technologies['automation-2'] t.researched=false t.researched=true")
    ev = call("events_read", {"after": before}, c)["result"]["events"]
    check("research news carries unlocks and a design note", len(ev) == 1 and ev[0]["technology"] == "automation-2" and "assembling-machine-2" in ev[0]["unlocks_recipes"] and "half again" in ev[0]["design_note"], ev)
    r = call("design_note", {"technology": "logistic-robotics"}, c)["result"]
    check("design note by name", "robots" in r["design_note"], r)
    import pathlib, re
    noted = re.findall(r'^  \["([a-z0-9-]+)"\] = ', (pathlib.Path(__file__).resolve().parent.parent / "mods/skippy-copilot/scripts/notes.lua").read_text(encoding="utf-8"), re.M)
    bad = [n for n in noted if not call("lookup", {"name": n, "kind": "technology"}, c)["ok"]]
    check("every design note names a real technology (%d notes)" % len(noted), len(noted) > 20 and not bad, bad)
    # ---- added with mod 0.3.0, written without a server to run them on: first run is the test of these checks too ----
    r = call("alerts", None, c)
    check("alerts: answers with no player in the game", r["ok"] and "alerts" in r["result"], r)
    r = call("player", None, c)
    check("player: says so when nobody is in the game", not r["ok"] or "name" in r["result"], r)
    r = call("frames", None, c)
    check("frames: says so when nobody is in the game", (not r["ok"] and "no player" in r["error"]) or "view" in r.get("result", {}), r)
    r = call("occupancy", {"x": -16, "y": -10, "width": 36, "height": 18}, c)["result"]
    def occ(x, y):
        return r["rows"][y + 10][x + 16]
    check("occupancy: machine, belt and water block; ore and free ground do not", occ(3, 1) == "#" and occ(5, 4) == "#" and occ(13, -6) == "#" and occ(-6, -6) == "." and occ(15, 8) == ".", r["rows"])
    c.send_command("/sc game.surfaces.nauvis.create_entity{name='pipe',position={-14.5,6.5},force='player'}")
    check("occupancy: a pipe is marked as a pipe", call("occupancy", {"x": -16, "y": -10, "width": 36, "height": 18}, c)["result"]["rows"][16][1] == "p")
    r = call("bottlenecks", None, c)["result"]
    check("bottlenecks: unpowered machines are put first", "power_first" in r and "fix power" in r["power_first"], r)
    piece = [{"name": "transport-belt", "x": 15.5, "y": 8.5, "direction": 4}]
    r = call("build", {"entities": piece}, c)["result"]
    check("build: a dry run places nothing", r["would_place"] == 1 and call("tile", {"x": 15, "y": 8}, c)["result"]["free"], r)
    r = call("build", {"entities": [{"name": "transport-belt", "x": 3.5, "y": 1.5, "direction": 4}]}, c)["result"]
    check("build: a piece on top of a machine is refused with a reason", r["failed_count"] == 1 and "in the way" in r["failed"][0]["why"], r)
    r = call("build", {"entities": [{"name": "warp-drive", "x": 15.5, "y": 8.5}]}, c)["result"]
    check("build: an unknown name is refused", "no building named" in r["failed"][0]["why"], r)
    r = call("build", {"entities": piece + [{"name": "transport-belt", "x": 3.5, "y": 1.5, "direction": 4}], "dry_run": False}, c)["result"]
    check("build: nothing is placed when any piece fails", r["placed"] == 0 and call("tile", {"x": 15, "y": 8}, c)["result"]["free"], r)
    r = call("build", {"entities": piece, "dry_run": False}, c)["result"]
    t = call("tile", {"x": 15, "y": 8}, c)["result"]
    check("build: a clean plan is placed, facing the way asked", r["placed"] == 1 and t["things"][0]["name"] == "transport-belt" and t["things"][0]["direction"].lower() == "east", (r, t))
    c.send_command("/sc local f=game.forces.player f.recipes['lab'].enabled=false")
    r = call("build", {"entities": [{"name": "lab", "x": 15.5, "y": -1.5}]}, c)["result"]
    check("build: nothing before it is researched", "not researched" in r["failed"][0]["why"], r)
    c.send_command("/sc game.forces.player.recipes['lab'].enabled=true")
    r = call("reveal_map", {"depth": 64}, c)
    check("reveal_map: the known map grows", r["ok"] and r["result"]["now"][0] < r["result"]["was"][0], r)

    # ---- the avatar (mod 0.4.0): real pathfinder, real walking; these wait in real time ----
    import time
    def wait_job(limit=90):
        for _ in range(limit * 2):
            st = call("avatar", None, c)["result"]
            if not st.get("job"):
                return st
            time.sleep(0.5)
        return call("avatar", None, c)["result"]
    r = call("avatar_walk", {"x": 15, "y": 9}, c)
    check("modes: the avatar does not move in free-hand mode", not r["ok"] and "free-hand" in r["error"], r)
    check("modes: switching to my-character", call("set_mode", {"mode": "my-character"}, c)["result"]["changed"] is True)
    r = call("avatar_walk", {"x": 15, "y": 9}, c)
    check("avatar: a walk starts", r["ok"] and "job" in r["result"], r)
    st = wait_job()
    check("avatar: it arrives on foot", st["last_job"]["ok"] and abs(st["x"] - 15) <= 2 and abs(st["y"] - 9) <= 2 and st["last_job"]["ticks"] > 30, st)
    check("avatar: reach is the game's own", st["reach"]["build"] > 0 and st["reach"]["mine"] > 0, st.get("reach"))
    r = call("avatar_mine", {"x": -6, "y": -2, "count": 2}, c)
    check("avatar: mining starts on ore", r["ok"] and r["result"]["gives"] == "iron-ore", r)
    st = wait_job()
    check("avatar: it carries what it mined", st["last_job"]["ok"] and st.get("carries", {}).get("iron-ore") == 2, st)
    r = call("build", {"entities": [{"name": "transport-belt", "x": 18.5, "y": 9.5, "direction": 4}]}, c)["result"]
    check("avatar: a dry run says what it must carry", r.get("avatar_lacks") == {"transport-belt": 1}, r)
    c.send_command("/sc local b = game.surfaces.nauvis.find_entities_filtered{type='character'}[1] b.get_main_inventory().insert{name='transport-belt', count=1}")
    r = call("build", {"entities": [{"name": "transport-belt", "x": 18.5, "y": 9.5, "direction": 4}], "dry_run": False}, c)["result"]
    st = wait_job()
    t = call("tile", {"x": 18, "y": 9}, c)["result"]
    check("avatar: it builds by hand from its inventory", r.get("queued") == 1 and st["last_job"]["ok"] and t["things"] and t["things"][0]["name"] == "transport-belt", (r, st.get("last_job"), t))
    check("modes: back to free-hand", call("set_mode", {"mode": "free-hand"}, c)["result"]["mode"] == "free-hand")
    p = call("progress", {"items": ["iron-plate"], "entities": ["transport-belt", "lab"]}, c)
    check("progress: facts for milestones", p["ok"] and p["result"]["built"]["transport-belt"] >= 1 and "researched" in p["result"] and p["result"]["won"] is False, p)
    r = call("avatar_travel", {"planet": "vulcanus"}, c)
    check("travel: refused in free-hand mode", not r["ok"], r)

    check("say", call("say", {"text": "check"}, c)["ok"])
    check("set_state", call("set_state", {"state": "working", "note": "check"}, c)["ok"] and not call("set_state", {"state": "napping"}, c)["ok"])
    check("chat_read", "last_id" in call("chat_read", None, c)["result"])
    print("\n%d failed" % len(fails) if fails else "\nall checks passed")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
