"""Round 5: status of the copper load row inserters (x 171.5..183.5, y -294.5) and the count of working ones."""
from _game import tools

LUA = r'''
local s = game.surfaces.nauvis
local SN = {}
for k, v in pairs(defines.entity_status) do SN[v] = k end
local cnt = {}
local n = 0
for _, i in pairs(s.find_entities_filtered{name = 'fast-inserter', area = {{170, -295.5}, {185, -293.5}}}) do
  n = n + 1
  local k = tostring(SN[i.status])
  cnt[k] = (cnt[k] or 0) + 1
end
local o = {'loader inserters: ' .. n}
for k, v in pairs(cnt) do o[#o + 1] = k .. ' ' .. v end
rcon.print(table.concat(o, '\n'))
'''
if __name__ == "__main__":
    print(tools["run_lua"](LUA))
