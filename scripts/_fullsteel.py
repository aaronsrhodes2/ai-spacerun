"""Where do the full-output steel furnaces sit, and what does their output inserter drop into (and is that full)?"""
from _game import tools

LUA = r'''
local E = defines.entity_status
local o = {}
for _, s in pairs(game.surfaces) do
  local n, full, starve, dropfull, dropnames = 0, 0, 0, 0, {}
  for _, f in pairs(s.find_entities_filtered{type = 'furnace'}) do
    local ok, prev = pcall(function() return f.previous_recipe end)
    local r = f.get_recipe and f.get_recipe() or (prev and prev.name)
    local rn = (type(r) == 'table' and r.name) or r
    if rn == 'steel-plate' then
      n = n + 1
      if f.status == E.full_output then full = full + 1 end
      if f.status == E.no_ingredients then starve = starve + 1 end
      local ins = s.find_entities_filtered{type = 'inserter', area = {{f.position.x - 1.5, f.position.y - 1.5}, {f.position.x + 1.5, f.position.y + 1.5}}}
      for _, i in pairs(ins) do
        if i.drop_target and i.pickup_target and i.pickup_target.unit_number == f.unit_number then
          local d = i.drop_target
          local key = d.name
          dropnames[key] = (dropnames[key] or 0) + 1
          if d.get_inventory and d.get_inventory(defines.inventory.chest) then
            local inv = d.get_inventory(defines.inventory.chest)
            if inv.is_full() then dropfull = dropfull + 1 end
          end
        end
      end
    end
  end
  if n > 0 then
    local dn = {}
    for k, v in pairs(dropnames) do dn[#dn + 1] = k .. '=' .. v end
    o[#o + 1] = s.name .. ': steel furnaces ' .. n .. ', full ' .. full .. ', starved ' .. starve .. ', drop chest full ' .. dropfull .. ' | ' .. table.concat(dn, ', ')
  end
end
rcon.print(table.concat(o, '\n'))
'''

if __name__ == "__main__":
    print(tools["run_lua"](LUA))
