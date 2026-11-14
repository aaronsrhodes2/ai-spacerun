"""Lab capacity on Gleba against pack supply: per-lab speed, unit time of the current and queued research, packs a minute at full work."""
from _game import tools

LUA = """
local f=game.forces.player local g=game.surfaces.gleba local o={} local st={} for k,v in pairs(defines.entity_status) do st[v]=k end
local labs=g.find_entities_filtered{type='lab',force=f} local sp=0 local w=0
for _,l in pairs(labs) do sp=sp+(1+l.speed_bonus) if l.status==defines.entity_status.working then w=w+1 end
local m={} for _,it in pairs(l.get_module_inventory().get_contents()) do m[#m+1]=it.name..'/'..it.quality..'x'..it.count end
local c={} for _,it in pairs(l.get_inventory(defines.inventory.lab_input).get_contents()) do c[#c+1]=(it.name:gsub('%-science%-pack','')):sub(1,5)..it.count end
o[#o+1]='lab '..l.position.x..','..l.position.y..' '..l.quality.name..' '..(st[l.status] or '?')..' speed+'..l.speed_bonus..' prod+'..l.productivity_bonus..' mods '..table.concat(m,',')..' beacons '..(l.beacons_count or 0)..' | '..table.concat(c,' ') end
local base=prototypes.entity['lab'].get_researching_speed(labs[1].quality) local mod=f.laboratory_speed_modifier
o[#o+1]='labs '..#labs..' working '..w..' base speed '..base..' force modifier '..mod..' force productivity '..f.laboratory_productivity_bonus..' sum(1+bonus) '..sp
local function row(t) local sec=t.research_unit_energy/60 local per=(1+mod)*base*sp/sec*60 return t.name..': '..t.research_unit_count..' units x '..sec..' s, all labs at full work use '..math.floor(per)..' of each pack a minute' end
if f.current_research then o[#o+1]='now '..row(f.current_research)..' progress '..string.format('%.3f',f.research_progress) end
for _,t in pairs(f.research_queue) do o[#o+1]='queued '..row(t) end
local ps=f.get_item_production_statistics(g) for _,n in pairs({'agricultural','automation','production','chemical','logistic'}) do local nm=n..'-science-pack'
o[#o+1]=n..' gleba per min: made 1m '..math.floor(ps.get_flow_count{name=nm,category='input',precision_index=defines.flow_precision_index.one_minute,count=false})..' 10m '..math.floor(ps.get_flow_count{name=nm,category='input',precision_index=defines.flow_precision_index.ten_minutes,count=false})..' used 1m '..math.floor(ps.get_flow_count{name=nm,category='output',precision_index=defines.flow_precision_index.one_minute,count=false})..' 10m '..math.floor(ps.get_flow_count{name=nm,category='output',precision_index=defines.flow_precision_index.ten_minutes,count=false}) end
local inv={} for _,net in pairs(f.logistic_networks.gleba or {}) do for _,n in pairs({'speed-module-3','speed-module-2','productivity-module-3','productivity-module-2','productivity-module','lab','beacon','bulk-inserter','requester-chest','transport-belt','express-transport-belt','turbo-transport-belt','splitter','express-splitter','turbo-splitter','substation','medium-electric-pole','heating-tower','underground-belt','express-underground-belt','logistic-robot'}) do for _,q in pairs({'normal','uncommon','rare','epic'}) do local c=net.get_item_count({name=n,quality=q}) if c>0 then inv[#inv+1]=n..'/'..q:sub(1,2)..':'..c end end end
o[#o+1]='gleba net robots '..net.all_logistic_robots..' avail '..net.available_logistic_robots..' cons '..net.all_construction_robots..' stock '..table.concat(inv,' ') inv={} end
rcon.print(table.concat(o,'|'))
"""
print(tools["run_lua"](" ".join(LUA.split())).replace("|", "\n"))
