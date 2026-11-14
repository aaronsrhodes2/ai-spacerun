"""Which recycling recipes return steel plate or copper cable, and how much Fulgora holds of each input item (chests, hubs)."""
from _game import tools

LUA = r'''
local want = {['steel-plate'] = true, ['copper-cable'] = true}
local out = {}
for _, r in pairs(prototypes.recipe) do
  if r.category == 'recycling' then
    local hit = false
    for _, res in pairs(r.products) do if want[res.name] then hit = true end end
    if hit then
      local s = ''
      for _, res in pairs(r.products) do s = s .. res.name .. 'x' .. tostring(res.amount or res.amount_max) .. ' ' end
      out[#out + 1] = r.name .. ' -> ' .. s
    end
  end
end
rcon.print(table.concat(out, '\n'))
'''

STOCK = r'''
local s = game.surfaces.fulgora
local cnt = {}
for _, e in pairs(s.find_entities_filtered{type = {'container', 'logistic-container'}}) do
  local inv = e.get_inventory(defines.inventory.chest)
  if inv then
    for _, it in pairs(inv.get_contents()) do cnt[it.name] = (cnt[it.name] or 0) + it.count end
  end
end
local o = {}
for k, v in pairs(cnt) do o[#o + 1] = k .. '=' .. v end
rcon.print(table.concat(o, ', '))
'''

if __name__ == "__main__":
    print(tools["run_lua"](LUA))
    print("--- fulgora stock")
    print(tools["run_lua"](STOCK))
