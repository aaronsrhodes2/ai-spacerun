"""Read-only: what a ship parked in Aquilo orbit spends. Counts every explosive rocket and magazine aboard a platform (hub, belts, inserter
hands, turrets) and the asteroids round it, twice, and prints the difference per game minute.
Usage: _us_aquilo_watch.py INDEX [SECONDS]"""
import json
import sys
import time

from _game import tools

L = tools["run_lua"]
SNAP = ("local p=game.forces.player.platforms[%d] local s=p.surface local o={tick=game.tick,name=p.name,at=p.space_location and p.space_location.name or 'flying',ammo={},rocks={}} "
        "for _,n in pairs{'explosive-rocket','rocket','firearm-magazine','piercing-rounds-magazine','uranium-rounds-magazine'} do local c=p.hub.get_inventory(defines.inventory.hub_main).get_item_count(n) "
        "for _,b in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt','splitter'}}) do for li=1,b.get_max_transport_line_index() do c=c+b.get_transport_line(li).get_item_count(n) end end "
        "for _,t in pairs(s.find_entities_filtered{type='ammo-turret'}) do c=c+t.get_item_count(n) end for _,i in pairs(s.find_entities_filtered{type='inserter'}) do if i.held_stack.valid_for_read and i.held_stack.name==n then c=c+i.held_stack.count end end o.ammo[n]=c end "
        "for _,a in pairs(s.find_entities_filtered{type='asteroid'}) do o.rocks[a.name]=(o.rocks[a.name] or 0)+1 end o.turrets=s.count_entities_filtered{name='rocket-turret'} o.guns=s.count_entities_filtered{name='gun-turret'} "
        "local st=game.forces.player.get_item_production_statistics(s) o.made=st.get_input_count('explosive-rocket') o.used=st.get_output_count('explosive-rocket') "
        "local kc=game.forces.player.get_kill_count_statistics and 0 o.w=p.surface.count_tiles_filtered{name='space-platform-foundation'} rcon.print(helpers.table_to_json(o))")


def main():
    idx = int(sys.argv[1])
    secs = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    a = json.loads(L(SNAP % idx))
    print(a["name"], "at", a["at"], "| rocket turrets", a["turrets"], "guns", a["guns"], "| deck tiles", a["w"], "| asteroids in view", a["rocks"])
    time.sleep(secs)
    b = json.loads(L(SNAP % idx))
    mins = (b["tick"] - a["tick"]) / 3600.0
    for n in a["ammo"]:
        if a["ammo"][n] or b["ammo"][n]:
            print("  %-26s %7d -> %7d   %+.1f a minute" % (n, a["ammo"][n], b["ammo"][n], (b["ammo"][n] - a["ammo"][n]) / mins))
    print("  explosive rockets by the statistics: made %.1f, used %.1f a minute (%.1f game minutes); asteroids in view now %s" % ((b["made"] - a["made"]) / mins, (b["used"] - a["used"]) / mins, mins, b["rocks"]))


if __name__ == "__main__":
    main()
