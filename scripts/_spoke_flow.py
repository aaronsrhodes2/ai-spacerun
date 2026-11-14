"""Read only: chunk flow on each spoke belt of each wheel, estimated from what lies on a 100-tile stretch (express belt: 5.625 tiles a second),
sampled several times. West spoke: upstream of the spiral tap (x -160..-61) and after it (x -52..-48)."""
import time

from _game import tools
from _wheels import wheels

LUA = ("local s=game.surfaces['SURF'] local function cnt(a) local t={met=0,car=0,oxi=0} local nb=0 for _,e in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt'},area=a}) do nb=nb+1 for l=1,e.get_max_transport_line_index() do for _,it in pairs(e.get_transport_line(l).get_contents()) do local k=it.name:sub(1,3) if t[k] then t[k]=t[k]+it.count end end end end return nb..':'..t.met..'/'..t.car..'/'..t.oxi end "
       "rcon.print('W '..cnt({{-160,-1},{-60,0}})..' | N '..cnt({{-1,-160},{1,-60}})..' | E '..cnt({{60,-1},{160,1}})..' | S '..cnt({{-1,60},{1,160}})..' | Wy1 '..cnt({{-160,0},{-60,2}}))")
for name, planet, surface, turrets in wheels():
    print("==", name, "belts:metallic/carbonic/oxide on 100 tiles (x60..160 from the centre), three samples 5 s apart")
    for i in range(3):
        print("  ", tools["run_lua"](LUA.replace("SURF", surface)).strip())
        time.sleep(5)
