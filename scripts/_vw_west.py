"""Read only: what flows into the Vulcanus Wheel's hub on the west product belt (y=-4, x -31..-7, 25 tiles), six samples."""
import time

from _game import tools

LUA = ("local s=game.surfaces['platform-17'] local t={} local n=0 for _,e in pairs(s.find_entities_filtered{type='transport-belt',area={{-31,-4},{-6,-3}}}) do for l=1,2 do for _,it in pairs(e.get_transport_line(l).get_contents()) do t[it.name]=(t[it.name] or 0)+it.count n=n+it.count end end end "
       "local o={} for k,v in pairs(t) do o[#o+1]=k..' '..v end table.sort(o) local st={} for y=-4,-1 do local i=s.find_entities_filtered{type='inserter',position={-4.5,y+0.5},radius=0.3}[1] local k='?' for nm,v in pairs(defines.entity_status) do if v==i.status then k=nm end end st[#st+1]=k:sub(1,12) end "
       "rcon.print(n..' items: '..table.concat(o,', ')..' | inserters '..table.concat(st,' / '))")
tot = 0
for i in range(6):
    r = tools["run_lua"](LUA).strip()
    tot += int(r.split(" ")[0])
    print(r)
    time.sleep(4)
print("mean on 25 tiles %.1f -> about %.1f items a second if the belt runs free (5.625 tiles a second)" % (tot / 6, tot / 6 / 25 * 5.625))
