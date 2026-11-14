from _game import tools
LUA = r'''
local f = game.forces.player
local function ship(n) for _, p in pairs(f.platforms) do if p.name:sub(-#n) == n then return p end end end
local function setstone(ent, imp, qty, label)
  for _, pt in pairs(ent.get_logistic_point()) do
    if pt.mode == defines.logistic_mode.requester then
      local sec = pt.add_section()
      local sl = {value = {type = 'item', name = 'stone', quality = 'normal'}, min = qty}
      if imp then sl.max = qty sl.import_from = imp end
      sec.set_slot(1, sl)
      if imp then pcall(function() local fl = sec.filters[1] fl.minimum_delivery_count = qty sec.set_slot(1, fl) end) end
      return label .. ' ok'
    end
  end
  return label .. ' no requester point'
end
local o = {}
o[#o+1] = setstone(ship('Nauvis-Fulgora 1 Shuttle').hub, 'nauvis', 300, 'shuttle')
o[#o+1] = setstone(game.surfaces.fulgora.find_entities_filtered{type = 'cargo-landing-pad'}[1], nil, 300, 'fulgora pad')
rcon.print(table.concat(o, ', '))
'''
print(tools["run_lua"](LUA))
