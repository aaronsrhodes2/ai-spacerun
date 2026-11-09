"""
Automated rocket-fuel line (Captain 2026-11-09: fill trains' fuel by belt, not by hand-filled chests).
Source: the rocket-fuel belt at x=-254 (train unload -> chest at (-253.5,-127.5)); a fast splitter at (-254.5,-132.5) sends half down a new
fast belt (long runs are fast-underground hops) to the iron unload stop (burner inserters at (22.5,-158.5) and (43.5,-158.5) pick from the
belt on y=-159.5 and drop into the two locomotives at (22,-157), (43,-157)), then on to the copper unload stop (the existing burner inserters at
(90.5,-150.5), (111.5,-150.5) now pick from the belt on y=-151.5 instead of chests). Router: scripts/route_fuel.py (needs scripts/_fuelgrid.json).
Usage: scripts/build_fuel_line.py [--build]
"""
import json
import sys

from _game import tools

from route_fuel import load, make_free, route, to_entities

from bridge.factorio.planner import batches


def plan():
    x1, rows = load()
    free = make_free(x1, rows, extra_free=[(90, -152), (111, -152), (-254, -133)])
    segs = [((-255, -132), 8, (15, -160), 4), ((15, -160), 4, (23, -160), 4), ((23, -160), 4, (44, -160), 4),
            ((44, -160), 4, (89, -152), 4), ((89, -152), 4, (112, -152), 4)]
    acts = []
    for start, sd, goal, gd in segs:
        a = route(free, start, sd, goal, gd, must={(22, -160), (43, -160), (90, -152), (111, -152)})
        if a is None:
            raise SystemExit(f"no route {start}->{goal}")
        acts += a
    # the segment boundaries repeat their start tile as the first action of the next segment only if it was placed: dedupe by tile
    seen, out = set(), []
    for a in acts:
        key = (a[1], a[2]) if a[0] == "belt" else (a[1], a[2], a[3], a[4])
        if key in seen:
            continue
        seen.add(key)
        out.append(a)
    ents = to_entities(out)
    ents.append({"name": "fast-transport-belt", "x": 111.5 + 1, "y": -151.5, "direction": 4})  # dead end holds fuel
    return ents, out


def main():
    ents, acts = plan()
    # required feeder tiles must be plain belts
    belts = {(e["x"], e["y"]) for e in ents if e["name"] == "fast-transport-belt"}
    for need in [(22.5, -159.5), (43.5, -159.5), (90.5, -151.5), (111.5, -151.5)]:
        if need not in belts:
            raise SystemExit(f"feeder tile {need} is not a belt in the plan")
    split = {"name": "fast-splitter", "x": -254.0, "y": -132.5, "direction": 8}
    inserters = [{"name": "burner-inserter", "x": 22.5, "y": -158.5, "direction": 0}, {"name": "burner-inserter", "x": 43.5, "y": -158.5, "direction": 0}]
    print(len(ents), "belt entities;", sum(1 for e in ents if "underground" in e["name"]), "underground pieces")
    for part in batches(ents + inserters):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        bad = [f for f in (r.get("failed") or []) if (f["x"], f["y"]) not in ((90.5, -151.5), (111.5, -151.5))]   # my old chests, removed at build
        if r.get("error") or bad:
            raise SystemExit(f"dry run failed: {json.dumps(bad)[:3000]}")
    print("dry run clean (splitter, chest removal and seeding are done at build time)")
    if "--build" not in sys.argv:
        return
    print(tools["save_game"]("before-fuel-line"))
    # take the rocket fuel out of the two copper-unload chests (moved to the iron depot chests), then clear them
    print(tools["run_lua"](
        "local s=game.surfaces.nauvis local back=s.find_entities_filtered{name='steel-chest',position={-146.5,-406.5},radius=1}[1] local n=0 "
        "for _,p in pairs({{90.5,-151.5},{111.5,-151.5}}) do local c=s.find_entities_filtered{name='steel-chest',position=p,radius=0.4}[1] if c then "
        "local inv=c.get_inventory(defines.inventory.chest) local f=inv.get_item_count('rocket-fuel') inv.remove{name='rocket-fuel',count=f} "
        "back.get_inventory(defines.inventory.chest).insert{name='rocket-fuel',count=f} n=n+f c.destroy() end end rcon.print('moved '..n)"))
    print(tools["remove_entities"](-254.4, -133.0, -253.6, -132.0, names="fast-transport-belt"))
    for part in batches(ents + inserters + [split]):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        print(r.get("placed"), r.get("failed"))
    print(tools["run_lua"](
        "local s=game.surfaces.nauvis for _,p in pairs({{22.5,-158.5},{43.5,-158.5}}) do local i=s.find_entities_filtered{name='burner-inserter',position=p,radius=0.3}[1] "
        "if i then i.get_fuel_inventory().insert{name='rocket-fuel',count=1} end end rcon.print('seeded')"))


if __name__ == "__main__":
    main()
