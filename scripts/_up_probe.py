import json, sys
from _game import tools

LUA = """
local s = game.surfaces.gleba
local out = {}
for _, e in pairs(s.find_entities_filtered{force='player', name='transport-belt', area={{118,19},{135,50}}}) do
  out[#out+1] = {e.position.x, e.position.y, e.direction, e.get_transport_line(1).get_item_count()+e.get_transport_line(2).get_item_count()}
end
local rows = {}
for _, e in pairs(s.find_entities_filtered{force='player', name='transport-belt', area={{55,-1},{135,19}}}) do
  local k = e.position.y
  rows[k] = (rows[k] or 0) + 1
end
out.rows = rows
local lab = {}
for _, e in pairs(s.find_entities_filtered{force='player', type='lab'}) do
  local n = tostring(e.status); lab[n]=(lab[n] or 0)+1
end
out.labs = lab
rcon.print(helpers.table_to_json(out))
"""
print(tools["run_lua"](" ".join(LUA.splitlines())))
