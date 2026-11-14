"""Read only: blue's coal plants against the export cell's over N seconds (coal made a minute, chemical science, rocket fuel), and
what belt K's feed carries at x 53, y -33..-14. Gleba Wheel. Usage: _wxg_q5.py [seconds]"""
import sys
import time

from _game import tools

SURF = "platform-12"
secs = int(sys.argv[1]) if len(sys.argv) > 1 else 60
READ = ("local s=game.surfaces['SURF'] local function sum(a) local n=0 for _,e in pairs(s.find_entities_filtered{type='assembling-machine',area=a}) do local r=e.get_recipe() if r and r.name=='coal-synthesis' then n=n+e.products_finished end end return n end "
        "local b={} for y=-33,-14 do local e=s.find_entities_filtered{type='transport-belt',position={53.5,y+0.5},radius=0.3}[1] if e then for l=1,2 do for _,it in pairs(e.get_transport_line(l).get_contents()) do b[it.name]=(b[it.name] or 0)+it.count end end end end local q={} for k,v in pairs(b) do q[#q+1]=k..' '..v end "
        "local f=game.forces.player.get_item_production_statistics(s) rcon.print(game.tick..'|'..sum({{46,-47},{124,-16}})..'|'..sum({{57,-13},{88,-2}})..'|'..f.get_input_count('chemical-science-pack')..'|'..f.get_input_count('rocket-fuel')..'|'..table.concat(q,', '))").replace("SURF", SURF)
a =tools["run_lua"](READ).strip().split("|")
time.sleep(secs)
b = tools["run_lua"](READ).strip().split("|")
mins = (int(b[0]) - int(a[0])) / 3600
print("game minutes %.2f; blue coal crafts a minute %.1f; cell coal crafts a minute %.1f; chemical science a minute %.1f; rocket fuel a minute %.1f"
      % (mins, (int(b[1]) - int(a[1])) / mins, (int(b[2]) - int(a[2])) / mins, (int(b[3]) - int(a[3])) / mins, (int(b[4]) - int(a[4])) / mins))
print("feed north of the taps now:", b[5])
