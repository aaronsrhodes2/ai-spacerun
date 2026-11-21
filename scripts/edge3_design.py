#!/usr/bin/env python3
"""Edgerunner 3 = the UNIVERSAL 1 PROTO with a big T on its nose (the Captain, 2026-11-21: "take the universal proto and use that as the basis for
our edge runner ... add a big T shape onto the top of it, where it breaks through with railguns everything that it comes in contact with ... and
railguns to the sides as well, because when we're at rest we do need railguns to protect from the incoming ones while we're loading").
READ-ONLY: reads the live ship (platform-20), computes the extension, places nothing. The blueprint `universal-1-proto v1` (designs/) is the way back.

THE SHIP AS IT STANDS (tiles, nose north at y = -29, x -17..16 across the nose, 100 long): 12 cargo bays, 4 collectors, 16 rocket turrets, 30 guns, 84 panels, 28
accumulators, 4 thrusters, a closed ammunition loop (outer lane explosive rockets, inner lane magazines) round the whole hull.
WHAT IS ADDED
  T bar      a crossbar of width 2 x BAR_HALF on the nose, tiles y BAR_TOP .. -30, joined to the stem along the whole nose
  front line railguns 3 wide x 4 deep side by side along the bar's top row, facing NORTH, feed inserters one row behind, one rounds belt behind those.
             Nothing of ours stands in front of the bar, so no shot line crosses our parts.
  bar inside the bar's body behind the belt: a fusion plant (4 reactors, 8 generators, 2 coolers) in the middle, accumulators in both wings
  collectors the 4 collectors move to the bar's top row (an asteroid collector needs four empty columns in front of its centre); the chunk belt is re-laid down the stem
  rounds     the loop's OUTER lane carries RAILGUN ROUNDS instead of explosive rockets (rockets cannot touch a huge asteroid): the existing rocket port at the hub
             changes its filter; a filtered splitter at the nose feeds the bar's belt; the 16 rocket turrets become railguns on the same pads
  ears       railguns on new deck outside the flanks, facing WEST or EAST (SOUTH-west / -east where a west-facing arc would cross the bar): for the ship at rest
  tail       2 railguns facing SOUTH at the stern
Steps: plan | map | arcs        Usage: edge3_design.py plan ; edge3_design.py map"""
import json
import math
import sys

from _game import tools

L = tools["run_lua"]
BAR_HALF = 80
BAR_TOP = -66
NOSE_Y = -30
RW, RH = 3, 4
ARC = math.radians(36)
RANGE = 50
EAR_PITCH = 12
ACC_PER = 30            # MJ per legendary accumulator

FETCH = ("local s=game.surfaces['platform-20'] local o={} for _,e in pairs(s.find_entities_filtered{force='player'}) do local b=e.bounding_box o[#o+1]={e.name,math.floor(b.left_top.x+0.01),math.floor(b.left_top.y+0.01),math.ceil(b.right_bottom.x-0.01)-math.floor(b.left_top.x+0.01),math.ceil(b.right_bottom.y-0.01)-math.floor(b.left_top.y+0.01),e.direction} end "
         "local t={} for _,tl in pairs(s.find_tiles_filtered{name='space-platform-foundation'}) do t[#t+1]={tl.position.x,tl.position.y} end rcon.print(helpers.table_to_json({e=o,t=t,w=s.platform.weight}))")


def tiles_of(e):
    _, x, y, w, h, _ = e
    return {(x + i, y + j) for i in range(w) for j in range(h)}


def load():
    r = json.loads(L(FETCH))
    return [tuple(e) for e in r["e"]], {tuple(t) for t in r["t"]}, r["w"]


def build():
    ents, deck, weight = load()
    keep = [e for e in ents if e[0] != "rocket-turret" and not (e[0] == "asteroid-collector" and e[2] < -15)]
    removed = [e for e in ents if e not in keep]
    new, newdeck = [], set()
    # T bar deck
    for y in range(BAR_TOP, NOSE_Y + 1):
        for x in range(-BAR_HALF, BAR_HALF):
            if (x, y) not in deck:
                newdeck.add((x, y))
    # front line
    for i in range((2 * BAR_HALF) // RW):
        x = -BAR_HALF + i * RW
        new.append(("railgun", x, BAR_TOP, RW, RH, "N"))
        new.append(("inserter", x + 1, BAR_TOP + RH, 1, 1, 0))
    new.append(("rounds-belt-front", -BAR_HALF, BAR_TOP + RH + 1, 2 * BAR_HALF, 1, 0))
    # collectors on the front row between railgun groups would take railgun slots: they go on the wing tips and the stem line instead
    for cx in (-BAR_HALF + 2, -40, 40, BAR_HALF - 5):
        new = [n for n in new if not (n[0] in ("railgun", "inserter") and cx - 2 <= n[1] <= cx + 3 and n[2] <= BAR_TOP + RH)]
        new.append(("asteroid-collector", cx, BAR_TOP, 3, 3, "N"))
    # rocket turrets become railguns on the same pads
    for e in removed:
        if e[0] == "rocket-turret":
            new.append(("railgun-pad", e[1], e[2], RW, RH, "OUT"))
    # blocks inside the bar
    blocks = [("fusion plant (4 reactors, 8 generators, 2 coolers)", -28, BAR_TOP + 7, 56, 16),
              ("accumulators west wing", -BAR_HALF + 4, BAR_TOP + 7, 46, 14),
              ("accumulators east wing", BAR_HALF - 50, BAR_TOP + 7, 46, 14),
              ("chunk belt down the stem and spare", -3, BAR_TOP + 24, 6, 28)]
    return ents, keep, removed, new, deck, newdeck, blocks, weight


def ears(keep, new, deck):
    """Ears on new deck outside the flanks, every EAR_PITCH rows, facing W/E; if that arc fouls the bar or the stem, SW/SE."""
    xs = [t[0] for t in deck]
    out, extra = [], set()
    rows = {}
    for (x, y) in deck:
        lo, hi = rows.get(y, (10 ** 9, -10 ** 9))
        rows[y] = (min(lo, x), max(hi, x))
    for side in (-1, 1):
        for y in range(-24, 72, EAR_PITCH):
            if y not in rows:
                continue
            lo, hi = rows[y]
            edge = lo if side < 0 else hi
            x0 = edge - RH - 1 if side < 0 else edge + 2
            out.append(["railgun-ear", x0, y, RH, RW, "W" if side < 0 else "E"])
            for i in range(RH):
                for j in range(RW):
                    extra.add((x0 + i, y + j))
    for sx in (-6, 3):
        out.append(["railgun-ear", sx, 74, RW, RH, "S"])
        for i in range(RW):
            for j in range(RH):
                extra.add((sx + i, 74 + j))
    return out, extra


FACE = {"N": 0.0, "S": math.pi, "W": -math.pi / 2, "E": math.pi / 2, "SW": -3 * math.pi / 4, "SE": 3 * math.pi / 4, "OUT": None}


def foul(e, occ, face):
    cx, cy = e[1] + e[3] / 2, e[2] + e[4] / 2
    hit = set()
    for (tx, ty), o in occ.items():
        if o is e:
            continue
        dx, dy = tx + 0.5 - cx, ty + 0.5 - cy
        d = math.hypot(dx, dy)
        if d < 2.5 or d > RANGE:
            continue
        diff = abs((math.atan2(dx, -dy) - face + math.pi) % (2 * math.pi) - math.pi)
        if diff <= ARC:
            hit.add(o[0])
    return hit


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "plan"
    ents, keep, removed, new, deck, newdeck, blocks, weight = build()
    ear_list, ear_deck = ears(keep, new, deck | newdeck)
    occ = {}
    for e in keep + new:
        if e[0] in ("railgun", "railgun-pad"):
            continue
        for t in tiles_of(e):
            occ[t] = e
    for b in blocks:
        for i in range(b[3]):
            for j in range(b[4]):
                occ[(b[1] + i, b[2] + j)] = ("block",) + b[1:]
    # arcs: front line is clear by construction; test the ears (W/E, else SW/SE) and the pads (outward from the flank)
    fouled, fixed = [], 0
    for e in ear_list:
        e = tuple(e)
        facing = e[5]
        hit = foul(e, occ, FACE[facing])
        if hit and facing in ("W", "E"):
            alt = "SW" if facing == "W" else "SE"
            hit2 = foul(e, occ, FACE[alt])
            if not hit2:
                facing, hit, fixed = alt, hit2, fixed + 1
        if hit:
            fouled.append((e[1], e[2], facing, sorted(hit)))
    pads_bad = []
    for p in (n for n in new if n[0] == "railgun-pad"):
        side = "W" if p[1] < 0 else "E"
        hit = foul(p, occ, FACE[side])
        if hit:
            pads_bad.append((p[1], p[2], side, sorted(hit)))
    front = sum(1 for n in new if n[0] == "railgun")
    pads = sum(1 for n in new if n[0] == "railgun-pad")
    total = front + pads + len(ear_list)
    area_new = len(newdeck) + len(ear_deck - deck - newdeck)
    if step == "arcs":
        print("fouled ears: %d, fouled pads: %d, ears turned SW/SE to clear the bar: %d" % (len(fouled), len(pads_bad), fixed))
        for f in fouled[:10] + pads_bad[:10]:
            print("  ", f)
        return
    print("Edgerunner 3 = Universal 1 Proto + T bar (%d wide, %d deep)" % (2 * BAR_HALF, NOSE_Y - BAR_TOP + 1))
    print("live ship: %d entities, %d deck tiles, %.0f t; removed for the bar: %s" % (len(ents), len(deck), weight / 1000, ", ".join("%s x%d" % (k, sum(1 for e in removed if e[0] == k)) for k in sorted({e[0] for e in removed}))))
    print("railguns: %d on the front line, %d on the old rocket pads, %d ears at rest (W/E; %d turned SW/SE), 2 at the stern: %d in all" % (front, pads, len(ear_list) - 2, fixed, total))
    print("shot lines fouled: ears %d, pads %d (front line 0 by construction)" % (len(fouled), len(pads_bad)))
    print("new deck: %d tiles = %d foundation = %d rocket launches; ship becomes about %d tiles" % (area_new, area_new, math.ceil(area_new / 50.0), len(deck) + area_new))
    acc = sum(b[3] * b[4] for b in blocks[1:3]) // 4
    print("power: %d railguns x 3.9 MW = %.0f MW all firing; fusion 500 MW nameplate; accumulators in the wings room for about %d (%.0f GJ)" % (total, total * 3.9, acc, acc * ACC_PER / 1000))
    print("mass: about %.0f t now; the bar adds roughly %.0f t (deck and parts at the live ship's ratio): thrust must be checked; 4 thrusters today" % (weight / 1000, weight / 1000 * area_new / max(1, len(deck))))
    print("rounds: the loop's rocket lane carries railgun rounds; the reserve (30,000) rides in the hub (659 slots, 1,000 rounds a slot is NOT possible: railgun rounds stack 10)")
    print("blocks in the bar:")
    for b in blocks:
        print("   %-52s x %4d..%4d  y %4d..%4d" % (b[0], b[1], b[1] + b[3] - 1, b[2], b[2] + b[4] - 1))


if __name__ == "__main__":
    main()
