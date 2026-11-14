from _game import tools
LUA = r'''
local s = game.surfaces.nauvis
local o = {}
local n = 0
for _, e in pairs(s.find_entities_filtered{type = 'furnace'}) do
  n = n + 1
  if n <= 6 then
    local ok, r = pcall(function() return e.previous_recipe end)
    o[#o + 1] = e.position.x .. ',' .. e.position.y .. ' ok=' .. tostring(ok) .. ' type=' .. type(r) .. ' val=' .. tostring(type(r) == 'table' and r.name or r) .. ' status=' .. tostring(e.status) .. ' has_recipe=' .. tostring(e.get_recipe ~= nil)
  end
end
rcon.print('furnaces ' .. n .. '\n' .. table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
