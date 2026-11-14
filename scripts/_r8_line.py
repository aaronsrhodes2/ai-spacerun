"""Round 8: the y=-59.5 cable/circuit line: entities in one cell (x -320..-300, y -66..-52), their statuses, and the belt/chest contents feeding them."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local SN = {}
for k, v in pairs(defines.entity_status) do SN[v] = k end
local o = {}
for _, e in pairs(s.find_entities_filtered{area = {{-322, -62}, {-296, -50}}}) do
  if e.type ~= 'electric-pole' and e.name ~= 'substation' and e.type ~= 'tree' and e.type ~= 'transport-belt' and e.type ~= 'logistic-robot' and e.name ~= 'logistic-robot' then
    local extra = ''
    if e.type == 'transport-belt' or e.type == 'underground-belt' or e.type == 'splitter' then
      local parts = {}
      for li = 1, 2 do
        local ok, c = pcall(function() return e.get_transport_line(li).get_contents() end)
        if ok then for n, v in pairs(c) do parts[#parts + 1] = (type(v) == 'table' and (v.name .. '=' .. v.count) or (n .. '=' .. v)) end end
      end
      extra = ' [' .. table.concat(parts, ',') .. ']'
    end
    o[#o + 1] = e.name .. ' ' .. e.position.x .. ',' .. e.position.y .. ' dir=' .. tostring(e.direction) .. ' ' .. tostring(SN[e.status]) .. extra
  end
end
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
