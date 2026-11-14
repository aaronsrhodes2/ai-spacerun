"""Ingredients and craft time of the logistic-robot and construction-robot recipes."""
from _game import tools

LUA = r'''
local o = {}
for _, n in pairs({'logistic-robot', 'construction-robot', 'flying-robot-frame'}) do
  local r = prototypes.recipe[n]
  local ing = {}
  for _, i in pairs(r.ingredients) do ing[#ing + 1] = i.name .. 'x' .. i.amount end
  o[#o + 1] = n .. ' (' .. tostring(r.energy) .. 's): ' .. table.concat(ing, ', ')
end
rcon.print(table.concat(o, '\n'))
'''

if __name__ == "__main__":
    print(tools["run_lua"](LUA))
