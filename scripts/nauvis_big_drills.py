#!/usr/bin/env python3
"""Nauvis clean-up, stage 2: replace electric mining drills with big mining drills.
For each electric drill (uranium skipped: it needs acid piping) try a big drill that drops on the same belt tile, facing the same way
(centre = drop tile - 3 tiles). Its 5x5 footprint may only cover electric drills and electric poles, both of which are removed; planned big
drills never overlap. Electric drills left over are removed only if a planned big drill's 13x13 mining area covers them, otherwise kept.
Afterwards anything in the area without power gets a substation or medium pole nearby.
Big drills are created directly, so the script first checks that the big-mining-drill recipe is researched.
Usage: nauvis_big_drills.py X0 Y0 X1 Y1 [--apply]      (area to work on)"""
import sys

from _game import tools

LUA = """
local f=game.forces.player local s=game.surfaces.nauvis local apply=APPLY local area={{X0,Y0},{X1,Y1}} local o={}
if not f.recipes['big-mining-drill'].enabled then rcon.print('big mining drill not researched') return end
local DV={[0]={0,-1},[4]={1,0},[8]={0,1},[12]={-1,0}}
local drills={} for _,d in pairs(s.find_entities_filtered{force=f,name='electric-mining-drill',area=area}) do
 local res=s.find_entities_filtered{type='resource',position=d.position,radius=2.5}[1]
 if not (res and res.prototype.mineable_properties.required_fluid) then drills[#drills+1]=d end end
table.sort(drills,function(a,b) if a.direction~=b.direction then return a.direction<b.direction end if a.position.y~=b.position.y then return a.position.y<b.position.y end return a.position.x<b.position.x end)
local plan={} local consumed={} local polekill={}
for _,d in pairs(drills) do if not consumed[d.unit_number] then local v=DV[d.direction] local dp=d.drop_position local tx,ty=math.floor(dp.x)+0.5,math.floor(dp.y)+0.5
 local cx,cy=tx-3*v[1],ty-3*v[2] local ok=true
 for _,p in pairs(plan) do if math.abs(p.x-cx)<5 and math.abs(p.y-cy)<5 then ok=false break end end
 local eat={} local poles={}
 if ok then for _,e in pairs(s.find_entities_filtered{area={{cx-2.4,cy-2.4},{cx+2.4,cy+2.4}}}) do
   if e.name=='electric-mining-drill' and e.force==f then eat[#eat+1]=e elseif e.type=='electric-pole' and e.force==f then poles[#poles+1]=e
   elseif e.type~='resource' and e.type~='corpse' and e.type~='fish' and e.type~='item-entity' and e.type~='logistic-robot' and e.type~='construction-robot' and e.type~='character' then ok=false break end end end
 if ok then for dx=-2,2 do for dy=-2,2 do if s.get_tile(cx+dx,cy+dy).collides_with('water_tile') then ok=false end end end end
 if ok then local rn=0 for _,r in pairs(s.find_entities_filtered{type='resource',area={{cx-6.4,cy-6.4},{cx+6.4,cy+6.4}}}) do if not r.prototype.mineable_properties.required_fluid then rn=rn+1 end end if rn==0 then ok=false end end
 if ok then plan[#plan+1]={x=cx,y=cy,dir=d.direction} for _,e in pairs(eat) do consumed[e.unit_number]=e end for _,e in pairs(poles) do polekill[e.unit_number]=e end end end end
local redundant={} local kept=0
for _,d in pairs(drills) do if not consumed[d.unit_number] then local cov=false for _,p in pairs(plan) do if math.abs(p.x-d.position.x)<=6 and math.abs(p.y-d.position.y)<=6 then cov=true break end end if cov then redundant[#redundant+1]=d else kept=kept+1 end end end
local nc=0 for _ in pairs(consumed) do nc=nc+1 end local np=0 for _ in pairs(polekill) do np=np+1 end
o[#o+1]=(apply and 'APPLIED' or 'DRY RUN')..': electric drills '..#drills..' -> big drills '..#plan..'; replaced '..nc..', removed as covered '..#redundant..', kept '..kept..'; poles in the way '..np
if apply then
 local net=s.find_logistic_network_by_position({-40,42},f)
 local function gone(e) if e.valid then local inv=e.type=='mining-drill' and e.get_module_inventory() if inv and net then for _,it in pairs(inv.get_contents()) do net.insert({name=it.name,count=it.count,quality=it.quality}) end end e.destroy() end end
 for _,e in pairs(consumed) do gone(e) end for _,e in pairs(redundant) do gone(e) end for _,e in pairs(polekill) do gone(e) end
 local made,fail=0,0 for _,p in pairs(plan) do local e=s.create_entity{name='big-mining-drill',position={p.x,p.y},direction=p.dir,force=f,raise_built=true} if e then made=made+1 else fail=fail+1 end end
 local fixed,still=0,0
 for pass=1,3 do still=0 for _,e in pairs(s.find_entities_filtered{force=f,type={'mining-drill','inserter','furnace','assembling-machine','roboport','beacon'},area=area}) do
   if e.prototype.electric_energy_source_prototype and not e.is_connected_to_electric_network() then still=still+1
    local pos=s.find_non_colliding_position('substation',e.position,7,1,true) if pos then local sub=s.create_entity{name='substation',position=pos,force=f,raise_built=true} if sub then fixed=fixed+1 end end end end if still==0 then break end end
 o[#o+1]='big drills placed '..made..' failed '..fail..' | substations added '..fixed..' | still unpowered after that '..still
end
rcon.print(table.concat(o,'\\n'))
"""


def main():
    x0, y0, x1, y1 = sys.argv[1:5]
    lua = LUA.replace("\n", " ").replace("APPLY", "true" if "--apply" in sys.argv else "false")
    lua = lua.replace("{{X0,Y0},{X1,Y1}}", "{{%s,%s},{%s,%s}}" % (x0, y0, x1, y1))
    print(tools["run_lua"](lua))


if __name__ == "__main__":
    main()
