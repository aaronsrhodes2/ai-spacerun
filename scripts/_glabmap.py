"""ASCII map and entity list of an area on a surface. Usage: _glabmap.py gleba x0 y0 x1 y1 [list]"""
import sys

from _game import tools

surface, x0, y0, x1, y1 = sys.argv[1], *map(int, sys.argv[2:6])
LUA = """
local s=game.surfaces['%s'] local x0,y0,x1,y1=%d,%d,%d,%d local g={} local o={} local list=%s
local sym={['lab']='L',['transport-belt']='b',['underground-belt']='u',['splitter']='S',['inserter']='i',['logistic-container']='c',['container']='c',['electric-pole']='p',['beacon']='B',['roboport']='R',['cargo-landing-pad']='P',['cargo-bay']='Y',['reactor']='H',['heat-pipe']='h',['assembling-machine']='A',['furnace']='F',['pipe']='-',['pipe-to-ground']='-',['solar-panel']='s',['accumulator']='a',['rocket-silo']='O',['agricultural-tower']='T',['plant']='t',['tree']='t',['lamp']='l',['storage-tank']='K',['pump']='-',['constant-combinator']='k',['decider-combinator']='k',['arithmetic-combinator']='k',['radar']='r',['simple-entity']='x',['cliff']='#',['entity-ghost']='g',['loader']='d',['loader-1x1']='d'}
for _,e in pairs(s.find_entities_filtered{area={{x0,y0},{x1,y1}}}) do if e.type~='logistic-robot' and e.type~='construction-robot' and e.type~='resource' and e.type~='character' and e.type~='item-entity' and e.type~='fish' then local b=e.bounding_box local ch=sym[e.type] or '?'
for x=math.floor(b.left_top.x+0.01),math.ceil(b.right_bottom.x-0.01)-1 do for y=math.floor(b.left_top.y+0.01),math.ceil(b.right_bottom.y-0.01)-1 do g[x..','..y]=ch end end
if list and (e.type=='inserter' or e.type=='logistic-container' or e.type=='container' or e.type=='splitter' or e.type=='reactor' or e.type=='beacon' or e.type=='roboport' or e.type=='loader-1x1' or ch=='?' or ch=='k') then local ex='' if e.type=='inserter' then local fs={} for k=1,e.filter_slot_count do local fl=e.get_filter(k) if fl then fs[#fs+1]=fl.name end end ex=' d'..e.direction..' ['..table.concat(fs,',')..']'..(e.inserter_filter_mode or '')..' pick '..e.pickup_position.x..','..e.pickup_position.y..' drop '..e.drop_position.x..','..e.drop_position.y end
if e.type=='logistic-container' then local rq={} for _,se in pairs(e.get_logistic_sections() and e.get_logistic_sections().sections or {}) do for _,fl in pairs(se.filters) do if fl.value then rq[#rq+1]=fl.value.name..' '..fl.min end end end ex=' req['..table.concat(rq,',')..']' end
o[#o+1]=e.name..'/'..e.quality.name:sub(1,2)..'@'..e.position.x..','..e.position.y..ex end end end
local rows={} for y=y0,y1-1 do local r={} for x=x0,x1-1 do local c=g[x..','..y] if not c then local t=s.get_tile(x,y) c=(t.collides_with('water_tile') and '~') or '.' end r[#r+1]=c end rows[#rows+1]=string.format('%%4d ',y)..table.concat(r) end
rcon.print(table.concat(rows,'|')..'|'..table.concat(o,'|'))
"""
lua = LUA % (surface, x0, y0, x1, y1, "true" if len(sys.argv) > 6 else "false")
print("x0=%d" % x0)
print(tools["run_lua"](" ".join(lua.split())).replace("|", "\n"))
