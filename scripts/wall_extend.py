#!/usr/bin/env python3
"""Replicator wall after the repack (docs/replicator-compaction-plan.md): the old north line (y=-234.5), the west line (x=-366.5) and a new south line at y=-185.5
(x -366.5..-287.5) closing the box under the fluid-assembler unit, which stands at (-352,-192). The east side was never walled (the chem yard is there).
History: first extended north to y=-243.5 and south to y=-162.5 to cover the spill; the repack pulled everything back inside, so those lines were removed.
Usage: wall_extend.py [--apply]   (default dry run)"""
import json
import sys

from _game import tools

X0, X1 = -366.5, -287.5
S = -185.5
Q = {"quality": "epic"}
ents = [{"name": "stone-wall", "x": X0 + i, "y": S, "params": Q} for i in range(int(X1 - X0) + 1)]
ents += [{"name": "stone-wall", "x": X0, "y": -188.5 + i, "params": Q} for i in range(3)]       # west line down to the new south corner (-189.5 is the old west line's end)
if __name__ == "__main__":
    dry = "--apply" not in sys.argv
    res = json.loads(tools["place_entities"](json.dumps(ents), surface="nauvis", dry_run=dry))
    print(len(ents), "walls;", {k: v for k, v in res.items() if k in ("placed", "failed")})
