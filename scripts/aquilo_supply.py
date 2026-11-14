#!/usr/bin/env python3
"""Supply chain for the first Aquilo base (2026-11-13). Relay rule: outer ships fly outer planet <-> Fulgora only, cargo changes ship on
the Fulgora surface. Everything is factory-made stock moved by rocket; nothing is spawned.
  Nauvis -> Fulgora   'Nauvis-Fulgora 2 Shuttle' asks Nauvis for RELAY; the Fulgora landing pad asks for the same and takes it down
  Fulgora -> Aquilo   'Fulgora-Aquilo 1 Shuttle' asks Fulgora for CARGO (the relayed items plus Fulgora's own); Fulgora's silo sends it up
  Aquilo              the landing pad there asks for CARGO once it stands (step `pad`, after the first landing)
Why these: the cryogenic science trigger is crafting one cryogenic plant on Aquilo (20 processing units, 20 superconductors, 20 lithium
plates, 40 refined concrete); lithium needs holmium plate; the first heating towers burn rocket fuel until local solid fuel flows.
Safe to run again. Usage: aquilo_supply.py [pad|status]"""
import sys

from _game import tools

RELAY = {"processing-unit": 300, "refined-concrete": 60}
CARGO = dict(RELAY, **{"holmium-plate": 400, "superconductor": 100, "concrete": 100, "rocket-fuel": 100})
FN = ("local f=game.forces.player local function fill(ent,items,imp,tag) for _,pt in pairs(ent.get_logistic_point()) do if pt.mode==defines.logistic_mode.requester then local sec=nil "
      "for _,x in pairs(pt.sections) do if x.filters_count>0 and x.filters[1] and x.filters[1].value and x.filters[1].value.name==tag then sec=x end end sec=sec or pt.add_section() local i=0 "
      "for _,q in pairs(items) do i=i+1 local sl={value={type='item',name=q[1],quality='normal'},min=q[2]} if imp then sl.max=q[2] sl.import_from=imp end sec.set_slot(i,sl) "
      "if imp then pcall(function() local fl=sec.filters[i] fl.minimum_delivery_count=math.min(q[2],math.floor(1000000/prototypes.item[q[1]].weight)) sec.set_slot(i,fl) end) end end return true end end return false end "
      "local function ship(n) for _,p in pairs(f.platforms) do if p.name==n then return p end end end local o={} ")
SET = FN + ("o[#o+1]='relay ship '..tostring(fill(ship('Nauvis-Fulgora 2 Shuttle').hub,RELAY,'nauvis','processing-unit')) "
            "o[#o+1]='fulgora pad '..tostring(fill(game.surfaces.fulgora.find_entities_filtered{type='cargo-landing-pad'}[1],RELAY,nil,'processing-unit')) "
            "o[#o+1]='aquilo ship '..tostring(fill(ship('Fulgora-Aquilo 1 Shuttle').hub,CARGO,'fulgora','processing-unit')) rcon.print(table.concat(o,', '))")
PAD = FN + "local pad=game.surfaces.aquilo.find_entities_filtered{type='cargo-landing-pad'}[1] rcon.print('aquilo pad '..tostring(pad and fill(pad,CARGO,nil,'processing-unit')))"
STATUS = ("local f=game.forces.player local o={} for _,n in pairs{'Nauvis-Fulgora 2 Shuttle','Fulgora-Aquilo 1 Shuttle'} do for _,p in pairs(f.platforms) do if p.name==n then local inv=p.hub.get_inventory(defines.inventory.hub_main) local t={} "
          "for _,q in pairs(CARGO) do t[#t+1]=q[1]..' '..inv.get_item_count(q[1]) end o[#o+1]=n..' at '..(p.space_location and p.space_location.name or 'flight')..': '..table.concat(t,', ') end end end "
          "local pad=game.surfaces.fulgora.find_entities_filtered{type='cargo-landing-pad'}[1] local pi=pad.get_inventory(defines.inventory.cargo_landing_pad_main) local t={} for _,q in pairs(CARGO) do t[#t+1]=q[1]..' '..pi.get_item_count(q[1]) end o[#o+1]='fulgora pad: '..table.concat(t,', ') rcon.print(table.concat(o,' ; '))")


def tab(d):
    return "{" + ",".join("{'%s',%d}" % kv for kv in d.items()) + "}"


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "set"
    code = {"set": SET, "pad": PAD, "status": STATUS}[step]
    code = code.replace("RELAY", tab({k: RELAY[k] for k in ["processing-unit", "refined-concrete"]})).replace("CARGO", tab({k: CARGO[k] for k in ["processing-unit", "refined-concrete", "holmium-plate", "superconductor", "concrete", "rocket-fuel"]}))
    print(tools["run_lua"](code).replace(" ; ", "\n"))
