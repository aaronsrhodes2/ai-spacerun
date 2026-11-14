"""Where chemical, production and agricultural packs sit: every platform hub, Nauvis lab contents, lab bonuses, one-hour production."""
from _game import tools

LUA = """
local f=game.forces.player local o={}
for i,p in pairs(f.platforms) do if p.hub then local inv=p.hub.get_inventory(defines.inventory.hub_main) local c=inv.get_item_count('chemical-science-pack') local pr=inv.get_item_count('production-science-pack') local a=inv.get_item_count('agricultural-science-pack')
if c+pr+a>0 then o[#o+1]=i..' '..p.name:sub(-28)..' @'..(p.space_location and p.space_location.name or 'transit')..' chem '..c..' prod '..pr..' agri '..a..' provide '..tostring(p.hub.providing_to_other_platforms) end end end
local n=game.surfaces.nauvis local labs=n.find_entities_filtered{type='lab'} local t={} for _,l in pairs(labs) do for _,it in pairs(l.get_inventory(defines.inventory.lab_input).get_contents()) do t[it.name]=(t[it.name] or 0)+it.count end end
local tt={} for k,v in pairs(t) do tt[#tt+1]=k..':'..v end o[#o+1]='nauvis lab contents '..table.concat(tt,' ')
local mm={} for _,it in pairs(labs[1].get_module_inventory().get_contents()) do mm[#mm+1]=it.name..'/'..it.quality..':'..it.count end
o[#o+1]='nauvis lab modules '..table.concat(mm,' ')..' speed '..labs[1].speed_bonus..' prod '..labs[1].productivity_bonus
local gl=game.surfaces.gleba.find_entities_filtered{type='lab'}[1] o[#o+1]='gleba lab speed '..gl.speed_bonus..' prod '..gl.productivity_bonus
local ps=f.get_item_production_statistics('nauvis') for _,nm in pairs({'chemical-science-pack','production-science-pack'}) do
o[#o+1]='nauvis '..nm..' made per min: 1h '..math.floor(ps.get_flow_count{name=nm,category='input',precision_index=defines.flow_precision_index.one_hour,count=false})..' 10h '..math.floor(ps.get_flow_count{name=nm,category='input',precision_index=defines.flow_precision_index.ten_hours,count=false}) end
local w={} for _,e in pairs(n.find_entities_filtered{force=f,type={'container','logistic-container','cargo-landing-pad'}}) do local c=e.get_item_count('production-science-pack') if c>=100 then w[#w+1]=e.name..'@'..e.position.x..','..e.position.y..'='..c end end
o[#o+1]='nauvis production packs in chests: '..table.concat(w,' ')
rcon.print(table.concat(o,'|'))
"""
print(tools["run_lua"](" ".join(LUA.split())).replace("|", "\n"))
