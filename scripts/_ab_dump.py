import sys
from _game import tools
x1,y1,x2,y2=[float(a) for a in sys.argv[1:5]]
lua="""local s=game.surfaces.nauvis local g={} 
for _,e in pairs(s.find_entities_filtered{area={{X1,Y1},{X2,Y2}},type={'transport-belt','underground-belt','splitter'}}) do
 local c={[0]='^',[4]='>',[8]='v',[12]='<'}
 local ch=c[e.direction] or '?'
 if e.type=='underground-belt' then ch=(e.belt_to_ground_type=='input') and 'U' or 'O' end
 if e.type=='splitter' then ch='S' end
 g[#g+1]=string.format('%d,%d,%s',math.floor(e.position.x),math.floor(e.position.y),ch) end
rcon.print(table.concat(g,';'))"""
lua=lua.replace("X1",str(x1)).replace("Y1",str(y1)).replace("X2",str(x2)).replace("Y2",str(y2))
r=tools["run_lua"](lua)
m={}
for t in r.split(';'):
    p=t.split(',')
    if len(p)==3: m[(int(p[0]),int(p[1]))]=p[2]
for y in range(int(y1//1),int(y2//1)+1):
    print('%5d '%y+''.join(m.get((x,y),'.') for x in range(int(x1//1),int(x2//1)+1)))
print('x from',int(x1//1))
