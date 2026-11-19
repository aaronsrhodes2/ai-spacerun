#!/usr/bin/env python3
"""Hub-to-hub hand-over of explosive rockets at Aquilo (the Captain, 2026-11-18: "Hold for the Gleba shuttle").
Fulgora-Aquilo 5 Shuttle (platform 39) stood at Aquilo with no explosive rocket aboard, all 14 rocket turrets empty and big asteroids
closing; Fulgora, Gleba and Aquilo held none. Gleba-Aquilo 1 Shuttle (platform 38) held 5,600 at Gleba.
  send     38: providing_to_other_platforms on, and its schedule moved on to the Aquilo stop (it was waiting at Gleba for carbon fiber only)
  wait     blocks until 38 is in Aquilo orbit (prints a line a minute), then runs `give`
  give     39 asks the platforms in Aquilo orbit for what 38 holds beyond KEEP (request section `emergency-rockets 39`)
  done     removes the request, turns 38's providing off again, unpauses 39
  status   both ships
Usage: shuttle_handover.py send | wait | give | done | status"""
import sys
import time

from _game import tools

L = tools["run_lua"]
GIVER, TAKER = 38, 39
KEEP = 1300                     # 38 used 269 rockets in its last hour; it leaves Aquilo by its own rule at 1,800 or fewer
GROUP = "emergency-rockets 39"
ROCKET = "explosive-rocket"

STATUS = ("local o={} for _,i in pairs{%d,%d} do local p=game.forces.player.platforms[i] local s=p.surface local e,n=0,0 for _,t in pairs(s.find_entities_filtered{name='rocket-turret'}) do n=n+1 if t.get_inventory(defines.inventory.turret_ammo).is_empty() then e=e+1 end end "
          "local d=0 for _,x in pairs(s.find_entities_filtered{force='player'}) do if x.is_entity_with_health and x.health<x.max_health then d=d+1 end end "
          "o[#o+1]=i..' '..(p.space_location and p.space_location.name or ('flying '..string.format('%%.0f%%%%',(p.distance or 0)*100)))..' paused '..tostring(p.paused)..' rockets in hub '..p.hub.get_inventory(defines.inventory.hub_main).get_item_count('%s')..' rocket turrets empty '..e..'/'..n..' damaged '..d..' ghosts '..s.count_entities_filtered{type='entity-ghost'}..' big asteroids '..s.count_entities_filtered{type='asteroid',name={'big-oxide-asteroid','big-carbonic-asteroid','big-metallic-asteroid'}} end "
          "rcon.print(table.concat(o,' | '))") % (TAKER, GIVER, ROCKET)


def status():
    return L(STATUS).strip()


def give():
    have = int(L("rcon.print(game.forces.player.platforms[%d].hub.get_inventory(defines.inventory.hub_main).get_item_count('%s'))" % (GIVER, ROCKET)))
    n = max(0, have - KEEP)
    print("38 holds", have, "-> 39 asks for", n)
    print(L("local p=game.forces.player.platforms[%d] local pt for _,q in pairs(p.hub.get_logistic_point()) do if q.mode==defines.logistic_mode.requester then pt=q end end local sec for _,x in pairs(pt.sections) do if x.group=='%s' then sec=x end end if not sec then sec=pt.add_section('%s') end "
            "sec.set_slot(1,{value={type='item',name='%s',quality='normal',comparator='='},min=%d,max=%d,import_from='aquilo',request_from='platforms'}) local f=sec.get_slot(1) rcon.print('request set: min '..tostring(f.min)..' from '..tostring(f.request_from or '?'))" % (TAKER, GROUP, GROUP, ROCKET, n, n)))


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    if step == "send":
        print(L("local p=game.forces.player.platforms[%d] p.hub.providing_to_other_platforms=true local sc=p.schedule sc.current=2 p.schedule=sc p.paused=false rcon.print('38 provides '..tostring(p.hub.providing_to_other_platforms)..', schedule stop '..p.schedule.current..', state '..tostring(p.state))" % GIVER))
    elif step == "wait":
        while True:
            st = status()
            print(time.strftime("%H:%M"), st, flush=True)
            if (" | %d aquilo" % GIVER) in st:
                break
            time.sleep(60)
        give()
        time.sleep(45)
        print(status())
    elif step == "give":
        give()
    elif step == "done":
        print(L("local p=game.forces.player.platforms[%d] for _,q in pairs(p.hub.get_logistic_point()) do for i=#q.sections,1,-1 do if q.sections[i].group=='%s' then q.remove_section(i) end end end game.forces.player.platforms[%d].hub.providing_to_other_platforms=false p.paused=false rcon.print('request removed, 38 no longer provides, 39 running')" % (TAKER, GROUP, GIVER)))
    else:
        print(status())


if __name__ == "__main__":
    main()
