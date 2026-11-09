import sys,json
sys.path.insert(0,"scripts")
from _game import tools
X1,Y1,X2,Y2=[int(a) for a in sys.argv[1:5]]
SURF=sys.argv[5] if len(sys.argv)>5 else 'nauvis'
lua=" ".join(f"""
local s=game.surfaces['{SURF}']
local X1,Y1,X2,Y2={X1},{Y1},{X2},{Y2}
local grid={{}}
for y=Y1,Y2 do grid[y]={{}} for x=X1,X2 do grid[y][x]='.' end end
local arrows={{[0]='^',[4]='>',[8]='v',[12]='<'}}
local ins={{[0]='n',[4]='e',[8]='s',[12]='w'}}
local function mark(e,ch)
  local pos=e.position
  local cb=e.prototype.collision_box
  local w=math.max(1,math.floor((cb.right_bottom.x-cb.left_top.x)+0.5)) local h=math.max(1,math.floor((cb.right_bottom.y-cb.left_top.y)+0.5))
  if e.type=='splitter' and (e.direction==0 or e.direction==8) then w,h=2,1 elseif e.type=='splitter' then w,h=1,2 end
  local x0=math.floor(pos.x-w/2+0.5) local y0=math.floor(pos.y-h/2+0.5)
  for dx=0,w-1 do for dy=0,h-1 do local gx,gy=x0+dx,y0+dy if grid[gy] and grid[gy][gx] then grid[gy][gx]=ch end end end
end
for _,e in pairs(s.find_entities_filtered{{area={{{{X1,Y1}},{{X2+1,Y2+1}}}},force='player'}}) do
  local t=e.type
  if t=='furnace' then mark(e,'F')
  elseif t=='inserter' then
    local ch=ins[e.direction] if e.name:find('long') then ch=string.upper(ch) end
    if e.name=='burner-inserter' then ch='b' end
    mark(e,ch)
  elseif t=='transport-belt' then mark(e,arrows[e.direction])
  elseif t=='underground-belt' then mark(e,'U')
  elseif t=='splitter' then mark(e,'S')
  elseif t=='electric-pole' then mark(e,'P')
  elseif t=='container' then mark(e,'C')
  elseif t=='mining-drill' then mark(e,'D')
  elseif t=='assembling-machine' then mark(e,'A')
  elseif t=='pipe' or t=='pipe-to-ground' then mark(e,'=')
  elseif t=='straight-rail' or t=='curved-rail-a' or t=='curved-rail-b' then mark(e,'R')
  else mark(e,'?') end
end
local rows={{}}
for y=Y1,Y2 do local r={{}} for x=X1,X2 do r[#r+1]=grid[y][x] end rows[#rows+1]=string.format('%5d ',y)..table.concat(r) end
rcon.print(helpers.table_to_json(rows))
""".splitlines())
rows=json.loads(tools["run_lua"](lua))
print("x from",X1)
for r in rows: print(r)
