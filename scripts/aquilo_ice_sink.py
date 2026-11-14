#!/usr/bin/env python3
"""The ice sink of the Aquilo base (the Captain, 2026-11-13: "the biggest problem was what to do with all of the ice ... recycle ice").
Found 2026-11-14: the ice chest of the separation plant filled (4,550), the plant stopped, so no ammonia, no solid fuel, and the heating tower
ran out. Ice is the by-product of the ammonia that heats the base, so the surplus has to leave: a recycler (ice-recycling gives a quarter back).
  recycler   tiles x 38..39, y -5..-2 facing south, beside the heat pipe column x=37
  intake     requester chest (41.5,-3.5) asking ICE_ASK ice, fast inserter (40.5,-3.5) into the recycler
  output     two passive provider chests in front (38.5,-0.5) and (39.5,-0.5): the quarter that comes back returns to the network and round again
Usage: aquilo_ice_sink.py [--apply]"""
import json
import sys

import aquilo_base as base
from _game import tools

ICE_ASK = 400
E, S = 4, 8


def main():
    apply = "--apply" in sys.argv
    base.SIZE["recycler"] = (2, 4)
    base.HEATED.add("recycler")
    base.ents[:] = []
    base.put("recycler", 39.0, -3.0, S)
    base.put("fast-inserter", 40.5, -3.5, E)
    base.put("requester-chest", 41.5, -3.5)
    base.put("passive-provider-chest", 38.5, -0.5)
    base.put("passive-provider-chest", 39.5, -0.5)
    print("heat pipes added:", base.heat_all((30, -8, 46, 2)))
    print("new pieces:", base.drop_existing())
    r = json.loads(tools["place_entities"](json.dumps(base.ents), surface="aquilo", dry_run=not apply))
    print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:600])
    if apply:
        print(tools["run_lua"]("local s=game.surfaces.aquilo local c=s.find_entities_filtered{name='requester-chest',position={41.5,-3.5},radius=0.4}[1] "
                               "local pt=c.get_logistic_point(defines.logistic_member_index.logistic_container) local sec=pt.get_section(1) or pt.add_section() "
                               "sec.set_slot(1,{value={type='item',name='ice',quality='normal'},min=%d}) rcon.print('ice sink asks '..sec.filters[1].min)" % ICE_ASK))


if __name__ == "__main__":
    main()
