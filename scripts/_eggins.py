from _game import tools
LUA = r'''
local o = {}
local s = game.surfaces['gleba']
for _, e in pairs(s.find_entities_filtered{type='inserter', area={{55,12},{135,22}}}) do
  local f1 = e.use_filters and e.get_filter(1) or nil
  if f1 == 'pentapod-egg' or (e.pickup_target and e.pickup_target.name=='transport-belt' and e.position.y>16 and e.position.y<19) then
    local cb = e.get_control_behavior and e.get_control_behavior()
    local cond = ''
    if cb and cb.circuit_condition then cond = ' cond=' .. tostring(cb.circuit_condition.first_signal and cb.circuit_condition.first_signal.name) .. cb.circuit_condition.comparator .. tostring(cb.circuit_condition.constant) end
    o[#o+1] = e.position.x .. ',' .. e.position.y .. ' dir=' .. e.direction .. ' st=' .. e.status .. ' ' .. (e.name) .. ' filt=' .. tostring(f1) .. cond .. ' enable=' .. tostring(cb and cb.circuit_enable_disable)
  end
end
for _, e in pairs(s.find_entities_filtered{name='heating-tower', area={{55,10},{70,22}}}) do o[#o+1] = 'tower ' .. e.position.x .. ',' .. e.position.y .. ' st=' .. e.status end
for _, e in pairs(s.find_entities_filtered{name='decider-combinator', area={{90,15},{100,25}}}) do o[#o+1] = 'decider ' .. e.position.x .. ',' .. e.position.y .. ' st=' .. e.status end
rcon.print(table.concat(o, '\n'))
'''
print(tools["run_lua"](LUA))
