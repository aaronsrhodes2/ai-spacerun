"""Round 13: wait until the Copper Depot train (id 666) is waiting at the unload stop, then dump the unload inserters' status, targets and what is in the wagons/destination belts."""
import time

from _game import tools

WAIT = r'''
local t = game.train_manager.get_train_by_id(666)
if not t then rcon.print('NOTRAIN') return end
local p = t.front_stock.position
rcon.print(tostring(t.state) .. ' ' .. string.format('%.0f,%.0f', p.x, p.y))
'''

DUMP = r'''
local s = game.surfaces.nauvis
local SN = {}
for k, v in pairs(defines.entity_status) do SN[v] = k end
local t = game.train_manager.get_train_by_id(666)
local o = {}
for i, c in pairs(t.carriages) do
  if c.type == 'cargo-wagon' then
    local parts = {}
    for _, it in pairs(c.get_inventory(defines.inventory.cargo_wagon).get_contents()) do parts[#parts + 1] = it.name .. 'x' .. it.count end
    o[#o + 1] = 'wagon ' .. i .. ' at ' .. string.format('%.1f,%.1f', c.position.x, c.position.y) .. ' ' .. table.concat(parts, ',')
  end
end
local st = s.find_entities_filtered{type = 'train-stop', position = {87, -151}, radius = 3}[1]
o[#o + 1] = 'stop ' .. st.backer_name .. ' at ' .. st.position.x .. ',' .. st.position.y .. ' dir=' .. st.direction
for _, i in pairs(s.find_entities_filtered{name = 'bulk-inserter', position = st.position, radius = 20}) do
  local pk, dr = i.pickup_target, i.drop_target
  o[#o + 1] = 'INS ' .. string.format('%.1f,%.1f', i.position.x, i.position.y) .. ' ' .. tostring(SN[i.status]) .. ' pick=' .. (pk and pk.name or 'nil') .. ' drop=' .. (dr and dr.name or 'nil')
end
rcon.print(table.concat(o, '\n'))
'''

for _ in range(40):
    r = tools["run_lua"](WAIT)
    print(r, flush=True)
    if r.startswith('6 ') and r.split()[1].startswith('90,'):
        print(tools["run_lua"](DUMP))
        break
    time.sleep(2)
