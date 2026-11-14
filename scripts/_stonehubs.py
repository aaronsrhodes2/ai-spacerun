from _game import tools
LUA = r'''
local o = {}
for i, p in pairs(game.forces.player.platforms) do
  if p.hub then
    local inv = p.hub.get_inventory(defines.inventory.hub_main)
    local st = inv and inv.get_item_count('stone') or 0
    local free = inv and (inv.count_empty_stacks and inv.count_empty_stacks() or -1) or -1
    if st > 0 then o[#o+1] = i .. ' ' .. p.name .. ' stone=' .. st end
  end
end
rcon.print(table.concat(o, '\n'))
'''
print(tools["run_lua"](LUA))
