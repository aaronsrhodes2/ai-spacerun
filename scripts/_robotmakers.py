"""Machines making logistic or construction robots (any status) per surface, with what is in their output and inputs."""
from _game import tools

LUA = r'''
local o = {}
for _, s in pairs(game.surfaces) do
  for _, e in pairs(s.find_entities_filtered{type = 'assembling-machine'}) do
    local r = e.get_recipe()
    if r and (r.name == 'logistic-robot' or r.name == 'construction-robot' or r.name == 'flying-robot-frame') then
      local out = e.get_output_inventory()
      local outn = 0
      for _, it in pairs(out.get_contents()) do outn = outn + it.count end
      o[#o + 1] = s.name .. ' ' .. r.name .. ' at ' .. e.position.x .. ',' .. e.position.y .. ' status=' .. tostring(e.status)
        .. ' out=' .. outn .. ' frames=' .. e.get_item_count('flying-robot-frame') .. ' circ=' .. e.get_item_count('electronic-circuit')
        .. ' gear=' .. e.get_item_count('iron-gear-wheel')
    end
  end
end
rcon.print(table.concat(o, '\n'))
'''

if __name__ == "__main__":
    print(tools["run_lua"](LUA))
