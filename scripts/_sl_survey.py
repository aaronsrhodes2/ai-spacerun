import sys
from _game import tools
L = tools["run_lua"]
ITEMS = ["holmium-plate","construction-robot","logistic-robot","low-density-structure","processing-unit","speed-module-3","productivity-module-3","efficiency-module-3","uranium-fuel-cell","cryogenic-plant","concrete","refined-concrete","rocket-fuel","explosive-rocket","uranium-rounds-magazine","fusion-power-cell","superconductor","supercapacitor","lithium-plate","electromagnetic-plant","cryogenic-science-pack","rocket-part","quantum-processor","carbon-fiber","foundation","space-platform-foundation"]
lst = "{" + ",".join("'%s'" % i for i in ITEMS) + "}"
print(L("local o={} for _,n in pairs(%s) do local p=prototypes.item[n] o[#o+1]=n..' w='..(p and p.weight or 'nil')..' stack='..(p and p.stack_size or 'nil') end rcon.print(table.concat(o,chr(10)))" % lst) if False else "")
print(L("local o={} for _,n in pairs(%s) do local p=prototypes.item[n] o[#o+1]=n..' w='..tostring(p and p.weight)..' stack='..tostring(p and p.stack_size) end rcon.print(table.concat(o,string.char(10)))" % lst))
print("--- platforms")
print(L("local o={} for _,p in pairs(game.forces.player.platforms) do local h=p.hub o[#o+1]=p.index..' '..p.name..' | '..(p.space_location and p.space_location.name or 'flight')..' st'..p.state..' paused='..tostring(p.paused)..' | ex-rockets '..(h and h.valid and h.get_inventory(defines.inventory.hub_main).get_item_count('explosive-rocket') or -1) end rcon.print(table.concat(o,string.char(10)))"))
print("--- pads")
print(L("local o={} for _,s in pairs{'nauvis','fulgora','gleba','vulcanus','aquilo'} do local pad=game.surfaces[s].find_entities_filtered{type='cargo-landing-pad'}[1] if pad then local inv=pad.get_inventory(defines.inventory.cargo_landing_pad_main) local t={} for _,n in pairs(%s) do local c=inv.get_item_count(n) if c>0 then t[#t+1]=n..'='..c end end o[#o+1]=s..' pad at '..pad.position.x..','..pad.position.y..' slots '..#inv..' free '..inv.count_empty_stacks()..' :: '..table.concat(t,', ') end end rcon.print(table.concat(o,string.char(10)))" % lst))
