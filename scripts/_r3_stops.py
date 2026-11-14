"""Round 3: all Nauvis train stops with 'Copper' in the name: position, status, and wagons/trains parked; plus locomotive and cargo-wagon counts on Nauvis."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local SN = {}
for k, v in pairs(defines.entity_status) do SN[v] = k end
local o = {}
for _, st in pairs(s.find_entities_filtered{type = 'train-stop'}) do
  if st.backer_name and string.find(st.backer_name, 'Copper') then
    local parked = st.get_stopped_train and st.get_stopped_train() or nil
    o[#o + 1] = 'STOP ' .. st.backer_name .. ' at ' .. st.position.x .. ',' .. st.position.y .. ' status=' .. tostring(SN[st.status]) .. ' parked=' .. (parked and 'yes' or 'no')
  end
end
local lo, cw = 0, 0
for _, t in pairs(game.train_manager.get_trains{surface = s}) do
  for _, c in pairs(t.carriages) do
    if c.type == 'locomotive' then lo = lo + 1 end
    if c.type == 'cargo-wagon' then cw = cw + 1 end
  end
end
o[#o + 1] = 'locos ' .. lo .. ' cargo wagons ' .. cw
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
