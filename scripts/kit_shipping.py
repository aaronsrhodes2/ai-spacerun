#!/usr/bin/env python3
"""The building kit: a standing stock of building items on every planet, carried by one shuttle each (the Captain, 2026-11-13: a spare
or trashed item on Nauvis should reach the planet that needs it and be built there by the robots).
The game has no signal for ghosts across planets, so it is a kept stock, not send-on-demand:
  shuttle  one per planet (SHIPS) asks Nauvis for one rocket load of each kit item (a hub section named 'Building kit', import from Nauvis)
  pad      the planet's landing pad asks for the same, so the shuttle drops the kit there; robots build ghosts out of the pad
  Nauvis   rockets take the items out of the robot network: whatever the Captain trashes, and what scripts/nauvis_mall.py makes
Steady state costs no rockets: only what a planet used is sent again. Safe to run again (it rewrites its own sections).
Usage: kit_shipping.py [status]"""
import sys

from _game import tools

SHIPS = {"fulgora": "Nauvis-Fulgora 2 Shuttle", "gleba": "Nauvis-Gleba 3 Shuttle", "vulcanus": "Nauvis-Vulcanus 2 Shuttle"}
KIT = ["express-transport-belt", "express-underground-belt", "medium-electric-pole", "big-electric-pole", "substation", "fast-inserter",
       "bulk-inserter", "long-handed-inserter", "pipe", "pipe-to-ground", "pump", "storage-tank", "assembling-machine-3", "laser-turret",
       "roboport", "construction-robot", "passive-provider-chest", "requester-chest", "storage-chest", "steel-chest", "small-lamp",
       "repair-pack", "solar-panel", "accumulator", "stone-wall", "radar", "beacon", "constant-combinator", "decider-combinator",
       "arithmetic-combinator"]
SET = ("local f=game.forces.player local kit={KIT} local o={} local function fill(ent,imp) local done=false for _,pt in pairs(ent.get_logistic_point()) do if not done and pt.mode==defines.logistic_mode.requester then "
       "local sec=nil for _,x in pairs(pt.sections) do if x.group=='' and x.filters_count>0 and x.filters[1] and x.filters[1].value and x.filters[1].value.name==kit[1] then sec=x end end sec=sec or pt.add_section() "
       "for i,n in pairs(kit) do local c=math.min(100,math.floor(1000000/prototypes.item[n].weight)) local sl={value={type='item',name=n,quality='normal'},min=c} if imp then sl.max=c sl.import_from='nauvis' end sec.set_slot(i,sl) end done=true end end return done end "
       "for planet,ship in pairs({SHIPS}) do for _,p in pairs(f.platforms) do if p.name==ship then o[#o+1]=ship..' '..tostring(fill(p.hub,true)) end end "
       "local pad=game.surfaces[planet].find_entities_filtered{type='cargo-landing-pad'}[1] o[#o+1]=planet..' pad '..tostring(pad and fill(pad,false)) end rcon.print(table.concat(o,', '))")
STATUS = ("local f=game.forces.player local kit={KIT} local o={} for planet,ship in pairs({SHIPS}) do local pad=game.surfaces[planet].find_entities_filtered{type='cargo-landing-pad'}[1] local inv=pad.get_inventory(defines.inventory.cargo_landing_pad_main) "
          "local a,b=0,0 for _,n in pairs(kit) do if inv.get_item_count(n)>0 then a=a+1 end end for _,p in pairs(f.platforms) do if p.name==ship then local hi=p.hub.get_inventory(defines.inventory.hub_main) for _,n in pairs(kit) do if hi.get_item_count(n)>0 then b=b+1 end end "
          "o[#o+1]=planet..': pad holds '..a..' of '..#kit..' kit items, '..ship..' holds '..b..', at '..(p.space_location and p.space_location.name or 'flight')..', hub free '..hi.count_empty_stacks() end end end rcon.print(table.concat(o,' ; '))")


def fmt(code):
    return code.replace("{KIT}", "{" + ",".join("'%s'" % k for k in KIT) + "}").replace("{SHIPS}", "{" + ",".join("%s='%s'" % kv for kv in SHIPS.items()) + "}")


if __name__ == "__main__":
    print(tools["run_lua"](fmt(STATUS if "status" in sys.argv else SET)).replace(" ; ", "\n"))
