"""
Fit-out of the "Inner Planets Shuttle" (space platform surface platform-3): solar power, an on-board ammunition line and gun turrets, and the
Captain's own ghosts (three chemical plants, the east belt run) built as drawn. Everything is legendary, as the Captain ordered on 2026-11-10.

    sushi belt (row -7, eastward) --inserter--> crusher --> furnace --> assembler (firearm magazine) <-- furnace <-- crusher
    assembler --> ammo belt 1: east, north, west along row -22 (north turret row), south, west to the west turrets
              --> ammo belt 2: west, then south under the sushi belts to the two rear turrets

Power is solar (32 panels, 8 accumulators). A space platform has one global electric network (surface.has_global_electric_network), so every
entity is powered wherever it stands: the substations and poles placed here are not needed, and nothing can be kept unpowered by leaving it outside
a supply area. That is how the reactor's fuel inserters got power the moment the panels existed and started the reactor (a legendary reactor burns
one fuel cell every 80 s whether or not the steam is used).

All coordinates are tiles (x, y = the tile's top-left corner).
Usage: scripts/build_shuttle.py [--apply]
"""
import json
import sys

from _game import tools

SURFACE = "platform-3"
Q = {"quality": "legendary"}
N, E, S, W = 0, 4, 8, 12
BELT, UG = "express-transport-belt", "express-underground-belt"
ents = []


def one(name, tx, ty, d=0, **kw):                       # 1x1 entity on a tile
    ents.append({"name": name, "x": tx + 0.5, "y": ty + 0.5, "direction": d, "params": dict(Q), **kw})


def big(name, tx, ty, w, h, d=0, **kw):                 # w x h entity whose top-left tile is (tx, ty)
    ents.append({"name": name, "x": tx + w / 2, "y": ty + h / 2, "direction": d, "params": dict(Q), **kw})


def ug(tx, ty, d, kind):
    ents.append({"name": UG, "x": tx + 0.5, "y": ty + 0.5, "direction": d, "params": {"type": kind, **Q}})


def run(x1, y1, x2, y2, d):                             # straight belt from one tile to another, both included
    dx = (x2 > x1) - (x2 < x1)
    dy = (y2 > y1) - (y2 < y1)
    x, y = x1, y1
    while True:
        one(BELT, x, y, d)
        if (x, y) == (x2, y2):
            break
        x, y = x + dx, y + dy


def turret(tx, ty, ins_x, ins_y, ins_d):                # 2x2 turret (top-left tile) and the inserter that feeds it (direction = side it picks from)
    big("gun-turret", tx, ty, 2, 2)
    one("fast-inserter", ins_x, ins_y, ins_d)


# power: substations and medium poles (redundant on a platform, see the docstring), solar fields, accumulators
big("substation", 5, -21, 2, 2)
big("substation", 26, -18, 2, 2)
big("substation", 41, 1, 2, 2)
for px, py in ((-24, -9), (-7, -14), (42, -22), (21, 0)):
    one("medium-electric-pole", px, py)
for ty in (-18, -15, -12):                              # field west (between the two collector belts)
    for tx in (4, 7, 10, 13):
        big("solar-panel", tx, ty, 3, 3)
for tx in (17, 20, 23, 26, 29, 32, 35):                 # field middle
    big("solar-panel", tx, -21, 3, 3)
for tx in (17, 20, 23, 29, 32):
    big("solar-panel", tx, -18, 3, 3)
for ty in (-21, -18, -15, -12):                         # field east
    for tx in (42, 45):
        big("solar-panel", tx, ty, 3, 3)
for tx in range(17, 33, 2):
    big("accumulator", tx, -15, 2, 2)

# ammunition line, rows -11..-9, fed from the sushi belt on row -7
for cx, ore_x, ore_d in ((22, 24, W), (37, 36, E)):
    big("crusher", cx, -11, 2, 3, S, recipe="metallic-asteroid-crushing")
    one("fast-inserter", cx, -8, S)                     # chunk in (picks from the belt to the south)
    one("fast-inserter", cx + 1, -8, N)                 # chunk back out, filtered in configure()
    one("fast-inserter", ore_x, -10, ore_d)
big("electric-furnace", 25, -11, 3, 3)
big("electric-furnace", 33, -11, 3, 3)
one("fast-inserter", 28, -10, W)
one("fast-inserter", 32, -10, E)
big("assembling-machine-3", 29, -11, 3, 3, recipe="firearm-magazine")
one("fast-inserter", 31, -12, S)                        # to ammo belt 1
one("fast-inserter", 29, -12, S)                        # to ammo belt 2

# ammo belt 1
run(31, -13, 39, -13, E)
run(40, -13, 40, -21, N)
run(40, -22, 18, -22, W)
ug(17, -22, W, "input")
ug(15, -22, W, "output")
run(14, -22, 5, -22, W)
run(4, -22, 4, -20, S)
ug(4, -19, W, "input")
ug(2, -19, W, "output")
run(1, -19, 1, -14, S)
run(1, -13, -12, -13, W)
run(-13, -13, -13, -12, S)
run(-13, -11, -23, -11, W)
# ammo belt 2
run(29, -13, 21, -13, W)
run(20, -13, 20, -9, S)
ug(20, -8, S, "input")
ug(20, -5, S, "output")
run(20, -4, 20, 4, S)

# turrets
for cx in (6, 10, 14, 20, 26, 32, 38):                  # north row
    turret(cx - 1, -25, cx - 1, -23, S)
turret(37, -17, 39, -16, E)
turret(-5, -16, -5, -14, S)
turret(-21, -9, -21, -10, N)
turret(-15, -9, -15, -10, N)
turret(17, 0, 19, 0, E)                                 # rear
turret(17, -4, 19, -3, E)

GHOSTS = ("local s=game.surfaces['%s'] local o={} for _,g in pairs(s.find_entities_filtered{type='entity-ghost'}) do local r=(g.ghost_type=='assembling-machine') and g.get_recipe() or nil "
          "o[#o+1]={name=g.ghost_name,x=g.position.x,y=g.position.y,direction=g.direction,recipe=r and r.name or nil,"
          "kind=(g.ghost_type=='underground-belt') and g.belt_to_ground_type or nil} end rcon.print(helpers.table_to_json(o))" % SURFACE)

CONFIGURE = ("local s=game.surfaces['%s'] local n=0 for _,p in pairs({{23.5,-7.5},{38.5,-7.5}}) do local i=s.find_entity({name='fast-inserter',quality='legendary'},p) "
             "if i then i.use_filters=true i.set_filter(1,{name='metallic-asteroid-chunk',quality='normal'}) n=n+1 end end rcon.print('filtered '..n)" % SURFACE)


def unwrap(out):                                        # a tool answers with JSON, sometimes wrapped as {"result": "..."}
    try:
        r = json.loads(out)
    except ValueError:
        raise SystemExit("unexpected answer: " + out[:600])
    if isinstance(r, dict) and isinstance(r.get("result"), str):
        try:
            return json.loads(r["result"])
        except ValueError:
            raise SystemExit("unexpected answer: " + r["result"][:600])
    return r


def place(batch, dry):
    return unwrap(tools["place_entities"](json.dumps(batch), surface=SURFACE, dry_run=dry, clear_trees=False))


def main():
    apply = "--apply" in sys.argv
    found = unwrap(tools["run_lua"](GHOSTS)) or []
    ghosts = []
    for g in found:
        params = dict(Q)
        if g.get("kind"):
            params["type"] = g["kind"]
        e = {"name": g["name"], "x": g["x"], "y": g["y"], "direction": g["direction"], "params": params}
        if g.get("recipe"):
            e["recipe"] = g["recipe"]
        ghosts.append(e)
    print(f"plan: {len(ents)} new entities, {len(ghosts)} of the Captain's ghosts")
    for label, batch in (("new", ents), ("ghosts", ghosts)):
        if not batch:
            continue
        r = place(batch, dry=not apply)
        print(label, "dry" if not apply else "placed", r.get("placed"), "failed", len(r.get("failed") or []))
        for f in (r.get("failed") or [])[:30]:
            print("   ", f)
    if apply:
        print(tools["run_lua"](CONFIGURE))
    else:
        print("DRY RUN (add --apply)")


if __name__ == "__main__":
    main()
