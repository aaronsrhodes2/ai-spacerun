"""Scratch (read-only): belt K split into its feed (hub -> blue block) and its loop, and blue's chemistry machines."""
import sys

from _game import tools
import wheel_blue

SURF = sys.argv[1] if len(sys.argv) > 1 else "platform-12"
wheel_blue.layout()
K = wheel_blue.lines["K"]
cut = K.index((55, -31)) + 1
COUNT = ("local s=game.surfaces['SURF'] local b={} local n=0 for _,p in pairs(TILES) do local e=s.find_entities_filtered{type={'transport-belt','underground-belt'},position={p[1]+0.5,p[2]+0.5},radius=0.3}[1] if e then n=n+1 for l=1,2 do for _,it in pairs(e.get_transport_line(l).get_contents()) do local k=it.name..' lane'..l b[k]=(b[k] or 0)+it.count end end end end "
         "local q={} for k,v in pairs(b) do q[#q+1]=k..' '..v end table.sort(q) rcon.print('NAME '..n..' tiles: '..table.concat(q,', '))")
for name, tiles in (("feed", K[:cut]), ("loop", K[cut:])):
    print(tools["run_lua"](COUNT.replace("SURF", SURF).replace("NAME", name).replace("TILES", "{" + ",".join("{%d,%d}" % t for t in tiles) + "}")))
print(tools["run_lua"](("local s=game.surfaces['SURF'] local w={} for _,e in pairs(s.find_entities_filtered{type={'assembling-machine','furnace'},area={{46,-47},{124,-16}}}) do local k='?' for n,v in pairs(defines.entity_status) do if v==e.status then k=n end end local rc=e.get_recipe() "
                        "local key=(rc and rc.name or e.name)..' '..k w[key]=(w[key] or 0)+1 end local q={} for k,v in pairs(w) do q[#q+1]=k..' x'..v end table.sort(q) rcon.print(table.concat(q,'@@'))").replace("SURF", SURF)).replace("@@", "\n"))
