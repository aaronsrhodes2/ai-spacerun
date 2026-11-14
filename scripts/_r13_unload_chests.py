"""Round 13: at the Copper Depot unload track, unload the wagons straight into passive-provider chests (bulk inserters on the north side of y=-149 rails)
so the copper plate enters the logistic network. Slots: wagon 1 x 95.5..98.5, wagon 2 x 102.5, 105.5, 106.5. Dry run unless --apply."""
import json
import sys

from _game import tools

XS = [95.5, 96.5, 97.5, 98.5, 102.5, 105.5, 106.5]
ents = []
for x in XS:
    ents.append({"name": "passive-provider-chest", "x": x, "y": -151.5})
    ents.append({"name": "bulk-inserter", "x": x, "y": -150.5, "direction": 8})

dry = "--apply" not in sys.argv
res = json.loads(tools["place_entities"](json.dumps(ents), surface="nauvis", dry_run=dry))
print("DRY RUN" if dry else "APPLY", {k: v for k, v in res.items() if k in ("failed", "placed", "errors")})
if not dry:
    LUA = r'''
local s = game.surfaces.nauvis
local o = {}
for _, i in pairs(s.find_entities_filtered{name = 'bulk-inserter', area = {{95, -151}, {107, -150}}}) do
  o[#o + 1] = string.format('%.1f', i.position.x) .. ' pickup y=' .. string.format('%.1f', i.pickup_position.y) .. ' drop y=' .. string.format('%.1f', i.drop_position.y) .. ' dest=' .. (i.drop_target and i.drop_target.name or 'nil')
end
rcon.print(table.concat(o, '\n'))
'''
    print(tools["run_lua"](LUA))
