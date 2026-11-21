#!/usr/bin/env python3
"""Turbo belts for the Fulgora ghosts (2026-11-20): made at the Vulcanus foundry unit (scripts/omni_fluid_asm.py, site 99,-112), carried Vulcanus -> Nauvis -> Fulgora.
Four request layers (qm_relay.py method, sections tagged by their first item so they never touch other sections):
  1 Vulcanus pad asks turbo-transport-belt 150 + turbo-underground-belt 5: that is the demand the Vulcanus unit reads (missing requests of its network)
  2 `Nauvis-Vulcanus 2 Shuttle` hub: imports express belt parts + lubricant barrels from nauvis (the unit's inputs), and imports the turbo items from vulcanus
  3 Nauvis pad asks the same turbo items (so the ship unloads them there)
  4 `Nauvis-Fulgora 2 Shuttle` hub imports the turbo items from nauvis; the Fulgora pad already asks for them (ghost_requests.py, group ghost-auto-fulgora)
Usage: turbo_relay.py [set|status]   (safe to run again)"""
import sys

from _game import tools

TURBO = {"turbo-transport-belt": 150, "turbo-underground-belt": 5, "big-mining-drill": 10}
INPUTS = {"express-transport-belt": 200, "express-underground-belt": 10, "lubricant-barrel": 100}
FN = ("local f=game.forces.player local function fill(ent,items,imp,tag) for _,pt in pairs(ent.get_logistic_point()) do if pt.mode==defines.logistic_mode.requester then local sec=nil "
      "for _,x in pairs(pt.sections) do if x.filters_count>0 and x.filters[1] and x.filters[1].value and x.filters[1].value.name==tag then sec=x end end sec=sec or pt.add_section() local i=0 "
      "for _,q in pairs(items) do i=i+1 local sl={value={type='item',name=q[1],quality='normal'},min=q[2]} if imp then sl.max=q[2] sl.import_from=imp end sec.set_slot(i,sl) "
      "if imp then pcall(function() local fl=sec.filters[i] fl.minimum_delivery_count=math.min(q[2],math.floor(1000000/prototypes.item[q[1]].weight)) sec.set_slot(i,fl) end) end end return true end end return false end "
      "local function ship(n) for _,p in pairs(f.platforms) do if p.name:sub(-#n)==n then return p end end end local function pad(sn) return game.surfaces[sn].find_entities_filtered{type='cargo-landing-pad'}[1] end local o={} ")


def tab(d):
    return "{" + ",".join("{'%s',%d}" % kv for kv in d.items()) + "}"


SET = FN + ("local T=%s local I=%s local V=ship('Nauvis-Vulcanus 2 Shuttle').hub local F=ship('Nauvis-Fulgora 2 Shuttle').hub "
            "o[#o+1]='vulcanus pad '..tostring(fill(pad('vulcanus'),T,nil,'turbo-transport-belt')) "
            "o[#o+1]='ship inputs '..tostring(fill(V,I,'nauvis','express-transport-belt')) "
            "o[#o+1]='ship turbo from vulcanus '..tostring(fill(V,T,'vulcanus','turbo-transport-belt')) "
            "o[#o+1]='nauvis pad '..tostring(fill(pad('nauvis'),T,nil,'turbo-transport-belt')) "
            "o[#o+1]='fulgora ship turbo '..tostring(fill(F,T,'nauvis','turbo-transport-belt')) rcon.print(table.concat(o,', '))") % (tab(TURBO), tab(INPUTS))
STATUS = ("local f=game.forces.player local o={} for _,sn in ipairs({'vulcanus','nauvis','fulgora'}) do local pad=game.surfaces[sn].find_entities_filtered{type='cargo-landing-pad'}[1] local ln=game.surfaces[sn].find_logistic_network_by_position(pad.position,'player') "
          "o[#o+1]=sn..' network turbo belts '..ln.get_item_count('turbo-transport-belt')..' underground '..ln.get_item_count('turbo-underground-belt')..' express '..ln.get_item_count('express-transport-belt')..' lube barrels '..ln.get_item_count('lubricant-barrel') end "
          "local u=game.surfaces.vulcanus.find_entities_filtered{name='foundry',area={{90,-125},{115,-100}}} for _,e in pairs(u) do local r=e.get_recipe() if r then local nm={} for k,v in pairs(defines.entity_status) do nm[v]=k end o[#o+1]='unit foundry '..r.name..' '..nm[e.status]..' made '..e.products_finished end end "
          "rcon.print(table.concat(o,' ; '))")

if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    print(tools["run_lua"]({"set": SET, "status": STATUS}[step]).replace(" ; ", "\n"))
