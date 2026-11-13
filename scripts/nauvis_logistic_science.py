#!/usr/bin/env python3
"""Nauvis logistic science made none (2026-11-13): its seven inserter assemblers (x -198.5 ... -78.5 step 20, y -59.5) had iron and gears
but no electronic circuits on their belt, while the network held 232,000. Six of them get a blue chest (electronic circuits 200) on the north side
with an inserter into the assembler. Usage: nauvis_logistic_science.py [--apply]"""
import json
import sys

from _game import tools

XS = [-198.5 + 20 * i for i in range(7)]
# chest side: east of centre, except where a substation stands there (west instead). The last unit (-78.5) has a belt north of it: no room, left belt-fed.
SIDE = {-198.5: -1, -158.5: -1}
XS = [x + SIDE.get(x, 1) - 1 for x in XS if x != -78.5]
e = []
for x in XS:
    e += [{"name": "bulk-inserter", "x": x + 1, "y": -61.5, "direction": 0, "params": {"quality": "epic"}},
          {"name": "requester-chest", "x": x + 1, "y": -62.5, "params": {"quality": "epic"}}]
REQ = ("local s=game.surfaces.nauvis local n=0 for _,x in pairs(XS) do local c=s.find_entities_filtered{name='requester-chest',position={x+1,-62.5},radius=0.3}[1] if c then "
       "local ss=c.get_logistic_sections() local se=ss.sections[1] or ss.add_section() se.set_slot(1,{value={name='electronic-circuit',quality='normal'},min=200}) n=n+1 end "
       "local i=s.find_entities_filtered{type='inserter',position={x+1,-61.5},radius=0.3}[1] if i then i.use_filters=true i.inserter_filter_mode='whitelist' i.set_filter(1,'electronic-circuit') end end rcon.print('circuit chests set '..n)")
apply = "--apply" in sys.argv
print(tools["place_entities"](json.dumps(e), surface="nauvis", dry_run=not apply)[:500])
if apply:
    print(tools["run_lua"](REQ.replace("XS", "{" + ",".join(str(x) for x in XS) + "}")))
