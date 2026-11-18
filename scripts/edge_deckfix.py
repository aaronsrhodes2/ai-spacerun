#!/usr/bin/env python3
"""Edgerunner: lay the deck tiles the hub leaves as ghosts (it skips a few of every batch, cause unknown: seen 2026-11-17 and 2026-11-18).
Each tile is laid by script and PAID with one foundation taken from the hub, so nothing is created. Only tiles of the named build's own set.
Usage: edge_deckfix.py bar|bays|tanks|spoke|rails"""
import sys

import triangle_miner as TM
from _game import tools

L = tools["run_lua"]


def tiles(which):
    if which == "bar":
        import edge_bar as M
        return M.layout()[1]
    if which == "bays":
        import edge_bays as M
        return M.deck_tiles()
    if which == "tanks":
        import edge_tanks as M
        return M.layout()[1]
    if which == "spoke":
        import edge_spoke as M
        return M.layout()[1]
    if which == "rails":
        import edge_rails as M
        t = set()
        for side in (-1, 1):
            t |= M.survey(M.side_plan(side))[0]
        return t
    sys.exit(__doc__)


if __name__ == "__main__":
    ts = sorted(tiles(sys.argv[1]))
    lst = "{" + ",".join("{%d,%d}" % c for c in ts) + "}"
    print(L(TM.AT + "local inv=p.hub.get_inventory(defines.inventory.hub_main) local n,short=0,0 for _,q in pairs(" + lst + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' then "
            "if inv.remove{name='space-platform-foundation',count=1}==1 then local g=s.find_entities_filtered{type='tile-ghost',position={q[1]+0.5,q[2]+0.5},radius=0.3}[1] if g then g.destroy() end "
            "s.set_tiles({{name='space-platform-foundation',position={q[1],q[2]}}}) n=n+1 else short=short+1 end end end rcon.print('laid from hub stock '..n..', still missing (hub has no foundation) '..short)"))
