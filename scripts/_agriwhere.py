"""Where agricultural packs are on Nauvis: every container, lab, robot cargo, pods; and who requests them."""
from _game import tools

LUA = """
local f=game.forces.player local n=game.surfaces.nauvis local o={} local nm='agricultural-science-pack'
for _,e in pairs(n.find_entities_filtered{force=f,type={'container','logistic-container','cargo-landing-pad','lab','rocket-silo','cargo-bay','temporary-container'}}) do local c=e.get_item_count(nm) if c>0 then o[#o+1]=e.name..'@'..e.position.x..','..e.position.y..'='..c end end
local rc,rn=0,0 for _,e in pairs(n.find_entities_filtered{force=f,type='logistic-robot'}) do local c=e.get_inventory(defines.inventory.robot_cargo).get_item_count(nm) if c>0 then rc=rc+c rn=rn+1 end end o[#o+1]='robots carrying '..rc..' on '..rn
o[#o+1]='pods '..n.count_entities_filtered{type='cargo-pod'}
local rq={} for _,e in pairs(n.find_entities_filtered{force=f,type='logistic-container'}) do if e.prototype.logistic_mode=='requester' or e.prototype.logistic_mode=='buffer' then for _,se in pairs(e.get_logistic_sections().sections) do for _,fl in pairs(se.filters) do if fl.value and fl.value.name==nm then rq[#rq+1]=e.name..'@'..e.position.x..','..e.position.y..' min '..fl.min..' has '..e.get_item_count(nm) end end end end end
o[#o+1]='requesters: '..table.concat(rq,' ; ')
local ps=f.get_item_production_statistics(n) o[#o+1]='nauvis agri used: 1min '..ps.get_flow_count{name=nm,category='output',precision_index=defines.flow_precision_index.one_minute,count=true}..' 10min '..ps.get_flow_count{name=nm,category='output',precision_index=defines.flow_precision_index.ten_minutes,count=true}..' 1h '..ps.get_flow_count{name=nm,category='output',precision_index=defines.flow_precision_index.one_hour,count=true}
rcon.print(table.concat(o,'|'))
"""
print(tools["run_lua"](" ".join(LUA.split())).replace("|", "\n"))
