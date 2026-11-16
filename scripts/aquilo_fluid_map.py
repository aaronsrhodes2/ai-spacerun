#!/usr/bin/env python3
"""Aquilo fluid map (2026-11-15): which pipes and machine ports share a fluid network. Factorio 2.1 gives no fluidbox access from Lua, so the
networks are rebuilt from geometry: pipes join on all four sides, pipe-to-ground on its normal side (entity direction) and by the underground
pair in line (the other end faces back), machine ports from the prototype's pipe_connections (positions[] is per entity direction N,E,S,W).
Fluids are read from pipes (get_fluid_contents) and from machine ports (get_fluid(index)); an empty pipe shows '-'.
Usage: aquilo_fluid_map.py [x0 y0 x1 y1] [tiles]      ('tiles' also lists each network's pipe tiles; default: the Aquilo base, x -60..60, y -60..10). Pumps and tanks are not traced (reported if present)."""
import sys

from _game import tools

L = tools["run_lua"]

LUA = r'''
local s=game.surfaces.aquilo local AREA={{%s,%s},{%s,%s}}
local V={[0]={0,-1},[4]={1,0},[8]={0,1},[12]={-1,0}} local DI={[0]=1,[4]=2,[8]=3,[12]=4}
local par={} local function find(a) while par[a]~=a do par[a]=par[par[a]] a=par[a] end return a end
local function un(a,b) if not par[a] then par[a]=a end if not par[b] then par[b]=b end par[find(a)]=find(b) end
local function K(x,y) return math.floor(x)..','..math.floor(y) end
local function step(k,d,n) local x,y=k:match('(-?%%d+),(-?%%d+)') return (tonumber(x)+V[d][1]*(n or 1))..','..(tonumber(y)+V[d][2]*(n or 1)) end
local pip={} local fl={} local npipes={}
for _,e in pairs(s.find_entities_filtered{area=AREA,force='player',type={'pipe','pipe-to-ground'}}) do local k=K(e.position.x,e.position.y) pip[k]={kind=(e.type=='pipe') and 'pipe' or 'ptg',d=e.direction} local n=next(e.get_fluid_contents()) par[k]=k if n then fl[k]=n end end
local other=0 for _,e in pairs(s.find_entities_filtered{area=AREA,force='player',type={'storage-tank','pump'}}) do other=other+1 end
for k,p in pairs(pip) do for _,d in ipairs({0,4,8,12}) do if p.kind=='pipe' or p.d==d then local nk=step(k,d) local q=pip[nk] if q and (q.kind=='pipe' or q.d==(d+8)%%16) then un(k,nk) end end end
  if p.kind=='ptg' then local u=(p.d+8)%%16 for n=1,16 do local nk=step(k,u,n) local q=pip[nk] if q and q.kind=='ptg' and q.d==u then un(k,nk) break end end end end
local ports={} local lab={} local mfl={}
for _,e in pairs(s.find_entities_filtered{area=AREA,force='player',type='assembling-machine'}) do local pro=prototypes.entity[e.name] local r=e.get_recipe()
  for fbi,b in ipairs(pro.fluidbox_prototypes) do for _,c in ipairs(b.pipe_connections) do local pos=c.positions[DI[e.direction]] if pos then
    local ik=K(e.position.x+pos.x,e.position.y+pos.y) local cd=(c.direction+e.direction)%%16 local node='m'..e.unit_number..'#'..fbi
    ports[ik]={node=node,cd=cd,tgt=step(ik,cd)} par[node]=node lab[node]=(r and r.name or e.name)..'@'..e.position.x..','..e.position.y..'#'..fbi..(b.production_type=='input' and 'in' or 'out')
    local ok,f=pcall(function() return e.get_fluid(fbi) end) if ok and f then mfl[node]=f.name end end end end end
for ik,p in pairs(ports) do local q=pip[p.tgt] if q and (q.kind=='pipe' or q.d==(p.cd+8)%%16) then un(p.node,p.tgt) else local o=ports[p.tgt] if o and o.cd==(p.cd+8)%%16 then un(p.node,o.node) end end end
local comps={} for a,_ in pairs(par) do local r=find(a) local c=comps[r] if not c then c={pipes=0,fl={},ports={},keys={},minx=1e9} comps[r]=c end
  if lab[a] then c.ports[#c.ports+1]=lab[a] if mfl[a] then c.fl[mfl[a]]=true end else c.pipes=c.pipes+1 c.keys[#c.keys+1]=a if fl[a] then c.fl[fl[a]]=true end local x=tonumber(a:match('(-?%%d+),')) if x and x<c.minx then c.minx=x end end end
local list={} for _,c in pairs(comps) do if #c.ports>0 then list[#list+1]=c end end table.sort(list,function(a,b) return a.minx<b.minx end)
local out={} for _,c in ipairs(list) do local f={} for n,_ in pairs(c.fl) do f[#f+1]=n end table.sort(c.ports) out[#out+1]='NET pipes='..c.pipes..' fluid='..(#f>0 and table.concat(f,'/') or '-')..' :: '..table.concat(c.ports,' ; ') if %s and c.pipes>0 then table.sort(c.keys) out[#out+1]='  tiles: '..table.concat(c.keys,' ') end end
rcon.print('pumps/tanks in area (not traced): '..other..'\n'..table.concat(out,'\n'))
'''


def main():
    args = [x for x in sys.argv[1:] if x != "tiles"]
    a = args[:4] if len(args) >= 4 else ["-60", "-60", "60", "10"]
    code = " ".join((LUA % tuple(a + ["true" if "tiles" in sys.argv else "false"])).split("\n"))
    print(L(code))


if __name__ == "__main__":
    main()
