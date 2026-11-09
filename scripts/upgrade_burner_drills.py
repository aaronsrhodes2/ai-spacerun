"""
Replace the three rows of burner mining drills with electric drills dropping on the same belts.

Rows (all face south onto a belt just below): copper y=-87 (x -72..-56), iron y=-105 (x -32..-12), stone y=-51 (x 12..22).
Per row: remove the burner drills and the burner inserters that fuelled them, lay electric drills at pitch 4 (one free tile between for a medium pole),
accept a drill only if its drop tile holds a belt and its 5x5 mining area holds only the row's ore; restore the burner row if nothing could be placed.
Usage: scripts/upgrade_burner_drills.py [--build]
"""
import json
import sys

from _game import tools

ROWS = [
    # name, ore, old drill centre y, electric centre y, inserter tile y, x0 of first drill, count
    ("copper", "copper-ore", -87.0, -87.5, -89, -72, 4),
    ("iron", "iron-ore", -105.0, -105.5, -107, -32, 5),
    ("stone", "stone", -51.0, -51.5, -53, 12, 3),
]

LUA = """
local s=game.surfaces.nauvis
local out={}
local function ores(area) local set={} for _,r in pairs(s.find_entities_filtered{area=area,type='resource'}) do set[r.name]=true end local l={} for n,_ in pairs(set) do l[#l+1]=n end table.sort(l) return table.concat(l,'+') end
local rows=ROWS_JSON
for _,row in ipairs(rows) do
  local name,ore,oy,ey,iy,x0,count=row[1],row[2],row[3],row[4],row[5],row[6],row[7]
  local saved_d,saved_i={}, {}
  local xmax=x0+count*4
  for _,d in pairs(s.find_entities_filtered{name='burner-mining-drill',area={{x0-1,oy-1.2},{xmax+1,oy+1.2}}}) do saved_d[#saved_d+1]={d.position,d.direction} d.destroy() end
  for _,i in pairs(s.find_entities_filtered{name='burner-inserter',area={{x0-1,iy-0.2},{xmax+1,iy+1.2}}}) do if math.floor(i.position.y)==iy then saved_i[#saved_i+1]={i.position,i.direction} i.destroy() end end
  for _,g in pairs(s.find_entities_filtered{area={{x0-1,ey-2.5},{xmax+1,ey+2.5}},name='item-on-ground'}) do g.destroy() end
  local placed,skipped=0,0
  for k=0,count-1 do
    local cx=x0+4*k+1.5
    local ok=false
    if s.can_place_entity{name='electric-mining-drill',position={cx,ey},direction=defines.direction.south,force='player'} then
      local e=s.create_entity{name='electric-mining-drill',position={cx,ey},direction=defines.direction.south,force='player'}
      if e then
        local dx,dy=math.floor(e.drop_position.x),math.floor(e.drop_position.y)
        local belt=s.find_entities_filtered{position={dx+0.5,dy+0.5},type={'transport-belt','underground-belt','splitter'}}[1]
        local same=(ores({{cx-2.5,ey-2.5},{cx+2.5,ey+2.5}})==ore)
        if belt and same then ok=true placed=placed+1 else e.destroy() end
      end
    end
    if not ok then skipped=skipped+1 end
  end
  if placed>0 then
    for k=0,count-1 do local px=x0+4*k+3.5 s.create_entity{name='medium-electric-pole',position={px,ey},force='player'} end
  else
    for _,d in pairs(saved_d) do s.create_entity{name='burner-mining-drill',position=d[1],direction=d[2],force='player'} end
    for _,i in pairs(saved_i) do s.create_entity{name='burner-inserter',position=i[1],direction=i[2],force='player'} end
  end
  out[#out+1]=name..': removed '..#saved_d..' burner drills and '..#saved_i..' burner inserters; electric placed '..placed..', skipped '..skipped..(placed==0 and ' (burners restored)' or '')
end
rcon.print(helpers.table_to_json(out))
"""


def main():
    build = "--build" in sys.argv
    if not build:
        print("dry run: rows", ROWS)
        return
    print(tools["save_game"]("before-burner-drills"))
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    rows = json.dumps([list(r) for r in ROWS if not only or r[0] in only]).replace("[", "{").replace("]", "}")
    code = LUA.replace("ROWS_JSON", rows)
    print(tools["run_lua"](" ".join(code.splitlines()))[:2500])
    print(tools["run_lua"](" ".join("""
local s=game.surfaces.nauvis
local main=s.find_entity('medium-electric-pole',{97.5,-60.5}).electric_network_id
local res={}
for _,e in pairs(s.find_entities_filtered{name='electric-mining-drill',force='player',area={{-80,-112},{30,-45}}}) do
  if e.electric_network_id~=main then res[#res+1]=math.floor(e.position.x)..','..math.floor(e.position.y)..' net='..tostring(e.electric_network_id) end end
rcon.print('drills not on the main grid: '..#res..' '..table.concat(res,' '))""".splitlines())))


if __name__ == "__main__":
    main()
