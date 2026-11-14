#!/usr/bin/env python3
"""Stone for the wheels' Ring (military and production science): the one thing asteroids cannot give, so each wheel asks its own planet
for it by rocket (the Captain: stone may be shipped up). The Gleba and Nauvis wheels already had a section `stone 2000/4000`; the
Fulgora and Vulcanus wheels had none and their Rings stood still. `apply` adds a section in group 'wheel-stone <platform index>'
(idempotent: an existing one is rewritten); a wheel that already asks for stone in another section is left alone.
Usage: wheel_stone.py status | apply  [--only PLANET]"""
import sys

from _game import tools
from _wheels import wheels

WANT = {"fulgora": (1000, 2000), "vulcanus": (1000, 2000)}
LUA = ("local s=game.surfaces['SURF'] local p=s.platform local pt for _,q in pairs(p.hub.get_logistic_point()) do if q.mode==defines.logistic_mode.requester then pt=q end end local g='wheel-stone '..p.index local has,mine=nil,nil "
       "for i,sec in pairs(pt.sections) do if sec.group==g then mine=i else for _,fl in pairs(sec.filters) do if fl.value and fl.value.name=='stone' then has=(fl.min or 0)..'/'..tostring(fl.max) end end end end "
       "if APPLY and not has then if mine then pt.remove_section(mine) end local sec=pt.add_section(g) sec.set_slot(1,{value={type='item',name='stone',quality='normal'},min=MIN,max=MAX,import_from='PLANET'}) mine=true end "
       "local inv=p.hub.get_inventory(defines.inventory.hub_main) rcon.print('stone in hub '..inv.get_item_count('stone')..', other section asks '..tostring(has)..', wheel-stone section '..tostring(mine~=nil))")
for name, planet, surface, turrets in wheels():
    lo, hi = WANT.get(planet, (0, 0))
    apply = "apply" in sys.argv[1:2] and planet in WANT
    print("==", name, tools["run_lua"](LUA.replace("SURF", surface).replace("APPLY", "true" if apply else "false").replace("MIN", str(lo)).replace("MAX", str(hi)).replace("PLANET", planet)).strip())
