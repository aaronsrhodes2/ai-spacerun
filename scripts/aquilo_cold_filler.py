#!/usr/bin/env python3
"""Aquilo: barrel COLD fluoroketone off stack 1's cooler (the Captain, 2026-11-20: "Finish the filler"; started by another session, see
the skill's "Aquilo cold-fluoroketone filler" note). Foundation needs cold fluoroketone and Aquilo is where it is made.

The cooler at (-13.5,-44.5) faces south; its cold port meets the pipe at tile (-16,-42). The idle science plant south of it was removed.
  pipe (-15,-42) joins that pipe to the filler's one fluid input (top middle)
  filler: assembling machine 3 on tiles x -16..-14, y -41..-39, recipe fluoroketone-cold-barrel, facing north
  in:  the requester chest already at (-18,-41) asks for 20 empty barrels; inserter (-17,-41)
  out: inserter (-17,-39) (it replaces one heat pipe; the heat runs on round it) into the provider chest already at (-18,-39),
       switched off by wire while that chest holds CAP barrels, so the filler cannot drain the cryo loop
  heat: heat pipes (-14,-42), (-13,-42) and x -13 down to row -39, joined to the row at y -38: every new piece has one within a tile
Steps: plan | build [--apply] | status      Usage: aquilo_cold_filler.py build --apply ; aquilo_cold_filler.py status"""
import json
import sys

from _game import tools

L = tools["run_lua"]
CAP = 600


def c(tx, ty, w=1):
    return tx + w / 2, ty + w / 2


def ents():
    e = [{"name": "pipe", "x": -14.5, "y": -41.5}]
    for tx, ty in ((-14, -42), (-13, -42), (-13, -41), (-13, -40), (-13, -39)):
        e.append({"name": "heat-pipe", "x": tx + 0.5, "y": ty + 0.5})
    e.append({"name": "assembling-machine-3", "x": -14.5, "y": -39.5, "direction": 0, "recipe": "fluoroketone-cold-barrel"})
    e.append({"name": "bulk-inserter", "x": -16.5, "y": -40.5, "direction": 12})      # direction = pick-up side
    e.append({"name": "bulk-inserter", "x": -16.5, "y": -38.5, "direction": 4})
    return e


PRE = "local s=game.surfaces.aquilo local h=s.find_entities_filtered{name='heat-pipe',position={-16.5,-38.5},radius=0.3}[1] if h then h.destroy() rcon.print('heat pipe at (-17,-39) removed') else rcon.print('no heat pipe at (-17,-39)') end"
CONFIG = ("local s=game.surfaces.aquilo local W=defines.wire_connector_id local rq=s.find_entities_filtered{name='requester-chest',position={-17.5,-40.5},radius=0.3}[1] local out=s.find_entities_filtered{name='passive-provider-chest',position={-17.5,-38.5},radius=0.3}[1] "
          "local ins=s.find_entities_filtered{type='inserter',position={-16.5,-38.5},radius=0.3}[1] local o={} if rq then local pt=rq.get_logistic_point(defines.logistic_member_index.logistic_container) for k=#pt.sections,1,-1 do pt.remove_section(k) end "
          "pt.add_section().set_slot(1,{value={type='item',name='barrel',quality='normal'},min=20}) o[#o+1]='in chest asks 20 barrels' end "
          "if out and ins then ins.get_wire_connector(W.circuit_red,true).connect_to(out.get_wire_connector(W.circuit_red,true),false,defines.wire_origin.script) local cb=ins.get_or_create_control_behavior() cb.circuit_enable_disable=true "
          "cb.circuit_condition={first_signal={type='item',name='fluoroketone-cold-barrel'},comparator='<',constant=%d} o[#o+1]='out inserter stops at %d barrels' end rcon.print(table.concat(o,'; '))" % (CAP, CAP))
STATUS = ("local s=game.surfaces.aquilo local f=game.forces.player local m={} for k,v in pairs(defines.entity_status) do m[v]=k end local o={} local a=s.find_entities_filtered{name='assembling-machine-3',position={-14.5,-39.5},radius=0.5}[1] "
          "if a then local fl='' for i=1,a.fluids_count do local x=a.get_fluid(i) if x then fl=fl..x.name..' '..math.floor(x.amount) end end o[#o+1]='filler '..tostring(m[a.status])..(a.frozen and ' FROZEN' or '')..' made '..a.products_finished..' fluid ['..fl..']' else o[#o+1]='no filler' end "
          "for _,e in pairs(s.find_entities_filtered{area={{-19,-43},{-12,-37}}}) do if e.frozen then o[#o+1]='FROZEN '..e.name..'@'..e.position.x..','..e.position.y end end "
          "local cl=s.find_entities_filtered{name='cryogenic-plant',position={-13.5,-44.5},radius=1}[1] o[#o+1]='cooler '..tostring(cl and m[cl.status]) local t={} for _,it in pairs{'fluoroketone-cold-barrel','fluoroketone-hot-barrel','barrel'} do local n=0 "
          "for _,nw in pairs(f.logistic_networks.aquilo or {}) do n=n+nw.get_item_count(it) end t[#t+1]=it..' '..n end o[#o+1]='network: '..table.concat(t,', ') rcon.print(table.concat(o,string.char(10)))")


def main():
    a = sys.argv[1:]
    step = a[0] if a else "plan"
    apply = "--apply" in a
    if step in ("plan", "build"):
        go = apply and step == "build"
        if go:
            print(tools["save_game"]("pre-aquilo-filler-finish"))
            print("   " + L(PRE).strip())
        r = tools["place_entities"](json.dumps(ents()), surface="aquilo", dry_run=not go)
        print(str(r)[:500])
        if go:
            print("   " + L(CONFIG).strip())
    elif step == "status":
        print(L(STATUS))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
