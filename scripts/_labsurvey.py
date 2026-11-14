"""Survey every lab: where it is, what it is researching, whether it has its packs, and what each surface's labs lack."""
from _game import tools

LUA = r'''
local o = {}
local f = game.forces.player
o[#o + 1] = 'current=' .. tostring(f.current_research and f.current_research.name or 'none')
local q = {}
for _, t in pairs(f.research_queue or {}) do q[#q + 1] = t.name end
o[#o + 1] = 'queue=' .. table.concat(q, ',')
for _, sn in pairs({'nauvis', 'gleba', 'fulgora', 'vulcanus'}) do
  local s = game.surfaces[sn]
  if s then
    local tally = {}
    for _, e in pairs(s.find_entities_filtered{type = 'lab'}) do
      local st = e.status
      local key = tostring(st)
      tally[key] = (tally[key] or 0) + 1
      if st == defines.entity_status.missing_science_packs then
        local inv = e.get_inventory(defines.inventory.lab_input)
        local have = {}
        if inv then
          for _, it in pairs(inv.get_contents()) do have[#have + 1] = it.name .. '=' .. it.count end
        end
        if tally['sample'] == nil then
          tally['sample'] = 1
          o[#o + 1] = sn .. ' sample lab at ' .. e.position.x .. ',' .. e.position.y .. ' holds: ' .. table.concat(have, ' ')
        end
      end
    end
    local parts = {}
    for k, v in pairs(tally) do if k ~= 'sample' then parts[#parts + 1] = k .. '=' .. v end end
    o[#o + 1] = sn .. ' labs: ' .. table.concat(parts, ', ')
  end
end
rcon.print(table.concat(o, '\n'))
'''

if __name__ == "__main__":
    print(tools["run_lua"](LUA))
