#!/usr/bin/env python3
"""Fleet rework, part 1b: what was pinning shuttles on 2026-11-18, and the fixes (each safe to run again).
Found by reading how long every shuttle had stood at its stop (fleet_survey.py and LuaSchedule.ticks_in_station):
  furnaces   Nauvis-Gleba 1, 3 and 6 had stood at Nauvis for 30 hours: every furnace held 3 iron PLATES in its INPUT slot (a furnace given
             plates waits for 5 to make steel), so no ore went in, no plate came out, no magazine was made and the magazine count never
             reached the 800 the schedule asks for. `furnaces` moves such plates into the hub, on every shuttle.
  oxidizer   Courier 1 had stood at Vulcanus for 99 hours: no oxidizer tank was on the hub's wire, so "oxidizer >= 22,000" was never
             true (the old oxidizer-wire lesson). `oxidizer` wires one oxidizer tank and one fuel tank to the hub on any shuttle whose
             hub network lacks that signal.
  trash      a platform does not leave while its hub holds trash it cannot drop. The Nauvis landing pad was full (1,280 slots, 1,000 of
             them 49,986 tungsten carbide) and the Aquilo pad too. `trash` moves a pinned shuttle's trash back into its hold and switches
             off the drop sections (request slots with max 0) that made it, wherever the landing pad below has under PADFREE free slots.
  pad        `pad PLANET` turns on "trash unrequested" on that planet's landing pad, so robots carry what the pad does not ask for to
             storage and the pad cannot fill with one item again.
Steps: status | furnaces | oxidizer | trash | pad PLANET
Usage: fleet_unpin.py status ; fleet_unpin.py furnaces ; fleet_unpin.py oxidizer ; fleet_unpin.py trash ; fleet_unpin.py pad nauvis"""
import sys

from _game import tools

L = tools["run_lua"]
PADFREE = 50
EACH = "local o={} for i,p in pairs(game.forces.player.platforms) do if (p.name:find('Shuttle',1,true) or p.name:find('Courier',1,true)) and p.hub and p.hub.valid then local s=p.surface local hub=p.hub local inv=hub.get_inventory(defines.inventory.hub_main) "
END = " end end rcon.print(#o>0 and table.concat(o,string.char(10)) or 'nothing to do')"

STATUS = (EACH + "local tr=hub.get_inventory(defines.inventory.hub_trash) local t={} for _,x in pairs(tr.get_contents()) do t[#t+1]=x.name..' '..x.count end local jam=0 for _,f in pairs(s.find_entities_filtered{type='furnace'}) do if f.get_inventory(defines.inventory.crafter_input).get_item_count('iron-plate')>0 then jam=jam+1 end end "
          "local sig={} for _,c in pairs{defines.wire_connector_id.circuit_red,defines.wire_connector_id.circuit_green} do local net=hub.get_circuit_network(c) if net then for _,sg in pairs(net.signals or {}) do if sg.signal.type=='fluid' then sig[sg.signal.name]=true end end end end "
          "o[#o+1]=string.format('%3d %-26s %-9s stood %6d s%s%s%s%s',i,p.name:gsub('%[.-%]',''):sub(1,26),p.space_location and p.space_location.name or 'flying',math.floor(p.get_schedule().ticks_in_station/60),p.paused and ' PAUSED' or '',jam>0 and (' | furnaces jammed '..jam) or '',(not sig['thruster-oxidizer'] or not sig['thruster-fuel']) and ' | NO fuel/oxidizer signal' or '',#t>0 and (' | trash '..table.concat(t,', ')) or '')" + END)

FURNACES = (EACH + "local n,moved=0,0 for _,f in pairs(s.find_entities_filtered{type='furnace'}) do local fin=f.get_inventory(defines.inventory.crafter_input) local c=fin.get_item_count('iron-plate') if c>0 then local got=inv.insert{name='iron-plate',count=c} if got>0 then fin.remove{name='iron-plate',count=got} moved=moved+got n=n+1 end end end "
            "if n>0 then o[#o+1]=i..' '..p.name:gsub('%[.-%]','')..': furnaces cleared '..n..', iron plates into the hub '..moved end" + END)

OXIDIZER = (EACH + "local G=defines.wire_connector_id.circuit_green local sig={} local net=hub.get_circuit_network(G) if net then for _,sg in pairs(net.signals or {}) do if sg.signal.type=='fluid' then sig[sg.signal.name]=true end end end "
            "local done={} for _,fl in pairs{'thruster-oxidizer','thruster-fuel'} do if not sig[fl] then for _,t in pairs(s.find_entities_filtered{type='storage-tank'}) do if (t.get_fluid_contents()[fl] or 0)>0 or (t.fluidbox[1] and t.fluidbox[1].name==fl) then "
            "local a,b=hub.get_wire_connector(G,true),t.get_wire_connector(G,true) if not a.is_connected_to(b) then a.connect_to(b,false) end done[#done+1]=fl break end end end end "
            "if #done>0 then o[#o+1]=i..' '..p.name:gsub('%[.-%]','')..': wired to the hub: '..table.concat(done,', ') end" + END)

TRASH = (EACH + "local tr=hub.get_inventory(defines.inventory.hub_trash) local loc=p.space_location and p.space_location.name if loc and game.surfaces[loc] and not tr.is_empty() then local pad=game.surfaces[loc].find_entities_filtered{type='cargo-landing-pad'}[1] "
         "local free=pad and pad.get_inventory(defines.inventory.cargo_landing_pad_main).count_empty_stacks() or 0 if free<PADFREE then local off={} for _,q in pairs(hub.get_logistic_point()) do for _,sec in pairs(q.sections) do local drop=sec.filters_count>0 for k=1,sec.filters_count do local f=sec.get_slot(k) if f and f.value and not (f.max and f.max==0) then drop=false end end "
         "if drop and sec.active then sec.active=false off[#off+1]=sec.group end end end local moved=0 for _,x in pairs(tr.get_contents()) do local got=inv.insert{name=x.name,count=x.count,quality=x.quality} if got>0 then tr.remove{name=x.name,count=got,quality=x.quality} moved=moved+got end end "
         "o[#o+1]=i..' '..p.name:gsub('%[.-%]','')..' at '..loc..' (pad free '..free..'): trash back into the hold '..moved..', drop sections off: '..table.concat(off,', ') end end").replace("PADFREE", str(PADFREE)) + END

PAD = ("local pad=game.surfaces['%s'].find_entities_filtered{type='cargo-landing-pad'}[1] local n=0 for _,pt in pairs(pad.get_logistic_point()) do if pt.mode==defines.logistic_mode.requester then pt.trash_not_requested=true n=n+1 end end "
       "local inv=pad.get_inventory(defines.inventory.cargo_landing_pad_main) rcon.print('%s pad: trash unrequested on ('..n..' point), free slots now '..inv.count_empty_stacks()..' of '..#inv)")


def main():
    a = sys.argv[1:]
    step = a[0] if a else "status"
    if step == "status":
        print(L(STATUS))
    elif step == "furnaces":
        print(L(FURNACES))
    elif step == "oxidizer":
        print(L(OXIDIZER))
    elif step == "trash":
        print(L(TRASH))
    elif step == "pad":
        print(L(PAD % (a[1], a[1])))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
