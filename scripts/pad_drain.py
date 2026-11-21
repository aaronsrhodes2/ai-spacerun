#!/usr/bin/env python3
"""Free the slots of a full landing pad (2026-11-20, ranker: Vulcanus pad 0 of 1,280 free, 82k magazines + 30k plates nobody asked for).
A pad is not emptied by robots: its stock only leaves when something asks for it. This moves whole stacks of items the pad does NOT request
into storage chests of the pad's own logistic network (stock stays in the network, nothing is lost or made), biggest stack count first,
until TARGET slots are free. A chest that cannot take an item gives it back to the pad.
Usage: pad_drain.py SURFACE [--target N] [--apply]     (default target 400, dry run)"""
import sys

from _game import tools

surface = sys.argv[1]
target = int(sys.argv[sys.argv.index("--target") + 1]) if "--target" in sys.argv else 400
apply = "--apply" in sys.argv

LUA = """
local s=game.surfaces['SURF'] local APPLY=APPFLAG local TARGET=TGT
local pad=s.find_entities_filtered{type='cargo-landing-pad'}[1] local inv=pad.get_inventory(defines.inventory.cargo_landing_pad_main)
local asked={} for _,pt in pairs(pad.get_logistic_point()) do for _,sc in pairs(pt.sections) do for _,f in pairs(sc.filters) do if f.value then asked[f.value.name]=true end end end end
local net=s.find_logistic_network_by_position(pad.position,'player')
local chests={} for _,c in pairs(net.storages) do if c.valid and c.type=='logistic-container' then chests[#chests+1]=c end end
table.sort(chests,function(a,b) return (a.position.x-pad.position.x)^2+(a.position.y-pad.position.y)^2 < (b.position.x-pad.position.x)^2+(b.position.y-pad.position.y)^2 end)
local list={} for _,it in pairs(inv.get_contents()) do if not asked[it.name] then local st=prototypes.item[it.name].stack_size list[#list+1]={name=it.name,quality=it.quality,count=it.count,slots=math.ceil(it.count/st)} end end
table.sort(list,function(a,b) return a.slots>b.slots end)
local free=inv.count_empty_stacks() local o={} local ci=1
for _,e in ipairs(list) do if free>=TARGET then break end local left=e.count
  while left>0 and ci<=#chests do local ch=chests[ci] local ci_inv=ch.get_inventory(defines.inventory.chest) local want=left
    if APPLY then local took=inv.remove{name=e.name,quality=e.quality,count=want} if took>0 then local put=ci_inv.insert{name=e.name,quality=e.quality,count=took} if put<took then inv.insert{name=e.name,quality=e.quality,count=took-put} ci=ci+1 end left=left-put else left=0 end
    else local room=ci_inv.get_insertable_count{name=e.name,quality=e.quality} if room>=left then left=0 else left=left-room ci=ci+1 end end
  end
  o[#o+1]=e.name..' '..(e.count-left)..'/'..e.count
  free=APPLY and inv.count_empty_stacks() or free+(e.slots)
end
rcon.print('pad free slots now '..free..' ; moved: '..table.concat(o,', '))
"""

if __name__ == "__main__":
    print(tools["run_lua"](LUA.replace("SURF", surface).replace("APPFLAG", "true" if apply else "false").replace("TGT", str(target))).strip())
