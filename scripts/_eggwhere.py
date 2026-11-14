from _game import tools
LUA = r'''
local o = {}
local s = game.surfaces['gleba']
for _, e in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt','splitter'}, area={{55,8},{135,22}}}) do
  for i = 1, 2 do
    local ok, tl = pcall(function() return e.get_transport_line(i) end)
    if ok and tl then local c = tl.get_item_count('pentapod-egg') if c > 0 then o[#o+1] = 'belt ' .. e.position.x .. ',' .. e.position.y .. ' lane' .. i .. ' eggs=' .. c end end
  end
end
for _, e in pairs(s.find_entities_filtered{type='inserter', area={{55,8},{135,22}}}) do
  local st = e.status
  local pk = e.pickup_target and e.pickup_target.name or '-'
  local dp = e.drop_target and e.drop_target.name or '-'
  if e.filter_slot_count and e.use_filters then
    local f1 = e.get_filter(1)
    if f1 and f1 == 'pentapod-egg' then o[#o+1] = 'egg ins ' .. e.position.x .. ',' .. e.position.y .. ' st=' .. st .. ' pick=' .. pk .. ' drop=' .. dp end
  end
end
rcon.print(table.concat(o, '\n'))
'''
print(tools["run_lua"](LUA))
