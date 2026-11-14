"""Survey foundation makers (all surfaces) and platform hub stock of the foundation item."""
from _game import tools

MAKERS = r'''
local out = {}
for _, s in pairs(game.surfaces) do
  for _, e in pairs(s.find_entities_filtered{type = 'assembling-machine'}) do
    local r = e.get_recipe()
    if r and r.name == 'space-platform-foundation' then
      local o = e.get_output_inventory()
      out[#out + 1] = s.name .. ' ' .. e.position.x .. ',' .. e.position.y .. ' ' .. e.name
        .. ' status=' .. tostring(e.status) .. ' steel=' .. e.get_item_count('steel-plate')
        .. ' cable=' .. e.get_item_count('copper-cable') .. ' out=' .. o.get_item_count('space-platform-foundation')
    end
  end
end
rcon.print(table.concat(out, '\n'))
'''

HUBS = r'''
local o = {}
for _, p in pairs(game.forces.player.platforms) do
  if p.hub then
    local inv = p.hub.get_inventory(defines.inventory.hub_main)
    o[#o + 1] = p.name .. ' f=' .. inv.get_item_count('space-platform-foundation') .. ' steel=' .. inv.get_item_count('steel-plate')
      .. ' cable=' .. inv.get_item_count('copper-cable') .. ' at=' .. tostring(p.space_location and p.space_location.name)
  end
end
rcon.print(table.concat(o, '\n'))
'''

if __name__ == "__main__":
    print(tools["run_lua"](MAKERS))
    print(tools["run_lua"](HUBS))
