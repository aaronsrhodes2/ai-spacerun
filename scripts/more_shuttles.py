#!/usr/bin/env python3
"""More shuttles of the proven second design (the Captain, 2026-11-12: several fast shuttles per planet, Gleba first because its packs rot).
  create   a new platform at Nauvis for each name missing: "Nauvis-Gleba 2 Shuttle", "Nauvis-Vulcanus 2 Shuttle", "Nauvis-Fulgora 2 Shuttle"
           (names end in Shuttle so the autopilot repairs them). Prints platform index and surface.
  twin     after build_shuttle2.py and configure_shuttle2.py on the new surface: 200 iron plates from Nauvis stock into the hub for the first
           magazines, then the sibling ship's schedule and cargo requests copied over (same waits: it only leaves Nauvis fuelled and armed)
Usage: more_shuttles.py create | twin"""
import sys

from _game import tools

PAIRS = "{{'Nauvis-Gleba 2 Shuttle','Nauvis-Gleba 1 Shuttle'},{'Nauvis-Vulcanus 2 Shuttle','Nauvis-Vulcanus 1 Shuttle'},{'Nauvis-Fulgora 2 Shuttle','Nauvis-Fulgora 1 Shuttle'}}"
CREATE = ("local f=game.forces.player local o={} local have={} for i,p in pairs(f.platforms) do have[p.name]=i end for _,q in pairs(" + PAIRS + ") do "
          "if not have[q[1]] then local p=f.create_space_platform{name=q[1],planet='nauvis',starter_pack='space-platform-starter-pack'} p.apply_starter_pack() end end "
          "for i,p in pairs(f.platforms) do o[#o+1]=i..' '..p.name..' '..p.surface.name end rcon.print(table.concat(o,' | '))")
TWIN = ("local f=game.forces.player local o={} local by={} for i,p in pairs(f.platforms) do by[p.name]=p end local nb,bn=nil,0 for _,net in pairs(f.logistic_networks.nauvis or {}) do if net.all_logistic_robots>bn then nb=net bn=net.all_logistic_robots end end "
        "for _,q in pairs(" + PAIRS + ") do local p,old=by[q[1]],by[q[2]] if p and old then local inv=p.hub.get_inventory(defines.inventory.hub_main) "
        "if inv.get_item_count('iron-plate')<200 and inv.get_item_count('firearm-magazine')<200 then local got=nb.remove_item{name='iron-plate',count=200} inv.insert{name='iron-plate',count=got} end "
        "local secs=p.hub.get_logistic_sections() local mine={} for _,se in pairs(secs.sections) do for _,fl in pairs(se.filters) do if fl.value then mine[fl.value.name]=true end end end "
        "for _,se in pairs(old.hub.get_logistic_sections().sections) do for _,fl in pairs(se.filters) do if fl.value and not mine[fl.value.name] and string.find(fl.value.name,'science') then local ns=secs.add_section() "
        "ns.set_slot(1,{value={name=fl.value.name,quality='normal'},min=fl.min,import_from=fl.import_from,minimum_delivery_count=fl.minimum_delivery_count}) end end end "
        "local sch=p.schedule or {} sch.records=old.schedule.records sch.current=1 p.schedule=sch p.paused=false "
        "o[#o+1]=q[1]..': schedule copied ('..#p.schedule.records..' stops), paused '..tostring(p.paused) end end rcon.print(table.concat(o,' | '))")
print(tools["run_lua"]({"create": CREATE, "twin": TWIN}[sys.argv[1]]))
