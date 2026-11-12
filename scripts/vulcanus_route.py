#!/usr/bin/env python3
"""Vulcanus: land route for the tungsten belt, from the mine to the inside of the demolisher crossing.
Breadth-first search on a 2-tile grid: no lava, no rocks or cliffs, CLEAR tiles from the patrol paths of territories 5 and 1.
Prints the belt entity list as JSON to the file given, or places it.  Usage: vulcanus_route.py OUT.json"""
import json
import sys

from _game import tools

import os
START = tuple(int(v) for v in os.environ.get('ROUTE_START', '-376,-150').split(','))   # default: just south of the ore
GOAL = tuple(int(v) for v in os.environ.get('ROUTE_GOAL', '-258,-70').split(','))     # default: inside the T5 loop, 13 tiles west of the path
CLEAR = int(sys.argv[2]) if len(sys.argv) > 2 else 10
EXPAND = int(sys.argv[3]) if len(sys.argv) > 3 else 1   # tiles of margin around rocks, cliffs and ore

LUA = """
local s=game.surfaces.vulcanus local terr=s.get_territories() local paths={terr[5].get_patrol_path(),terr[1].get_patrol_path()}
local X0,X1,Y0,Y1,G=-700,-100,-300,120,2
local function dseg(px,py,a,b) local vx,vy=b.x-a.x,b.y-a.y local wx,wy=px-a.x,py-a.y local c=vx*vx+vy*vy local tt=c>0 and math.max(0,math.min(1,(wx*vx+wy*vy)/c)) or 0 local dx,dy=px-(a.x+tt*vx),py-(a.y+tt*vy) return math.sqrt(dx*dx+dy*dy) end
local function near(px,py) local m=1e9 for _,pp in pairs(paths) do for k=1,#pp do local a,b=pp[k],pp[k%%#pp+1] if math.abs(a.x-px)<80 or math.abs(b.x-px)<80 then local d=dseg(px,py,a,b) if d<m then m=d end end end end return m end
local W=math.floor((X1-X0)/G) local H=math.floor((Y1-Y0)/G) local pass={}
local blocked={} for _,e in pairs(s.find_entities_filtered{area={{X0,Y0},{X1,Y1}},type={'cliff','simple-entity'}}) do for dx=-EXP,EXP do for dy=-EXP,EXP do blocked[math.floor((e.position.x+dx-X0)/G)..','..math.floor((e.position.y+dy-Y0)/G)]=true end end end
for i=0,W do for j=0,H do local x,y=X0+i*G,Y0+j*G local ok=not blocked[i..','..j] if ok then for dx=-1,2 do for dy=-1,2 do if s.get_tile(x+dx,y+dy).name:find('lava') then ok=false end end end end if ok and near(x+1,y+1)<%d then ok=false end pass[i..','..j]=ok end end
local si,sj=math.floor((%d-X0)/G),math.floor((%d-Y0)/G) local gi,gj=math.floor((%d-X0)/G),math.floor((%d-Y0)/G)
local prev={} local q={{si,sj}} prev[si..','..sj]='s' local h=1 local found=false
while h<=#q do local c=q[h] h=h+1 if c[1]==gi and c[2]==gj then found=true break end for _,n in pairs{{1,0},{-1,0},{0,1},{0,-1}} do local a,b=c[1]+n[1],c[2]+n[2] local k=a..','..b if a>=0 and a<=W and b>=0 and b<=H and prev[k]==nil and pass[k] then prev[k]=c q[#q+1]={a,b} end end end
if not found then rcon.print('{"error":"no route","start":'..tostring(pass[si..','..sj])..',"goal":'..tostring(pass[gi..','..gj])..'}') else local out={} local c={gi,gj} while c~='s' do out[#out+1]={X0+c[1]*G,Y0+c[2]*G} c=prev[c[1]..','..c[2]] end rcon.print(helpers.table_to_json(out)) end
""".replace("\n", " ").replace("EXP", str(EXPAND)) % (CLEAR, START[0], START[1], GOAL[0], GOAL[1])


def belts(cells):
    """cells run goal -> start; reverse, then two belt tiles per step pointing along the step."""
    cells = cells[::-1]
    out = []
    for (x, y), (nx, ny) in zip(cells, cells[1:]):
        dx, dy = (nx - x) // 2, (ny - y) // 2
        d = {(1, 0): 4, (-1, 0): 12, (0, 1): 8, (0, -1): 0}[(dx, dy)]
        out.append({"name": "express-transport-belt", "x": x + 0.5, "y": y + 0.5, "direction": d})
        out.append({"name": "express-transport-belt", "x": x + dx + 0.5, "y": y + dy + 0.5, "direction": d})
    return out, cells


def main():
    raw = tools["run_lua"](LUA)
    if not raw.startswith(("[", "{")):
        print("lua said:", raw[:400])
        return
    res = json.loads(raw)
    if isinstance(res, dict):
        print(res)
        return
    b, cells = belts(res)
    turns = sum(1 for i in range(1, len(b)) if b[i]["direction"] != b[i - 1]["direction"])
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    print("cells", len(cells), "belt tiles", len(b), "turns", turns, "x", min(xs), max(xs), "y", min(ys), max(ys), "first", cells[0], "last", cells[-1])
    json.dump(b, open(sys.argv[1], "w"))


if __name__ == "__main__":
    main()
