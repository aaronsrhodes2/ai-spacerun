#!/usr/bin/env python3
"""Spent nuclear fuel goes home (the Captain, 2026-11-14: "all the shuttles should pick up depleted nuclear rods and take them back to
Nauvis for reprocessing"). Nauvis has the reprocessing centrifuges (secondary uranium line).

One logistic section per shuttle hub, group "depleted-return <platform index>" (the index keeps groups from being shared across hubs),
rewritten by where the shuttle is PARKED (never in flight):
  - at a PICKUP stop: request depleted-uranium-fuel-cell min(K, aboard + what the planet's network holds), import from that planet -> the
    planet's silo sends them up. Never more than is there: seven shuttles wait on all_requests_satisfied, an unfillable request would hold them.
  - at a DROP stop: min 0 max 0 -> what is aboard goes to hub trash -> trash in orbit drops to that planet's landing pad.
Routes with Nauvis: pick up at the other stop, drop at Nauvis. Routes without Nauvis (Fulgora-Aquilo, Gleba-Aquilo): pick up at Aquilo,
drop at the other stop (Fulgora / Gleba); a Nauvis shuttle then picks them up from that pad's network.
Usage: depleted_return.py status | cycle"""
import sys

from _game import tools

K = 200
ITEM = "depleted-uranium-fuel-cell"
LUA = ("local K=%d local out={} for _,p in pairs(game.forces.player.platforms) do if p.hub and p.hub.valid and p.schedule and #p.schedule.records>=2 and p.name:find('Shuttle',1,true) then "
       "local st={} local hasN=false for _,r in pairs(p.schedule.records) do st[#st+1]=r.station if r.station=='nauvis' then hasN=true end end "
       "local loc=p.space_location and p.space_location.name local mode='flight' if loc then if hasN then mode=(loc=='nauvis') and 'drop' or 'pickup' else mode=(loc=='aquilo') and 'pickup' or 'drop' end end "
       "local aboard=p.hub.get_inventory(defines.inventory.hub_main).get_item_count('%s') "
       "if mode~='flight' and %s then local pt for _,q in pairs(p.hub.get_logistic_point()) do if q.mode==defines.logistic_mode.requester then pt=q end end "
       "if pt then local g='depleted-return '..p.index local sec for _,s2 in pairs(pt.sections) do if s2.group==g then sec=s2 end end if not sec then sec=pt.add_section(g) end "
       "local have=0 if mode=='pickup' then for _,r in pairs(game.surfaces[loc].find_entities_filtered{type='roboport',force='player'}) do local nw=r.logistic_network if nw then have=math.max(have,nw.get_item_count('%s')) end end end "
       "local want=math.min(K,aboard+have) "
       "if mode=='pickup' and want>0 then sec.set_slot(1,{value={type='item',name='%s',quality='normal'},min=want,import_from=loc}) elseif mode=='pickup' then sec.clear_slot(1) else sec.set_slot(1,{value={type='item',name='%s',quality='normal'},min=0,max=0}) end end end "
       "out[#out+1]=p.name:gsub('%%[.-%%]%%s*','')..' @'..tostring(loc)..' '..mode..' aboard '..aboard end end rcon.print(table.concat(out,' ; '))")


def run(apply):
    return tools["run_lua"](LUA % (K, ITEM, "true" if apply else "false", ITEM, ITEM, ITEM)).strip()


def cycle():
    """Autopilot step. Never raises."""
    try:
        return run(True)
    except Exception as exc:  # noqa: BLE001
        return "depleted return error " + repr(exc)


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    print(run(step == "cycle"))
