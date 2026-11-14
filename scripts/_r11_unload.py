"""Round 11: the Copper Depot Unload stop (87,-151): status of the inserters that touch its rails, where they drop, and how full those destinations are."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local SN = {}
for k, v in pairs(defines.entity_status) do SN[v] = k end
local st = s.find_entities_filtered{type = 'train-stop', position = {87, -151}, radius = 3}[1]
local o = {}
local rails = s.find_entities_filtered{type = {'straight-rail', 'curved-rail-a', 'curved-rail-b'}, position = st.position, radius = 22}
local cnt, dests = {}, {}
for _, i in pairs(s.find_entities_filtered{name = 'bulk-inserter', position = st.position, radius = 24}) do
  local touches = false
  for _, r in ipairs(rails) do
    if math.abs(r.position.x - i.drop_position.x) <= 1.6 and math.abs(r.position.y - i.drop_position.y) <= 1.6 then touches = true end
    if math.abs(r.position.x - i.pickup_position.x) <= 1.6 and math.abs(r.position.y - i.pickup_position.y) <= 1.6 then touches = true end
  end
  if touches then
    local k = tostring(SN[i.status])
    cnt[k] = (cnt[k] or 0) + 1
    local d = i.drop_target
    local dn = d and d.name or 'wagon/none'
    if d and (d.type == 'container' or d.type == 'logistic-container') then
      local inv = d.get_inventory(defines.inventory.chest)
      dn = dn .. ' free_slots=' .. inv.count_empty_stacks() .. '/' .. #inv
    elseif d and d.type == 'transport-belt' then
      dn = dn .. ' belt'
    end
    dests[dn] = (dests[dn] or 0) + 1
  end
end
for k, v in pairs(cnt) do o[#o + 1] = 'STATUS ' .. k .. ' ' .. v end
for k, v in pairs(dests) do o[#o + 1] = 'DEST ' .. v .. 'x ' .. k end
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
