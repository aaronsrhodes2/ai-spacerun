#!/usr/bin/env python3
"""Vulcanus coal from inside territory 5 (17 million there; under 1 million outside every territory).
The tungsten belt already passes 20 tiles east of the coal field: it runs west along y -209.5 and turns south at (-587.5,-209.5).
  mine    seven big drills either side of a collector belt along y -209.5 (x -640..-588.5, flowing east). The collector meets that corner
          from the west while the ore meets it from the east, so both side-load: ore keeps the east lane, coal the west lane, all the way.
  cross   at the robot crossing the north blue chests ask for ore only and the south ones for coal only: their inserters load opposite lanes,
          so the lanes stay separate on the east belt. 200 more robots.
  west    west side of the crossing: the three old red chests take ore only; two new red chests (-255.5,-68.5/-67.5) take coal only
  unload  at the base end: two unloaders take ore only (still gated on packs < 6000), the third takes coal only, gated on coal < 12000.
          A full ore lane can never block the coal lane, and the other way round.
Usage: vulcanus_coal.py mine|west|cross|unload [--apply]
Ore left on the coal lane from before the change has to be moved off once (it was moved into the base unload chests)."""
import json
import sys

from _game import tools

Y = -209.5
UNDER = []          # (x_in, x_out) pairs of underground belt along the collector, filled in from the dry run


def mine():
    e = []
    for x in (-637.5, -630.5, -623.5):
        e.append({"name": "big-mining-drill", "x": x, "y": Y - 3, "direction": 8})
    for x in (-637.5, -630.5, -623.5, -616.5):
        e.append({"name": "big-mining-drill", "x": x, "y": Y + 3, "direction": 0})
    e += [{"name": "substation", "x": x, "y": -212} for x in (-634, -627, -620)]
    e += [{"name": "substation", "x": -606, "y": -212}, {"name": "big-electric-pole", "x": -592, "y": -212}]
    skip = {}
    for a, b in UNDER:
        skip[a] = "input"
        skip[b] = "output"
        for i in range(int(b - a) - 1):
            skip[a + 1 + i] = None
    x = -639.5
    while x <= -588.5:
        if x in skip:
            if skip[x]:
                e.append({"name": "express-underground-belt", "x": x, "y": Y, "direction": 4, "type": skip[x]})
        else:
            e.append({"name": "express-transport-belt", "x": x, "y": Y, "direction": 4})
        x += 1
    return e


CROSS = ("local s=game.surfaces.vulcanus local f=game.forces.player local n=0 "
         "local function req(x,y,name,ct) local c=s.find_entities_filtered{name='requester-chest',position={x,y},radius=0.3}[1] local ss=c.get_logistic_sections() local se=ss.sections[1] or ss.add_section() "
         "for i=1,4 do se.clear_slot(i) end se.set_slot(1,{value={name=name,quality='normal'},min=ct}) n=n+1 end "
         "for _,x in pairs{-229.5,-228.5,-227.5} do req(x,-71.5,'tungsten-ore',800) req(x,-67.5,'coal',800) end "
         "local rp=s.find_entities_filtered{name='roboport',position={-262,-64},radius=1}[1] local added=rp.insert{name='logistic-robot',count=200} "
         "rcon.print('requests set on '..n..' chests, robots added '..added)")

UNLOAD = ("local s=game.surfaces.vulcanus local o={} "
          "local function cfg(x,y,item,sig,const) local i=s.find_entities_filtered{type='inserter',position={x,y},radius=0.3}[1] i.use_filters=true i.inserter_filter_mode='whitelist' i.set_filter(1,item) "
          "local cb=i.get_or_create_control_behavior() cb.connect_to_logistic_network=true cb.logistic_condition={first_signal={type='item',name=sig},comparator='<',constant=const} o[#o+1]=item..' at '..x..','..y end "
          "cfg(-118.5,-70.5,'tungsten-ore','metallurgic-science-pack',6000) cfg(-116.5,-70.5,'tungsten-ore','metallurgic-science-pack',6000) cfg(-117.5,-69.5,'coal','coal',12000) "
          "rcon.print(table.concat(o,' | '))")


WEST = ("local s=game.surfaces.vulcanus local n=0 for _,i in pairs(s.find_entities_filtered{type='inserter',area={{-260,-71},{-255,-66}}}) do i.use_filters=true i.inserter_filter_mode='whitelist' "
        "i.set_filter(1, i.position.x>-257 and 'coal' or 'tungsten-ore') n=n+1 end rcon.print('filters set on '..n..' inserters')")


def west():
    return ([{"name": "bulk-inserter", "x": -256.5, "y": y, "direction": 12} for y in (-68.5, -67.5)]
            + [{"name": "passive-provider-chest", "x": -255.5, "y": y} for y in (-68.5, -67.5)])


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    if step == "mine":
        if True:
            r = json.loads(tools["place_entities"](json.dumps(mine()), surface="vulcanus", dry_run=not apply))
            print("placed", r["placed"], "failed", r["failed"])
    elif step == "west":
        print(tools["place_entities"](json.dumps(west()), surface="vulcanus", dry_run=not apply))
        if apply:
            print(tools["run_lua"](WEST))
    elif step == "cross":
        print(tools["run_lua"](CROSS) if apply else "(dry run) would set crossing requests and add 200 robots")
    elif step == "unload":
        print(tools["run_lua"](UNLOAD) if apply else "(dry run) would set unloader filters")


if __name__ == "__main__":
    main()
