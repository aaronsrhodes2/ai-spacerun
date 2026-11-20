#!/usr/bin/env python3
"""Checks the mod's designs, places and cron tools (0.20.0) and the ghost tools (0.19.0) against the local test server,
where the unit tests only had stand-ins: blueprint stacks in a script inventory, build_blueprint, ghost tags, revive,
upgrade orders, and new ghosts placed over pieces marked for deconstruction. Run after scripts/modcheck.py, on the
test server only (never the live game). Usage: nightcheck.py"""
import json
import sys
import time

from modtest import call, client

fails = []


def check(name, cond, detail=""):
    print("ok  " if cond else "FAIL", name, "" if cond else json.dumps(detail)[:400], flush=True)
    if not cond:
        fails.append(name)


def ok(tool, args=None, c=None):
    r = call(tool, args, c)
    if not r.get("ok"):
        print("     %s refused: %s" % (tool, r.get("error")), flush=True)
    return r.get("result") or {}, r


def lua(c, code):
    return (c.send_command("/sc " + code) or "").strip()


ROW = [{"name": "assembling-machine-2", "x": 41.5, "y": 41.5, "recipe": "iron-gear-wheel"},
       {"name": "inserter", "x": 41.5, "y": 43.5},
       {"name": "transport-belt", "x": 41.5, "y": 44.5, "direction": "east"}]


def main():
    c = client()
    lua(c, "rcon.print(1)")                                   # the first /sc only warns
    lua(c, "local s=game.surfaces.nauvis for _,e in pairs(s.find_entities_filtered{area={{20,20},{90,60}},force='player'}) do e.destroy() end rcon.print('clear')")
    ok("set_mode", {"mode": "free-hand"}, c)

    # ---- places
    r, raw = ok("mark_place", {"name": "night test site", "x": 40, "y": 40}, c)
    check("mark_place takes a tag on charted ground", raw.get("ok") and r["place"]["ours"], raw)
    r, _ = ok("places", {"near": "night"}, c)
    check("places reads it back", r.get("count") == 1, r)

    # ---- designs: write, deploy as ghosts, tags
    r, raw = ok("design_save", {"name": "night-gear-cell", "description": "night check: one gear machine on a belt", "pieces": ROW, "note": "v1"}, c)
    check("design_save from pieces (set_blueprint_entities)", raw.get("ok") and r.get("pieces") == 3, raw)
    r, raw = ok("design_deploy", {"name": "night-gear-cell", "at": "night test site"}, c)
    check("dry run checks every piece", raw.get("ok") and r.get("would_place") == 3 and not r.get("failed"), raw)
    r, raw = ok("design_deploy", {"name": "night-gear-cell", "at": "night test site", "dry_run": False}, c)
    check("deploy places ghosts (build_blueprint)", raw.get("ok") and r.get("ghosts") == 3, raw)
    dep = r.get("deployment")
    tags = lua(c, "local n=0 for _,g in pairs(game.surfaces.nauvis.find_entities_filtered{area={{30,30},{50,50}},type='entity-ghost'}) do if g.tags and g.tags.skippy_deployment then n=n+1 end end rcon.print(n)")
    check("ghosts carry their deployment tag", tags == "3", tags)
    gpos = lua(c, "local o={} for _,g in pairs(game.surfaces.nauvis.find_entities_filtered{area={{30,30},{50,50}},type='entity-ghost'}) do o[#o+1]=g.ghost_name..'@'..g.position.x..','..g.position.y end rcon.print(table.concat(o,' '))")
    print("     ghosts stand at:", gpos, flush=True)
    ins = [p for p in gpos.split() if p.startswith("inserter@")]
    if ins:
        x, y = (float(v) for v in ins[0].split("@")[1].split(","))
        w, _ = ok("what_is", {"x": int(x // 1), "y": int(y // 1)}, c)
        check("what_is names the design from the ghost's tags", (w.get("design") or {}).get("deployment") == dep, w)

    # ---- revive (build_now), upgrade orders
    ok("design_undeploy", {"deployment": dep, "dry_run": False}, c)
    r, raw = ok("design_deploy", {"name": "night-gear-cell", "x": 60, "y": 40, "dry_run": False, "build_now": True}, c)
    check("build_now revives the ghosts", raw.get("ok") and r.get("built_now") == 3, raw)
    dep2 = r.get("deployment")
    r, raw = ok("design_edit", {"name": "night-gear-cell", "replace": {"inserter": "fast-inserter"}, "note": "faster feed"}, c)
    check("design_edit makes version 2", raw.get("ok") and r.get("version") == 2, raw)
    r, raw = ok("design_redeploy", {"deployment": dep2, "dry_run": False}, c)
    check("redeploy by upgrade orders", raw.get("ok") and r.get("how") == "upgrade" and r.get("upgrade_orders") == 1, raw)
    up = lua(c, "for _,e in pairs(game.surfaces.nauvis.find_entities_filtered{area={{50,30},{70,50}},name='inserter'}) do local t=e.get_upgrade_target() rcon.print(t and t.name or 'none') return end rcon.print('no inserter')")
    check("the inserter is marked for upgrade (order_upgrade)", up == "fast-inserter", up)
    check("an upgrade planner string comes back", str(r.get("planner", "")).startswith("0"), r.get("planner"))

    # ---- a new layout: clear the footprint, new ghosts over it
    lua(c, "game.surfaces.nauvis.create_entity{name='pipe',position={59.5,40.5},force='player'} rcon.print('pipe')")
    two = [p for p in ROW if p["name"] != "inserter"]
    ok("design_save", {"name": "night-gear-cell", "pieces": two, "note": "v3: robots feed it"}, c)
    r, raw = ok("design_redeploy", {"deployment": dep2}, c)
    check("a changed layout plans a rebuild", raw.get("ok") and r.get("how") == "rebuild", raw)
    print("     would clear:", r.get("cleared"), flush=True)
    r, raw = ok("design_redeploy", {"deployment": dep2, "dry_run": False}, c)
    state = lua(c, "local o={} for _,e in pairs(game.surfaces.nauvis.find_entities_filtered{area={{50,30},{70,50}},force='player'}) do "
                   "o[#o+1]=(e.type=='entity-ghost' and ('ghost:'..e.ghost_name) or e.name)..(e.type~='entity-ghost' and e.to_be_deconstructed() and ':marked' or '') end "
                   "table.sort(o) rcon.print(table.concat(o,' '))")
    print("     after the rebuild order:", state, flush=True)
    check("the redeploy went through", raw.get("ok"), raw)
    check("the piece the new layout drops is marked for deconstruction", "inserter:marked" in state, state)
    check("so is the stray pipe in the footprint", "pipe:marked" in state, state)
    # a kept piece is either rebuilt from a ghost over it, or the game kept it standing and unmarked: both are right
    for name in ("assembling-machine-2", "transport-belt"):
        check("%s comes back (a ghost over it, or kept)" % name, ("ghost:" + name) in state or (name in state.split()), state)

    # ---- tiling, export and import
    r, raw = ok("design_save", {"name": "night-pole", "description": "night check: one pole", "pieces": [{"name": "medium-electric-pole", "x": 0.5, "y": 0.5}]}, c)
    r, raw = ok("design_tile", {"name": "night-pole", "x": 20, "y": 55, "width": 40, "height": 1, "step_x": 7, "dry_run": False}, c)
    check("design_tile lays a line of copies", raw.get("ok") and (r.get("placed") or 0) >= 4, raw)
    r, _ = ok("design_export", {"name": "night-gear-cell"}, c)
    s = r.get("string", "")
    r, raw = ok("design_save", {"name": "night-imported", "description": "night check: imported", "string": s}, c)
    check("export then import round-trips", raw.get("ok") and r.get("pieces") == 2, raw)

    # ---- cron
    ok("cron_change", {"name": "night-ghosts", "action": "remove"}, c)
    r, raw = ok("cron_add", {"name": "night-ghosts", "tool": "ghost_needs", "args": {"surface": "nauvis"}, "every_minutes": 1,
                             "purpose": "night check", "expect_ok": "a list", "expect_bad": "an error"}, c)
    check("cron_add takes a job", raw.get("ok"), raw)
    r, raw = ok("cron_change", {"name": "night-ghosts", "action": "run_now"}, c)
    check("cron runs a tool now", raw.get("ok") and r["job"]["runs"] == 1 and r["job"]["last_ok"], raw)
    time.sleep(75)                                         # one game minute and a little: the timer itself
    r, _ = ok("cron_list", None, c)
    job = [j for j in r.get("jobs", []) if j["name"] == "night-ghosts"]
    check("the timer runs it again by itself", job and job[0]["runs"] >= 2, job)
    ok("cron_change", {"name": "night-ghosts", "action": "remove"}, c)

    # ---- ghosts to requests, read only
    r, raw = ok("ghost_needs", {"surface": "nauvis"}, c)
    check("ghost_needs reads the real ghosts", raw.get("ok") or "no logistic network" in str(raw), raw)
    r, raw = ok("ghost_requests", {"surface": "nauvis"}, c)
    check("ghost_requests dry run answers", raw.get("ok"), raw)

    ok("forget_place", {"name": "night test site"}, c)
    print()
    print("%d failed: %s" % (len(fails), ", ".join(fails)) if fails else "all passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
