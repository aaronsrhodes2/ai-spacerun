from _game import tools
L = tools["run_lua"]
for s in ("nauvis","fulgora","gleba","vulcanus","aquilo"):
    print(L("local o={} for _,si in pairs(game.surfaces['%s'].find_entities_filtered{name='rocket-silo'}) do local ok,tr=pcall(function() return si.use_transitional_requests end) o[#o+1]=si.position.x..','..si.position.y..' status '..si.status..' trans='..tostring(tr)..' parts '..si.rocket_parts..' rocket '..tostring(si.rocket~=nil)..' quality '..si.quality.name end rcon.print('%s: '..table.concat(o,' ; '))" % (s,s)))
