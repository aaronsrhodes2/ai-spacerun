"""Replace every assembling-machine-1 of ours with an assembling-machine-2 in place,
keeping position, direction and recipe. Free once automation-2 is researched.
Contents of the old machine are lost, which is a few intermediates at most."""
import json

from _game import tools

old = json.loads(tools["run_lua"](" ".join("""
local out = {}
for _, e in pairs(game.surfaces.nauvis.find_entities_filtered{force='player', name='assembling-machine-1'}) do
  out[#out+1] = {x=e.position.x, y=e.position.y, direction=e.direction, recipe=e.get_recipe() and e.get_recipe().name or nil}
end
rcon.print(helpers.table_to_json(out))
""".splitlines())))
print(len(old), "assembling-machine-1 found")
if old:
    xs = [e["x"] for e in old]; ys = [e["y"] for e in old]
    print(tools["remove_entities"](min(xs) - 2, min(ys) - 2, max(xs) + 2, max(ys) + 2, names="assembling-machine-1"))
    new = [{"name": "assembling-machine-2", "x": e["x"], "y": e["y"], "direction": e["direction"], **({"recipe": e["recipe"]} if e["recipe"] else {})} for e in old]
    r = json.loads(tools["place_entities"](json.dumps(new)))
    print("placed", r["placed"], "failed", r["failed"])

# Inserters that fed the old machines can keep an item in hand across the swap, and then
# wait forever for a machine that cannot take it (seen 2026-11-06: copper plates in the
# gear inserters starved four green chains). Give the new machines a moment, then clear
# any inserter still stuck holding something.
import time
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
