#!/usr/bin/env python3
"""Watches one platform until it reaches a place, is hurt, or the minutes run out. One line a minute.
Usage: watch_shuttle.py NAME UNTIL_PLACE [MINUTES]     e.g. watch_shuttle.py "Nauvis-Gleba 5 Shuttle II" nauvis 60"""
import sys
import time

from _game import tools

LUA = ("for _,p in pairs(game.forces.player.platforms) do if p.name=='NAME' then local s=p.surface local fl={} for _,t in pairs(s.find_entities_filtered{name='storage-tank'}) do for k,v in pairs(t.get_fluid_contents()) do fl[k]=(fl[k] or 0)+v end end "
       "local dmg,dead=0,s.count_entities_filtered{type='entity-ghost'} for _,e in pairs(s.find_entities_filtered{force='player'}) do if e.health and e.max_health and e.health<e.max_health*0.6 then dmg=dmg+1 end end local inv=p.hub.get_inventory(defines.inventory.hub_main) "
       "rcon.print((p.space_location and p.space_location.name or 'flight')..'|'..dmg..'|'..dead..'|fuel '..math.floor(fl['thruster-fuel'] or 0)..' oxidizer '..math.floor(fl['thruster-oxidizer'] or 0)..' water '..math.floor(fl['water'] or 0)"
       "..' magazines '..inv.get_item_count('firearm-magazine')..' ore '..inv.get_item_count('iron-ore')..' speed '..string.format('%.0f',p.speed or 0)..' free slots '..inv.count_empty_stacks()) return end end rcon.print('gone|0|0|')")


def main():
    name, until = sys.argv[1], sys.argv[2]
    minutes = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    left = False
    for i in range(minutes):
        where, dmg, ghosts, rest = tools["run_lua"](LUA.replace("NAME", name)).strip().split("|")
        print(time.strftime("%H:%M"), where, "badly damaged", dmg, "destroyed", ghosts, rest, flush=True)
        if where != until:
            left = True
        if int(ghosts) > 0:
            return print("STOP: something was destroyed")
        if where == until and (left or i == 0):
            return print("ARRIVED at", until)
        time.sleep(60)
    print("TIME UP")


if __name__ == "__main__":
    main()
