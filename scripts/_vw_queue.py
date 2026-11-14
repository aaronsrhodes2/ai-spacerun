"""Read only: is the Vulcanus Wheel's west product belt queueing in front of the hub? Items on the y=-4 row (x -40..-7), on the product
column x=-40 (y -14..14) and on the y=1 out-belt (x -57..-41), and the two inserters into the hub. Usage: _vw_queue.py [samples] [seconds]"""
import sys
import time

from _game import tools

n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
gap = int(sys.argv[2]) if len(sys.argv) > 2 else 15
LUA = ("local s=game.surfaces['platform-17'] local function cnt(a) local c,f,nb=0,0,0 for _,b in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt'},area=a}) do nb=nb+1 for l=1,b.get_max_transport_line_index() do local k=b.get_transport_line(l).get_item_count() c=c+k if l<=2 and k>=4 then f=f+1 end end end return c..' ('..f..' full lanes on '..nb..' belts)' end "
       "local inv=s.platform.hub.get_inventory(defines.inventory.hub_main) rcon.print('tick '..game.tick..' | row y=-4: '..cnt({{-40,-4},{-6,-3}})..' | column x=-40: '..cnt({{-40,-14},{-39,14}})..' | y=1 out-belt: '..cnt({{-57,1},{-40,2}})..' | hub LDS '..inv.get_item_count('low-density-structure')..' carbon '..inv.get_item_count('carbon'))")
for i in range(n):
    print(tools["run_lua"](LUA).strip())
    if i + 1 < n:
        time.sleep(gap)
