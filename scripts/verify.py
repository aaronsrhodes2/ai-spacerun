"""
Build verifier: reads a box of the map and reports broken links, so nobody finds them by eye.

    inserter_no_pickup / inserter_no_drop   an inserter with nothing to take from / put into
    unpowered                               a powered machine not on any electric network, or status no_power
    belt_dead_end                           a belt whose end leads nowhere and that no inserter picks from
    machine_state                           counts of status per machine type (information)

Usage: scripts/verify.py x1 y1 x2 y2        (defaults to the blue science block)
Exit code 1 when any hard problem is found.
"""
import json
import sys

from _game import tools

LUA = """
local s=game.surfaces.nauvis
local box={{%(x1)s,%(y1)s},{%(x2)s,%(y2)s}}
local st={}
for k,v in pairs(defines.entity_status) do st[v]=k end
local out={inserter_no_pickup={},inserter_no_drop={},unpowered={},belt_dead_end={},machine_state={}}
local picked={}
local function add(list,e,extra) if #out[list]<40 then out[list][#out[list]+1]=e.name..' '..e.position.x..','..e.position.y..(extra or '') end end
for _,e in pairs(s.find_entities_filtered{area=box,type={'inserter'}}) do
  local p=e.pickup_target if p then picked[p.unit_number or 0]=true end
  if not p then add('inserter_no_pickup',e) end
  if not e.drop_target then add('inserter_no_drop',e) end
end
local powered={'inserter','assembling-machine','furnace','lab','mining-drill','radar','roboport','pump','offshore-pump','chemical-plant','oil-refinery'}
for _,e in pairs(s.find_entities_filtered{area=box,type={'inserter','assembling-machine','furnace','lab','mining-drill','chemical-plant','oil-refinery'}}) do
  local status=st[e.status] or 'nil'
  if e.electric_network_id==nil and e.prototype.electric_energy_source_prototype~=nil then add('unpowered',e,' (no network)')
  elseif status=='no_power' then add('unpowered',e,' (no_power)') end
  if e.type~='inserter' then
    local key=e.name..':'..status
    out.machine_state[key]=(out.machine_state[key] or 0)+1
  end
end
for _,b in pairs(s.find_entities_filtered{area=box,type='transport-belt'}) do
  local o=b.belt_neighbours.outputs
  if #o==0 then
    local used=false
    local d=b.direction
    local dirs={[0]={0,-1},[4]={1,0},[8]={0,1},[12]={-1,0}} local v=dirs[d]
    local ahead=s.find_entities_filtered{position={b.position.x+v[1],b.position.y+v[2]}}
    for _,a in pairs(ahead) do if a.type~='transport-belt' and a.type~='inserter' and a.type~='straight-rail' then used=true end end
    for _,i in pairs(s.find_entities_filtered{position=b.position,radius=2,type='inserter'}) do
      if i.pickup_target==b or i.drop_target==b then used=true end
    end
    if not used then add('belt_dead_end',b) end
  end
end
rcon.print(helpers.table_to_json(out))
"""


def verify(x1, y1, x2, y2):
    raw = tools["run_lua"](" ".join((LUA % dict(x1=x1, y1=y1, x2=x2, y2=y2)).splitlines()))
    try:
        return json.loads(raw)
    except ValueError:
        raise SystemExit(f"verifier Lua failed: {raw[:600]}")


def main():
    box = [float(a) for a in sys.argv[1:5]] if len(sys.argv) >= 5 else [-362, -80, -204, -50]
    r = verify(*box)
    hard = 0
    for k in ("inserter_no_pickup", "inserter_no_drop", "unpowered", "belt_dead_end"):
        items = r.get(k) or []
        if isinstance(items, dict):
            items = []
        print(f"{k}: {len(items)}")
        for i in items[:15]:
            print("   ", i)
        if k != "belt_dead_end":
            hard += len(items)
    print("machine_state:", json.dumps(r.get("machine_state"), indent=0)[:1500])
    sys.exit(1 if hard else 0)


if __name__ == "__main__":
    main()
