"""Scratch (read-only): totals made on a wheel at this tick, to difference two readings. Usage: _wxg_meter.py [SURFACE]"""
import sys

from _game import tools

SURF = sys.argv[1] if len(sys.argv) > 1 else "platform-12"
print(tools["run_lua"](("local s=game.surfaces['SURF'] local f=game.forces.player.get_item_production_statistics(s) local inv=s.platform.hub.get_inventory(defines.inventory.hub_main) local o={'tick '..game.tick} "
                        "for _,n in pairs{'rocket-fuel','chemical-science-pack','logistic-science-pack','automation-science-pack','military-science-pack','production-science-pack','space-science-pack','coal','carbon','sulfur','low-density-structure','processing-unit'} do "
                        "o[#o+1]=n..' made '..f.get_input_count(n)..' used '..f.get_output_count(n)..' hub '..inv.get_item_count(n) end rcon.print(table.concat(o,'@@'))").replace("SURF", SURF)).replace("@@", "\n"))
