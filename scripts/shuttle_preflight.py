#!/usr/bin/env python3
"""Pre-flight check of build_shuttle2 ships (2026-11-14, after three new ships flew with empty turrets).
  check NAME   every platform whose name contains NAME (plain find, so the icon prefix does not matter): turrets armed, junk on the two
               ammunition belts, hub trash, requests whose max is below the stock, fluids, schedule stops, ghosts.
  sweep NAME   move everything that is not a magazine off the two ammunition belts into the hub (only what the hub takes). Starter-pack
               junk and what unfiltered hub inserters pulled out before configure_shuttle2.py ran sits at the belt ends and starves the
               turrets behind it: the hub inserters show waiting_for_space_in_destination and the turrets no_ammo.
The ammunition belts of the design: nose x 5.5, y -17.5..-3.5 then y -18.5, x -2.5..5.5; rear x -0.5, y 5.5..15.5.
Usage: shuttle_preflight.py check|sweep "Nauvis-Gleba 6" """
import sys

from _game import tools

HEAD = """
local f=game.forces.player local o={} local want='%(want)s'
local function ammo_belts(s) local r={} for _,e in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt'}}) do local x,y=e.position.x,e.position.y
if (x==5.5 and y>=-17.5 and y<=-3.5) or (y==-18.5 and x>=-2.5 and x<=5.5) or (x==-0.5 and y>=5.5 and y<=15.5) then r[#r+1]=e end end return r end
for i,p in pairs(f.platforms) do if p.name:find(want,1,true) and p.hub then local s=p.surface local inv=p.hub.get_inventory(defines.inventory.hub_main) local l={}
"""
CHECK = HEAD + """
local guns=s.find_entities_filtered{type='ammo-turret'} local arm=0 for _,e in pairs(guns) do if e.get_inventory(defines.inventory.turret_ammo).get_item_count()>0 then arm=arm+1 end end
local junk,mags=0,0 for _,e in pairs(ammo_belts(s)) do for ln=1,e.get_max_transport_line_index() do for _,it in pairs(e.get_transport_line(ln).get_contents()) do if it.name=='firearm-magazine' then mags=mags+it.count else junk=junk+it.count end end end end
local tr=0 for _,it in pairs(p.hub.get_inventory(defines.inventory.hub_trash).get_contents()) do tr=tr+it.count end
local over={} for _,se in pairs(p.hub.get_logistic_sections().sections) do for _,fl in pairs(se.filters) do if fl.value and fl.max and inv.get_item_count(fl.value.name)>fl.max then over[#over+1]=fl.value.name..' '..inv.get_item_count(fl.value.name)..'>'..fl.max end end end
local fl={} for _,sg in pairs(p.hub.get_signals(defines.wire_connector_id.circuit_green) or {}) do if sg.signal.type=='fluid' then fl[sg.signal.name]=sg.count end end
local sc=p.schedule local stops={} if sc and sc.records then for ri,rec in pairs(sc.records) do stops[#stops+1]=rec.station..(sc.current==ri and '*' or '')..'('..#(rec.wait_conditions or {})..')' end end
local bad={} if arm<#guns then bad[#bad+1]='TURRETS' end if junk>0 then bad[#bad+1]='BELT JUNK' end if tr>0 then bad[#bad+1]='TRASH' end if #over>0 then bad[#bad+1]='OVER MAX' end
if not (fl['water'] and fl['thruster-fuel'] and fl['thruster-oxidizer']) then bad[#bad+1]='FLUID WIRE' end if #stops<2 then bad[#bad+1]='SCHEDULE' end
o[#o+1]='#'..i..' '..p.name:sub(-26)..' at '..(p.space_location and p.space_location.name or 'transit')..': turrets '..arm..'/'..#guns..', belt magazines '..mags..' junk '..junk..', hub magazines '..inv.get_item_count('firearm-magazine')
..', trash '..tr..', over max ['..table.concat(over,', ')..'], water '..tostring(fl['water'])..' fuel '..tostring(fl['thruster-fuel'])..' oxidizer '..tostring(fl['thruster-oxidizer'])
..', stops '..table.concat(stops,' ')..', ghosts '..s.count_entities_filtered{type='entity-ghost'}..', free hub slots '..inv.count_empty_stacks()..' => '..(#bad>0 and table.concat(bad,', ') or 'READY')
end end rcon.print(table.concat(o,'|'))
"""
SWEEP = HEAD + """
local moved,left=0,0 for _,e in pairs(ammo_belts(s)) do for ln=1,e.get_max_transport_line_index() do local tl=e.get_transport_line(ln) for _,it in pairs(tl.get_contents()) do if it.name~='firearm-magazine' then
local n=inv.insert{name=it.name,count=it.count,quality=it.quality} if n>0 then moved=moved+tl.remove_item{name=it.name,count=n,quality=it.quality} end left=left+it.count-n end end end end
o[#o+1]='#'..i..' '..p.name:sub(-26)..': moved '..moved..' junk items from the ammunition belts into the hub, '..left..' left'
end end rcon.print(table.concat(o,'|'))
"""

if __name__ == "__main__":
    lua = {"check": CHECK, "sweep": SWEEP}[sys.argv[1]] % dict(want=sys.argv[2])
    print(tools["run_lua"](" ".join(lua.split())).replace("|", "\n"))
