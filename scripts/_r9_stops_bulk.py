"""Round 9: at every Nauvis train stop named '* Load' or '* Unload', replace the fast-inserters and plain inserters that touch the track
(pickup or drop within 1.5 tiles of a rail) with bulk inserters in place. Dry run by default; --apply to do it."""
import sys

from _game import tools

APPLY = "--apply" in sys.argv

LUA = r'''
local s = game.surfaces.nauvis
local f = game.forces.player
local apply = %s
local o = {}
local seen = {}
local totals = {fast = 0, plain = 0, done = 0}
for _, st in pairs(s.find_entities_filtered{type = 'train-stop'}) do
  local nm = st.backer_name or ''
  if string.find(nm, ' Load') or string.find(nm, ' Unload') then
    local rails = s.find_entities_filtered{type = {'straight-rail', 'curved-rail-a', 'curved-rail-b'}, position = st.position, radius = 22}
    local found, done = 0, 0
    for _, i in pairs(s.find_entities_filtered{name = {'fast-inserter', 'inserter'}, position = st.position, radius = 24}) do
      local key = i.position.x .. ',' .. i.position.y
      if not seen[key] then
        local touches = false
        for _, p in ipairs({i.pickup_position, i.drop_position}) do
          for _, r in ipairs(rails) do
            if math.abs(r.position.x - p.x) <= 1.6 and math.abs(r.position.y - p.y) <= 1.6 then touches = true; break end
          end
          if touches then break end
        end
        if touches then
          seen[key] = true
          found = found + 1
          if i.name == 'fast-inserter' then totals.fast = totals.fast + 1 else totals.plain = totals.plain + 1 end
          if apply then
            local e = s.create_entity{name = 'bulk-inserter', position = i.position, direction = i.direction, force = f, fast_replace = true, spill = false}
            if e then done = done + 1; totals.done = totals.done + 1 end
          end
        end
      end
    end
    if found > 0 then o[#o + 1] = nm .. ' at ' .. st.position.x .. ',' .. st.position.y .. ': ' .. found .. ' inserters' .. (apply and (' replaced ' .. done) or '') end
  end
end
table.sort(o)
o[#o + 1] = 'TOTAL fast ' .. totals.fast .. ' plain ' .. totals.plain .. (apply and (' replaced ' .. totals.done) or '')
rcon.print(table.concat(o, '\n'))
''' % ('true' if APPLY else 'false')

if __name__ == "__main__":
    print('APPLY' if APPLY else 'DRY RUN')
    print(tools["run_lua"](LUA))
