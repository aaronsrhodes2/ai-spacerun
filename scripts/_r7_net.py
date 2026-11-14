"""Round 7: electric network of the 6 unpowered assemblers and the substations around (-70..-36,-467): network ids, satisfaction, neighbours."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local o = {}
local m = s.find_entities_filtered{name = 'assembling-machine-3', position = {-50, -466.5}, radius = 10}
for _, e in pairs(m) do
  o[#o + 1] = 'MACH ' .. e.position.x .. ',' .. e.position.y .. ' net=' .. tostring(e.electric_network_id) .. ' energy=' .. string.format('%.0f', e.energy)
end
for _, p in pairs(s.find_entities_filtered{name = 'substation', position = {-50, -467}, radius = 60}) do
  local nb = {}
  local ok, con = pcall(function() return p.get_wire_connector(defines.wire_connector_id.pole_copper, false) end)
  if ok and con then
    for _, c in pairs(con.connections) do nb[#nb + 1] = string.format('%.0f,%.0f', c.target.owner.position.x, c.target.owner.position.y) end
  end
  o[#o + 1] = 'SUB ' .. p.position.x .. ',' .. p.position.y .. ' net=' .. tostring(p.electric_network_id) .. ' wired to: ' .. table.concat(nb, ' | ')
end
local stats = nil
local first = m[1]
if first and first.electric_network_id then
  local ok, st = pcall(function() return first.electric_network_statistics end)
  if ok and st then
    local inp = 0
    for name, v in pairs(st.input_counts) do inp = inp + 1 end
    o[#o + 1] = 'net producers: ' .. inp
  end
end
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
