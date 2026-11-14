"""Readout of every platform whose name contains the argument (plain find): place, state, hub stock, trash, requests, schedule, tanks, turrets.
Usage: _shipscan.py Nauvis-Gleba [brief]"""
import sys

from _game import tools

LUA = """
local f=game.forces.player local o={} local want='%s' local brief=%s
local function sh(n) return (n:gsub('%%-science%%-pack','')) end
for i,p in pairs(f.platforms) do if p.name:find(want,1,true) then local hub=p.hub local l={}
l[#l+1]='#'..i..' '..p.name..' ['..p.surface.name..'] at '..(p.space_location and p.space_location.name or 'transit')..' state '..p.state..' paused '..tostring(p.paused)..' can_leave '..tostring(p.can_leave_current_location())
if hub then
local t={} for _,it in pairs(hub.get_inventory(defines.inventory.hub_main).get_contents()) do t[#t+1]=sh(it.name)..':'..it.count end l[#l+1]='  hub '..table.concat(t,' ')
local tr={} for _,it in pairs(hub.get_inventory(defines.inventory.hub_trash).get_contents()) do tr[#tr+1]=sh(it.name)..':'..it.count end l[#l+1]='  trash '..(#tr>0 and table.concat(tr,' ') or 'empty')..' | provide '..tostring(hub.providing_to_other_platforms)
for si,se in pairs(hub.get_logistic_sections().sections) do local rq={} for _,fl in pairs(se.filters) do if fl.value then rq[#rq+1]=sh(fl.value.name)..' '..fl.min..'..'..tostring(fl.max)..'@'..tostring(fl.import_from and fl.import_from.name or fl.import_from) end end
if #rq>0 then l[#l+1]='  sec'..si..' manual='..tostring(se.is_manual)..' active='..tostring(se.active)..' group='..tostring(se.group)..': '..table.concat(rq,', ') end end
local g={} for _,sg in pairs(hub.get_signals(defines.wire_connector_id.circuit_green) or {}) do if sg.signal.type=='fluid' then g[#g+1]=sg.signal.name..'='..sg.count end end l[#l+1]='  green fluids '..table.concat(g,' ')
end
if not brief then local sc=p.schedule if sc and sc.records then for ri,rec in pairs(sc.records) do local w={} for _,c in pairs(rec.wait_conditions or {}) do local d=c.type if c.condition then d=d..'('..tostring(c.condition.first_signal and c.condition.first_signal.name)..tostring(c.condition.comparator)..tostring(c.condition.constant)..')' end if c.ticks then d=d..'('..c.ticks..'t)' end w[#w+1]=(c.compare_type or '')..' '..d end
l[#l+1]='  stop'..ri..(sc.current==ri and '*' or '')..' '..rec.station..': '..table.concat(w,';') end else l[#l+1]='  NO SCHEDULE' end
local s=p.surface local tu={} local arm=0 local guns=s.find_entities_filtered{type='ammo-turret'} for _,e in pairs(guns) do local n=e.get_inventory(defines.inventory.turret_ammo).get_item_count() tu[#tu+1]=n if n>0 then arm=arm+1 end end
l[#l+1]='  turrets '..#guns..' armed '..arm..': '..table.concat(tu,',')
local gh=s.count_entities_filtered{type='entity-ghost'} local tg=s.count_entities_filtered{type='tile-ghost'} local n=s.count_entities_filtered{force=f}
local bays=s.count_entities_filtered{type='cargo-bay'} local th=s.count_entities_filtered{type='thruster'} local col=s.count_entities_filtered{type='asteroid-collector'}
l[#l+1]='  entities '..n..' ghosts '..gh..' tile ghosts '..tg..' bays '..bays..' thrusters '..th..' collectors '..col..' hub slots '..#hub.get_inventory(defines.inventory.hub_main)
local st={} for k,v in pairs(defines.entity_status) do st[v]=k end local m={} for _,e in pairs(s.find_entities_filtered{type={'assembling-machine','furnace','thruster','asteroid-collector','solar-panel'}}) do local k=(e.type=='assembling-machine' and e.get_recipe() and e.get_recipe().name or e.name)..'='..(st[e.status] or '?') m[k]=(m[k] or 0)+1 end
local mm={} for k,v in pairs(m) do mm[#mm+1]=k..'x'..v end l[#l+1]='  machines '..table.concat(mm,' ')
end
o[#o+1]=table.concat(l,'\\n') end end
rcon.print(table.concat(o,'\\n'))
"""
brief = "true" if len(sys.argv) > 2 else "false"
print(tools["run_lua"](" ".join((LUA % (sys.argv[1], brief)).split())))
