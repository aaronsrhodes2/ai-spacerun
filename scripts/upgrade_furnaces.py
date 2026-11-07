"""Replace every stone furnace of ours with a steel furnace in place (2x speed, same 2x2
size and fuel use per second). Free once advanced-material-processing is researched.
The furnace recipe follows its input, so nothing is set. Contents are lost (a few plates).
Ends with the same stuck-inserter pass as upgrade_assemblers.py."""
import json
import time

from _game import tools

ok = json.loads(tools["run_lua"]("rcon.print(helpers.table_to_json({enabled=game.forces.player.recipes['steel-furnace'].enabled}))"))
if not ok["enabled"]:
    raise SystemExit("steel-furnace isn't researched yet")
old = json.loads(tools["run_lua"](" ".join("""
local out = {}
for _, e in pairs(game.surfaces.nauvis.find_entities_filtered{force='player', name='stone-furnace'}) do
  out[#out+1] = {x=e.position.x, y=e.position.y, direction=e.direction}
end
rcon.print(helpers.table_to_json(out))
""".splitlines())))
print(len(old), "stone furnaces found")
if old:
    xs = [e["x"] for e in old]; ys = [e["y"] for e in old]
    print(tools["remove_entities"](min(xs) - 2, min(ys) - 2, max(xs) + 2, max(ys) + 2, names="stone-furnace"))
    new = [{"name": "steel-furnace", "x": e["x"], "y": e["y"], "direction": e["direction"]} for e in old]
    r = json.loads(tools["place_entities"](json.dumps(new)))
    print("placed", r["placed"], "failed", r["failed"])
    print("fuel:", tools["seed_starter_fuel"](min(xs) - 2, min(ys) - 2, max(xs) + 2, max(ys) + 2, drill_coal=1))
time.sleep(5)
print(tools["run_lua"](" ".join("""
local cleared = {}
for _, e in pairs(game.surfaces.nauvis.find_entities_filtered{force='player', type='inserter'}) do
  if e.status == defines.entity_status.waiting_for_space_in_destination and e.held_stack.valid_for_read then
    local n = e.held_stack.name
    cleared[n] = (cleared[n] or 0) + e.held_stack.count
    e.held_stack.clear()
  end
end
rcon.print(helpers.table_to_json({unstuck=cleared}))
""".splitlines())))
