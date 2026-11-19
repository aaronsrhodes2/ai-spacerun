#!/usr/bin/env python3
"""The universal shuttle (the Captain, 2026-11-18): ONE hull for the inner runs (Nauvis <-> Vulcanus / Gleba / Fulgora) and the outer runs
(Gleba or Fulgora <-> Aquilo), stable when parked at either end, flying and fighting on asteroid chunks alone, on a timed schedule.
Prototype: `Universal 1 Proto` (no "Shuttle" in the name on purpose: the fleet scripts pick ships by that word and must leave a prototype alone).

DESIGN. North is the nose. The hub covers tiles -4..3. Long and narrow: 38 wide over the turrets, 100 long, 722 t, four thrusters, twelve cargo
bays (the Captain widened the spine by hand while it was being built: 659 hub slots).
  hub edge     Every machine trades with the hub by inserter and every inserter is gated on the hub's own stock (red wire), so nothing is handed
               machine to machine except coal. The hub is the only store: a crusher can always hand back, so it cannot wedge on a full product slot.
               west   oxidizer plant, metallic crusher, ROCKET PORT, magazine assembler, ice melter
               east   fuel plant, carbonic crusher, MAGAZINE PORT, explosive rocket assembler, coal plant (hands coal round the corner to explosives)
               south  oxide crusher, rocket assembler, explosives plant
               north  chunks in, valve (drops through a hole in the deck), first cargo bay, ORE PORT, PLATE PORT
  ports        The hub has 32 face tiles and they are the scarce thing. A port is one bulk inserter between the hub and a belt:
               ore out / plates back: a smelter row north-east of the bays (four furnaces on two belts), so furnaces cost two face tiles, not eight;
               rockets out / magazines out: two belts that side-load the ammunition loop, rockets from OUTSIDE (under the loop and back), magazines
               from inside, so each kind has a lane of its own for good.
  fuel first   Two deciders share the carbon: fuel while the tanks hold less than FUEL_FIRST, rockets after that (and always while the hub holds
               fewer rockets than ROCKET_FLOOR). Without it the ship made 15 rockets and 1,049 fuel a minute at Nauvis and could not keep a timetable.
  crushers     Each crusher's RECIPE is set by two deciders reading the hub: crush while its own product is under its cap, REPROCESS while its product
               is at the cap and another product is low, nothing otherwise. Aquilo's orbit has oxide chunks and almost nothing else: there the oxide
               crusher fills the ice and then reshuffles oxide chunks into carbonic and metallic ones. Chunks over 20 a kind and works goods over
               their caps go overboard through the valve; ammunition is never on the valve's list.
  ammunition   A closed LOOP belt round the whole ship (east flank north, nose, west flank south, stern), explosive rockets on the outer lane,
               firearm magazines on the inner lane; two splitters at the stern feed dead-end spurs beside the thrusters. The hub holds the reserve
               (caps 6,000 and 6,000), the works refill the hub, the schedule reads the hub. 16 rocket turrets (big and huge asteroids ONLY),
               30 gun turrets (medium, then small, nothing else).
  chunks       four collectors (two on the nose, one a flank at the nose end), one sushi belt into the hub.
  fluids       water row 8 with two risers; oxidizer down the west side, fuel down the east side, four tanks each, lanes beside the solar field
               to the rear block. All eight tanks on the hub's green wire: the schedule reads the whole stock.
  power        84 legendary panels in the tail between the tanks and the thrusters (sheltered by the hull in flight); 28 accumulators; a pole at
               (4,-5) only as a meter. In space the sun never sets: short of power everything just runs slower, nothing switches off.
  schedule     every stop: RUN and quiet 60 s and 30 s, OR RUN and TMAX. RUN = fuel, oxidizer (tanks, green wire) and the hub's own count of
               magazines, plus explosive rockets on a leg with big asteroids. Each stop has its own levels (RUNS): the far stop asks only for the
               leg home. No cargo conditions, no drop sections, no requests.
SIZED FOR  about 23 explosive rockets a minute (one explosives plant at 37.5 crafts a minute feeds one rocket and one explosive rocket assembler;
  face tiles limit it to one chain) and about 90 magazines a minute (four furnaces, 376 plates; one assembler could make 187). A ship of this size
  parked in Aquilo orbit spent 6.6 explosive rockets a minute (Fulgora-Aquilo 5, measured over 8.5 minutes, `_us_aquilo_watch.py`).
PROVEN (2026-11-18, docs/bottleneck-plan.md has the numbers)
  - built from foundation items and free entities; works running from chunks alone at Nauvis; lanes of the loop stay pure; recipes switch by circuit;
  - Nauvis -> Gleba -> Nauvis on the timed schedule, three times; turrets never empty, no rocket fired (inner legs have no big asteroids).
    Trips 1 and 3 without a scratch. Trip 2 lost the west nose collector on the leg home at 185 km/s (full tanks): four nose guns were added after it,
    and that speed has not been flown again.
NOT PROVEN  anything about Aquilo: the leg, the rocket balance against big asteroids, and above all standing parked there. Parked at a planet the works
  are CHUNK-LIMITED (about 10 carbonic chunks a minute at Nauvis with four collectors), so the rocket line runs under its size.
BUILD NOTES  never lift tile ghosts while the hub is laying deck (`_us_poke.py` wakes the ones that stick); a hub inserter must be born filtered.
Steps: check | create | request [N] | deck | build [--apply] | config | route [HOME] DEST [--go] | status | rates [SECONDS] [--catch] | map
Usage: universal_shuttle.py check ; universal_shuttle.py create ; universal_shuttle.py deck ; universal_shuttle.py build --apply"""
import json
import sys
import time

NAME, PLANET = "Universal 1 Proto", "nauvis"
Q = "legendary"
N, E, S, W = 0, 4, 8, 12
DIR = {(0, -1): N, (1, 0): E, (0, 1): S, (-1, 0): W}
NY = -24                       # the loop's nose row
XW, XE = -13, 12               # the loop's flank columns
SOL_Y0, ROWS = 23, 12          # solar field: first row, rows of seven panels
SY = SOL_Y0 + 3 * ROWS + 1     # the loop's stern row
TY = SY + 7                    # thrusters' first row
# hub stock levels (items)
C_CAP, ORE_CAP, ICE_CAP = 2000, 1500, 800          # a crusher crushes while its product is under this
C_LOW, ORE_LOW, ICE_LOW = 500, 400, 200            # ... and reprocesses at its cap while another product is under this
PLATE_CAP, EXPL_CAP, ROCKET_CAP = 600, 400, 200
FUEL_FIRST, ROCKET_FLOOR = 90000, 500              # carbon goes to fuel while the tanks hold less than FUEL_FIRST, unless the hub holds fewer rockets than ROCKET_FLOOR
ER_CAP, MAG_CAP = 6000, 6000                       # the reserve in the hub
VALVE = {"metallic-asteroid-chunk": 20, "carbonic-asteroid-chunk": 20, "oxide-asteroid-chunk": 20, "sulfur": 800, "carbon": 4000, "iron-ore": 3000,
         "ice": 2000, "iron-plate": 2000, "coal": 200, "explosives": 1500, "rocket": 1000, "calcite": 50, "copper-ore": 50}
# RUN levels by kind of leg: fluids are the sum of four tanks, ammunition is the hub's own count
RUNS = {"inner": {"home": dict(fuel=70000, rockets=0, mags=800), "away": dict(fuel=40000, rockets=0, mags=500)},      # no big asteroids on the inner legs
        "outer": {"home": dict(fuel=85000, rockets=4000, mags=2500), "away": dict(fuel=60000, rockets=1500, mags=1000)}}
TMIN, QUIET, TMAX_HOME, TMAX_FAR = 30, 60, 900, 300

ents, cells, filt, recipes, gates, occ, fluid, opening, tiles, holes = [], [], [], [], [], {}, {}, {}, set(), set()
crushers, collectors = [], []


def put(name, tx, ty, w=1, h=1, d=N, f=None, recipe=None, gate=None, margin=True, **params):
    for c in [(tx + i, ty + j) for i in range(w) for j in range(h)]:
        assert c not in occ and not (-4 <= c[0] < 4 and -4 <= c[1] < 4), "%s at %s overlaps %s" % (name, c, occ.get(c, "the hub"))
        occ[c] = name
    m = 1 if margin else 0
    for x in range(tx - m, tx + w + m):
        for y in range(ty - m, ty + h + m):
            tiles.add((x, y))
    e = {"name": name, "x": tx + w / 2, "y": ty + h / 2, "direction": d, "params": dict({"quality": Q}, **params)}
    ents.append(e)
    cells.append([(tx + i, ty + j) for i in range(w) for j in range(h)])
    if f:
        filt.append((e["x"], e["y"], f))
    if recipe:
        recipes.append((e["x"], e["y"], recipe))
    if gate:
        gates.append((e["x"], e["y"], gate[0], gate[1], gate[2] if len(gate) > 2 else "<"))
    return e


def ins(x, y, d, f=None, gate=None, name="fast-inserter"):
    """A filtered inserter is CREATED with its filter (create_entity takes use_filters / filter_mode / filters through place_entities' params).
    Placed bare and filtered a moment later, a hub inserter moves whatever the hub holds: the valve threw about 600 foundations overboard
    that way on 2026-11-18 before its combinator stood."""
    if f:
        return put(name, x, y, d=d, f=f, gate=gate, use_filters=True, filter_mode="whitelist", filters=[{"index": i + 1, "name": n} for i, n in enumerate(f)])
    return put(name, x, y, d=d, gate=gate)


def sgn(a):
    return (a > 0) - (a < 0)


def belts(path, end):
    for i, t in enumerate(path):
        kind = t[2] if len(t) > 2 else None
        if kind == "out":
            a = path[i - 1]
            assert abs(t[0] - a[0]) + abs(t[1] - a[1]) <= 9
            put("express-underground-belt", t[0], t[1], d=DIR[(sgn(t[0] - a[0]), sgn(t[1] - a[1]))], type="output")
            continue
        if i + 1 < len(path):
            b = path[i + 1]
            assert kind == "in" or abs(b[0] - t[0]) + abs(b[1] - t[1]) == 1, "gap in belt at %s" % (t,)
            d = DIR[(sgn(b[0] - t[0]), sgn(b[1] - t[1]))]
        else:
            d = end
        if kind == "in":
            put("express-underground-belt", t[0], t[1], d=d, type="input")
        else:
            put("express-transport-belt", t[0], t[1], d=d)


def row(x0, x1, y):
    return [(x, y) for x in range(x0, x1 + sgn(x1 - x0), sgn(x1 - x0) or 1)]


def col(x, y0, y1):
    return [(x, y) for y in range(y0, y1 + sgn(y1 - y0), sgn(y1 - y0) or 1)]


def pipe(f, *ts):
    for x, y in ts:
        put("pipe", x, y)
        fluid[(x, y)] = f


def ptg(f, x, y, d):
    put("pipe-to-ground", x, y, d=d)
    fluid[(x, y)] = f
    opening[(x, y)] = {v: k for k, v in DIR.items()}[d]                  # a pipe to ground joins only at its open end


def collector(tx, ty, d):
    """A collector's front row hangs over open space: deck under its two back rows only, and nothing in front of it."""
    put("asteroid-collector", tx, ty, 3, 3, d=d, margin=False)
    dx, dy = {v: k for k, v in DIR.items()}[d]
    for i in range(3):
        for j in range(3):
            front = (dx < 0 and i == 0) or (dx > 0 and i == 2) or (dy < 0 and j == 0) or (dy > 0 and j == 2)
            if front:
                for k in range(3):                                       # the front row and two tiles beyond it
                    holes.add((tx + i + dx * k, ty + j + dy * k))
            else:
                tiles.add((tx + i, ty + j))
    collectors.append((tx, ty, d))


def gun(tx, ty, ix, iy, d):
    put("gun-turret", tx, ty, 2, 2)
    ins(ix, iy, d)


def rkt(tx, ty, ix, iy, d):
    put("rocket-turret", tx, ty, 3, 3)
    ins(ix, iy, d)


def I(n):
    return "I('%s')" % n


def cnd(sig, cmp, k, how=None):
    return "{first_signal=%s,comparator='%s',constant=%d%s}" % (I(sig), cmp, k, ",compare_type='%s'" % how if how else "")


def layout():
    # ---- hub edge, north ----
    put("constant-combinator", -5, -5)                                    # the valve's caps
    ins(-4, -5, N, name="bulk-inserter")                                  # chunks in: everything, the valve throws out the surplus
    ins(-3, -5, S, ["calcite"], name="bulk-inserter")                     # the valve, drops into the hole at -3,-6; born harmless, its filter comes by wire
    filt.pop()                                                            # ... so config leaves it to VALVE_LUA
    holes.add((-3, -6))
    put("decider-combinator", -3, -8, 1, 2)                               # the valve's brain
    # Twelve bays: the Captain widened the spine by hand on 2026-11-18 (three bays west of it, two east), moved the chunk belt out to column -12
    # and the smelter row out to columns 6..11. The layout below is the ship as they left it.
    for tx, ty in ((-2, -8), (-2, -12), (-2, -16), (-2, -20), (-6, -12), (-6, -16), (-6, -20), (-10, -12), (-10, -16), (-10, -20), (2, -16), (2, -20)):
        put("cargo-bay", tx, ty, 4, 4)                                    # a bay must touch the hub or a bay
    ins(2, -5, S, ["iron-ore"], gate=("iron-plate", PLATE_CAP), name="bulk-inserter")     # ORE PORT
    ins(3, -5, N, ["iron-plate"], name="bulk-inserter")                   # PLATE PORT
    put("medium-electric-pole", 4, -5)                                    # the meter: network statistics are only readable through a pole
    belts([(2, -6), (2, -7), (2, -8)] + row(2, 5, -9) + col(6, -9, -20), N)   # ore: north, east under the bays' south edge, north again; dead end
    belts(col(7, -20, -9) + row(7, 4, -8) + [(3, -8), (3, -7), (3, -6)], S)   # plates: back the same way, ends at the port
    for yt in (-11, -14, -17, -20):
        put("electric-furnace", 9, yt, 3, 3)
        ins(8, yt, W, ["iron-ore"], name="long-handed-inserter")          # over the plate belt
        ins(8, yt + 2, E)
    # ---- west ----
    put("chemical-plant", -8, -6, 3, 3, d=E, recipe="thruster-oxidizer")  # facing east: water in on its east side, oxidizer out west
    ins(-5, -4, E, ["iron-ore"], gate=("iron-ore", 100, ">"))
    put("crusher", -8, -3, 3, 2, d=E)
    ins(-5, -3, E, ["metallic-asteroid-chunk"])
    ins(-5, -2, W)
    put("decider-combinator", -9, -3, 1, 2)
    put("decider-combinator", -11, -3, 1, 2)
    crushers.append(dict(pos=(-6.5, -2), a=(-8.5, -2), b=(-10.5, -2), ra="metallic-asteroid-crushing", rb="metallic-asteroid-reprocessing",
                         ca=[cnd("iron-ore", "<", ORE_CAP)],
                         cb=[cnd("iron-ore", ">=", ORE_CAP), cnd("carbon", "<", C_LOW, "and"), cnd("iron-ore", ">=", ORE_CAP, "or"), cnd("ice", "<", ICE_LOW, "and")]))
    ins(-5, -1, E, ["explosive-rocket"], name="bulk-inserter")            # ROCKET PORT
    belts([(-6, -1), (-7, -1), (-8, -1), (-9, -1, "in"), (-14, -1, "out"), (-15, -1), (-15, 0), (-14, 0)], E)   # under the loop and back: outer lane
    put("assembling-machine-3", -8, 0, 3, 3, recipe="firearm-magazine")
    ins(-5, 0, E, ["iron-plate"], gate=("firearm-magazine", MAG_CAP), name="bulk-inserter")
    ins(-5, 2, W)
    put("chemical-plant", -8, 3, 3, 3, recipe="ice-melting")
    ins(-5, 3, E, ["ice"])
    # ---- east ----
    put("chemical-plant", 5, -6, 3, 3, d=W, recipe="thruster-fuel")       # facing west: water in on its west side, fuel out east
    ins(4, -4, W, ["carbon"])                                             # gated by the fuel-first decider (FIRST)
    put("decider-combinator", 9, -6, 1, 2)                                # fuel gate
    put("decider-combinator", 9, 2, 1, 2)                                 # coal gate
    put("crusher", 5, -3, 3, 2, d=E)
    ins(4, -3, W, ["carbonic-asteroid-chunk"])
    ins(4, -2, E)
    put("decider-combinator", 9, -3, 1, 2)
    put("decider-combinator", 11, -3, 1, 2)
    full = [cnd("carbon", ">=", C_CAP), cnd("sulfur", ">=", 50, "and")]
    crushers.append(dict(pos=(6.5, -2), a=(9.5, -2), b=(11.5, -2), ra="advanced-carbonic-asteroid-crushing", rb="carbonic-asteroid-reprocessing",
                         ca=[cnd("carbon", "<", C_CAP), cnd("sulfur", "<", 50, "or")],
                         cb=full + [cnd("iron-ore", "<", ORE_LOW, "and"), cnd("carbon", ">=", C_CAP, "or"), cnd("sulfur", ">=", 50, "and"), cnd("ice", "<", ICE_LOW, "and")]))
    ins(4, -1, W, ["firearm-magazine"], name="bulk-inserter")             # MAGAZINE PORT
    belts([(5, -1), (6, -1), (7, -1, "in"), (11, -1, "out")], E)          # side-loads the loop from inside: inner lane
    put("assembling-machine-3", 5, 0, 3, 3, recipe="explosive-rocket")
    ins(4, 0, W, ["rocket", "explosives"], gate=("explosive-rocket", ER_CAP))
    ins(4, 2, E)
    put("chemical-plant", 5, 3, 3, 3, d=S, recipe="coal-synthesis")
    ins(4, 3, W, ["carbon", "sulfur"])                                    # gated by the fuel-first decider (FIRST)
    ins(4, 5, E)                                                          # coal round the corner into the explosives plant
    # ---- south ----
    put("crusher", -5, 5, 3, 2, d=E)
    ins(-4, 4, N, ["oxide-asteroid-chunk"])
    ins(-3, 4, S)
    put("decider-combinator", -5, 7, 2, 1, d=E)
    put("decider-combinator", -6, 9, 2, 1, d=E)
    crushers.append(dict(pos=(-3.5, 6), a=(-4, 7.5), b=(-5, 9.5), ra="oxide-asteroid-crushing", rb="oxide-asteroid-reprocessing",
                         ca=[cnd("ice", "<", ICE_CAP)],
                         cb=[cnd("ice", ">=", ICE_CAP), cnd("carbon", "<", C_LOW, "and"), cnd("ice", ">=", ICE_CAP, "or"), cnd("iron-ore", "<", ORE_LOW, "and")]))
    put("assembling-machine-3", -2, 5, 3, 3, recipe="rocket")
    ins(-2, 4, N, ["iron-plate", "explosives"], gate=("rocket", ROCKET_CAP))
    ins(0, 4, S)
    put("chemical-plant", 1, 5, 3, 3, d=S, recipe="explosives")
    ins(1, 4, N, ["sulfur"], gate=("explosives", EXPL_CAP))
    ins(3, 4, S)
    # ---- chunks: four collectors, one belt ----
    collector(-11, NY - 4, N)
    collector(8, NY - 4, N)
    ins(-8, NY - 3, W)
    ins(7, NY - 3, E)
    collector(-20, -21, W)
    collector(17, -21, E)
    ins(-17, -20, W)
    ins(16, -20, E)
    belts([(-7, NY - 3), (-7, NY - 2), (-7, NY - 1, "in"), (-7, NY + 1, "out")] + [(-7, NY + 2)] + row(-7, -12, -21) + col(-12, -20, -9) + row(-12, -4, -8) + [(-4, -7), (-4, -6)], S)
    belts([(6, NY - 3), (6, NY - 2), (6, NY - 1, "in"), (6, NY + 1, "out")] + row(6, -6, NY + 2), W)
    belts([(15, -20), (15, -21), (15, -22), (14, -22), (13, -22, "in"), (11, -22, "out")] + row(10, 7, -22), W)
    belts([(-16, -20), (-16, -21), (-16, -22), (-15, -22), (-14, -22, "in"), (-12, -22, "out")] + row(-11, -8, -22), E)
    # ---- the ammunition loop ----
    belts([(13, SY), (13, SY - 1)] + col(XE, SY - 1, NY) + row(XE - 1, XW, NY) + col(XW, NY + 1, SY - 3), S)
    put("express-splitter", XW - 1, SY - 2, 2, 1, d=S)
    belts([(XW, SY - 1)] + row(XW, XE - 1, SY), E)
    put("express-splitter", XE, SY, 1, 2, d=E)
    belts(col(XW - 1, SY - 1, SY + 10), S)                                # west spur
    belts(col(XE + 1, SY + 1, SY + 10), S)                                # east spur
    # ---- turrets ----
    for x in (-5, 2):
        rkt(x, NY - 4, x + 1, NY - 1, S)
    gun(-2, NY - 3, -2, NY - 1, S)
    gun(0, NY - 3, 1, NY - 1, S)
    # Nose corners (2026-11-18): on the second return leg, at 185 km/s with full tanks, the west nose collector was shot off: two guns in the middle
    # of the nose were all that covered it. Four more: one outboard of each nose collector, one at the top of each flank.
    gun(-13, NY - 3, -12, NY - 1, S)
    gun(11, NY - 3, 11, NY - 1, S)
    gun(XW - 3, NY, XW - 1, NY, E)
    gun(XE + 2, NY, XE + 1, NY, W)
    for y in (-18, -5, 9, 24, 39, 53):
        if y + 2 < SY - 2:
            rkt(XW - 4, y, XW - 1, y + 1, E)
            rkt(XE + 2, y, XE + 1, y + 1, W)
    for y in (-14, -10, 2, 5, 14, 19, 29, 34, 44, 49):
        if y + 1 < SY - 2:
            gun(XW - 3, y, XW - 1, y, E)
            gun(XE + 2, y, XE + 1, y, W)
    for g1, r1, g2 in ((SY + 1, SY + 4, SY + 9),):
        gun(XW - 4, g1, XW - 2, g1, E)
        rkt(XW - 5, r1, XW - 2, r1 + 1, E)
        gun(XW - 4, g2, XW - 2, g2, E)
        gun(XE + 3, g1, XE + 2, g1, W)
        rkt(XE + 3, r1, XE + 2, r1 + 1, W)
        gun(XE + 3, g2, XE + 2, g2, W)
    # ---- water ----
    pipe("water", (-6, 6), (-6, 7), (-8, 6), (-8, 7), *row(-12, 10, 8), (-3, 9), (0, 9), *col(-12, 7, -7), *row(-11, -5, -7), (-5, -6),
         *col(10, 7, -7), *row(9, 4, -7), (4, -6), (5, 6), (5, 7))
    put("storage-tank", -3, 10, 3, 3)
    put("storage-tank", 0, 10, 3, 3)
    # ---- oxidizer: west ----
    pipe("oxidizer", (-9, -4), *col(-10, -4, 6), *col(-10, 10, 22), (-11, 22), *col(-12, 22, SY - 2), *row(-12, 5, SY + 2))
    ptg("oxidizer", -10, 7, N)
    ptg("oxidizer", -10, 9, S)
    ptg("oxidizer", -12, SY - 1, N)
    ptg("oxidizer", -12, SY + 1, S)
    for x in (-7, 5):
        ptg("oxidizer", x, SY + 3, N)
        ptg("oxidizer", x, SY + 5, S)
        pipe("oxidizer", (x, SY + 6), (x, TY), (x, TY + 1), (x + 1, TY + 1), (x + 1, TY + 2))
    # ---- fuel: east ----
    pipe("fuel", (8, -4), *col(8, -3, 6), *col(8, 10, 22), (9, 22), (10, 22), *col(11, 22, SY - 2), (11, SY + 2), (11, SY + 3), *row(-12, 12, SY + 4),
         (-12, SY + 5), (-12, SY + 6), (-12, TY), (0, SY + 5), (0, SY + 6), (0, TY), (0, TY + 1), (-1, TY + 1), (-1, TY + 2), *col(12, SY + 5, TY + 2), (11, TY + 2))
    ptg("fuel", 8, 7, N)
    ptg("fuel", 8, 9, S)
    ptg("fuel", 11, SY - 1, N)
    ptg("fuel", 11, SY + 1, S)
    for j in range(4):
        put("storage-tank", -9, 10 + 3 * j, 3, 3)
        put("storage-tank", 9, 10 + 3 * j, 3, 3)
    put("constant-combinator", 5, 11)                                     # empty: a relay for the green wire to the fuel tanks
    for tx in (-11, -5, 1, 7):
        put("thruster", tx, TY, 4, 5)
    # ---- power ----
    for i in range(7):
        for j in range(ROWS):
            put("solar-panel", -11 + 3 * i, SOL_Y0 + 3 * j, 3, 3)
    for ax in range(-6, 8, 2):
        for ay in range(14, 22, 2):
            put("accumulator", ax, ay, 2, 2)
    # ---- checks ----
    for (x, y), f in fluid.items():
        for dx, dy in DIR:
            n = (x + dx, y + dy)
            g = fluid.get(n)
            joins = opening.get((x, y), (dx, dy)) == (dx, dy) and opening.get(n, (-dx, -dy)) == (-dx, -dy)
            assert g is None or g == f or not joins, "%s pipe at %s touches %s" % (f, (x, y), g)
    for x in range(-5, 5):
        for y in range(-5, 5):
            tiles.add((x, y))
    keep = {(x, y) for (x, y) in tiles if y <= TY + 4 and (x, y) not in holes and not (TY <= y and -11 <= x <= 10 and (x, y) not in occ)}
    keep = {t for t in keep if not (t[1] > TY + 4)}
    tiles.clear()
    tiles.update(keep)
    for c, n in occ.items():
        assert c in tiles or n == "asteroid-collector", "%s at %s has no deck" % (n, c)
    seen, todo = {(0, 0)}, [(0, 0)]
    while todo:
        x, y = todo.pop()
        for dx, dy in DIR:
            n = (x + dx, y + dy)
            if n in tiles and n not in seen:
                seen.add(n)
                todo.append(n)
    assert seen == tiles, "deck not in one piece: %s" % sorted(tiles - seen)[:8]
    kinds = {}
    for e in ents:
        kinds[e["name"]] = kinds.get(e["name"], 0) + 1
    return {"entities": len(ents), "tiles": len(tiles), "x": (min(x for x, y in tiles), max(x for x, y in tiles)),
            "y": (min(y for x, y in tiles), max(y for x, y in tiles)), "kinds": kinds}


GLYPH = {"express-transport-belt": "=", "express-underground-belt": "u", "express-splitter": "Y", "fast-inserter": "i", "bulk-inserter": "I", "long-handed-inserter": "l",
         "cargo-bay": "#", "crusher": "X", "electric-furnace": "F", "chemical-plant": "P", "assembling-machine-3": "M", "decider-combinator": "d",
         "constant-combinator": "c", "solar-panel": "s", "accumulator": "a", "pipe": "-", "pipe-to-ground": "~", "storage-tank": "K", "asteroid-collector": "C",
         "gun-turret": "g", "rocket-turret": "R", "thruster": "T", "medium-electric-pole": "!"}


def ascii_map():
    xs = range(min(x for x, y in tiles | set(occ)) - 1, max(x for x, y in tiles | set(occ)) + 2)
    out = []
    for y in range(min(y for x, y in tiles | set(occ)) - 1, TY + 6):
        line = ""
        for x in xs:
            if -4 <= x < 4 and -4 <= y < 4:
                line += "H"
            elif (x, y) in occ:
                line += GLYPH.get(occ[(x, y)], "?")
            else:
                line += "." if (x, y) in tiles else " "
        out.append("%4d %s" % (y, line))
    return "\n".join(out)


# ------------------------------------------------------------------ the game
def L(code):
    from _game import tools
    return tools["run_lua"](code)


AT = "local p for _,q in pairs(game.forces.player.platforms) do if q.name:find('%s',1,true) then p=q end end if not p then rcon.print('no platform') return end local s=p.surface local hub=p.hub " % NAME


def surface():
    r = L(AT + "rcon.print(s.name..'|'..p.index)").strip()
    return None if r == "no platform" else r.split("|")


REQUEST = (AT + "local pt for _,q in pairs(hub.get_logistic_point()) do if q.mode==defines.logistic_mode.requester then pt=q end end local sec for _,q in pairs(pt.sections) do if q.group=='' and q.filters_count<=1 then sec=q end end "
           "sec=sec or pt.add_section() if COUNT>0 then sec.set_slot(1,{value={type='item',name='space-platform-foundation',quality='normal'},min=COUNT,import_from='nauvis'}) else sec.clear_slot(1) end "
           "rcon.print('foundation request '..tostring(COUNT)..', aboard '..hub.get_inventory(defines.inventory.hub_main).get_item_count('space-platform-foundation'))")
DECK = (AT + "local n,have=0,0 for _,q in pairs(CELLS) do if s.get_tile(q[1],q[2]).name=='space-platform-foundation' then have=have+1 elseif s.count_entities_filtered{type='tile-ghost',position={q[1]+0.5,q[2]+0.5},radius=0.3}==0 then "
        "if s.create_entity{name='tile-ghost',inner_name='space-platform-foundation',position={q[1],q[2]},force='player'} then n=n+1 end end end rcon.print(have..'|'..n)")
STAND = (AT + "local t={} for _,q in pairs(s.find_tiles_filtered{name='space-platform-foundation'}) do t[#t+1]=q.position.x..','..q.position.y end local e={} "
         "for _,q in pairs(s.find_entities_filtered{force='player'}) do if q.type~='entity-ghost' and q.type~='tile-ghost' then e[#e+1]=q.name..'@'..q.position.x..','..q.position.y end end "
         "rcon.print(table.concat(t,';')..'|'..table.concat(e,';')..'|'..hub.get_inventory(defines.inventory.hub_main).get_item_count('space-platform-foundation')..'|'..s.count_entities_filtered{type='tile-ghost'})")

HEAD = AT + "local W=defines.wire_connector_id local function I(n) return {type='item',name=n} end local function join(a,b) if not a.is_connected_to(b) then return a.connect_to(b,false) end return true end "
CONFIG = (HEAD + "local n,r,g,miss=0,0,0,0 local function ins(x,y) return s.find_entities_filtered{type='inserter',position={x,y},radius=0.3}[1] end "
          "pcall(function() hub.get_or_create_control_behavior().read_contents=true end) "
          "for _,q in pairs(FILT) do local i=ins(q[1],q[2]) if i then i.use_filters=true i.inserter_filter_mode='whitelist' for k,name in pairs(q[3]) do i.set_filter(k,name) end n=n+1 else miss=miss+1 end end "
          "for _,q in pairs(REC) do for _,m in pairs(s.find_entities_filtered{type='assembling-machine',position={q[1],q[2]},radius=0.5}) do if not m.get_recipe() or m.get_recipe().name~=q[3] then m.set_recipe(q[3]) end r=r+1 end end "
          "for _,q in pairs(GATES) do local i=ins(q[1],q[2]) if i then join(i.get_wire_connector(W.circuit_red,true),hub.get_wire_connector(W.circuit_red,true)) local cb=i.get_or_create_control_behavior() cb.circuit_enable_disable=true "
          "cb.circuit_condition={first_signal=I(q[3]),comparator=q[5],constant=q[4]} g=g+1 else miss=miss+1 end end "
          "rcon.print('inserters filtered '..n..', recipes '..r..', gates '..g..', missing '..miss)")
CRUSH = (HEAD + "local function dec(x,y) return s.find_entities_filtered{name='decider-combinator',position={x,y},radius=0.6}[1] end local o={} "
         "for _,k in pairs(LIST) do local c=s.find_entities_filtered{name='crusher',position=k.pos,radius=0.6}[1] local a,b=dec(k.a[1],k.a[2]),dec(k.b[1],k.b[2]) if c and a and b then "
         "a.get_or_create_control_behavior().parameters={conditions=k.ca,outputs={{signal={type='recipe',name=k.ra},copy_count_from_input=false,constant=1}}} "
         "b.get_or_create_control_behavior().parameters={conditions=k.cb,outputs={{signal={type='recipe',name=k.rb},copy_count_from_input=false,constant=1}}} "
         "local ok=join(a.get_wire_connector(W.combinator_input_red,true),hub.get_wire_connector(W.circuit_red,true)) and join(b.get_wire_connector(W.combinator_input_red,true),a.get_wire_connector(W.combinator_input_red,true)) "
         "and join(b.get_wire_connector(W.combinator_output_green,true),a.get_wire_connector(W.combinator_output_green,true)) and join(c.get_wire_connector(W.circuit_green,true),a.get_wire_connector(W.combinator_output_green,true)) "
         "c.get_or_create_control_behavior().circuit_set_recipe=true o[#o+1]=k.ra..' wired '..tostring(ok) else o[#o+1]=k.ra..' MISSING' end end rcon.print(table.concat(o,', '))")
VALVE_LUA = (HEAD + "local dec=s.find_entities_filtered{name='decider-combinator',position={-2.5,-7},radius=0.6}[1] local cc=s.find_entities_filtered{name='constant-combinator',position={-4.5,-4.5},radius=0.4}[1] "
             "local v=s.find_entities_filtered{type='inserter',position={-2.5,-4.5},radius=0.3}[1] if not (dec and cc and v) then rcon.print('valve parts missing') return end "
             "local cb0=cc.get_or_create_control_behavior() local sec=cb0.get_section(1) or cb0.add_section() local k=0 "
             "for name,c in pairs(CAPS) do k=k+1 sec.set_slot(k,{value={type='item',name=name,quality='normal'},min=c}) end "
             "dec.get_or_create_control_behavior().parameters={conditions={{first_signal={type='virtual',name='signal-each'},first_signal_networks={red=true,green=false},comparator='>',second_signal={type='virtual',name='signal-each'},second_signal_networks={red=false,green=true}},"
             "{first_signal={type='virtual',name='signal-each'},first_signal_networks={red=false,green=true},comparator='>',constant=0,compare_type='and'}},outputs={{signal={type='virtual',name='signal-each'},copy_count_from_input=false}}} "
             "local a=join(dec.get_wire_connector(W.combinator_input_red,true),hub.get_wire_connector(W.circuit_red,true)) local b=join(dec.get_wire_connector(W.combinator_input_green,true),cc.get_wire_connector(W.circuit_green,true)) "
             "local c=join(v.get_wire_connector(W.circuit_green,true),dec.get_wire_connector(W.combinator_output_green,true)) v.use_filters=true v.inserter_filter_mode='whitelist' local cb=v.get_or_create_control_behavior() cb.circuit_set_filters=true cb.circuit_enable_disable=true "
             "cb.circuit_condition={first_signal={type='virtual',name='signal-anything'},comparator='>',constant=0} rcon.print('valve wired '..tostring(a and b and c)..', caps '..k)")
TURRETS = (AT + "local r,g=0,0 for _,t in pairs(s.find_entities_filtered{name='rocket-turret'}) do local i=0 for _,sz in pairs{'big','huge'} do for _,k in pairs{'metallic','carbonic','oxide'} do i=i+1 t.set_priority_target(i,sz..'-'..k..'-asteroid') end end "
           "t.ignore_unprioritised_targets=true r=r+1 end for _,t in pairs(s.find_entities_filtered{name='gun-turret'}) do local i=0 for _,sz in pairs{'medium','small'} do for _,k in pairs{'metallic','carbonic','oxide'} do i=i+1 t.set_priority_target(i,sz..'-'..k..'-asteroid') end end "
           "t.ignore_unprioritised_targets=true g=g+1 end rcon.print('rocket turrets on big and huge only: '..r..', gun turrets on medium then small only: '..g)")
TANKS = (HEAD + "local function tank(x,y) return s.find_entities_filtered{name='storage-tank',position={x,y},radius=0.5}[1] end local ok=true local n=0 local function link(a,b) if a and b then if join(a.get_wire_connector(W.circuit_green,true),b.get_wire_connector(W.circuit_green,true)) then n=n+1 else ok=false end else ok=false end end "
         "local relay=s.find_entities_filtered{name='constant-combinator',position={5.5,11.5},radius=0.4}[1] local w1,w2=tank(-1.5,11.5),tank(1.5,11.5) link(hub,w1) link(w1,w2) link(w2,relay) "
         "local prev=w1 for j=0,3 do local t=tank(-7.5,11.5+3*j) link(prev,t) prev=t end prev=relay for j=0,3 do local t=tank(10.5,11.5+3*j) link(prev,t) prev=t end "
         "local sg=hub.get_signals(defines.wire_connector_id.circuit_green) local f={} for _,q in pairs(sg or {}) do if q.signal.type=='fluid' then f[#f+1]=q.signal.name..' '..q.count end end "
         "rcon.print('tank wires '..n..' ok '..tostring(ok)..' | green at the hub: '..table.concat(f,', '))")

# Fuel first (2026-11-18). Parked at Nauvis the catch was about 10 carbonic chunks a minute; with the coal plant given first call the ship made 15 rockets
# and only 1,049 fuel a minute, and a shuttle that cannot fuel cannot keep a timetable. Two deciders read the hub (items on red, tanks on green):
#   fuel plant takes carbon   while carbon > 200, or while the tanks hold less than FUEL_FIRST
#   coal plant takes carbon   while explosives < cap and (tanks at FUEL_FIRST or more, or carbon > 300, or fewer than ROCKET_FLOOR rockets in the hub)
# so rockets come first only under the floor, then fuel up to the level a leg needs, then rockets up to their cap.
FIRST = (HEAD + "local function dec(x,y) return s.find_entities_filtered{name='decider-combinator',position={x,y},radius=0.6}[1] end local function ins(x,y) return s.find_entities_filtered{type='inserter',position={x,y},radius=0.3}[1] end "
         "local df,dc,kc=dec(9.5,-5),dec(9.5,3),dec(9.5,-2) local fi,ci=ins(4.5,-3.5),ins(4.5,3.5) if not (df and dc and kc and fi and ci) then rcon.print('fuel-first parts missing') return end "
         "local R={red=true,green=false} local G={red=false,green=true} local function c(sig,cmp,k,net,how) return {first_signal=sig,first_signal_networks=net,comparator=cmp,constant=k,compare_type=how} end local F={type='fluid',name='thruster-fuel'} "
         "df.get_or_create_control_behavior().parameters={conditions={c(I('carbon'),'>',200,R),c(F,'<',FUELFIRST,G,'or')},outputs={{signal={type='virtual',name='signal-F'},copy_count_from_input=false,constant=1}}} "
         "dc.get_or_create_control_behavior().parameters={conditions={c(I('explosives'),'<',EXPLCAP,R),c(F,'>=',FUELFIRST,G,'and'),c(I('explosives'),'<',EXPLCAP,R,'or'),c(I('carbon'),'>',300,R,'and'),c(I('explosives'),'<',EXPLCAP,R,'or'),c(I('explosive-rocket'),'<',FLOOR,R,'and')},"
         "outputs={{signal={type='virtual',name='signal-C'},copy_count_from_input=false,constant=1}}} local ok=true "
         "for _,q in pairs({{df,fi,'signal-F'},{dc,ci,'signal-C'}}) do local d,i=q[1],q[2] ok=join(d.get_wire_connector(W.combinator_input_red,true),kc.get_wire_connector(W.combinator_input_red,true)) and ok "
         "ok=join(d.get_wire_connector(W.combinator_input_green,true),hub.get_wire_connector(W.circuit_green,true)) and ok ok=join(i.get_wire_connector(W.circuit_green,true),d.get_wire_connector(W.combinator_output_green,true)) and ok "
         "local hr,ir=hub.get_wire_connector(W.circuit_red,true),i.get_wire_connector(W.circuit_red,true) if ir.is_connected_to(hr) then ir.disconnect_from(hr) end "
         "local cb=i.get_or_create_control_behavior() cb.circuit_enable_disable=true cb.circuit_condition={first_signal={type='virtual',name=q[3]},comparator='>',constant=0} end rcon.print('fuel first wired '..tostring(ok))")

STATUS = (AT + "local st={} local sm={} for k,v in pairs(defines.entity_status) do sm[v]=k end for _,c in pairs(s.find_entities_filtered{type={'assembling-machine','furnace','asteroid-collector','ammo-turret'}}) do local k=sm[c.status] or '?' "
          "local rc=c.type=='assembling-machine' and c.get_recipe() k=(rc and rc.name or c.name)..' '..k st[k]=(st[k] or 0)+1 end local o={} for k,v in pairs(st) do o[#o+1]=k..' '..v end table.sort(o) local fl={} for _,t in pairs(s.find_entities_filtered{name='storage-tank'}) do for k,v in pairs(t.get_fluid_contents()) do fl[k]=(fl[k] or 0)+v end end "
          "local f={} for k,v in pairs(fl) do f[#f+1]=k..' '..math.floor(v) end local inv=hub.get_inventory(defines.inventory.hub_main) local c={} for _,it in pairs(inv.get_contents()) do c[#c+1]=it.name..' '..it.count end table.sort(c) "
          "local a,cap=0,0 for _,e in pairs(s.find_entities_filtered{name='accumulator'}) do a=a+e.energy cap=cap+e.electric_buffer_size end local dmg=0 for _,e in pairs(s.find_entities_filtered{force='player'}) do if e.is_entity_with_health and e.health<e.max_health then dmg=dmg+1 end end "
          "local empty,least=0,999 for _,t in pairs(s.find_entities_filtered{type='ammo-turret'}) do local k=t.get_inventory(defines.inventory.turret_ammo).get_item_count() if k==0 then empty=empty+1 end if k<least then least=k end end "
          "local mods={} for _,m in pairs(s.find_entities_filtered{type={'assembling-machine','furnace'}}) do local mi=m.get_module_inventory() if mi then for _,it in pairs(mi.get_contents()) do mods[it.name]=(mods[it.name] or 0)+it.count end end end local mo={} for k,v in pairs(mods) do mo[#mo+1]=k..' '..v end "
          "local tr=hub.get_inventory(defines.inventory.hub_trash) local sc=p.schedule local wait=sc and p.get_schedule().ticks_in_station or -1 "
          "rcon.print(table.concat(o,' ; ')..' ; TANKS '..table.concat(f,', ')..' ; HUB slots '..#inv..' free '..inv.count_empty_stacks()..': '..table.concat(c,', ')..' ; trash slots used '..(tr and (#tr-tr.count_empty_stacks()) or 0)..' ; modules '..table.concat(mo,', ')"
          "..' ; accumulators '..string.format('%.0f%%',cap>0 and 100*a/cap or 0)..', damaged '..dmg..', entity ghosts '..s.count_entities_filtered{type='entity-ghost'}..', tile ghosts '..s.count_entities_filtered{type='tile-ghost'}..', turrets empty '..empty..' least '..least"
          "..' ; at '..(p.space_location and p.space_location.name or 'in transit')..', speed '..string.format('%.1f',p.speed*60)..' km/s, weight '..math.floor(p.weight/1000)..' t, paused '..tostring(p.paused)..', stop '..(sc and sc.current or 0)..', ticks in station '..tostring(wait))")

# cumulative counters: production statistics of the platform's surface, crafts finished by recipe, the meter pole's energy counters, chunk stock
SNAP = (AT + "local f=game.forces.player local it=f.get_item_production_statistics(s) local fl=f.get_fluid_production_statistics(s) local o={tick=game.tick,made={},used={},crafts={},chunks={},power={},draw={}} "
        "for _,n in pairs{'explosive-rocket','rocket','firearm-magazine','explosives','coal','iron-plate','iron-ore','carbon','sulfur','ice','metallic-asteroid-chunk','carbonic-asteroid-chunk','oxide-asteroid-chunk'} do o.made[n]=it.get_input_count(n) o.used[n]=it.get_output_count(n) end "
        "for _,n in pairs{'thruster-fuel','thruster-oxidizer','water'} do o.made[n]=fl.get_input_count(n) o.used[n]=fl.get_output_count(n) end "
        "for _,m in pairs(s.find_entities_filtered{type='assembling-machine'}) do local rc=m.get_recipe() local k=m.name=='crusher' and string.format('crusher at %.1f,%.1f (products, any recipe)',m.position.x,m.position.y) or (rc and rc.name) if k then o.crafts[k]=(o.crafts[k] or 0)+m.products_finished end end "
        "local inv=hub.get_inventory(defines.inventory.hub_main) for _,n in pairs{'metallic-asteroid-chunk','carbonic-asteroid-chunk','oxide-asteroid-chunk'} do local c=inv.get_item_count(n) "
        "for _,b in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt'}}) do for li=1,2 do c=c+b.get_transport_line(li).get_item_count(n) end end "
        "for _,k in pairs(s.find_entities_filtered{type={'asteroid-collector','assembling-machine','inserter'}}) do if k.type=='inserter' then if k.held_stack.valid_for_read and k.held_stack.name==n then c=c+k.held_stack.count end else c=c+k.get_item_count(n) end end o.chunks[n]=c end "
        "local pole=s.find_entities_filtered{type='electric-pole',limit=1}[1] if pole then local st=pole.electric_network_statistics for n,v in pairs(st.output_counts) do o.power[n]=v end for n,v in pairs(st.input_counts) do o.draw[n]=v end end "
        "o.sun=(p.space_location and p.space_location.solar_power_in_space or 100)/100 o.panels=s.count_entities_filtered{name='solar-panel'} rcon.print(helpers.table_to_json(o))")


def lua_list(rows):
    return "{" + ",".join(rows) + "}"


def configure():
    f = lua_list("{%s,%s,{%s}}" % (x, y, ",".join("'%s'" % n for n in names)) for x, y, names in filt)
    rec = lua_list("{%s,%s,'%s'}" % r for r in recipes)
    gt = lua_list("{%s,%s,'%s',%d,'%s'}" % g for g in gates)
    print(L(CONFIG.replace("FILT", f).replace("REC", rec).replace("GATES", gt)))
    ks = lua_list("{pos={%s,%s},a={%s,%s},b={%s,%s},ra='%s',rb='%s',ca={%s},cb={%s}}" % (k["pos"] + k["a"] + k["b"] + (k["ra"], k["rb"], ",".join(k["ca"]), ",".join(k["cb"]))) for k in crushers)
    print(L(CRUSH.replace("LIST", ks)))
    print(L(VALVE_LUA.replace("CAPS", "{" + ",".join("['%s']=%d" % kv for kv in VALVE.items()) + "}")))
    print(L(TURRETS))
    print(L(TANKS))
    print(L(FIRST.replace("FUELFIRST", str(FUEL_FIRST)).replace("FLOOR", str(ROCKET_FLOOR)).replace("EXPLCAP", str(EXPL_CAP))))


def standing():
    t, e, stock, ghosts = L(STAND).strip().split("|")
    have = {tuple(int(float(v)) for v in c.split(",")) for c in t.split(";") if c}
    there = set(e.split(";")) if e else set()
    return have, there, int(stock), int(ghosts)


def build(apply):
    from _game import tools
    have, there, stock, ghosts = standing()
    todo, waiting = [], 0
    for e, own in zip(ents, cells):
        if "%s@%g,%g" % (e["name"], e["x"], e["y"]) in there:
            continue
        if all(c in have for c in own if c not in holes):
            todo.append(e)
        else:
            waiting += 1
    print("standing %d, to place %d, waiting for deck %d (deck %d of %d, foundation aboard %d, tile ghosts %d)" % (len(there), len(todo), waiting, len(have & tiles), len(tiles), stock, ghosts))
    ok = bad = 0
    sf = surface()[0]
    for i in range(0, len(todo), 400):
        r = json.loads(tools["place_entities"](json.dumps(todo[i:i + 400]), surface=sf, dry_run=not apply))
        f = r.get("failed") or []
        ok += r.get("placed", 0)
        bad += len(f)
        if f:
            print("failed", json.dumps(f)[:700])
    print("placed" if apply else "dry run", ok, "failed", bad)
    if apply and ok:
        configure()                                                  # gates and wires at once: a new machine must not run ungated
    return waiting


def route(home, dest, go):
    """HOME <-> DEST on the timed pattern. Each stop has its own RUN levels: the far stop asks only for what the leg home needs, because
    a ship that waits in Aquilo orbit for rockets it cannot make there fast enough is a ship that is being eaten."""
    kind = "outer" if "aquilo" in (dest, home) else "inner"

    def c(fluidname, k):
        return {"type": "circuit", "compare_type": "and", "condition": {"first_signal": {"type": "fluid", "name": fluidname}, "comparator": ">=", "constant": k}}

    def ic(item, k):
        return {"type": "item_count", "compare_type": "and", "condition": {"first_signal": {"type": "item", "name": item}, "comparator": ">=", "constant": k}}

    def stop(station, r, tmax):
        run = [c("thruster-fuel", r["fuel"]), c("thruster-oxidizer", r["fuel"]), ic("firearm-magazine", r["mags"])] + ([ic("explosive-rocket", r["rockets"])] if r["rockets"] else [])
        fb = [dict(x) for x in run]
        fb[0]["compare_type"] = "or"
        return {"station": station, "wait_conditions": run + [{"type": "inactivity", "compare_type": "and", "ticks": QUIET * 60}, {"type": "time", "compare_type": "and", "ticks": TMIN * 60}]
                + fb + [{"type": "time", "compare_type": "and", "ticks": tmax * 60}]}

    here = L(AT + "rcon.print(p.space_location and p.space_location.name or 'none')").strip()
    stops = [stop(home, RUNS[kind]["home"], TMAX_HOME), stop(dest, RUNS[kind]["away"], TMAX_FAR)]
    sc = {"current": 2 if here == dest else 1, "records": stops}
    js = json.dumps(sc).replace("\\", "\\\\").replace("'", "\\'")
    print(L(AT + "p.schedule=helpers.json_to_table('%s') p.paused=%s rcon.print('schedule %s <-> %s (%s), current '..p.schedule.current..', paused '..tostring(p.paused))"
            % (js, "false" if go else "true", home, dest, kind)))
    for st in stops:
        print("  %-9s RUN %s | then quiet %d s and %d s, or %d s" % (st["station"], RUNS[kind]["home" if st["station"] == home else "away"], QUIET, TMIN, (TMAX_HOME if st["station"] == home else TMAX_FAR)))


def snap():
    return json.loads(L(SNAP))


def rates(seconds, catch):
    if catch:                                                        # the valve would throw the catch away uncounted: lift the chunk caps for the window
        caps = dict(VALVE)
        caps.update({k: 400 for k in caps if "chunk" in k})
        print(L(VALVE_LUA.replace("CAPS", "{" + ",".join("['%s']=%d" % kv for kv in caps.items()) + "}")))
    a = snap()
    time.sleep(seconds)
    b = snap()
    if catch:
        print(L(VALVE_LUA.replace("CAPS", "{" + ",".join("['%s']=%d" % kv for kv in VALVE.items()) + "}")))
    mins = (b["tick"] - a["tick"]) / 3600.0
    if mins <= 0:
        sys.exit("the game did not advance")
    print("over %.2f game minutes, per minute:" % mins)
    for n in sorted(b["made"]):
        made, used = (b["made"][n] - a["made"].get(n, 0)) / mins, (b["used"][n] - a["used"].get(n, 0)) / mins
        if made or used:
            print("  %-26s made %9.1f   used %9.1f" % (n, made, used))
    print("crafts finished per minute:")
    for n in sorted(b["crafts"]):
        d = (b["crafts"][n] - a["crafts"].get(n, 0)) / mins
        if d:
            print("  %-40s %8.1f" % (n, d))
    if catch:
        # A crusher's products_finished cannot be split by recipe once the recipe changes by circuit, and the statistics leave chunks out of crushing.
        # So the chunks CRUSHED are read off the products (with +100% productivity: 10 ice, 10 carbon, 40 iron ore a chunk); chunks that went through
        # reprocessing are not in this number, so the real catch is this or a little more.
        print("chunks crushed per minute, from the products (reprocessed chunks not counted):")
        for kind, item, per in (("metallic", "iron-ore", 40.0), ("carbonic", "carbon", 10.0), ("oxide", "ice", 10.0)):
            n = kind + "-asteroid-chunk"
            print("  %-10s %6.1f   stock aboard %d -> %d" % (kind, (b["made"][item] - a["made"].get(item, 0)) / mins / per, a["chunks"][n], b["chunks"][n]))
    secs = (b["tick"] - a["tick"]) / 60.0
    made = sum(b["power"].get(n, 0) - a["power"].get(n, 0) for n in b["power"]) / secs / 1e6
    print("power: made %.2f MW; panels %d x 150 kW x sun %.2f here = %.2f MW available (Aquilo orbit, sun 0.60: %.2f MW)" % (made, b["panels"], b["sun"], b["panels"] * 0.15 * b["sun"], b["panels"] * 0.15 * 0.6))
    draw = sorted(((b["draw"][n] - a["draw"].get(n, 0)) / secs / 1e6, n) for n in b["draw"])
    print("  drawn %.2f MW: %s" % (sum(d for d, n in draw), ", ".join("%s %.2f" % (n, d) for d, n in reversed(draw) if d > 0.005)))


def main():
    a = sys.argv[1:]
    step = a[0] if a else "check"
    info = layout()
    if step in ("check", "map"):
        print(info)
        if step == "map":
            print(ascii_map())
        return
    from _game import tools
    from _wheels import create
    if step == "create":
        print("save:", tools["save_game"]("pre-universal-shuttle"))
        print(create(NAME, PLANET))
        return
    sf = surface()
    if not sf:
        sys.exit("no platform named " + NAME)
    print("==", NAME, sf[0], "platform", sf[1])
    if step == "request":
        n = int(a[1]) if len(a) > 1 else len(tiles) + 200
        print(L(REQUEST.replace("COUNT", str(n))))
    elif step == "deck":
        have = laid = 0
        ts = sorted(tiles, key=lambda t: abs(t[0]) + abs(t[1]))
        for i in range(0, len(ts), 1500):
            h, n = L(DECK.replace("CELLS", lua_list("{%d,%d}" % t for t in ts[i:i + 1500]))).strip().split("|")
            have, laid = have + int(h), laid + int(n)
        print("deck tiles %d: standing %d, ghosts laid now %d" % (len(ts), have, laid))
    elif step == "build":
        build("--apply" in a)
    elif step == "config":
        configure()
    elif step == "route":
        names = [x for x in a[1:] if not x.startswith("--")]
        route(names[0] if len(names) > 1 else PLANET, names[-1], "--go" in a)
    elif step == "status":
        print(L(STATUS).replace(" ; ", "\n"))
    elif step == "rates":
        rates(int(a[1]) if len(a) > 1 and a[1].isdigit() else 120, "--catch" in a)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
