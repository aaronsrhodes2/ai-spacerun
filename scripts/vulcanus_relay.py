#!/usr/bin/env python3
"""Relay electric engine units and electric mining drills Nauvis -> Vulcanus (2026-11-20) for the big-mining-drill foundry unit (scripts/big_drill_unit.py).
Same method as qm_relay.py: a ship-hub section on Nauvis-Vulcanus 2 Shuttle importing from nauvis, the Vulcanus pad asking for the same.
Usage: vulcanus_relay.py [set|status]   (safe to run again)"""
import sys

from _game import tools

ITEMS = {"electric-engine-unit": 100, "electric-mining-drill": 10}
FN = ("local f=game.forces.player local function fill(ent,items,imp,tag) for _,pt in pairs(ent.get_logistic_point()) do if pt.mode==defines.logistic_mode.requester then local sec=nil "
      "for _,x in pairs(pt.sections) do if x.filters_count>0 and x.filters[1] and x.filters[1].value and x.filters[1].value.name==tag then sec=x end end sec=sec or pt.add_section() local i=0 "
      "for _,q in pairs(items) do i=i+1 local sl={value={type='item',name=q[1],quality='normal'},min=q[2]} if imp then sl.max=q[2] sl.import_from=imp end sec.set_slot(i,sl) "
      "if imp then pcall(function() local fl=sec.filters[i] fl.minimum_delivery_count=math.min(q[2],math.floor(1000000/prototypes.item[q[1]].weight)) sec.set_slot(i,fl) end) end end return true end end return false end "
      "local function ship(n) for _,p in pairs(f.platforms) do if p.name:sub(-#n)==n then return p end end end local o={} ")
tab = "{" + ",".join("{'%s',%d}" % kv for kv in ITEMS.items()) + "}"
SET = FN + ("local T=" + tab + " o[#o+1]='ship '..tostring(fill(ship('Nauvis-Vulcanus 2 Shuttle').hub,T,'nauvis','electric-engine-unit')) "
            "o[#o+1]='vulcanus pad '..tostring(fill(game.surfaces.vulcanus.find_entities_filtered{type='cargo-landing-pad'}[1],T,nil,'electric-engine-unit')) rcon.print(table.concat(o,', '))")
STATUS = ("local f=game.forces.player local o={} for _,p in pairs(f.platforms) do if p.name:sub(-25)=='Nauvis-Vulcanus 2 Shuttle' then local inv=p.hub.get_inventory(defines.inventory.hub_main) "
          "o[#o+1]='ship eng '..inv.get_item_count('electric-engine-unit')..' drill '..inv.get_item_count('electric-mining-drill') end end "
          "local pad=game.surfaces.vulcanus.find_entities_filtered{type='cargo-landing-pad'}[1] local pi=pad.get_inventory(defines.inventory.cargo_landing_pad_main) "
          "o[#o+1]='pad eng '..pi.get_item_count('electric-engine-unit')..' drill '..pi.get_item_count('electric-mining-drill') "
          "local ln=game.surfaces.vulcanus.find_logistic_network_by_position(pad.position,'player') o[#o+1]='vulcanus network eng '..ln.get_item_count('electric-engine-unit')..' drill '..ln.get_item_count('electric-mining-drill') rcon.print(table.concat(o,' ; '))")

if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    print(tools["run_lua"]({"set": SET, "status": STATUS}[step]).replace(" ; ", "\n"))
