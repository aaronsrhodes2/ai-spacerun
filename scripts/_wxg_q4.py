"""Scratch (read-only): where the Gleba Wheel's rocket fuel goes: hub, pad requests, platforms in orbit, science packs in the hub."""
import sys

from _game import tools

SURF = sys.argv[1] if len(sys.argv) > 1 else "platform-12"
PLANET = sys.argv[2] if len(sys.argv) > 2 else "gleba"


def q(lua):
    print(tools["run_lua"](lua.replace("SURF", SURF).replace("PLANET", PLANET)).replace("@@", "\n"))


q("local s=game.surfaces['SURF'] local hub=s.platform.hub local inv=hub.get_inventory(defines.inventory.hub_main) local tr=hub.get_inventory(defines.inventory.hub_trash) local o={} "
  "o[#o+1]='hub rocket-fuel '..inv.get_item_count('rocket-fuel')..' trash '..(tr and tr.get_item_count('rocket-fuel') or -1)..' free slots '..inv.count_empty_stacks() "
  "local f=game.forces.player.get_item_production_statistics(s) local P=defines.flow_precision_index for _,n in pairs{'rocket-fuel','automation-science-pack','logistic-science-pack','chemical-science-pack','military-science-pack','production-science-pack','space-science-pack'} do "
  "o[#o+1]=n..' made '..string.format('%.1f',f.get_flow_count{name=n,category='input',precision_index=P.ten_minutes})..' used '..string.format('%.1f',f.get_flow_count{name=n,category='output',precision_index=P.ten_minutes})..' a minute (10 min), total made '..f.get_input_count(n)..', in hub '..inv.get_item_count(n) end "
  "local lp=hub.get_logistic_point(defines.logistic_member_index.logistic_container) if lp then for _,sec in pairs(lp.sections) do for i=1,sec.filters_count do local fl=sec.filters[i] if fl and fl.value and fl.value.name=='rocket-fuel' then o[#o+1]='wheel hub request rocket-fuel min '..tostring(fl.min)..' max '..tostring(fl.max)..' group '..sec.group end end end end rcon.print(table.concat(o,'@@'))")
q("local o={} local g=game.surfaces['PLANET'] for _,pad in pairs(g.find_entities_filtered{type='cargo-landing-pad'}) do local inv=pad.get_inventory(defines.inventory.cargo_landing_pad_main) o[#o+1]='pad '..pad.position.x..','..pad.position.y..' rocket-fuel '..inv.get_item_count('rocket-fuel') "
  "local lp=pad.get_logistic_point(defines.logistic_member_index.logistic_container) if lp then for _,sec in pairs(lp.sections) do if sec.active then for i=1,sec.filters_count do local fl=sec.filters[i] if fl and fl.value and (fl.value.name=='rocket-fuel' or fl.value.name:find('science',1,true)) then o[#o+1]='  pad asks '..fl.value.name..' min '..tostring(fl.min)..' have '..inv.get_item_count(fl.value.name) end end end end end end "
  "local n=0 for _,net in pairs(game.forces.player.logistic_networks['PLANET'] or {}) do n=n+net.get_item_count('rocket-fuel') end o[#o+1]='PLANET networks hold rocket-fuel '..n "
  "for _,p in pairs(game.forces.player.platforms) do if p.space_location and p.space_location.name=='PLANET' and p.hub then local hi=p.hub.get_inventory(defines.inventory.hub_main) local line=p.name..' ['..p.surface.name..'] rocket-fuel '..hi.get_item_count('rocket-fuel')..' providing='..tostring(p.hub.providing_to_other_platforms) "
  "local lp=p.hub.get_logistic_point(defines.logistic_member_index.logistic_container) if lp then for _,sec in pairs(lp.sections) do for i=1,sec.filters_count do local fl=sec.filters[i] if fl and fl.value and fl.value.name=='rocket-fuel' then line=line..' ASKS rocket-fuel min '..tostring(fl.min) end end end end o[#o+1]=line end end rcon.print(table.concat(o,'@@'))")
