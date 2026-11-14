"""Round 4: straight rail tiles near the Copper Depot Load stop (165,-295): position, direction, and whether a train is on them."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local o = {}
local stop = s.find_entities_filtered{name = 'train-stop', position = {165, -295}, radius = 3}[1]
if stop then o[#o + 1] = 'STOP ' .. stop.backer_name .. ' at ' .. stop.position.x .. ',' .. stop.position.y .. ' dir=' .. stop.direction end
for _, r in pairs(s.find_entities_filtered{type = {'straight-rail'}, position = {165, -295}, radius = 14}) do
  o[#o + 1] = 'RAIL ' .. r.position.x .. ',' .. r.position.y .. ' dir=' .. r.direction .. ' train=' .. (r.train and 'yes' or 'no')
end
for _, t in pairs(game.train_manager.get_trains{surface = s}) do
  local f = t.front_stock.position
  if math.abs(f.x - 165) < 16 and math.abs(f.y + 295) < 16 then o[#o + 1] = 'TRAIN near stop at ' .. f.x .. ',' .. f.y .. ' speed=' .. t.speed end
end
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
