#!/usr/bin/env python3
"""Vulcanus rocket part ingredients made locally (processing unit, low density structure, rocket fuel).
  oil      field x 26..73, y 97..117, anchored on refinery R3 at (RX,RY) = (54.5,111.5). Refineries face north, chemical plants face south (dir 8).
           Acid main along y RY+3 fed by three new wells; R1, R2 -> solid fuel from heavy oil; R3 + R4 -> heavy-oil cracking -> light oil ->
           two rocket fuel assemblers and light-oil cracking -> gas -> plastic; water from acid neutralisation + steam condensation;
           processing unit, two electronic circuit and one advanced circuit assemblers on the east side.
  metal    free ground x 60..90, y 62..79: lava pump (80.5,53.5), lava main y 75.5, molten iron foundry (73.5,72.5) and molten copper
           foundry (82.5,72.5); north of them iron plate (64.5,66.5), low density structure (73.5,66.5) and copper cable (82.5,66.5).
Usage: vulcanus_parts.py oil|metal [--apply]"""
import json
import sys

from _game import tools

RX, RY = 54.5, 111.5


def io(x, y, req=None, west=True):
    """Blue chest + inserter on the west side, or inserter + red chest on the east side, of a 3x3 machine at (x,y)."""
    if west:
        return [{"name": "requester-chest", "x": x - 3, "y": y, "req": req}, {"name": "bulk-inserter", "x": x - 2, "y": y, "direction": 12}]
    return [{"name": "bulk-inserter", "x": x + 2, "y": y, "direction": 12}, {"name": "passive-provider-chest", "x": x + 3, "y": y}]


def pipes(pts):
    return [{"name": "pipe", "x": x, "y": y} for x, y in pts]


def oil():
    e = []
    for x in (RX - 24, RX - 16, RX - 8, RX):
        e.append({"name": "oil-refinery", "x": x, "y": RY, "direction": 0, "recipe": "simple-coal-liquefaction"})
        e += [{"name": "requester-chest", "x": x - 4, "y": RY, "req": {"coal": 300, "calcite": 60}}, {"name": "bulk-inserter", "x": x - 3, "y": RY, "direction": 12}]
    for x in (RX - 24, RX - 16):
        e += pipes([(x - 2, RY - 3)])
        e.append({"name": "chemical-plant", "x": x - 3, "y": RY - 5, "direction": 8, "recipe": "solid-fuel-from-heavy-oil"})
        e += [{"name": "bulk-inserter", "x": x - 3, "y": RY - 7, "direction": 8}, {"name": "passive-provider-chest", "x": x - 3, "y": RY - 8}]
    e += pipes([(RX - 10 + i, RY - 3) for i in range(9)])
    e += pipes([(RX + i, RY - 3) for i in range(6)])
    e.append({"name": "chemical-plant", "x": RX - 1, "y": RY - 5, "direction": 8, "recipe": "heavy-oil-cracking"})
    e += pipes([(RX - 13 + i, RY - 7) for i in range(14)])
    e += pipes([(RX + 2 + i, RY - 7) for i in range(4)])
    e += pipes([(RX + 5, RY - 4), (RX + 5, RY - 5), (RX + 5, RY - 6)])
    e += pipes([(RX + 6, RY - 5), (RX + 7, RY - 5), (RX + 8, RY - 5), (RX + 9, RY - 5)])
    e.append({"name": "chemical-plant", "x": RX + 1, "y": RY - 9, "direction": 8, "recipe": "light-oil-cracking"})
    e += pipes([(RX + 2, RY - 11)])
    e.append({"name": "chemical-plant", "x": RX + 1, "y": RY - 13, "direction": 8, "recipe": "plastic-bar"})
    e += io(RX + 1, RY - 13, {"coal": 40}) + io(RX + 1, RY - 13, west=False)
    for x in (RX - 6, RX - 13):
        e.append({"name": "assembling-machine-3", "x": x, "y": RY - 5, "direction": 0, "recipe": "rocket-fuel"})
        e += [{"name": "bulk-inserter", "x": x + 2, "y": RY - 5, "direction": 4}, {"name": "requester-chest", "x": x + 3, "y": RY - 5, "req": {"solid-fuel": 100}},
              {"name": "bulk-inserter", "x": x - 2, "y": RY - 5, "direction": 4}, {"name": "passive-provider-chest", "x": x - 3, "y": RY - 5}]
    e.append({"name": "chemical-plant", "x": RX + 8, "y": RY + 1, "direction": 8, "recipe": "acid-neutralisation"})
    e += pipes([(RX + 9, RY - 1)])
    e.append({"name": "chemical-plant", "x": RX + 8, "y": RY - 3, "direction": 8, "recipe": "steam-condensation"})
    e += io(RX + 8, RY + 1, {"calcite": 20})
    e.append({"name": "assembling-machine-3", "x": RX + 13, "y": RY + 1, "direction": 8, "recipe": "processing-unit"})
    e += io(RX + 13, RY + 1, {"electronic-circuit": 100, "advanced-circuit": 20}) + io(RX + 13, RY + 1, west=False)
    for y, rec, req in ((RY - 4, "electronic-circuit", {"iron-plate": 100, "copper-cable": 300}), (RY - 8, "electronic-circuit", {"iron-plate": 100, "copper-cable": 300}),
                        (RY - 12, "advanced-circuit", {"plastic-bar": 40, "copper-cable": 80, "electronic-circuit": 40})):
        e.append({"name": "assembling-machine-3", "x": RX + 13, "y": y, "direction": 0, "recipe": rec})
        e += io(RX + 13, y, req) + io(RX + 13, y, west=False)
    e += pipes([(x + 0.5, RY + 3) for x in range(8, int(RX + 13) + 1)])
    e += [{"name": "pumpjack", "x": 13.5, "y": 109.5, "direction": 8}, {"name": "pumpjack", "x": 9.5, "y": 108.5, "direction": 8},
          {"name": "pumpjack", "x": 21.5, "y": 90.5, "direction": 4}]
    e += pipes([(12.5, 111.5), (12.5, 112.5), (12.5, 113.5), (8.5, 110.5), (8.5, 111.5), (8.5, 112.5), (8.5, 113.5), (23.5, 91.5)])
    e += pipes([(24.5, y + 0.5) for y in range(91, 114)])
    e += [{"name": "substation", "x": x, "y": y} for x, y in ((50, 116), (50, 102), (62, 100), (72, 112), (30, 116))]
    return e


CLEAR = ("local s=game.surfaces.vulcanus local n=0 for _,e in pairs(s.find_entities_filtered{area={{56,96},{64,104}},force='player'}) do e.destroy() n=n+1 end "
         "rcon.print('lattice cluster at (60,100) removed, entities '..n)")


def metal():
    """Lava pump (80.5,53.5) on the east pool -> pipe round to a lava main along y 75.5; iron column x 73.5, copper column x 82.5."""
    e = [{"name": "offshore-pump", "x": 80.5, "y": 53.5, "direction": 4}]
    e += pipes([(79.5, y + 0.5) for y in range(53, 58)] + [(x + 0.5, 57.5) for x in range(80, 88)] + [(87.5, y + 0.5) for y in range(58, 76)])
    e += pipes([(x + 0.5, 75.5) for x in range(71, 87)])
    for x, rec in ((72.5, "molten-iron-from-lava"), (82.5, "molten-copper-from-lava")):   # iron foundry is NOT under the LDS foundry: its second outlet must not touch the copper pipe
        e.append({"name": "foundry", "x": x, "y": 72.5, "direction": 0, "recipe": rec})
        e += [{"name": "requester-chest", "x": x - 4, "y": 72.5, "req": {"calcite": 20}}, {"name": "bulk-inserter", "x": x - 3, "y": 72.5, "direction": 12},
              {"name": "bulk-inserter", "x": x + 3, "y": 72.5, "direction": 12}, {"name": "passive-provider-chest", "x": x + 4, "y": 72.5}]
    e += pipes([(x + 0.5, 69.5) for x in range(63, 73)])
    e += pipes([(x + 0.5, 69.5) for x in range(74, 82)])
    for x, rec, req in ((64.5, "casting-iron", None), (73.5, "casting-low-density-structure", {"plastic-bar": 40}), (82.5, "casting-copper-cable", None)):
        e.append({"name": "foundry", "x": x, "y": 66.5, "direction": 0, "recipe": rec})
        if req:
            e += [{"name": "requester-chest", "x": x - 4, "y": 66.5, "req": req}, {"name": "bulk-inserter", "x": x - 3, "y": 66.5, "direction": 12}]
        e += [{"name": "bulk-inserter", "x": x + 3, "y": 66.5, "direction": 12}, {"name": "passive-provider-chest", "x": x + 4, "y": 66.5}]
    e += [{"name": "substation", "x": 70, "y": 78}, {"name": "substation", "x": 84, "y": 78}]
    return e


REQ = ("local s=game.surfaces.vulcanus local n=0 for _,q in pairs(%s) do local c=s.find_entities_filtered{name='requester-chest',position={q[1],q[2]},radius=0.3}[1] if c then "
       "local secs=c.get_logistic_sections() local sec=secs.sections[1] or secs.add_section() local i=0 for name,ct in pairs(q[3]) do i=i+1 sec.set_slot(i,{value={name=name,quality='normal'},min=ct}) end n=n+1 end end "
       "local d=%s local t=0 for _,m in pairs(s.find_entities_filtered{type='assembling-machine',area={{%s,%s},{%s,%s}}}) do local k=m.position.x..','..m.position.y if d[k] then m.direction=d[k] t=t+1 end end "
       "rcon.print('requests set on '..n..' chests, directions set on '..t..' machines')")


def place(ents, apply, area):
    reqs = [(x["x"], x["y"], x["req"]) for x in ents if x.get("req")]
    for x in ents:
        x.pop("req", None)
    dirs = {"%s,%s" % (x["x"], x["y"]): x["direction"] for x in ents if x["name"] in ("chemical-plant", "assembling-machine-3", "oil-refinery", "foundry")}
    fails = []
    placed = 0
    for i in range(0, len(ents), 300):
        r = json.loads(tools["place_entities"](json.dumps(ents[i:i + 300]), surface="vulcanus", dry_run=not apply))
        placed += r["placed"]
        fails += r["failed"] if isinstance(r["failed"], list) else []
    print(len(ents), "entities, placed", placed, "failed", len(fails), fails[:15])
    if apply:
        spec = "{" + ",".join("{%s,%s,{%s}}" % (x, y, ",".join("['%s']=%d" % kv for kv in r.items())) for x, y, r in reqs) + "}"
        dspec = "{" + ",".join("['%s']=%d" % kv for kv in dirs.items()) + "}"
        print(tools["run_lua"](REQ % (spec, dspec, area[0], area[1], area[2], area[3])))


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    if step == "oil":
        if apply:
            print(tools["run_lua"](CLEAR))
        place(oil(), apply, (0, 80, 80, 120))
    elif step == "metal":
        place(metal(), apply, (55, 60, 95, 80))


if __name__ == "__main__":
    main()
