"""Survey steel, copper cable and foundation stock in the chests and machines of each planet surface."""
from _game import tools

LUA = r'''
local o = {}
for _, sn in pairs({'nauvis', 'fulgora', 'vulcanus', 'gleba'}) do
  local s = game.surfaces[sn]
  local st, cu, f, n = 0, 0, 0, 0
  for _, e in pairs(s.find_entities_filtered{type = {'container', 'logistic-container'}}) do
    n = n + 1
    local inv = e.get_inventory(defines.inventory.chest)
    if inv then
      st = st + inv.get_item_count('steel-plate')
      cu = cu + inv.get_item_count('copper-cable')
      f = f + inv.get_item_count('space-platform-foundation')
    end
  end
  local m = {}
  for _, e in pairs(s.find_entities_filtered{name = {'assembling-machine-3', 'electric-furnace', 'stone-furnace', 'steel-furnace'}}) do
    local r = e.get_recipe()
    local k = e.name .. ':' .. (r and r.name or 'none')
    m[k] = (m[k] or 0) + 1
  end
  local mm = {}
  for k, v in pairs(m) do mm[#mm + 1] = k .. '=' .. v end
  o[#o + 1] = sn .. ' chests=' .. n .. ' steel=' .. st .. ' cable=' .. cu .. ' foundation=' .. f .. ' | ' .. table.concat(mm, ', ')
end
rcon.print(table.concat(o, '\n'))
'''

if __name__ == "__main__":
    print(tools["run_lua"](LUA))
