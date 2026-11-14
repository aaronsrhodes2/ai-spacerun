"""Read only: the White Science platform (platform-1): hub, machine statuses by recipe, belts, requests, schedule."""
from _game import tools

S = "platform-1"
lua = (
    "local s=game.surfaces['%s'] local p=s.platform local h=p.hub local inv=h.get_inventory(defines.inventory.hub_main) local o={} "
    "local c={} for _,it in pairs(inv.get_contents()) do c[#c+1]=it.name..' '..it.count end "
    "o[#o+1]='hub free '..inv.count_empty_stacks()..'/'..#inv..': '..table.concat(c,', ') "
    "local tr=h.get_inventory(defines.inventory.hub_trash) local c2={} if tr then for _,it in pairs(tr.get_contents()) do c2[#c2+1]=it.name..' '..it.count end end o[#o+1]='trash: '..table.concat(c2,', ') "
    "o[#o+1]='paused '..tostring(p.paused)..' state '..tostring(p.state)..' loc '..tostring(p.space_location and p.space_location.name)..' sched '..(p.schedule and serpent.line(p.schedule) or 'none'):sub(1,300) "
    "local st={} for _,e in pairs(s.find_entities_filtered{type={'assembling-machine','furnace','asteroid-collector','inserter','thruster','solar-panel','accumulator','cargo-bay'}}) do local k='?' for n,v in pairs(defines.entity_status) do if v==e.status then k=n end end "
    "local rc=(e.type=='assembling-machine' or e.type=='furnace') and e.get_recipe() k=e.name..(rc and ('/'..rc.name) or '')..' '..k st[k]=(st[k] or 0)+1 end local l={} for k,v in pairs(st) do l[#l+1]=k..' '..v end table.sort(l) o[#o+1]=table.concat(l,'\\n') "
    "local bt={} for _,e in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt','splitter'}}) do for li=1,e.get_max_transport_line_index() do for _,it in pairs(e.get_transport_line(li).get_contents()) do bt[it.name]=(bt[it.name] or 0)+it.count end end end "
    "local b={} for k,v in pairs(bt) do b[#b+1]=k..' '..v end o[#o+1]='on belts: '..table.concat(b,', ') "
    "local rq={} for _,lp in pairs(h.get_logistic_point()) do for _,sec in pairs(lp.sections) do for i,fl in pairs(sec.filters) do if fl.value then rq[#rq+1]=fl.value.name..':'..(fl.min or 0)..'/'..tostring(fl.max)..'['..(sec.group or '')..(sec.active and '' or ' off')..']' end end end end o[#o+1]='requests: '..table.concat(rq,' ') "
    "local a=s.count_entities_filtered{type='asteroid-chunk'} o[#o+1]='free chunks near '..a "
    "local bb=nil for _,e in pairs(s.find_entities()) do local q=e.bounding_box if not bb then bb={q.left_top.x,q.left_top.y,q.right_bottom.x,q.right_bottom.y} else bb[1]=math.min(bb[1],q.left_top.x) bb[2]=math.min(bb[2],q.left_top.y) bb[3]=math.max(bb[3],q.right_bottom.x) bb[4]=math.max(bb[4],q.right_bottom.y) end end o[#o+1]='bbox '..serpent.line(bb) "
    "rcon.print(table.concat(o,'\\n'))" % S)
print(tools["run_lua"](lua))
