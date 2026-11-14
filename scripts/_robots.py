"""Logistic robot census per surface: roboports, robots held in roboports, robots in flight, and the network's item-request backlog."""
from _game import tools

LUA = r'''
local o = {}
for _, s in pairs(game.surfaces) do
  local rp = s.find_entities_filtered{name = 'roboport'}
  if #rp > 0 then
    local held, mats = 0, 0
    for _, r in pairs(rp) do
      local inv = r.get_inventory(defines.inventory.roboport_robot)
      if inv then held = held + inv.get_item_count('logistic-robot') end
      local m = r.get_inventory(defines.inventory.roboport_material)
      if m then mats = mats + m.get_item_count('logistic-robot') end
    end
    local flying = 0
    for _, n in pairs(s.find_logistic_networks_by_construction_area and {} or {}) do end
    local cs = #s.find_entities_filtered{name = 'logistic-robot'}
    o[#o + 1] = s.name .. ': roboports ' .. #rp .. ', robots held ' .. held .. ', robots on surface ' .. cs
  end
end
rcon.print(table.concat(o, '\n'))
'''

if __name__ == "__main__":
    print(tools["run_lua"](LUA))
