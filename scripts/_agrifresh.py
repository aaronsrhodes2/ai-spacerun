"""How stale Gleba's agricultural packs are where they are used: spoil percent in the lab inputs, on the lab belt and in the science chest."""
from _game import tools

LUA = """
local g=game.surfaces.gleba local o={} local function stat(tag,list) local n,s,mx=0,0,0 for _,p in pairs(list) do n=n+1 s=s+p if p>mx then mx=p end end o[#o+1]=tag..': stacks '..n..' mean spoiled '..(n>0 and string.format('%.1f',100*s/n) or '-')..' pct, worst '..string.format('%.1f',100*mx)..' pct' end
local a={} for _,l in pairs(g.find_entities_filtered{type='lab'}) do local inv=l.get_inventory(defines.inventory.lab_input) for i=1,#inv do local st=inv[i] if st.valid_for_read and st.name=='agricultural-science-pack' then a[#a+1]=st.spoil_percent end end end stat('lab inputs',a)
local b={} for _,e in pairs(g.find_entities_filtered{type='transport-belt',area={{127,22},{128,43}}}) do for ln=1,2 do for _,d in pairs(e.get_transport_line(ln).get_detailed_contents()) do if d.stack.name=='agricultural-science-pack' then b[#b+1]=d.stack.spoil_percent end end end end stat('lab belt',b)
local c={} local ch=g.find_entities_filtered{position={128.5,20.5},type='logistic-container'}[1] local inv=ch.get_inventory(defines.inventory.chest) for i=1,#inv do local st=inv[i] if st.valid_for_read and st.name=='agricultural-science-pack' then c[#c+1]=st.spoil_percent end end stat('science chest',c)
local sp=0 for _,e in pairs(g.find_entities_filtered{type='transport-belt',area={{127,22},{128,43}}}) do sp=sp+e.get_item_count('spoilage') end o[#o+1]='spoilage on lab belt '..sp
local ps=game.forces.player.get_item_production_statistics(g) o[#o+1]='spoilage made per min on gleba (10 min) '..math.floor(ps.get_flow_count{name='spoilage',category='input',precision_index=defines.flow_precision_index.ten_minutes,count=false})
rcon.print(table.concat(o,'|'))
"""
print(tools["run_lua"](" ".join(LUA.split())).replace("|", "\n"))
