"""Module, lab and beacon stock in the biggest Nauvis network by quality, and what the lab and beacon prototypes allow."""
from _game import tools

LUA = """
local f=game.forces.player local nb,bn=nil,0 for _,net in pairs(f.logistic_networks.nauvis or {}) do if net.all_logistic_robots>bn then nb=net bn=net.all_logistic_robots end end local o={}
for _,n in pairs({'productivity-module','productivity-module-2','productivity-module-3','speed-module','speed-module-2','speed-module-3','lab','biolab','beacon','requester-chest','bulk-inserter','substation','heating-tower','logistic-robot','roboport'}) do for _,q in pairs({'normal','uncommon','rare','epic','legendary'}) do local c=nb.get_item_count({name=n,quality=q}) if c>0 then o[#o+1]=n..'/'..q..':'..c end end end
local b=prototypes.entity['beacon'] o[#o+1]='beacon eff epic '..tostring(b.distribution_effectivity+3*(b.distribution_effectivity_bonus_per_quality_level or 0))..' range '..b.get_supply_area_distance('epic')..' slots '..b.module_inventory_size..' profile1 '..tostring(b.profile and b.profile[1])..' profile2 '..tostring(b.profile and b.profile[2])..' profile4 '..tostring(b.profile and b.profile[4])
for _,m in pairs({'productivity-module','productivity-module-2','productivity-module-3','speed-module-3'}) do local e=prototypes.item[m].module_effects o[#o+1]=m..' prod '..tostring(e.productivity)..' speed '..tostring(e.speed)..' researched '..tostring(f.recipes[m].enabled) end
o[#o+1]='epic unlocked '..tostring(f.is_quality_unlocked('epic'))..' legendary '..tostring(f.is_quality_unlocked('legendary'))..' biolab '..tostring(f.recipes['biolab'] and f.recipes['biolab'].enabled)..' lab allowed effects '..serpent.line(prototypes.entity['lab'].allowed_effects)
rcon.print(table.concat(o,'|'))
"""
print(tools["run_lua"](" ".join(LUA.split())).replace("|", "\n"))
