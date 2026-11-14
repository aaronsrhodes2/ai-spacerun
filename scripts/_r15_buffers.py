"""Buffer chests on Nauvis: how many, where (50-tile areas), and the ones near the uranium / Kovarex centrifuge block (-345..-315, -110..-80): requests, contents, mode."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local o = {}
local g = {}
local near = {}
for _, c in pairs(s.find_entities_filtered{name = 'buffer-chest'}) do
  local k = math.floor(c.position.x / 50) * 50 .. ',' .. math.floor(c.position.y / 50) * 50
  g[k] = (g[k] or 0) + 1
  if c.position.x > -350 and c.position.x < -310 and c.position.y > -115 and c.position.y < -75 then near[#near + 1] = c end
end
local keys = {}
for k, v in pairs(g) do keys[#keys + 1] = v .. ' @' .. k end
table.sort(keys)
o[#o + 1] = 'buffer chests by 50-tile area: ' .. table.concat(keys, ' | ')
o[#o + 1] = 'near the centrifuge block: ' .. #near
for i, c in ipairs(near) do
  if i <= 24 then
    local inv = c.get_inventory(defines.inventory.chest)
    local cont = {}
    for _, it in pairs(inv.get_contents()) do cont[#cont + 1] = it.name .. 'x' .. it.count end
    local req = {}
    local pt = c.get_logistic_point(defines.logistic_member_index.logistic_container)
    if pt then
      for _, sec in pairs(pt.sections) do for _, f in pairs(sec.filters) do req[#req + 1] = tostring(f.value and f.value.name or f.name) .. '>=' .. tostring(f.min) end end
      o[#o + 1] = 'BUF ' .. c.position.x .. ',' .. c.position.y .. ' mode=' .. tostring(pt.mode) .. ' requests[' .. table.concat(req, ',') .. '] has[' .. table.concat(cont, ',') .. '] slots=' .. #inv
    end
  end
end
local cents = s.find_entities_filtered{type = {'assembling-machine'}, area = {{-350, -115}, {-310, -75}}}
local cn = {}
for _, e in pairs(cents) do local r = e.get_recipe() local nm = r and r.name or 'none' cn[nm] = (cn[nm] or 0) + 1 end
local ks = {}
for k, v in pairs(cn) do ks[#ks + 1] = v .. 'x ' .. k end
o[#o + 1] = 'machines in that block: ' .. table.concat(ks, ', ')
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
