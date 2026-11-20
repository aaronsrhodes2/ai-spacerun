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
SHIPS = {
    "Courier 1": [("big-mining-drill", 9, "vulcanus"), ("turbo-transport-belt", 150, "vulcanus"), ("turbo-underground-belt", 4, "vulcanus")],   # for Fulgora
    "Gleba-Aquilo 1": [("stack-inserter", 12, "gleba")],                                                                                     # for Aquilo
    # bioflux feeds the captive biter spawner on Nauvis (1 a minute; it spoils in 2 hours, so small lots on every ship)
    "Nauvis-Gleba 1": [("electronic-circuit", 200, "nauvis"), ("bioflux", 200, "gleba")],     # circuits: Gleba's biochamber recipe has none
    "Nauvis-Gleba 2": [("bioflux", 200, "gleba")],
    "Nauvis-Gleba 3": [("bioflux", 200, "gleba")],
    "Nauvis-Gleba 4": [("bioflux", 200, "gleba")],
    "Nauvis-Gleba 5": [("bioflux", 200, "gleba")],
    "Nauvis-Gleba 6": [("bioflux", 200, "gleba")],
}
PADS = {"gleba": [("electronic-circuit", 200)], "nauvis": [("bioflux", 400)]}

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
