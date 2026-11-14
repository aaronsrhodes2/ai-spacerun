#!/usr/bin/env python3
"""A rocket silo for Aquilo (the Captain, 2026-11-14: "It needs a launching pad").
Site: the clean land field west of the landing pad, silo centre (-5.5, 3.5) = tiles x -10..-2, y -1..7. About 35 tiles from the
power block, 17 from roboport (4,-11), inside that roboport's logistic area (network 3635), so robots reach it and no roboport is added.
The footprint is written to scripts/aquilo_silo_site.txt for the other agent.
Layout (tile coordinates):
  silo       rocket-silo at (-5.5, 3.5), epic. use_transitional_requests = true (a platform's request for goods is answered: robots
             load the rocket from the network), read_mode = orbital_requests (like the other planets' silos)
  parts      north side: three fast inserters at y -1.5 (x -7.5, -5.5, -3.5; direction N = they pick up from the north) from three
             requester chests at y -2.5: processing unit, low density structure, rocket fuel, 50 each (one rocket = 50 parts = 50 of each).
             The request sections are created INACTIVE (`arm` switches them on) so the silo does not pull the pad's last processing
             units and rocket fuel while no low density structure is there to go with them.
  heat       the silo and the inserters must touch a heat pipe. Heat pipes at x -8.5, -6.5, -4.5, -2.5 between and beside the
             inserters (y -1.5) touch the silo's top edge and every inserter; they join through y -2.5 to a spine at y -3.5
             (x -8.5..-2.5). A route found by breadth-first search over free land tiles joins the spine to the base heat network
             (the tower's), so no second tower and no extra fuel.
  power      one substation at (-1, -2), joined to the substation at (4,-2). The silo draws 250 kW idle and up to 3.99 MW while it
             crafts rocket parts (150 s of crafting a rocket, about 600 MJ).
Steps: check | build [--apply] | arm | disarm | status
Usage: aquilo_silo.py check ; aquilo_silo.py build --apply"""
import json
import sys
from collections import deque

import aquilo_base as ab
from _game import tools

S = ab.SURF
CX, CY = -5.5, 3.5
BOX = (-14, -16, 14, 9)                  # where the heat route may run
PARTS = [("processing-unit", -7.5), ("low-density-structure", -5.5), ("rocket-fuel", -3.5)]
PER_ROCKET = 50
ab.SIZE["rocket-silo"] = (9, 9)


def layout():
    ab.ents.clear()
    ab.put("rocket-silo", CX, CY)
    for _, x in PARTS:
        ab.put("fast-inserter", x, -1.5, ab.N)
        ab.put("requester-chest", x, -2.5)
    for x in (-8.5, -6.5, -4.5, -2.5):
        ab.put("heat-pipe", x, -1.5)
        ab.put("heat-pipe", x, -2.5)
        ab.put("heat-pipe", x, -3.5)
    for x in (-7.5, -5.5, -3.5):
        ab.put("heat-pipe", x, -3.5)    # spine closes the gaps between the stubs
    ab.put("substation", -1.0, -2.0)


def base_heat():
    got = tools["run_lua"]("local t={} for _,e in pairs(game.surfaces.%s.find_entities_filtered{name={'heat-pipe','heating-tower'},area={{%d,%d},{%d,%d}}}) do local bb=e.bounding_box for y=math.floor(bb.left_top.y+0.01),math.ceil(bb.right_bottom.y-0.01)-1 do for x=math.floor(bb.left_top.x+0.01),math.ceil(bb.right_bottom.x-0.01)-1 do t[#t+1]=x..','..y end end end rcon.print(table.concat(t,' '))" % ((S,) + BOX[:2] + BOX[2:])).split()
    return {tuple(int(v) for v in g.split(",")) for g in got}


def route():
    """Breadth-first search over free land tiles from our heat pipes to the base network; adds the pipes of the path to `ents`."""
    mine = set()
    for e in ab.ents:
        if e["name"] == "heat-pipe":
            mine |= ab.tiles_of(e)
    occupied = set()
    for e in ab.ents:
        occupied |= ab.tiles_of(e)
    free = ab.free_grid(*BOX) - occupied
    base = base_heat() - mine
    seen = {t: None for t in mine}
    q = deque(mine)
    end = None
    while q and end is None:
        c = q.popleft()
        for n in ((c[0] + 1, c[1]), (c[0] - 1, c[1]), (c[0], c[1] + 1), (c[0], c[1] - 1)):
            if n in seen:
                continue
            if n in base:                      # touching the base network: done, c is the last new pipe
                end = c
                break
            if n in free:
                seen[n] = c
                q.append(n)
    if end is None:
        return None
    path = []
    c = end
    while c is not None and c not in mine:
        path.append(c)
        c = seen[c]
    for x, y in path:
        ab.put("heat-pipe", x + .5, y + .5)
    return path


def plan():
    layout()
    tiles = set()
    for e in ab.ents:
        tiles |= ab.tiles_of(e)
    free = ab.free_grid(-14, -6, 4, 9)
    bad = sorted(t for t in tiles if t[0] <= 4 and t[1] <= 9 and t[0] >= -14 and t[1] >= -6 and t not in free)
    path = route()
    return bad, path


def set_config():
    """Silo flags and the three requests (sections inactive until `arm`)."""
    parts = ",".join("{'%s',%s}" % (n, x) for n, x in PARTS)
    return tools["run_lua"](
        "local s=game.surfaces.%s local P={%s} local si=s.find_entities_filtered{name='rocket-silo',position={%s,%s},radius=1}[1] if not si then rcon.print('no silo') return end "
        "si.use_transitional_requests=true local b=si.get_or_create_control_behavior() b.read_mode=defines.control_behavior.rocket_silo.read_mode.orbital_requests local n=0 "
        "for _,p in pairs(P) do local c=s.find_entities_filtered{name='requester-chest',position={p[2],-2.5},radius=0.4}[1] if c then local lp=c.get_logistic_point(defines.logistic_member_index.logistic_container) "
        "local have=false for _,sec in pairs(c.get_logistic_sections().sections) do for i=1,sec.filters_count do local f=sec.get_slot(i) if f and f.value and f.value.name==p[1] then have=true end end end "
        "if not have then local sec=c.get_logistic_sections().add_section() sec.set_slot(1,{value={name=p[1],quality='normal'},min=%d}) sec.active=false n=n+1 end end end "
        "rcon.print('silo trans='..tostring(si.use_transitional_requests)..' read_mode='..tostring(b.read_mode)..' new request sections '..n)" % (S, parts, CX, CY, PER_ROCKET))


def arm(on):
    return tools["run_lua"](
        "local s=game.surfaces.%s local n=0 for _,x in pairs({-7.5,-5.5,-3.5}) do local c=s.find_entities_filtered{name='requester-chest',position={x,-2.5},radius=0.4}[1] if c then for _,sec in pairs(c.get_logistic_sections().sections) do sec.active=%s n=n+1 end end end rcon.print('sections set active=%s: '..n)"
        % (S, "true" if on else "false", "true" if on else "false"))


def status():
    print(tools["run_lua"](
        "local s=game.surfaces.%s local si=s.find_entities_filtered{name='rocket-silo',position={%s,%s},radius=1}[1] if not si then rcon.print('no silo standing') return end "
        "local o={'silo status '..si.status..' energy '..math.floor(si.energy/1000)..' kJ trans='..tostring(si.use_transitional_requests)..' parts='..tostring(si.rocket_parts)..' temp='..tostring(si.temperature)} "
        "local n=s.find_logistic_network_by_position(si.position,game.forces.player) o[#o+1]='logistic network '..tostring(n and n.network_id) "
        "local nets=si.electric_network_id o[#o+1]='electric network '..tostring(nets) "
        "for _,x in pairs({-7.5,-5.5,-3.5}) do local c=s.find_entities_filtered{name='requester-chest',position={x,-2.5},radius=0.4}[1] if c then local r='' for _,sec in pairs(c.get_logistic_sections().sections) do for i=1,sec.filters_count do local f=sec.get_slot(i) if f and f.value then r=r..f.value.name..'>='..tostring(f.min)..' active='..tostring(sec.active) end end end "
        "o[#o+1]='chest '..x..': '..r..' holds '..c.get_inventory(defines.inventory.chest).get_item_count() end end "
        "for _,i in pairs(s.find_entities_filtered{name='fast-inserter',area={{-9,-3},{-2,0}}}) do o[#o+1]='inserter '..i.position.x..' '..i.status end "
        "o[#o+1]='launch-ready rocket: '..tostring(si.rocket ~= nil) rcon.print(table.concat(o,'\\n'))" % (S, CX, CY)))


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "check"
    apply = "--apply" in sys.argv
    if step in ("check", "build"):
        bad, path = plan()
        print("pieces:", len(ab.ents), " tiles not free land:", bad)
        print("heat route (tiles):", path if path is None else len(path), path)
        if bad or path is None:
            print("NOT BUILDABLE as planned")
            return
        print("new pieces (not yet standing):", ab.drop_existing())
        if step == "build":
            r = json.loads(tools["place_entities"](json.dumps(ab.ents), surface=S, dry_run=not apply))
            print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:900])
            if apply:
                print(set_config())
                print(tools["run_lua"]("local f=game.forces.player f.chart(game.surfaces.%s,{{-30,-30},{30,25}}) rcon.print('charted')" % S))
    elif step == "arm":
        print(arm(True))
    elif step == "disarm":
        print(arm(False))
    elif step == "status":
        status()


if __name__ == "__main__":
    main()
