#!/usr/bin/env python3
"""Waits until the Aquilo landing pad holds the relayed robots, fuel cells and ice (the Captain's base on Aquilo, 2026-11-13).
One line a minute; ends when the pad has 20 fuel cells and 20 construction robots, or after MINUTES (default 240).
Usage: watch_aquilo_cargo.py [MINUTES]"""
import sys
import time

from _game import tools

LUA = ("local f=game.forces.player local o={} for _,p in pairs(f.platforms) do if p.name:sub(-#'Fulgora-Aquilo 1 Shuttle')=='Fulgora-Aquilo 1 Shuttle' then o[#o+1]='ship '..tostring(p.space_location and p.space_location.name or 'flight') end if p.name:sub(-#'Nauvis-Fulgora 2 Shuttle')=='Nauvis-Fulgora 2 Shuttle' then local inv=p.hub.get_inventory(defines.inventory.hub_main) o[#o+1]='relay '..tostring(p.space_location and p.space_location.name or 'flight')..' cells '..inv.get_item_count('uranium-fuel-cell') end end "
       "local pad=game.surfaces.aquilo.find_entities_filtered{type='cargo-landing-pad'}[1] local pi=pad.get_inventory(defines.inventory.cargo_landing_pad_main) local fp=game.surfaces.fulgora.find_entities_filtered{type='cargo-landing-pad'}[1].get_inventory(defines.inventory.cargo_landing_pad_main) "
       "rcon.print(table.concat(o,' | ')..' | fulgora pad cells '..fp.get_item_count('uranium-fuel-cell')..' robots '..fp.get_item_count('construction-robot')..' | AQUILO pad cells '..pi.get_item_count('uranium-fuel-cell')..' robots '..pi.get_item_count('construction-robot')..' logistic '..pi.get_item_count('logistic-robot')..' ice '..pi.get_item_count('ice'))")


def main():
    minutes = int(sys.argv[1]) if len(sys.argv) > 1 else 240
    for _ in range(minutes):
        line = tools["run_lua"](LUA).strip()
        print(time.strftime("%H:%M"), line, flush=True)
        if "AQUILO pad cells" in line:
            try:
                c = int(line.split("AQUILO pad cells ")[1].split()[0])
                r = int(line.split("AQUILO pad cells ")[1].split("robots ")[1].split()[0])
                if c >= 20 and r >= 20:
                    return print("ARRIVED: the pad holds the cells and robots")
            except (IndexError, ValueError):
                pass
        time.sleep(60)
    print("TIME UP")


if __name__ == "__main__":
    main()
