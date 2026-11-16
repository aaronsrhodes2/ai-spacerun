#!/usr/bin/env python3
"""Carbon-fiber works on Gleba (the Captain, 2026-11-15: fusion on Aquilo needs 350 carbon fiber = 3,500 yumako mash; "new dedicated towers").
Separate from the stable cell, in the network west of the hub: a yumako processor (fruit -> mash, a little seed) feeds a carbon-fiber biochamber (organic recipe) by one
inserter; the fiber goes to a provider chest for the Aquilo ship. Both are gated on fiber in the network < FIBER_CAP, so mash never piles up and rots.
No new towers yet (the yumako patch is full: gleba_farms dry yumako N found blocked spots): the works draws fruit from the network pool, so watch the cell's fruit starvation alarm.
Usage: gleba_fiber.py dry | build | status"""
import json
import sys

from _game import tools
import gleba_cell as G

OX, OY = 72, 26
FIBER_CAP = 400
Q = "epic"
PQ = "legendary"


def plan():
    P = G.Plan()
    xa, xb = OX + 1.5, OX + 5.5
    # A: yumako processor (biochamber): fruit and nutrients from one requester chest
    P.add("biochamber", xa, OY + 3.5, 0, "yumako-processing", Q)
    P.add("requester-chest", xa, OY + 0.5, request={"yumako": 250, "nutrients": 10})
    P.add("bulk-inserter", xa, OY + 1.5, 0, None, Q, cond=("carbon-fiber", "<", FIBER_CAP))
    P.add("bulk-inserter", OX + 3.5, OY + 3.5, 12, None, Q)                       # mash west -> east
    P.add("bulk-inserter", xa - 1, OY + 5.5, 0, None, Q, filt="yumako-seed")      # seeds to the farm
    P.add("passive-provider-chest", xa - 1, OY + 6.5)
    P.add("bulk-inserter", xa + 1, OY + 5.5, 0, None, Q, filt="spoilage")         # rot out
    P.add("passive-provider-chest", xa + 1, OY + 6.5)
    # B: carbon-fiber assembler
    P.add("biochamber", xb, OY + 3.5, 0, "carbon-fiber", Q)             # carbon fiber is an organic recipe: biochamber, not an assembler (found live)
    P.add("requester-chest", xb, OY + 0.5, request={"carbon": 200, "nutrients": 10})
    P.add("bulk-inserter", xb, OY + 1.5, 0, None, Q, cond=("carbon-fiber", "<", FIBER_CAP))
    P.add("bulk-inserter", xb, OY + 5.5, 0, None, Q)
    P.add("passive-provider-chest", xb, OY + 6.5)
    P.add("medium-electric-pole", OX + 3.5, OY + 2.5, 0, None, PQ)
    P.add("medium-electric-pole", OX + 3.5, OY + 5.5, 0, None, PQ)
    return P


def status():
    code = ("local s=game.surfaces.gleba local f=game.forces.player local m={} for k,v in pairs(defines.entity_status) do m[v]=k end local o={} "
            "for _,e in pairs(s.find_entities_filtered{area={{%d,%d},{%d,%d}},type='assembling-machine'}) do o[#o+1]=(e.get_recipe() and e.get_recipe().name or '-')..' '..(m[e.status] or '?') end "
            "local net=s.find_logistic_network_by_position({%s,%s},f) local fib=net and net.get_item_count('carbon-fiber') or -1 "
            "local ch=0 for _,c in pairs(s.find_entities_filtered{name='passive-provider-chest',area={{%d,%d},{%d,%d}}}) do ch=ch+c.get_inventory(defines.inventory.chest).get_item_count('carbon-fiber') end "
            "rcon.print(table.concat(o,', ')..' | fiber in network '..fib..' in works chests '..ch..' | carbon in network '..(net and net.get_item_count('carbon') or -1)..' mash '..(net and net.get_item_count('yumako-mash') or -1))"
            ) % (OX, OY, OX + 8, OY + 8, OX + 4, OY + 4, OX, OY, OX + 8, OY + 8)
    print(G.L(code))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "dry"
    if cmd == "status":
        return status()
    P = plan()
    if cmd == "dry":
        placed, failed = G.place(P, True)
        print("dry run: placed", placed, "failed", json.dumps(failed)[:2000])
        return
    tools["save_game"]("skippy")
    placed, failed = G.place(P, False)
    print("placed", placed, "failed", json.dumps(failed)[:2000])
    for r in G.cfg_lua(P):
        print(r)


if __name__ == "__main__":
    main()
