"""Read only: who asks for an item: every platform hub's request slots for it and the landing pad of a planet. Usage: _fwx_who.py ITEM PLANET"""
import sys

from _game import tools

item, planet = sys.argv[1], sys.argv[2]
LUA = ("local o={} local function secs(e,label) local lp=e.get_logistic_sections() if not lp then return end for _,sec in pairs(lp.sections) do for k=1,sec.filters_count do local f=sec.get_slot(k) "
       "if f and f.value and f.value.name=='%s' then o[#o+1]=label..' ['..(sec.group or '')..'] active '..tostring(sec.active)..' min '..tostring(f.min)..' max '..tostring(f.max)..' import_from '..tostring(f.import_from and (f.import_from.name or f.import_from))..' request_from '..tostring(f.request_from) end end end end "
       "for _,p in pairs(game.forces.player.platforms) do if p.hub and p.hub.valid then secs(p.hub,p.name..' @'..tostring(p.space_location and p.space_location.name)..' has '..p.hub.get_inventory(defines.inventory.hub_main).get_item_count('%s')) end end "
       "local s=game.surfaces['%s'] for _,pad in pairs(s.find_entities_filtered{type='cargo-landing-pad'}) do o[#o+1]='pad holds '..pad.get_inventory(defines.inventory.cargo_landing_pad_main).get_item_count('%s')..' network '..(pad.logistic_network and pad.logistic_network.get_item_count('%s') or -1) secs(pad,'pad') "
       "local lp=pad.get_logistic_point(defines.logistic_member_index.logistic_container) if lp then o[#o+1]='pad point mode '..tostring(lp.mode)..' trash_not_requested '..tostring(lp.trash_not_requested) end end rcon.print(table.concat(o,'\\n'))") % (item, item, planet, item, item)
print(tools["run_lua"](LUA))
