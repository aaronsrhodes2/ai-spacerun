"""Round 4: locomotives and cargo wagons held in Nauvis storage (chests), plus the Copper Depot schedule."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local o = {}
local tot = {}
for _, c in pairs(s.find_entities_filtered{type = {'container', 'logistic-container'}}) do
  local inv = c.get_inventory(defines.inventory.chest)
  if inv then
    for _, it in pairs({'locomotive', 'cargo-wagon'}) do
      local n = inv.get_item_count(it)
      if n > 0 then
        tot[it] = (tot[it] or 0) + n
        if #o < 15 then o[#o + 1] = 'CHEST ' .. it .. ' x' .. n .. ' at ' .. c.position.x .. ',' .. c.position.y end
      end
    end
  end
end
o[#o + 1] = 'TOTAL locomotive=' .. (tot['locomotive'] or 0) .. ' cargo-wagon=' .. (tot['cargo-wagon'] or 0)
for _, t in pairs(game.train_manager.get_trains{surface = s}) do
  local sch = t.schedule
  if sch and sch.records then
    local names = {}
    for _, r in pairs(sch.records) do names[#names + 1] = tostring(r.station) end
    local s2 = table.concat(names, ' > ')
    if string.find(s2, 'Copper Depot') then
      o[#o + 1] = 'COPPER TRAIN carriages=' .. #t.carriages .. ' sched=' .. s2 .. ' current=' .. tostring(sch.current)
      local f = t.front_stock
      o[#o + 1] = '  front ' .. f.name .. ' dir=' .. tostring(t.speed) .. ' rail=' .. (f.position.x .. ',' .. f.position.y)
    end
  end
end
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
