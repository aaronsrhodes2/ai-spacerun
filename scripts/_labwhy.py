"""Why are the labs idle: current research and its packs, lab status per surface, the packs each Nauvis lab lacks, pad stock."""
from _game import tools

LUA = """
local f=game.forces.player local o={}
local r=f.current_research
if r then local ing={} for _,i in pairs(r.research_unit_ingredients) do ing[#ing+1]=i.name end
o[#o+1]='research '..r.name..' units '..r.research_unit_count..' progress '..string.format('%.3f',f.research_progress)..' packs '..table.concat(ing,',') end
local q={} for _,t in pairs(f.research_queue) do local a=false for _,i in pairs(t.research_unit_ingredients) do if i.name=='agricultural-science-pack' then a=true end end q[#q+1]=t.name..(a and '(agri)' or '(no agri)') end
o[#o+1]='queue '..table.concat(q,' ')
local st={} for k,v in pairs(defines.entity_status) do st[v]=k end
for _,s in pairs(game.surfaces) do local labs=s.find_entities_filtered{type='lab',force=f} if #labs>0 then local c={} local miss={}
for _,l in pairs(labs) do local n=st[l.status] or '?' c[n]=(c[n] or 0)+1 if r then local inv=l.get_inventory(defines.inventory.lab_input) for _,i in pairs(r.research_unit_ingredients) do if inv.get_item_count(i.name)==0 then miss[i.name]=(miss[i.name] or 0)+1 end end end end
local a={} for k,v in pairs(c) do a[#a+1]=k..'='..v end local b={} for k,v in pairs(miss) do b[#b+1]=k..'='..v end
o[#o+1]=s.name..' labs '..#labs..': '..table.concat(a,' ')..' | labs lacking: '..table.concat(b,' ') end end
for _,sn in pairs({'nauvis','gleba'}) do local s=game.surfaces[sn] for _,pad in pairs(s.find_entities_filtered{type='cargo-landing-pad'}) do local t={} for _,it in pairs(pad.get_inventory(defines.inventory.cargo_landing_pad_main).get_contents()) do if it.name:find('science') then t[#t+1]=it.name:gsub('%-science%-pack','')..':'..it.count end end
local rq={} for _,se in pairs(pad.get_logistic_sections().sections) do for _,fl in pairs(se.filters) do if fl.value and fl.value.name:find('science') then rq[#rq+1]=fl.value.name:gsub('%-science%-pack','')..'>='..fl.min end end end
o[#o+1]=sn..' pad '..pad.position.x..','..pad.position.y..' stock '..table.concat(t,' ')..' | requests '..table.concat(rq,' ') end
local nets={} for _,net in pairs(f.logistic_networks[sn] or {}) do local n=net.get_item_count('agricultural-science-pack') if n>0 or net.all_logistic_robots>100 then nets[#nets+1]='robots '..net.all_logistic_robots..' agri '..n..' auto '..net.get_item_count('automation-science-pack')..' logi '..net.get_item_count('logistic-science-pack')..' chem '..net.get_item_count('chemical-science-pack')..' prod '..net.get_item_count('production-science-pack') end end
o[#o+1]=sn..' nets: '..table.concat(nets,' ; ') end
rcon.print(table.concat(o,'\\n'))
"""
print(tools["run_lua"](" ".join(LUA.split())))
