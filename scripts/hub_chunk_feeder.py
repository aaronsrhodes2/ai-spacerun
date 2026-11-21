#!/usr/bin/env python3
"""Hub-to-crusher feeder for stored carbonic chunks on the Gleba Wheel (2026-11-20, ranker: coal synthesis starved of carbon, hub 350 carbon, 1,305 carbonic chunks stored).
The crushers on the wheel are belt-fed from the asteroid flow, so chunks that reach the hub stay there. This turns the west hub inserter at (-4.5,-0.5) round
(it took from the dead end of the west spoke) and chains: hub -> inserter (carbonic chunk filter) -> chest (-5.5,-0.5) -> inserter -> chest (-7.5,-0.5)
-> inserter -> crusher (-10,-1.5, 2 wide, basic carbonic crushing) -> inserter (-11.5,-2.5) -> underground (-12.5,-2.5 to -4.5) under the west spoke belt, round and down onto its free north lane (the south lane is full) -> hub.
Usage: hub_chunk_feeder.py [build|status]   (build is safe to run again: it skips what is already there)"""
import sys

from _game import tools

BUILD = """
local s=game.surfaces['platform-12'] local f=game.forces.player local o={} local Q='normal'
local c0=s.find_entities_filtered{name='crusher'}[1] if c0 then Q=c0.quality.name end
local function has(n,x,y) return s.find_entities_filtered{name=n,position={x,y},radius=0.4}[1] end
local function put(n,x,y,d,q) if has(n,x,y) then o[#o+1]='have '..n..' '..x..','..y return has(n,x,y) end local e=s.create_entity{name=n,position={x,y},direction=d,force=f,quality=q,raise_built=true} o[#o+1]=(e and 'made ' or 'FAILED ')..n..' '..x..','..y return e end
local b=s.find_entities_filtered{name='express-transport-belt',position={-5.5,-0.5},radius=0.4}[1] if b then b.destroy() o[#o+1]='belt tile removed' end
local lamp=s.find_entities_filtered{name='small-lamp',position={-9.5,-1.5},radius=0.4}[1] if lamp then lamp.destroy() o[#o+1]='lamp removed' end
local hi=s.find_entities_filtered{type='inserter',position={-4.5,-0.5},radius=0.4}[1]
if hi and hi.drop_position.x<-4.6 then o[#o+1]='hub inserter already turned' elseif hi then hi.destroy() hi=nil end
if not hi then hi=put('bulk-inserter',-4.5,-0.5,4) if hi then o[#o+1]='hub inserter drop '..hi.drop_position.x end end
if hi then hi.set_filter(1,{name='carbonic-asteroid-chunk',quality='normal'}) hi.inserter_filter_mode='whitelist' hi.use_filters=true end
put('steel-chest',-5.5,-0.5,0) put('steel-chest',-7.5,-0.5,0)
local b2=put('bulk-inserter',-6.5,-0.5,4) local c2=put('bulk-inserter',-8.5,-0.5,4)
local cr=put('crusher',-10,-1.5,0,Q) if cr then cr.set_recipe('carbonic-asteroid-crushing') end
local d=put('bulk-inserter',-11.5,-2.5,4) 
local function ug(x,y,t) if not has('express-underground-belt',x,y) then local e=s.create_entity{name='express-underground-belt',position={x,y},direction=0,type=t,force=f,raise_built=true} o[#o+1]=(e and 'made ' or 'FAILED ')..'ug '..x..','..y end end ug(-12.5,-2.5,'input') ug(-12.5,-4.5,'output') put('express-transport-belt',-12.5,-5.5,4) put('express-transport-belt',-11.5,-5.5,8) put('express-transport-belt',-11.5,-4.5,8)
rcon.print(table.concat(o,' ; '))
"""
STATUS = """
local s=game.surfaces['platform-12'] local o={}
local cr=s.find_entities_filtered{name='crusher',position={-10,-1.5},radius=0.5}[1]
if cr then o[#o+1]='crusher '..cr.status..' recipe '..tostring(cr.get_recipe() and cr.get_recipe().name)..' products_finished '..cr.products_finished end
for _,p in ipairs({{-5.5,-0.5},{-7.5,-0.5}}) do local c=s.find_entities_filtered{type='container',position=p,radius=0.4}[1] if c then o[#o+1]='chest '..p[1]..' chunks '..c.get_inventory(defines.inventory.chest).get_item_count('carbonic-asteroid-chunk') end end
local h=s.platform.hub.get_inventory(defines.inventory.hub_main) o[#o+1]='hub carbon '..h.get_item_count('carbon')..' carbonic '..h.get_item_count('carbonic-asteroid-chunk')
for _,e in pairs(s.find_entities_filtered{type='inserter',area={{-13,-3},{-4,0}}}) do o[#o+1]='ins '..e.position.x..','..e.position.y..' status '..e.status end
rcon.print(table.concat(o,' ; '))
"""

if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    print(tools["run_lua"]({"build": BUILD, "status": STATUS}[step].replace("\n", " ")).replace(" ; ", "\n"))
