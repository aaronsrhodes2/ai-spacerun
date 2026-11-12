#!/usr/bin/env python3
"""Nauvis chemical science: the eight assemblers (y -66.5, x -344.5..-316.5) were starved of engine units.
The ingredient belt (y -63.5, flowing west) got about 48 engines a minute from four belt-side assemblers; eight chemical science assemblers at
speed 3.28 need about 130 a minute. Meanwhile the robot-fed engine assemblers elsewhere sat full.
  feed     blue chest (engine-unit 200) at (-304.5,-59.5) + long-handed inserter (-304.5,-61.5) reaching over the sulfur belt onto the
           north lane of the ingredient belt: the network's engines now reach the science assemblers
  engines  four more robot-fed engine assemblers at x -320.5, y -118.5..-109.5 (blue chest west, red chest east), substation (-325,-114)
Usage: nauvis_chem_science.py feed|engines [--apply]"""
import json
import sys

from _game import tools

REQ = ("local s=game.surfaces.nauvis local n=0 for _,q in pairs(SPEC) do local c=s.find_entities_filtered{name='requester-chest',position={q[1],q[2]},radius=0.3}[1] if c then "
       "local ss=c.get_logistic_sections() local se=ss.sections[1] or ss.add_section() local i=0 for name,ct in pairs(q[3]) do i=i+1 se.set_slot(i,{value={name=name,quality='normal'},min=ct}) end n=n+1 end end "
       "rcon.print('requests set on '..n..' chests')")


def feed():
    return [{"name": "requester-chest", "x": -304.5, "y": -59.5, "req": {"engine-unit": 200}},
            {"name": "long-handed-inserter", "x": -304.5, "y": -61.5, "direction": 8}]


def engines(ys=(-118.5, -115.5, -112.5, -109.5), sub=(-325, -114)):
    e = [{"name": "substation", "x": sub[0], "y": sub[1]}]
    for y in ys:
        e += [{"name": "assembling-machine-3", "x": -320.5, "y": y, "direction": 0, "recipe": "engine-unit"},
              {"name": "requester-chest", "x": -323.5, "y": y, "req": {"steel-plate": 50, "iron-gear-wheel": 50, "pipe": 100}},
              {"name": "bulk-inserter", "x": -322.5, "y": y, "direction": 12},
              {"name": "bulk-inserter", "x": -318.5, "y": y, "direction": 12},
              {"name": "passive-provider-chest", "x": -317.5, "y": y}]
    return e


def main():
    ents = {"feed": feed, "engines": engines, "engines2": lambda: engines((-106.5, -103.5, -100.5), (-325, -102))}[sys.argv[1]]()
    apply = "--apply" in sys.argv
    reqs = [(x["x"], x["y"], x.pop("req")) for x in ents if x.get("req")]
    print(tools["place_entities"](json.dumps(ents), surface="nauvis", dry_run=not apply)[:600])
    if apply:
        spec = "{" + ",".join("{%s,%s,{%s}}" % (x, y, ",".join("['%s']=%d" % kv for kv in r.items())) for x, y, r in reqs) + "}"
        print(tools["run_lua"](REQ.replace("SPEC", spec)))


if __name__ == "__main__":
    main()
