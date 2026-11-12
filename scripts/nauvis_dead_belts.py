#!/usr/bin/env python3
"""Nauvis clean-up, stage 1: remove belt networks that nothing touches.
A network is every belt, underground belt (both ends paired) and splitter joined by belt flow. It is "touched" when an inserter picks from or drops
onto any piece of it, or a mining drill drops onto it. Untouched networks cannot feed or be fed by anything, so they are dead.
Also removed: networks that nothing drops onto (only inserters taking from them) and that are already empty: they can never hold an item again.
NOT removed: networks that are merely empty and idle right now, and networks nothing takes from (removing those would make their feeders spill).
Items lying on removed belts go into the logistic network's storage; what does not fit is reported, and those belts are left in place.
Usage: nauvis_dead_belts.py [--apply] [--surface nauvis]"""
import sys

from _game import tools

LUA = """
local f=game.forces.player local s=game.surfaces['SURFACE'] local apply=APPLY local o={}
local belts=s.find_entities_filtered{force=f,type={'transport-belt','underground-belt','splitter'}}
local comp={} local members={} local ncomp=0
local function nb(b) local t={} for _,dir in pairs{'inputs','outputs'} do for _,n in pairs(b.belt_neighbours[dir]) do t[#t+1]=n end end
 if b.type=='underground-belt' then local u=b.underground_belt_neighbour if u then t[#t+1]=u end end return t end
for _,b in pairs(belts) do if not comp[b.unit_number] then ncomp=ncomp+1 local q={b} comp[b.unit_number]=ncomp local h=1 while h<=#q do local c=q[h] h=h+1
 for _,n in pairs(nb(c)) do if n.valid and not comp[n.unit_number] then comp[n.unit_number]=ncomp q[#q+1]=n end end end members[ncomp]=q end end
local served={} local fed={}
local function touch(pos,feeds) for _,x in pairs(s.find_entities_filtered{position=pos,type={'transport-belt','underground-belt','splitter'}}) do if comp[x.unit_number] then served[comp[x.unit_number]]=true if feeds then fed[comp[x.unit_number]]=true end end end end
for _,e in pairs(s.find_entities_filtered{force=f,type={'inserter','mining-drill','loader','loader-1x1'}}) do
 if e.type=='inserter' then touch(e.pickup_position,false) touch(e.drop_position,true) elseif e.type=='mining-drill' then touch(e.drop_position,true) else served[comp[e.unit_number] or 0]=true fed[comp[e.unit_number] or 0]=true end end
local net=s.find_logistic_network_by_position({-40,42},f)
local nets,pieces,items,moved,kept=0,0,0,0,0 local big={}
for c=1,ncomp do local q=members[c] local pre=0 if not fed[c] then for _,b in pairs(q) do for l=1,b.get_max_transport_line_index() do pre=pre+#b.get_transport_line(l) end end end if not served[c] or (not fed[c] and pre==0) then local it=0 local x0,x1,y0,y1=1e9,-1e9,1e9,-1e9
 for _,b in pairs(q) do for l=1,b.get_max_transport_line_index() do it=it+#b.get_transport_line(l) end x0=math.min(x0,b.position.x) x1=math.max(x1,b.position.x) y0=math.min(y0,b.position.y) y1=math.max(y1,b.position.y) end
 nets=nets+1 pieces=pieces+#q items=items+it big[#big+1]={#q,it,x0,y0,x1,y1}
 if apply then for _,b in pairs(q) do if b.valid then local ok=true for l=1,b.get_max_transport_line_index() do local line=b.get_transport_line(l)
   for _,st in pairs(line.get_contents()) do local d=net and net.insert({name=st.name,count=st.count,quality=st.quality}) or 0 if d>0 then line.remove_item({name=st.name,count=d,quality=st.quality}) moved=moved+d end if d<st.count then ok=false end end end
  if ok then b.destroy() else kept=kept+1 end end end end end end
table.sort(big,function(a,b) return a[1]>b[1] end)
o[#o+1]=(apply and 'REMOVED' or 'DRY RUN')..': belt networks '..ncomp..', untouched '..nets..' with '..pieces..' pieces holding '..items..' items'..(apply and (' | items moved to storage '..moved..', pieces kept because storage was full '..kept) or '')
for i=1,math.min(12,#big) do local b=big[i] o[#o+1]=string.format(' %d pieces, %d items, x %.0f..%.0f y %.0f..%.0f',b[1],b[2],b[3],b[5],b[4],b[6]) end
rcon.print(table.concat(o,'\\n'))
"""


def main():
    surface = sys.argv[sys.argv.index("--surface") + 1] if "--surface" in sys.argv else "nauvis"
    apply = "--apply" in sys.argv
    print(tools["run_lua"](LUA.replace("\n", " ").replace("SURFACE", surface).replace("APPLY", "true" if apply else "false")))


if __name__ == "__main__":
    main()
