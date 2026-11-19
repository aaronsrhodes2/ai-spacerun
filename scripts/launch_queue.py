#!/usr/bin/env python3
"""What the rocket silos of a planet are being asked to lift, by platform, in launches (read-only).
Why: on 2026-11-18 the Gleba labs had no logistic or production science packs while Nauvis held 96,000 and five Nauvis-Gleba shuttles
stood in Nauvis orbit with none aboard. A rocket lifts by weight (1,000 kg): 1,000 science packs, but only 25 uranium rounds or 25
explosive rockets or 50 foundations, so one platform asking for thousands of those takes the silos for hundreds of launches.
Usage: launch_queue.py [PLANET]   (default nauvis)"""
import sys

from _game import tools

L = tools["run_lua"]
PLANET = sys.argv[1] if len(sys.argv) > 1 else "nauvis"

SILOS = ("local s=game.surfaces['%s'] local m={} for k,v in pairs(defines.entity_status) do m[v]=k end local o={} "
         "for _,e in pairs(s.find_entities_filtered{type='rocket-silo'}) do local c={} local inv=e.get_inventory(defines.inventory.rocket_silo_rocket) "
         "if inv then for _,it in pairs(inv.get_contents()) do c[#c+1]=it.name..' '..it.count end end "
         "o[#o+1]='silo @'..math.floor(e.position.x)..','..math.floor(e.position.y)..' '..tostring(m[e.status])..' parts '..tostring(e.rocket_parts)..' cargo ['..table.concat(c,', ')..']' end "
         "rcon.print(table.concat(o,string.char(10)))") % PLANET

NEED = ("local f=game.forces.player local rows={} "
        "for i,p in pairs(f.platforms) do "
        "  if p.space_location and p.space_location.name=='%s' and p.hub and p.hub.valid then "
        "    local inv=p.hub.get_inventory(defines.inventory.hub_main) local total=0 local parts={} "
        "    for _,pt in pairs(p.hub.get_logistic_point()) do "
        "      if pt.mode==defines.logistic_mode.requester then "
        "        for _,sec in pairs(pt.sections) do "
        "          if sec.active then "
        "            for k=1,sec.filters_count do "
        "              local fl=sec.get_slot(k) "
        "              if fl and fl.value and fl.min and fl.min>0 and fl.request_from~='platforms' then "
        "                local imp=fl.import_from and (type(fl.import_from)=='string' and fl.import_from or fl.import_from.name) "
        "                if imp==nil or imp=='%s' then "
        "                  local short=fl.min-inv.get_item_count(fl.value.name) "
        "                  if short>0 then local n=math.ceil(short*prototypes.item[fl.value.name].weight/1000000) total=total+n parts[#parts+1]=fl.value.name..' '..short..' ('..n..')' end "
        "                end "
        "              end "
        "            end "
        "          end "
        "        end "
        "      end "
        "    end "
        "    if total>0 then rows[#rows+1]={total,p.name:gsub('%%[.-%%]',''),table.concat(parts,', ')} end "
        "  end "
        "end "
        "table.sort(rows,function(a,b) return a[1]>b[1] end) local o={} for _,r in pairs(rows) do o[#o+1]=string.format('%%5d launches  %%s: %%s',r[1],r[2],r[3]:sub(1,300)) end "
        "rcon.print(#o>0 and table.concat(o,string.char(10)) or 'no platform in orbit is short of anything')") % (PLANET, PLANET)

print(L(SILOS))
print(L(" ".join(NEED.split())))
