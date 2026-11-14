"""Sample the Gleba labs every 20 s: working count, labs lacking each pack, research and progress, pad stock of the five packs in use.
Usage: _labwatch.py [samples=5]"""
import sys
import time

from _game import tools

LUA = """
local f=game.forces.player local g=game.surfaces.gleba local labs=g.find_entities_filtered{type='lab',force=f} local w=0 local miss={} local r=f.current_research
for _,l in pairs(labs) do if l.status==defines.entity_status.working then w=w+1 end if r then local inv=l.get_inventory(defines.inventory.lab_input) for _,i in pairs(r.research_unit_ingredients) do if inv.get_item_count(i.name)==0 then local k=i.name:sub(1,4) miss[k]=(miss[k] or 0)+1 end end end end
local m={} for k,v in pairs(miss) do m[#m+1]=k..'='..v end local pad=g.find_entities_filtered{type='cargo-landing-pad'}[1] local t={}
for _,n in pairs({'automation','logistic','chemical','production'}) do t[#t+1]=n:sub(1,4)..' '..pad.get_item_count(n..'-science-pack') end
local ch=0 for _,c in pairs(g.find_entities_filtered{name='requester-chest',area={{121,23},{134,41}}}) do ch=ch+c.get_item_count('production-science-pack') end
rcon.print('tick '..game.tick..' working '..w..'/'..#labs..' lacking ['..table.concat(m,' ')..'] '..(r and r.name or 'none')..' '..string.format('%.4f',f.research_progress)..' pad '..table.concat(t,', ')..' lab chests prod '..ch..' agri chest '..g.find_entities_filtered{position={128.5,20.5},type='logistic-container'}[1].get_item_count('agricultural-science-pack'))
"""
lua = " ".join(LUA.split())
n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
for k in range(n):
    print(tools["run_lua"](lua).strip(), flush=True)
    if k < n - 1:
        time.sleep(20)
