"""Round 3: rocket silos on all surfaces: status, rocket parts held, and launches recorded."""
from _game import tools

LUA = r'''
local SN = {}
for k, v in pairs(defines.entity_status) do SN[v] = k end
local o = {}
for _, s in pairs(game.surfaces) do
  for _, e in pairs(s.find_entities_filtered{type = 'rocket-silo'}) do
    local parts = e.get_inventory(defines.inventory.rocket_silo_rocket) or nil
    local held = 'n/a'
    local ok, v = pcall(function() return e.rocket_parts end)
    if ok and v then held = tostring(v) end
    o[#o + 1] = 'SILO ' .. s.name .. ' ' .. e.position.x .. ',' .. e.position.y .. ' ' .. tostring(SN[e.status]) .. ' parts=' .. held
  end
end
if #o == 0 then o[1] = 'no silos' end
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
