"""White Science: return building items that a freshly placed hub inserter put on the chunk loop (before its filter was set) to the hub.
Only items that are neither chunks nor the platform's products are moved; prints what it moved and the release inserter's state."""
from _game import tools

print(tools["run_lua"](
    "local s=game.surfaces['platform-1'] local hub=s.platform.hub local ok={['carbon']=1,['ice']=1,['iron-plate']=1,['iron-ore']=1,['space-science-pack']=1,['metallic-asteroid-chunk']=1,['carbonic-asteroid-chunk']=1,['oxide-asteroid-chunk']=1,['copper-ore']=1,['sulfur']=1,['calcite']=1} "
    "local m={} for _,e in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt','splitter'}}) do for l=1,e.get_max_transport_line_index() do local tl=e.get_transport_line(l) for _,it in pairs(tl.get_contents()) do if not ok[it.name] then "
    "local n=tl.remove_item{name=it.name,count=it.count,quality=it.quality} if n>0 then hub.insert{name=it.name,count=n,quality=it.quality} m[it.name]=(m[it.name] or 0)+n end end end end end "
    "local i=s.find_entities_filtered{type='inserter',position={-2.5,4.5},radius=0.3}[1] local f={} for k=1,i.filter_slot_count do local x=i.get_filter(k) if x then f[#f+1]=x.name end end "
    "if i.held_stack.valid_for_read and not ok[i.held_stack.name] then local n=hub.insert(i.held_stack) m[i.held_stack.name]=(m[i.held_stack.name] or 0)+n i.held_stack.clear() end "
    "local o={} for k,v in pairs(m) do o[#o+1]=k..' '..v end local st='?' for n,v in pairs(defines.entity_status) do if v==i.status then st=n end end "
    "local sg={} local net=i.get_circuit_network(defines.wire_connector_id.circuit_red) if net and net.signals then for _,g in pairs(net.signals) do sg[#sg+1]=g.signal.name..'='..g.count end end "
    "rcon.print('returned to the hub: '..table.concat(o,', ')..' | release inserter '..st..' filters ['..table.concat(f,',')..'] red {'..table.concat(sg,' ')..'}')"))
