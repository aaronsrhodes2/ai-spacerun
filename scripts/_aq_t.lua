local s=game.surfaces.aquilo local o={} local st={} for k,v in pairs(defines.entity_status) do st[v]=k end
o[#o+1]='tick '..game.tick..' speed '..game.speed..' players '..#game.connected_players..' paused '..tostring(game.tick_paused)
local e=s.find_entities_filtered{name='chemical-plant',position={32.5,-3.5},radius=0.5}[1] local fl='' for i=1,e.fluids_count do local fd=e.get_fluid(i) if fd then fl=fl..' '..fd.name..'='..math.floor(fd.amount) end end o[#o+1]='fuel plant '..st[e.status]..fl..' out '..e.get_inventory(defines.inventory.crafter_output).get_item_count('solid-fuel')..' made '..e.products_finished
local c=s.find_entities_filtered{name='passive-provider-chest',position={32.5,-0.5},radius=0.5}[1] o[#o+1]='fuel chest '..c.get_inventory(defines.inventory.chest).get_item_count('solid-fuel')
local pj=s.find_entities_filtered{name='pumpjack',position={35.5,-2.5},radius=0.5}[1] o[#o+1]='pumpjack '..st[pj.status]
rcon.print(table.concat(o,'\n'))
