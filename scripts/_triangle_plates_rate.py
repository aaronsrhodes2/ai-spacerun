#!/usr/bin/env python3
"""Read-only: rates of the triangle plate works (scripts/triangle_plates.py) over N GAME minutes (default 10).
Prints per game minute: plates made (iron, copper), ore, carbon, ice, chunks caught, hub stocks, the Nauvis pad's copper / iron
plates and free slots, the Nauvis Wheel's copper plate, collectors full, ring chunks, low-power entities, and the solar output
needed (machines working x their drain, from the prototypes). Usage: _triangle_plates_rate.py [game minutes] [sample every s]"""
import sys
import time

from _game import tools
import triangle_miner as tm

ITEMS = ["iron-plate", "copper-plate", "iron-ore", "copper-ore", "carbon", "ice", "metallic-asteroid-chunk", "carbonic-asteroid-chunk", "oxide-asteroid-chunk"]
SAMPLE = (tm.AT + "local f=game.forces.player.get_item_production_statistics(s) local inv=p.hub.get_inventory(defines.inventory.hub_main) local tr=p.hub.get_inventory(defines.inventory.hub_trash) local o={game.tick} "
          "for _,n in pairs(ITEMS) do o[#o+1]=f.get_input_count(n) end for _,n in pairs(ITEMS) do o[#o+1]=inv.get_item_count(n) end "
          "local pad=game.surfaces.nauvis.find_entities_filtered{type='cargo-landing-pad',position={-216,-228},radius=3}[1] local pi=pad.get_inventory(defines.inventory.cargo_landing_pad_main) "
          "o[#o+1]=pi.get_item_count('copper-plate') o[#o+1]=pi.get_item_count('iron-plate') o[#o+1]=pi.count_empty_stacks() "
          "local wc=0 for _,q in pairs(game.forces.player.platforms) do if q.name:find('Nauvis Wheel',1,true) then wc=q.hub.get_inventory(defines.inventory.hub_main).get_item_count('copper-plate') end end o[#o+1]=wc "
          "local full=0 for _,c in pairs(s.find_entities_filtered{type='asteroid-collector'}) do if c.status==defines.entity_status.full_output then full=full+1 end end o[#o+1]=full "
          "local ring=0 for _,b in pairs(s.find_entities_filtered{type='transport-belt',area={{-9.5,-9.5},{9.5,8.99}}}) do local x,y=b.position.x,b.position.y if x<-8.4 or x>7.4 or y<-8.4 or y>7.4 then for l=1,2 do ring=ring+b.get_transport_line(l).get_item_count() end end end o[#o+1]=ring "
          "local lp,w=0,0 for _,e in pairs(s.find_entities_filtered{type={'furnace','assembling-machine','asteroid-collector','inserter'}}) do if e.status==defines.entity_status.low_power or e.status==defines.entity_status.no_power then lp=lp+1 end "
          "if e.status==defines.entity_status.working then local ok,u=pcall(function() return e.prototype.get_max_energy_usage(e.quality)*(1+math.max(-0.8,(e.consumption_bonus or 0))) end) if ok and u then w=w+u end end end o[#o+1]=lp o[#o+1]=string.format('%.2f',w*60/1e6) "
          "o[#o+1]=tr and (#tr-tr.count_empty_stacks()) or 0 "
          "rcon.print(table.concat(o,' '))").replace("ITEMS", "{" + ",".join("'%s'" % n for n in ITEMS) + "}")


def sample():
    v = tools["run_lua"](SAMPLE).split()
    n = len(ITEMS)
    return {"tick": int(v[0]), "made": dict(zip(ITEMS, map(float, v[1:1 + n]))), "hub": dict(zip(ITEMS, map(int, v[1 + n:1 + 2 * n]))),
            "pad_cu": int(v[1 + 2 * n]), "pad_fe": int(v[2 + 2 * n]), "pad_free": int(v[3 + 2 * n]), "wheel_cu": int(v[4 + 2 * n]),
            "full": int(v[5 + 2 * n]), "ring": int(v[6 + 2 * n]), "lowpower": int(v[7 + 2 * n]), "mw_working": float(v[8 + 2 * n]), "trash": int(v[9 + 2 * n])}


def line(a, b):
    m = (b["tick"] - a["tick"]) / 3600.0
    r = {k: (b["made"][k] - a["made"][k]) / m for k in ITEMS}
    short = {"iron-plate": "Fe-pl", "copper-plate": "Cu-pl", "iron-ore": "Fe-ore", "copper-ore": "Cu-ore", "carbon": "C", "ice": "ice",
             "metallic-asteroid-chunk": "met", "carbonic-asteroid-chunk": "car", "oxide-asteroid-chunk": "oxi"}
    return ("%.1f game min | per min: %s | hub %s | pad Cu %d Fe %d free %d | wheel Cu %d | collectors full %d ring %d trash %d | low power %d, working draw %.1f MW"
            % (m, " ".join("%s %.0f" % (short[k], r[k]) for k in ITEMS), " ".join("%s %d" % (short[k], b["hub"][k]) for k in ITEMS[:6]),
               b["pad_cu"], b["pad_fe"], b["pad_free"], b["wheel_cu"], b["full"], b["ring"], b["trash"], b["lowpower"], b["mw_working"]))


def main():
    mins = float(sys.argv[1]) if len(sys.argv) > 1 else 10
    every = float(sys.argv[2]) if len(sys.argv) > 2 else 60
    a = sample()
    prev = a
    print("start tick", a["tick"], "hub", a["hub"], "pad Cu", a["pad_cu"], "Fe", a["pad_fe"], "free", a["pad_free"], "wheel Cu", a["wheel_cu"], flush=True)
    while True:
        time.sleep(every)
        b = sample()
        print("  step", line(prev, b), flush=True)
        prev = b
        if (b["tick"] - a["tick"]) / 3600.0 >= mins:
            break
    print("TOTAL", line(a, b), flush=True)


if __name__ == "__main__":
    main()
