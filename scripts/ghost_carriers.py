#!/usr/bin/env python3
"""Carrier requests for ghost materials that no ship was asking for (the Captain, 2026-11-20: trace every alert, open the pipeline).
`alert_trace.py` showed pads asking orbit for items that no ship on the route held or asked its source planet for. This writes ONE
request section per ship, group `ghost-carry-<ship index>` (ours alone, rewritten each run), from the table below. A request on a ship
in orbit is also what the source planet's Replicator sees as demand (its silos read orbital requests), so the ask starts the making.
Also writes pad slots (group `ghost-carry-pad-<planet>`) for parts a planet lacks to make an item itself.
The table is hand-kept: update it from the tracer's verdicts.   Usage: ghost_carriers.py [--apply]"""
import sys

from _game import tools

L = tools["run_lua"]
# ship name part: [(item, count, source planet)]
FIBER = [("carbon-fiber", 300, "gleba"), ("lithium-plate", 300, "gleba"), ("fluoroketone-hot-barrel", 60, "gleba")]   # foundation line: on to Nauvis
BIO = [("bioflux", 200, "gleba")]      # feeds the captive biter spawner on Nauvis (1 a minute; spoils in 2 hours, so small lots on every ship)
SHIPS = {
    "Courier 1": [("big-mining-drill", 9, "vulcanus"), ("turbo-transport-belt", 150, "vulcanus"), ("turbo-underground-belt", 4, "vulcanus")],   # for Fulgora
    # for Aquilo: stack inserters. For the foundation line (foundation_line.py): Aquilo's lithium and hot fluoroketone, relayed by the Gleba pad
    # carbon and iron ore: its Gleba stop waits for 2,000 of each (it remakes its ammunition from them) and its crushers get no chunks at rest.
    # Asked from Gleba's own stock, NOT relayed over the pad: a pad slot would also pull carbon and ore out of every other ship in orbit.
    "Gleba-Aquilo 1": [("stack-inserter", 12, "gleba"), ("lithium-plate", 2000, "aquilo"), ("fluoroketone-hot-barrel", 170, "aquilo"),
                       ("carbon", 2000, "gleba"), ("iron-ore", 2000, "gleba")],
    "Nauvis-Gleba 1": [("electronic-circuit", 200, "nauvis")] + BIO + FIBER,     # circuits: Gleba's biochamber recipe has none
    "Nauvis-Gleba 2": BIO + FIBER,
    "Nauvis-Gleba 3": BIO + FIBER,
    "Nauvis-Gleba 4": BIO + FIBER,
    "Nauvis-Gleba 5": BIO + FIBER,
    "Nauvis-Gleba 6": BIO + FIBER,
    "Nauvis-Vulcanus 1": [("tungsten-plate", 2000, "vulcanus")],
    "Nauvis-Vulcanus 2": [("tungsten-plate", 2000, "vulcanus")],
    "Nauvis-Vulcanus 3": [("tungsten-plate", 2000, "vulcanus")],
    # the ask that makes Nauvis build foundation (its silos read orbital requests): 50 a rocket
    "Nauvis-Fulgora 1": [("foundation", 200, "nauvis")],
    "Nauvis-Fulgora 2": [("foundation", 200, "nauvis")],
    "Nauvis-Fulgora 3": [("foundation", 200, "nauvis")],
}
PADS = {"gleba": [("electronic-circuit", 200), ("lithium-plate", 2000), ("fluoroketone-hot-barrel", 400)],
        "nauvis": [("bioflux", 400), ("tungsten-plate", 6000), ("carbon-fiber", 2000), ("lithium-plate", 2000), ("fluoroketone-hot-barrel", 400)]}

SHIP = ("local f=game.forces.player local o={} for i,p in pairs(f.platforms) do if p.name:find('%s',1,true) and p.hub and p.hub.valid then local pt for _,q in pairs(p.hub.get_logistic_point()) do if q.mode==defines.logistic_mode.requester then pt=q end end "
        "local g='ghost-carry-'..i for k=#pt.sections,1,-1 do if pt.sections[k].group==g then if %s then pt.remove_section(k) end end end if %s then local s=pt.add_section(g) local n=0 for _,r in pairs{%s} do n=n+1 s.set_slot(n,{value={type='item',name=r[1],quality='normal'},min=r[2],max=r[2],import_from=r[3]}) end end o[#o+1]=p.name:gsub('%%[.-%%]','')..' group '..g end end rcon.print(table.concat(o,'; '))")
PAD = ("local s=game.surfaces['%s'] for _,pad in pairs(s.find_entities_filtered{type='cargo-landing-pad'}) do for _,pt in pairs(pad.get_logistic_point()) do if pt.mode==defines.logistic_mode.requester then local g='ghost-carry-pad-%s' "
       "for k=#pt.sections,1,-1 do if pt.sections[k].group==g then pt.remove_section(k) end end local x=pt.add_section(g) local n=0 for _,r in pairs{%s} do n=n+1 x.set_slot(n,{value={type='item',name=r[1],quality='normal'},min=r[2]}) end end end end rcon.print('pad section written')")


def main():
    apply = "--apply" in sys.argv
    for name, rows in SHIPS.items():
        print("%-16s %s" % (name, ", ".join("%d %s from %s" % (c, i, p) for i, c, p in rows)))
        if apply:
            a = "true"
            print("   " + L(SHIP % (name, a, a, ",".join("{'%s',%d,'%s'}" % r for r in rows))).strip())
    for planet, rows in PADS.items():
        print("pad %-12s %s" % (planet, ", ".join("%d %s" % (c, i) for i, c in rows)))
        if apply:
            print("   " + L(PAD % (planet, planet, ",".join("{'%s',%d}" % r for r in rows))).strip())


if __name__ == "__main__":
    main()
