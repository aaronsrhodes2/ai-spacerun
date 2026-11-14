"""Read only: where science packs are made, used and stocked; landing pad requests; lab statuses."""
from _game import tools

PACKS = ["automation-science-pack", "logistic-science-pack", "military-science-pack", "chemical-science-pack", "production-science-pack",
         "utility-science-pack", "space-science-pack"]

lua = (
    "local f=game.forces.player local packs={%s} local out={} "
    "local pr=defines.flow_precision_index.ten_minutes "
    "for _,s in pairs(game.surfaces) do local st=f.get_item_production_statistics(s) local line={} "
    "for _,k in pairs(packs) do local a=st.get_flow_count{name=k,category='input',precision_index=pr} local b=st.get_flow_count{name=k,category='output',precision_index=pr} "
    "if a>0.5 or b>0.5 then line[#line+1]=k:sub(1,5)..' +'..math.floor(a)..' -'..math.floor(b) end end "
    "local labs=s.find_entities_filtered{type='lab'} local ls={} for _,l in pairs(labs) do local n='?' for k,v in pairs(defines.entity_status) do if v==l.status then n=k end end ls[n]=(ls[n] or 0)+1 end "
    "local lt={} for k,v in pairs(ls) do lt[#lt+1]=k..'='..v end "
    "if #line>0 or #labs>0 then out[#out+1]=s.name..' | '..table.concat(line,', ')..' | labs '..table.concat(lt,',') end "
    "for _,pad in pairs(s.find_entities_filtered{type='cargo-landing-pad'}) do local inv=pad.get_inventory(defines.inventory.cargo_landing_pad_main) local c={} "
    "for _,k in pairs(packs) do c[#c+1]=k:sub(1,5)..'='..inv.get_item_count(k) end "
    "local rq={} local lp=pad.get_logistic_point(defines.logistic_member_index.logistic_container) or pad.get_logistic_point()[1] "
    "if lp then for _,sec in pairs(lp.sections) do for i,fl in pairs(sec.filters) do if fl.value and fl.value.name and fl.value.name:find('science') then rq[#rq+1]=fl.value.name:sub(1,5)..':'..(fl.min or 0)..(sec.active and '' or '(off)')..'['..(sec.group or '')..']' end end end end "
    "out[#out+1]='  pad '..pad.position.x..','..pad.position.y..' free '..inv.count_empty_stacks()..' has '..table.concat(c,' ')..' asks '..table.concat(rq,' ') end "
    "end rcon.print(table.concat(out,'\\n'))" % ",".join("'%s'" % p for p in PACKS))
print(tools["run_lua"](lua))

lua2 = (
    "local f=game.forces.player local out={} for i,p in pairs(f.platforms) do local h=p.hub if h and h.valid then local inv=h.get_inventory(defines.inventory.hub_main) "
    "local loc=p.space_location and p.space_location.name or 'transit' "
    "out[#out+1]=i..' '..p.name:gsub('^%[.-%]%s*','')..' @'..loc..' '..p.surface.name..' prov='..tostring(h.providing_to_other_platforms)..' free='..inv.count_empty_stacks()..' space='..inv.get_item_count('space-science-pack')..' red='..inv.get_item_count('automation-science-pack')..' paused='..tostring(p.paused) end end rcon.print(table.concat(out,'\\n'))")
print(tools["run_lua"](lua2))
