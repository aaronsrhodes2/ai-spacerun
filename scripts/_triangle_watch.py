#!/usr/bin/env python3
"""Read-only watcher for the Triangle strip miner: one line per sample (mode, hub stocks, ring chunks, machine states, flows).
Usage: _triangle_watch.py [samples] [seconds between]   (optional --draw ITEM:COUNT removes that much of a product from the hub first: a test draw)"""
import sys
import time

import triangle_miner as M

LINE = (M.HEAD + "local hub=p.hub local inv=hub.get_inventory(defines.inventory.hub_main) local function sg(name,x,y,id) local e=at(name,x,y) local ok,v=pcall(function() return e.get_signals(id) end) local o={} if ok and v then for _,q in pairs(v) do o[#o+1]=q.signal.name:gsub('signal%-','')..'='..q.count end end return table.concat(o,',') end "
        "local st={} for _,e in pairs(s.find_entities_filtered{name='crusher'}) do local r=e.get_recipe() local k=(r and r.name:sub(1,3)..(r.name:find('crush') and 'C' or 'R') or '?') local w=e.status==defines.entity_status.working and 'W' or (e.status==defines.entity_status.full_output and 'F' or '-') st[#st+1]=k..w end table.sort(st) "
        "local bt={} for _,e in pairs(s.find_entities_filtered{type='transport-belt',area={{-10,-10},{9,9}}}) do for l=1,2 do for _,it in pairs(e.get_transport_line(l).get_contents()) do bt[it.name:sub(1,1)]=(bt[it.name:sub(1,1)] or 0)+it.count end end end "
        "rcon.print(game.tick..' MODE '..sg('decider-combinator',-4,7.5,W.combinator_output_red)..' | hub ore '..inv.get_item_count('iron-ore')..' carbon '..inv.get_item_count('carbon')..' ice '..inv.get_item_count('ice')..' | ring m'..(bt.m or 0)..' c'..(bt.c or 0)..' o'..(bt.o or 0)..' | '..table.concat(st,' '))")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    n = int(args[0]) if args else 12
    gap = float(args[1]) if len(args) > 1 else 5
    if "--draw" in sys.argv:
        for spec in sys.argv[sys.argv.index("--draw") + 1].split(","):
            item, cnt = spec.split(":")
            print("test draw", M.lua(M.HEAD + "rcon.print('removed %s '..p.hub.get_inventory(defines.inventory.hub_main).remove{name='%s',count=%s})" % (item, item, cnt)))
    for _ in range(n):
        print(M.lua(LINE), flush=True)
        time.sleep(gap)


if __name__ == "__main__":
    main()
