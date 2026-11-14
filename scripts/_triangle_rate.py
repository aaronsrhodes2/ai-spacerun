#!/usr/bin/env python3
"""Read-only: chunk catch and product rates of the Triangle strip miner over a window (default 90 s of wall time), from the surface's item statistics.
Usage: _triangle_rate.py [seconds]"""
import sys
import time

import triangle_miner as M

Q = (M.HEAD + "local f=game.forces.player.get_item_production_statistics(s) local o={} for _,n in pairs({'metallic-asteroid-chunk','carbonic-asteroid-chunk','oxide-asteroid-chunk','iron-ore','carbon','ice'}) do o[#o+1]=n..'='..f.get_input_count(n)..'/'..f.get_output_count(n) end "
     "local bt=0 local cnt=0 for _,e in pairs(s.find_entities_filtered{type='transport-belt'}) do for l=1,2 do for _,it in pairs(e.get_transport_line(l).get_contents()) do if it.name:find('chunk') then bt=bt+it.count end end end end "
     "local w=0 for _,c in pairs(s.find_entities_filtered{type='asteroid-collector'}) do if c.status==defines.entity_status.working then w=w+1 end end rcon.print(game.tick..'|'..table.concat(o,';')..'|'..bt..'|'..w)")


def sample():
    t, body, belts, w = M.lua(Q).split("|")
    return int(t), {kv.split("=")[0]: [float(x) for x in kv.split("=")[1].split("/")] for kv in body.split(";")}, int(belts), int(w)


def main():
    wait = float(sys.argv[1]) if len(sys.argv) > 1 else 90
    t0, a, b0, _ = sample()
    time.sleep(wait)
    t1, b, b1, w = sample()
    mins = (t1 - t0) / 3600.0
    print("window %.2f game minutes; collectors working at end %d of %d" % (mins, w, 98))
    for k in a:
        print("%-26s made %7.1f/min   used %7.1f/min" % (k, (b[k][0] - a[k][0]) / mins, (b[k][1] - a[k][1]) / mins))
    print("chunks on all belts: %d -> %d (%+.1f/min)" % (b0, b1, (b1 - b0) / mins))


if __name__ == "__main__":
    main()
