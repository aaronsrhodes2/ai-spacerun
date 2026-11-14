"""One-off: wait until Gleba-Aquilo 1 Shuttle reaches Aquilo orbit, then apply the ammo-reserve exit rule to its Aquilo stop (route --go --packs=300 --reserve=900)."""
import subprocess
import sys
import time

from _game import tools

LUA = ("for _,q in pairs(game.forces.player.platforms) do if q.name:find('Gleba-Aquilo',1,true) then rcon.print(tostring(q.space_location and q.space_location.name)..' '..q.state..' '..q.hub.get_inventory(defines.inventory.hub_main).get_item_count('explosive-rocket')) end end")
end = time.time() + 3000
while time.time() < end:
    out = tools["run_lua"](LUA).strip()
    print(time.strftime("%H:%M:%S"), out, flush=True)
    if out.startswith("aquilo"):
        r = subprocess.run([sys.executable, "-u", "scripts/aquilo_gleba_route.py", "route", "--go", "--packs=300", "--reserve=900"], capture_output=True, text=True)
        print(r.stdout[-400:], flush=True)
        print(tools["run_lua"](LUA).strip(), flush=True)
        break
    time.sleep(10)
