"""
Compact shuttle, second design (2026-11-10), built around the platform hub so that nothing depends on a shared belt loop:

    collectors -> chunk belt -> one inserter into the hub (takes only the chunk types the hub is short of; the rest is thrown into space at the belt's end)
    hub -> crushers -> hub (iron ore) / ice melter (water) / fuel plant;  hub -> furnaces -> hub -> assembler -> hub (magazines)
    hub -> turrets, directly or over two short belts (nose, rear): the magazine stock sits upstream of every turret
    nose and flanks: fifteen solar panels and six accumulators (nuclear until 2026-11-10);  rear: tanks, four thrusters fed through two-tile gaps

Rare quality throughout: epic and legendary are not unlocked by research. All coordinates are tiles (top-left corner); the hub covers -4..3.
Usage: scripts/build_shuttle2.py --surface platform-3 [--apply]
"""
import json
import sys

from _game import tools

Q = {"quality": "epic"}
N, E, S, W = 0, 4, 8, 12
BELT, UG, PIPE, PTG, INS = "express-transport-belt", "express-underground-belt", "pipe", "pipe-to-ground", "fast-inserter"
ents = []
tiles = set()
HOLES = {(-10, -4)}                                     # the chunk belt's dump drops here


def big(name, tx, ty, w, h, d=0, **kw):
    ents.append({"name": name, "x": tx + w / 2, "y": ty + h / 2, "direction": d, "params": dict(Q), **kw})
    for x in range(tx - 1, tx + w + 1):
        for y in range(ty - 1, ty + h + 1):
            tiles.add((x, y))


def one(name, tx, ty, d=0, **kw):
    big(name, tx, ty, 1, 1, d, **kw)


def ins(tx, ty, pick, name=INS):                        # direction = the side it picks from
    one(name, tx, ty, pick)


def ug(tx, ty, d, kind):
    one(UG, tx, ty, d)
    ents[-1]["params"]["type"] = kind


def run(name, x1, y1, x2, y2, d=0):
    dx, dy = (x2 > x1) - (x2 < x1), (y2 > y1) - (y2 < y1)
    x, y = x1, y1
    while True:
        one(name, x, y, d)
        if (x, y) == (x2, y2):
            break
        x, y = x + dx, y + dy


def pipes(*pts):
    for x, y in pts:
        one(PIPE, x, y)


def turret(tx, ty, ix, iy, pick):
    big("gun-turret", tx, ty, 2, 2)
    ins(ix, iy, pick)


# nose: solar panels and accumulators where the reactor, heat exchanger and turbine stood until 2026-11-10 (the Captain's order: solar instead of nuclear)
big("solar-panel", -2, -10, 3, 3)
for tx, ty in ((1, -10), (1, -8), (-2, -6), (0, -6), (-1, -12), (-1, -14)):
    big("accumulator", tx, ty, 2, 2)

# turrets fed straight from the hub
turret(-4, -7, -4, -5, S)
turret(3, -7, 3, -5, S)
turret(5, 3, 4, 3, W)

# nose ammunition belt
ins(4, -4, W, "bulk-inserter")
run(BELT, 5, -4, 5, -18, N)
run(BELT, 5, -19, -3, -19, W)
turret(2, -17, 2, -18, N)
turret(-3, -17, -3, -18, N)
# four more nose turrets (2026-11-10, after flight damage on the Fulgora run): the two nose turrets did twice the work of any other
turret(0, -17, 0, -18, N)
turret(7, -17, 6, -17, W)
turret(7, -14, 6, -14, W)
turret(2, -14, 4, -14, E)

# rear ammunition belt
ins(-1, 4, N, "bulk-inserter")
run(BELT, -1, 5, -1, 9, S)
ug(-1, 10, S, "input")
ug(-1, 12, S, "output")
run(BELT, -1, 13, -1, 15, S)
turret(1, 13, 0, 13, W)
turret(-4, 13, -2, 14, E)

# collectors and the chunk belt
big("asteroid-collector", -7, -16, 3, 3, N)
ins(-6, -13, N)
big("asteroid-collector", -10, -12, 3, 3, W)
ins(-7, -11, W)
big("asteroid-collector", -10, -8, 3, 3, W)
ins(-7, -7, W)
run(BELT, -6, -12, -6, -5, S)
run(BELT, -6, -4, -8, -4, W)
ins(-5, -4, W, "bulk-inserter")                         # chunk into the hub, filter set by circuit
ins(-9, -4, E)                                          # dump: what the hub did not want goes into space

# north-east collectors (added after the first refill measurement: three collectors on one corner gave 2 oxide chunks a minute at Nauvis)
# their belt runs west along y=-12, under the ammunition belt and the heat exchanger, and joins the head of the chunk belt
big("asteroid-collector", 9, -16, 3, 3, N)
ins(10, -13, N)
big("asteroid-collector", 13, -16, 3, 3, E)
ins(14, -13, N)
big("asteroid-collector", 11, -10, 3, 3, E)
ins(12, -11, S)
run(BELT, 14, -12, 8, -12, W)
ug(7, -12, W, "input")
ug(3, -12, W, "output")
ug(2, -12, W, "input")
ug(-2, -12, W, "output")
run(BELT, -3, -12, -5, -12, W)

# west side: metallic crusher, furnace, oxidizer plant
big("crusher", -7, -3, 2, 3, N, recipe="metallic-asteroid-crushing")
ins(-5, -3, E)
ins(-5, -1, W)
big("electric-furnace", -8, 0, 3, 3)
ins(-5, 0, E)
ins(-5, 2, W)
big("chemical-plant", -8, 3, 3, 3, W, recipe="thruster-oxidizer")
ins(-5, 3, E)

# east side: furnace, assembler
big("electric-furnace", 5, -3, 3, 3)
ins(4, -3, W)
ins(4, -1, E)
big("assembling-machine-3", 5, 0, 3, 3, recipe="firearm-magazine")
ins(4, 0, W)
ins(4, 2, E)

# south side: oxide and carbonic crushers, melter, fuel plant
big("crusher", -4, 5, 3, 2, E, recipe="oxide-asteroid-crushing")
ins(-4, 4, N)
ins(-2, 4, S)                                           # chunk back, filtered in configure()
big("crusher", 0, 5, 3, 2, E, recipe="carbonic-asteroid-crushing")
ins(0, 4, N)
ins(2, 4, S)
ins(-3, 7, N)
ins(1, 7, N)
big("chemical-plant", -4, 8, 3, 3, N, recipe="ice-melting")
big("chemical-plant", 0, 8, 3, 3, S, recipe="thruster-fuel")

# water: row 11, riser to the oxidizer plant, riser on the east side to the heat exchanger, two tanks
run(PIPE, -9, 11, 11, 11)
run(PIPE, -9, 10, -9, 5)
run(PIPE, 8, 10, 8, 8)
big("storage-tank", 5, 8, 3, 3)
big("storage-tank", 9, 8, 3, 3)

# thruster fuel: plant -> column 3 -> header row 17 -> tanks, thrusters
pipes((2, 7), (3, 7), (3, 8), (3, 9))
one(PTG, 3, 10, N)
one(PTG, 3, 12, S)
run(PIPE, 3, 13, 3, 16)
run(PIPE, -12, 17, 12, 17)
big("storage-tank", 5, 13, 3, 3)
big("storage-tank", 9, 13, 3, 3)
pipes((7, 16), (11, 16))
run(PIPE, -12, 18, -12, 21)
one(PTG, 0, 18, N)
one(PTG, 0, 20, S)
pipes((0, 21), (0, 22), (-1, 22), (-1, 23))
run(PIPE, 12, 18, 12, 23)
one(PIPE, 11, 23)

# oxidizer: plant -> column -5 -> header row 19 -> tanks, thrusters
run(PIPE, -5, 5, -5, 9)
one(PTG, -5, 10, N)
one(PTG, -5, 12, S)
run(PIPE, -5, 13, -5, 15)
one(PTG, -5, 16, N)
one(PTG, -5, 18, S)
run(PIPE, -7, 19, 5, 19)
big("storage-tank", -8, 13, 3, 3)
big("storage-tank", -12, 13, 3, 3)
run(PIPE, -9, 13, -9, 15)
pipes((-7, 20), (-7, 21), (-7, 22), (-6, 22), (-6, 23))
pipes((5, 20), (5, 21), (5, 22), (6, 22), (6, 23))

# power: fifteen panels in all, one in the nose and fourteen in two columns on each flank, inside the width the collectors and tanks already set
for ty in (-4, -1, 2, 5):
    big("solar-panel", 9, ty, 3, 3)
for ty in (-4, -1, 2, 5, 8):
    big("solar-panel", 12, ty, 3, 3)
for ty in (-3, 0, 3, 6, 9):
    big("solar-panel", -12, ty, 3, 3)

# three deciders for the chunk whitelist (configure_shuttle2.py wires them)
for ty in (-6, -8, -10):
    big("decider-combinator", -5, ty, 1, 2)

# thrusters
for tx in (-11, -5, 1, 7):
    big("thruster", tx, 21, 4, 5)

for x in range(-5, 5):                                  # the hub's own apron
    for y in range(-5, 5):
        tiles.add((x, y))
for x in range(-7, -4):                                 # a collector needs open space on its front row and three rows ahead of it
    for y in range(-19, -15):
        HOLES.add((x, y))
for x in range(-13, -9):
    for y in (-12, -11, -10, -8, -7, -6):
        HOLES.add((x, y))
for x, y in [(x, y) for x in range(9, 12) for y in range(-19, -15)] + [(x, y) for x in range(15, 19) for y in range(-16, -13)] + \
        [(x, y) for x in range(13, 17) for y in range(-10, -7)]:
    HOLES.add((x, y))                                   # the three north-east collectors
tiles = {(x, y) for (x, y) in tiles if y <= 25 and (x, y) not in HOLES}


def lua_tiles(surface):
    want = ",".join("{%d,%d}" % t for t in sorted(tiles))
    return ("local s=game.surfaces['%s'] local want={} local add={} for _,p in pairs({%s}) do want[p[1]..','..p[2]]=true add[#add+1]={name='space-platform-foundation',position=p} end "
            "s.set_tiles(add) local rm={} for _,t in pairs(s.find_tiles_filtered{name='space-platform-foundation'}) do if not want[t.position.x..','..t.position.y] then "
            "rm[#rm+1]={name='empty-space',position=t.position} end end s.set_tiles(rm) rcon.print('foundation '..#add..' removed '..#rm)" % (surface, want))


def unwrap(out):
    r = json.loads(out)
    if isinstance(r, dict) and isinstance(r.get("result"), str):
        try:
            return json.loads(r["result"])
        except ValueError:
            return r
    return r


def main():
    surface = sys.argv[sys.argv.index("--surface") + 1]
    apply = "--apply" in sys.argv
    print(f"plan: {len(ents)} entities, {len(tiles)} foundation tiles ({len(tiles) * 200 / 1000:.0f} t)")
    if apply:
        print(tools["run_lua"](lua_tiles(surface)).strip())
    # place_entities stacks a second copy on top of an identical entity, so anything already standing is left out
    have = tools["run_lua"]("local t={} for _,e in pairs(game.surfaces['%s'].find_entities_filtered{force='player'}) do t[#t+1]=e.name..'@'..e.position.x..','..e.position.y end "
                            "rcon.print(table.concat(t,';'))" % surface)
    have = set(json.loads(have).get("result", "").split(";")) if have.strip().startswith("{") else set(have.strip().split(";"))
    todo = [e for e in ents if "%s@%g,%g" % (e["name"], e["x"], e["y"]) not in have]
    print(f"already standing: {len(ents) - len(todo)}")
    r = unwrap(tools["place_entities"](json.dumps(todo), surface=surface, dry_run=not apply, clear_trees=False))
    print("placed" if apply else "dry", r.get("placed"), "failed", len(r.get("failed") or []))
    for f in (r.get("failed") or [])[:40]:
        print("   ", f)


if __name__ == "__main__":
    main()
