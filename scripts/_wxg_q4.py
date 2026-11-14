"""Scratch (read-only): who takes goods from a providing wheel: the planet's pad, and every platform in the orbit with what it
asks of other platforms. Usage: _wxg_q4.py [SURFACE] [PLANET]"""
import sys

from _game import tools

SURF = sys.argv[1] if len(sys.argv) > 1 else "platform-12"
PLANET = sys.argv[2] if len(sys.argv) > 2 else "gleba"


def q(lua):
    print(tools["run_lua"](lua.replace("SURF", SURF).replace("PLANET", PLANET)).replace("@@", "\n"))


q("local s=game.surfaces['SURF'] local hub=s.platform.hub local inv=hub.get_inventory(defines.inventory.hub_main) local tr=hub.get_inventory(defines.inventory.hub_trash) local o={} "
  "local t={} for _,n in pairs{'rocket-fuel','low-density-structure','processing-unit','automation-science-pack','logistic-science-pack','chemical-science-pack','military-science-pack','production-science-pack','utility-science-pack','space-science-pack'} do t[#t+1]=n..' '..inv.get_item_count(n)..(tr and tr.get_item_count(n)>0 and (' (trash '..tr.get_item_count(n)..')') or '') end "
  "o[#o+1]='WHEEL HUB tick '..game.tick..': '..table.concat(t,', ')..'; providing='..tostring(hub.providing_to_other_platforms) "
  "local g=game.surfaces['PLANET'] for _,pad in pairs(g.find_entities_filtered{type='cargo-landing-pad'}) do local pi=pad.get_inventory(defines.inventory.cargo_landing_pad_main) o[#o+1]='PAD rocket-fuel '..pi.get_item_count('rocket-fuel')..' chemical '..pi.get_item_count('chemical-science-pack')..' low-density '..pi.get_item_count('low-density-structure') end "
  "for _,p in pairs(game.forces.player.platforms) do if p.space_location and p.space_location.name=='PLANET' and p.hub and p.surface.name~='SURF' then local hi=p.hub.get_inventory(defines.inventory.hub_main) local line=p.name..' ['..p.surface.name..'] providing='..tostring(p.hub.providing_to_other_platforms)..' holds rocket-fuel '..hi.get_item_count('rocket-fuel')..' chemical '..hi.get_item_count('chemical-science-pack') "
  "local lp=p.hub.get_logistic_point(defines.logistic_member_index.logistic_container) local asks={} if lp then for _,sec in pairs(lp.sections) do if sec.active then for i=1,sec.filters_count do local fl=sec.filters[i] if fl and fl.value and fl.request_from and fl.request_from~='planet' then asks[#asks+1]=fl.value.name..' '..tostring(fl.min)..' from '..tostring(fl.request_from) end end end end end "
  "o[#o+1]=line..' | asks of platforms: '..(#asks>0 and table.concat(asks,', ') or 'nothing') end end rcon.print(table.concat(o,'@@'))")
