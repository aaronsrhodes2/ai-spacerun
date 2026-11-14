#!/usr/bin/env python3
"""Ghost demand for the Replicator (the Captain, 2026-11-14, "non-builder mode", stage 1).
In ghost mode (snapshots/build_mode.json, or place_entities(ghost=true)) machines are entity ghosts that construction robots build from items
the logistic network holds. The Replicator only reads MISSING REQUESTS of requester chests (omni_maker.py), not construction ghosts, so a ghost
whose item is out of stock waited forever (tested: 1 power switch ghost, 0 in stock, nothing made in 4+ minutes).
This script closes the gap: it sums the items every entity ghost and tile ghost on Nauvis needs, subtracts what the network holds (normal quality:
ghosts are normal, scripts/upgrade_quality.py raises them afterwards), and writes the SHORTFALL as the requests of one requester chest inside the
network; that chest's unmet request is a missing request, which the Replicator then makes. The autopilot runs `update` every few cycles.
Steps: build [--apply] | update | status | off.   Usage: ghost_demand.py update"""
import json
import sys

from _game import tools

SURF = "nauvis"
CHEST = (-195.5, -221.5)
MAXSLOTS = 40

CHEST_FIND = "local s=game.surfaces.nauvis local c=s.find_entities_filtered{name='requester-chest',position={%s,%s},radius=0.4}[1] " % CHEST


def build(apply):
    ents = [{"name": "requester-chest", "x": CHEST[0], "y": CHEST[1], "direction": 0, "params": {"quality": "epic"}}]
    r = json.loads(tools["place_entities"](json.dumps(ents), surface=SURF, dry_run=not apply, ghost=False))
    print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or []))


UPDATE = ("local s=game.surfaces.nauvis local f=game.forces.player " + CHEST_FIND +
          "if not c then rcon.print('no ghost-demand chest: run build --apply') return end "
          "local need={} local function add(ep,n) if ep and ep.items_to_place_this then for _,it in pairs(ep.items_to_place_this) do need[it.name]=(need[it.name] or 0)+it.count*n end end end "
          "for _,g in pairs(s.find_entities_filtered{type='entity-ghost',force=f}) do add(g.ghost_prototype,1) end "
          "for _,g in pairs(s.find_entities_filtered{type='tile-ghost',force=f}) do add(g.ghost_prototype,1) end "
          "local net=c.logistic_network local pt=c.get_logistic_point(defines.logistic_member_index.logistic_container) "
          "local sec=pt.sections[1] or pt.add_section() sec.filters={} local rows={} local k=0 "
          "for name,n in pairs(need) do local have=net and net.get_item_count{name=name,quality='normal'} or 0 local short=n-have if short>0 then rows[#rows+1]={name,short,n,have} end end "
          "table.sort(rows,function(a,b) return a[2]>b[2] end) for i,r in ipairs(rows) do if i<=%d then sec.set_slot(i,{value={type='item',name=r[1],quality='normal'},min=r[2]}) k=k+1 end end "
          "local t={} for i,r in ipairs(rows) do if i<=6 then t[#t+1]=r[1]..' short '..r[2]..' (need '..r[3]..', have '..r[4]..')' end end "
          "local total=0 for _,n in pairs(need) do total=total+n end rcon.print('ghost items needed '..total..' kinds '..(function() local c2=0 for _ in pairs(need) do c2=c2+1 end return c2 end)()..'; short kinds '..#rows..'; requested '..k..' | '..table.concat(t,' ; '))" % MAXSLOTS)


def update():
    print(tools["run_lua"](UPDATE))


def off():
    print(tools["run_lua"](CHEST_FIND + "if c then local pt=c.get_logistic_point(defines.logistic_member_index.logistic_container) local sec=pt.sections[1] if sec then sec.filters={} end rcon.print('requests cleared') end"))


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    if step == "build":
        build("--apply" in sys.argv)
    elif step == "off":
        off()
    else:
        update()
