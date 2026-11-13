"""Gleba fruit-cut test: removes the feed belt tile at (126.5,0.5) for MINUTES game minutes, puts it back, and prints the egg state all along.
Usage: _glebacut.py MINUTES [seconds between lines]"""
import json
import sys
import time

from _game import tools


def lua(x):
    return tools["run_lua"](x)


S = ("local s=game.surfaces.gleba local a,b,rest,work=0,0,0,0 for _,m in pairs(s.find_entities_filtered{name='biochamber',area={{92,13},{124,16}}}) do "
     "local n=m.get_inventory(defines.inventory.crafter_input).get_item_count('pentapod-egg')+m.get_output_inventory().get_item_count('pentapod-egg')+(m.is_crafting() and 1 or 0) "
     "if m.position.x>116 then a=a+n elseif m.position.x<98 then b=b+n else rest=rest+n end if m.status==defines.entity_status.working then work=work+1 end end "
     "local function belts(x0,y0,x1,y1,item) local c=0 for _,bl in pairs(s.find_entities_filtered{type='transport-belt',area={{x0,y0},{x1+1,y1+1}}}) do for l=1,2 do c=c+bl.get_transport_line(l).get_item_count(item) end end return c end "
     "local res=0 for _,x in pairs{130.5,132.5,134.5} do res=res+s.find_entities_filtered{type='logistic-container',position={x,10.5},radius=0.3}[1].get_inventory(defines.inventory.chest).get_item_count('spoilage') end "
     "rcon.print(string.format('%.1f',game.tick/3600)..' min | keeper A eggs '..a..' keeper B eggs '..b..' production '..rest..' working '..work..' | fruit '..(belts(74,3,125,3,'yumako')+belts(74,3,125,3,'jellynut'))..' nutrients '..(belts(76,9,124,9,'nutrients')+belts(67,11,124,11,'nutrients'))"
     "..' reserve '..res..' | enemies '..s.count_entities_filtered{force='enemy',area={{30,-30},{160,60}}}..' labs working '..s.count_entities_filtered{type='lab',status=defines.entity_status.working})")
minutes = float(sys.argv[1])
iv = int(sys.argv[2]) if len(sys.argv) > 2 else 40
print(lua(S), flush=True)
print(lua("local b=game.surfaces.gleba.find_entities_filtered{type='transport-belt',position={126.5,0.5},radius=0.3}[1] if b then b.destroy() end rcon.print('feed belt tile removed')"), flush=True)
t0 = int(lua("rcon.print(game.tick)"))
try:
    while int(lua("rcon.print(game.tick)")) - t0 < minutes * 3600:
        time.sleep(iv)
        print(lua(S), flush=True)
finally:
    print(tools["place_entities"](json.dumps([{"name": "turbo-transport-belt", "x": 126.5, "y": 0.5, "direction": 8, "params": {"quality": "epic"}}]), surface="gleba", dry_run=False)[:120], flush=True)
for i in range(6):
    time.sleep(iv)
    print(lua(S), flush=True)
