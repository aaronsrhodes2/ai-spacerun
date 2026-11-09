import sys, time
sys.path.insert(0,"scripts")
from _game import tools
lua=("local s=game.surfaces.nauvis local o={} local sp=s.find_entities_filtered{name='fast-splitter',position={-254.0,-132.5},radius=0.8}[1] o[#o+1]='splitter '..tostring(sp and sp.valid)"
 " local n=0 local far=-1e9 for _,e in pairs(s.find_entities_filtered{name={'fast-transport-belt','fast-underground-belt'},area={{-256,-162},{113,-130}}}) do local c=0 for i=1,e.get_max_transport_line_index() do c=c+e.get_transport_line(i).get_item_count('rocket-fuel') end if c>0 then n=n+c if e.position.x>far then far=e.position.x end end end"
 " o[#o+1]='rocket fuel on new belt '..n..' furthest x '..far"
 " for _,p in pairs({{22.5,-158.5},{43.5,-158.5},{90.5,-150.5},{111.5,-150.5}}) do local i=s.find_entities_filtered{name='burner-inserter',position=p,radius=0.3}[1] if i then local pt=i.pickup_target local dt=i.drop_target o[#o+1]=string.format('inserter %.1f,%.1f status %s pick %s drop %s',p[1],p[2],tostring(i.status),pt and pt.name or '-',dt and dt.name or '-') end end"
 " rcon.print(table.concat(o,' | '))")
for i in range(8):
    print(time.strftime("%H:%M:%S"), tools["run_lua"](lua), flush=True)
    time.sleep(30)
