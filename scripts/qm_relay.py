#!/usr/bin/env python3
"""Relay quality-module-2 and advanced circuits Nauvis -> Fulgora (2026-11-20, stage 0 of docs/fulgora-legendary-workshop.md).
Quality module 3 is crafted on Fulgora (superconductors and processing units are there); tier 2 and the circuits come from Nauvis on
'Nauvis-Fulgora 2 Shuttle'. Same method as aquilo_supply.py: a ship-hub section importing from nauvis, the Fulgora pad asking for the same.
Usage: qm_relay.py [set|status]   (safe to run again)"""
import sys

from _game import tools

ITEMS = {"quality-module-2": 100, "advanced-circuit": 600}
FN = ("local f=game.forces.player local function fill(ent,items,imp,tag) for _,pt in pairs(ent.get_logistic_point()) do if pt.mode==defines.logistic_mode.requester then local sec=nil "
      "for _,x in pairs(pt.sections) do if x.filters_count>0 and x.filters[1] and x.filters[1].value and x.filters[1].value.name==tag then sec=x end end sec=sec or pt.add_section() local i=0 "
      "for _,q in pairs(items) do i=i+1 local sl={value={type='item',name=q[1],quality='normal'},min=q[2]} if imp then sl.max=q[2] sl.import_from=imp end sec.set_slot(i,sl) "
      "if imp then pcall(function() local fl=sec.filters[i] fl.minimum_delivery_count=math.min(q[2],math.floor(1000000/prototypes.item[q[1]].weight)) sec.set_slot(i,fl) end) end end return true end end return false end "
      "local function ship(n) for _,p in pairs(f.platforms) do if p.name:sub(-#n)==n then return p end end end local o={} ")
tab = "{" + ",".join("{'%s',%d}" % kv for kv in ITEMS.items()) + "}"
SET = FN + ("local T=" + tab + " o[#o+1]='ship '..tostring(fill(ship('Nauvis-Fulgora 2 Shuttle').hub,T,'nauvis','quality-module-2')) "
            "o[#o+1]='fulgora pad '..tostring(fill(game.surfaces.fulgora.find_entities_filtered{type='cargo-landing-pad'}[1],T,nil,'quality-module-2')) rcon.print(table.concat(o,', '))")
STATUS = ("local f=game.forces.player local o={} for _,p in pairs(f.platforms) do if p.name:sub(-24)=='Nauvis-Fulgora 2 Shuttle' then local inv=p.hub.get_inventory(defines.inventory.hub_main) "
          "o[#o+1]='ship qm2 '..inv.get_item_count('quality-module-2')..' ac '..inv.get_item_count('advanced-circuit') end end "
          "local pad=game.surfaces.fulgora.find_entities_filtered{type='cargo-landing-pad'}[1] local pi=pad.get_inventory(defines.inventory.cargo_landing_pad_main) "
          "o[#o+1]='pad qm2 '..pi.get_item_count('quality-module-2')..' ac '..pi.get_item_count('advanced-circuit') "
          "local ln=game.surfaces.fulgora.find_logistic_network_by_position(pad.position,'player') o[#o+1]='fulgora network qm2 '..ln.get_item_count('quality-module-2')..' ac '..ln.get_item_count('advanced-circuit')..' sc '..ln.get_item_count('superconductor') rcon.print(table.concat(o,' ; '))")

if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    print(tools["run_lua"]({"set": SET, "status": STATUS}[step]).replace(" ; ", "\n"))
