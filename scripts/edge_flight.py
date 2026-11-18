#!/usr/bin/env python3
"""Watch Edgerunner in flight (the Captain, 2026-11-18: "carefully moving the edge runner between the inner planets").
One line per sample: where it is, speed, propellant, hull count and damage, empty turrets, asteroids in sight, ammunition on the belts.
Stops when the ship arrives, or after MAX samples. It only reads; flying is  edge_flight.py go PLANET  (one-stop schedule, unpaused)
and  edge_flight.py hold  (pause where it is).
Usage: edge_flight.py watch [seconds] [max] | go PLANET | hold | targets | once"""
import sys
import time

from _game import tools

L = tools["run_lua"]
IDX = 37
SAMPLE = ("local p=game.forces.player.platforms[%d] local s=p.surface local fl={} for _,t in pairs(s.find_entities_filtered{type='storage-tank'}) do for k,v in pairs(t.get_fluid_contents()) do fl[k]=(fl[k] or 0)+v end end "
          "local n,dmg,worst=0,0,1 for _,e in pairs(s.find_entities_filtered{force='player'}) do n=n+1 if e.health and e.max_health and e.max_health>0 and e.health<e.max_health then dmg=dmg+1 local r=e.health/e.max_health if r<worst then worst=r end end end "
          "local empty={} for _,t in pairs(s.find_entities_filtered{type='ammo-turret'}) do if t.get_inventory(defines.inventory.turret_ammo).is_empty() then empty[t.name]=(empty[t.name] or 0)+1 end end "
          "local em={} for k,v in pairs(empty) do em[#em+1]=k..' '..v end "
          "local ast={} for _,a in pairs(s.find_entities_filtered{type='asteroid'}) do local k=a.name:match('^(%%a+)') ast[k]=(ast[k] or 0)+1 end local as={} for k,v in pairs(ast) do as[#as+1]=k..' '..v end "
          "local am={} for _,b in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt','splitter'}}) do for i=1,b.get_max_transport_line_index() do for _,it in pairs(b.get_transport_line(i).get_contents()) do "
          "if it.name:find('magazine') or it.name:find('rocket') or it.name:find('railgun') then am[it.name]=(am[it.name] or 0)+it.count end end end end local ams={} for k,v in pairs(am) do ams[#ams+1]=k..' '..v end "
          "local ghosts=s.count_entities_filtered{type='entity-ghost'}+s.count_entities_filtered{type='tile-ghost'} "
          "local c=p.space_connection local where=p.space_location and ('at '..p.space_location.name) or (c and string.format('%%s %%.0f/%%d km',c.name,p.distance*c.length,c.length) or '?') "
          "rcon.print(string.format('%%s | %%.1f km/s | fuel %%.0f ox %%.0f | hull %%d dmg %%d worst %%.0f%%%% ghosts %%d | empty: %%s | asteroids: %%s | belts: %%s',where,p.speed*60,fl['thruster-fuel'] or 0,fl['thruster-oxidizer'] or 0,n,dmg,worst*100,ghosts,"
          "#em>0 and table.concat(em,', ') or 'none',#as>0 and table.concat(as,', ') or 'none',table.concat(ams,', ')))") % IDX
GO = ("local p=game.forces.player.platforms[%d] p.schedule={current=1,records={{station='PLANET',wait_conditions={{type='time',ticks=216000}}}}} p.paused=false rcon.print('bound for PLANET, state '..p.state)") % IDX
# Who shoots what (first flight, 2026-11-18). A railgun shot goes through everything on its line, our own belts included: railguns fire only at
# huge asteroids. Rocket turrets out-range the guns and shot every medium asteroid first, 30 times faster than the works makes rockets:
# they fire only at big and huge. Guns take the small and medium ones.
TARGETS = ("local s=game.forces.player.platforms[%d].surface local function set(name,sizes) local n=0 for _,t in pairs(s.find_entities_filtered{name=name}) do local i=0 "
           "for _,z in pairs(sizes) do for _,k in pairs({'metallic','carbonic','oxide'}) do i=i+1 t.set_priority_target(i,z..'-'..k..'-asteroid') end end t.ignore_unprioritised_targets=true n=n+1 end return n end "
           "rcon.print('railguns (huge only) '..set('railgun-turret',{'huge'})..', rocket turrets (big and huge) '..set('rocket-turret',{'big','huge'}))") % IDX
HOLD = "local p=game.forces.player.platforms[%d] p.paused=true rcon.print('paused, '..(p.space_location and p.space_location.name or 'in transit'))" % IDX

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "once"
    if cmd == "go":
        print(L(GO.replace("PLANET", sys.argv[2])))
    elif cmd == "targets":
        print(L(TARGETS))
    elif cmd == "hold":
        print(L(HOLD))
    elif cmd == "once":
        print(L(SAMPLE))
    else:
        every = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        most = int(sys.argv[3]) if len(sys.argv) > 3 else 50
        left = False
        for _ in range(most):
            try:
                line = L(SAMPLE).strip()
            except Exception as e:                                        # one bad read must not end the watch
                line = "read failed: %s" % e
            print(time.strftime("%H:%M:%S"), line, flush=True)
            if not line.startswith("at "):
                left = True
            elif left:
                break
            time.sleep(every)
