#!/usr/bin/env python3
"""Rate test for the Triangle strip miner: force a mode and keep removing that product from the hub (as a requesting platform would), count what was removed.
This is the machine-limited rate while a chunk backlog lasts. Removed items are destroyed (our own product, a test).
Usage: _triangle_drain.py iron|carbon|ice [seconds] [interval]"""
import sys
import time

import triangle_miner as M

ITEM = {"iron": "iron-ore", "carbon": "carbon", "ice": "ice"}


def main():
    mode = sys.argv[1]
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 40
    gap = float(sys.argv[3]) if len(sys.argv) > 3 else 2
    item = ITEM[mode]
    M.lua(M.HEAD + "local o=at('constant-combinator',3.5,7.5) local ob=o.get_or_create_control_behavior() while ob.sections_count>0 do ob.remove_section(1) end local sec=ob.add_section() sec.set_slot(1,{value={type='virtual',name='signal-M',quality='normal'},min=%d}) rcon.print(1)" % {"iron": 1, "carbon": 2, "ice": 3}[mode])
    rm = M.HEAD + "local inv=p.hub.get_inventory(defines.inventory.hub_main) local n=inv.get_item_count('%s') if n>0 then n=inv.remove{name='%s',count=n} end rcon.print(game.tick..' '..n)" % (item, item)
    t0 = None
    total = 0
    end = time.time() + secs
    first = True
    while time.time() < end:
        t, n = (int(x) for x in M.lua(rm).split())
        if first:
            t0, first = t, False
            continue
        total += n
        t1 = t
        time.sleep(gap)
    mins = (t1 - t0) / 3600.0
    print("%s: removed %d over %.2f game minutes = %.0f per minute (%.1f per second)" % (item, total, mins, total / mins, total / mins / 60))
    M.lua(M.HEAD + "local o=at('constant-combinator',3.5,7.5) local ob=o.get_or_create_control_behavior() while ob.sections_count>0 do ob.remove_section(1) end rcon.print('override cleared (automatic)')")


if __name__ == "__main__":
    main()
