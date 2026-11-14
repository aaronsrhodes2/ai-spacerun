"""Round 8: robot cells at x -146.5 (status, inputs, outputs), advanced-circuit and flying-robot-frame stock in chests, and total logistic robots on Nauvis."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local SN = {}
for k, v in pairs(defines.entity_status) do SN[v] = k end
local o = {}
for _, e in pairs(s.find_entities_filtered{type = 'assembling-machine', area = {{-150, -212}, {-143, -197}}}) do
  local r = e.get_recipe()
  if r and r.name == 'logistic-robot' then
    o[#o + 1] = 'CELL ' .. e.position.y .. ' ' .. tostring(SN[e.status]) .. ' adv=' .. e.get_item_count('advanced-circuit') .. ' frames=' .. e.get_item_count('flying-robot-frame') .. ' bots_out=' .. e.get_item_count('logistic-robot')
  end
end
local adv, frames, bots = 0, 0, 0
for _, c in pairs(s.find_entities_filtered{type = {'container', 'logistic-container'}}) do
  local inv = c.get_inventory(defines.inventory.chest)
  if inv then
    adv = adv + inv.get_item_count('advanced-circuit')
    frames = frames + inv.get_item_count('flying-robot-frame')
    bots = bots + inv.get_item_count('logistic-robot')
  end
end
o[#o + 1] = 'chests: advanced-circuit ' .. adv .. ', frames ' .. frames .. ', robots in chests ' .. bots
local total, charging = 0, 0
for _, r in pairs(s.find_entities_filtered{name = 'logistic-robot'}) do total = total + 1 end
o[#o + 1] = 'logistic robots flying on nauvis: ' .. total
local nets = 0
for _, n in pairs(s.find_logistic_networks_by_construction_area({-150, -205}, game.forces.player)) do
  nets = nets + 1
  o[#o + 1] = 'NET robots=' .. n.all_logistic_robots .. ' available=' .. n.available_logistic_robots .. ' cells=' .. #n.cells
end
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
