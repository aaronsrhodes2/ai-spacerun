#!/usr/bin/env python3
"""Soak test for the Triangle strip miner: for N minutes of wall time act like requesting platforms (every INTERVAL s take DRAW of each product, rotating which
product is hit hardest) and log one line a sample: mode, stocks, ring chunks, belt chunks, machine states, collectors working. Removed items are destroyed (own product).
Usage: _triangle_soak.py [minutes] [interval s]"""
import sys
import time

import triangle_miner as M

LINE = (M.HEAD + "local hub=p.hub local inv=hub.get_inventory(defines.inventory.hub_main) local function sg(name,x,y,id) local e=at(name,x,y) local ok,v=pcall(function() return e.get_signals(id) end) local o={} if ok and v then for _,q in pairs(v) do o[#o+1]=q.signal.name:gsub('signal%-','')..'='..q.count end end return table.concat(o,',') end "
        "local st={} for _,e in pairs(s.find_entities_filtered{name='crusher'}) do local r=e.get_recipe() local k=(r and r.name:sub(1,3)..(r.name:find('crush') and 'C' or 'R') or '?') local w=e.status==defines.entity_status.working and 'W' or (e.status==defines.entity_status.full_output and 'F' or '-') st[#st+1]=k..w end table.sort(st) "
        "local ring={} for _,e in pairs(s.find_entities_filtered{type='transport-belt',area={{-10,-10},{9,8.9}}}) do for l=1,2 do for _,it in pairs(e.get_transport_line(l).get_contents()) do ring[it.name:sub(1,1)]=(ring[it.name:sub(1,1)] or 0)+it.count end end end "
        "local bt=0 for _,e in pairs(s.find_entities_filtered{type='transport-belt'}) do for l=1,2 do for _,it in pairs(e.get_transport_line(l).get_contents()) do bt=bt+it.count end end end "
        "local w=0 for _,c in pairs(s.find_entities_filtered{type='asteroid-collector'}) do if c.status==defines.entity_status.working then w=w+1 end end local lowp=0 for _,e in pairs(s.find_entities_filtered{type='assembling-machine'}) do if e.status==defines.entity_status.low_power or e.status==defines.entity_status.no_power then lowp=lowp+1 end end "
        "rcon.print(game.tick..' MODE '..sg('decider-combinator',-4,7.5,W.combinator_output_red)..' | ore '..inv.get_item_count('iron-ore')..' carbon '..inv.get_item_count('carbon')..' ice '..inv.get_item_count('ice')..' free slots '..inv.count_empty_stacks()..' | ring m'..(ring.m or 0)..' c'..(ring.c or 0)..' o'..(ring.o or 0)..' | belts '..bt..' | '..table.concat(st,' ')..' | collectors working '..w..' lowpower machines '..lowp)")


def main():
    mins = float(sys.argv[1]) if len(sys.argv) > 1 else 12
    gap = float(sys.argv[2]) if len(sys.argv) > 2 else 30
    items = ["iron-ore", "carbon", "ice"]
    end = time.time() + mins * 60
    i = 0
    while time.time() < end:
        hard = items[i % 3]
        draw = ["%s=%d" % (n, 400 if n == hard else 100) for n in items]
        M.lua(M.HEAD + "local inv=p.hub.get_inventory(defines.inventory.hub_main) for n,c in pairs({%s}) do inv.remove{name=n,count=c} end rcon.print(1)" % ",".join("['%s']=%s" % tuple(d.split("=")) for d in draw))
        print("draw", ",".join(draw), flush=True)
        print(M.lua(LINE), flush=True)
        i += 1
        time.sleep(gap)


if __name__ == "__main__":
    main()
