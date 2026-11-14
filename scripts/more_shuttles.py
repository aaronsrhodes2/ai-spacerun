#!/usr/bin/env python3
"""More shuttles of the proven second design (the Captain, 2026-11-12: several fast shuttles per planet, Gleba first because its packs rot).
  create   lists which names of PAIRS have no platform yet (dry run). With --apply it makes a new platform at Nauvis for each missing name
           (names end in Shuttle so the autopilot repairs them) and prints platform index and surface.
           It refuses to duplicate: a name counts as present when any platform's name, with a leading "[...] " icon tag stripped, equals
           it or contains it (plain find). On 2026-11-14 exact matching missed the icon-prefixed names and made six empty duplicates.
  twin     after build_shuttle2.py and configure_shuttle2.py on the new surface: 200 iron plates from Nauvis stock into the hub for the first
           magazines, then the sibling ship's schedule and science requests copied over (same waits: it only leaves Nauvis fuelled and armed).
           Sections that belong to a named group on the sibling (orbit-ferry, foundation-ferry, plates-up) are NOT copied: they are that
           ship's own job. Ships that already have a schedule are skipped.
After twin, and before the first flight, run `shuttle_preflight.py check "<name>"` (and `sweep` if it reports belt junk).
Usage: more_shuttles.py create [--apply] | twin"""
import sys

from _game import tools

PAIRS = "{{'Nauvis-Gleba 2 Shuttle','Nauvis-Gleba 1 Shuttle'},{'Nauvis-Vulcanus 2 Shuttle','Nauvis-Vulcanus 1 Shuttle'},{'Nauvis-Fulgora 2 Shuttle','Nauvis-Fulgora 1 Shuttle'},{'Nauvis-Gleba 3 Shuttle','Nauvis-Gleba 1 Shuttle'},{'Nauvis-Gleba 4 Shuttle','Nauvis-Gleba 1 Shuttle'},{'Nauvis-Gleba 5 Shuttle','Nauvis-Gleba 1 Shuttle'},{'Nauvis-Gleba 6 Shuttle','Nauvis-Gleba 1 Shuttle'},{'Nauvis-Vulcanus 3 Shuttle','Nauvis-Vulcanus 1 Shuttle'},{'Nauvis-Fulgora 3 Shuttle','Nauvis-Fulgora 1 Shuttle'}}"
# by_name(n): the platform called n, icon prefix or not. Exact match on the stripped name first, then a plain find (no patterns: names hold '-').
LOOKUP = ("local f=game.forces.player local o={} local function bare(n) return (n:gsub('^%[.-%]%s*','')) end "
          "local function by_name(n) for i,p in pairs(f.platforms) do if bare(p.name)==n then return p,i end end "
          "for i,p in pairs(f.platforms) do if p.name:find(n,1,true) then return p,i end end end ")
CREATE = (LOOKUP + "local apply=APPLY for _,q in pairs(" + PAIRS + ") do local p,i=by_name(q[1]) "
          "if p then o[#o+1]='have '..q[1]..' (#'..i..' '..p.surface.name..')' elseif not apply then o[#o+1]='MISSING '..q[1]..' (dry run: add --apply to create)' "
          "else local np=f.create_space_platform{name=q[1],planet='nauvis',starter_pack='space-platform-starter-pack'} np.apply_starter_pack() o[#o+1]='CREATED '..q[1]..' '..np.surface.name end end "
          "rcon.print(table.concat(o,' | '))")
TWIN = (LOOKUP + "local nb,bn=nil,0 for _,net in pairs(f.logistic_networks.nauvis or {}) do if net.all_logistic_robots>bn then nb=net bn=net.all_logistic_robots end end "
        "for _,q in pairs(" + PAIRS + ") do local p,old=by_name(q[1]),by_name(q[2]) if p and old and p~=old and not (p.schedule and p.schedule.records and #p.schedule.records>0) then local inv=p.hub.get_inventory(defines.inventory.hub_main) "
        "if inv.get_item_count('iron-plate')<200 and inv.get_item_count('firearm-magazine')<200 then local got=nb.remove_item{name='iron-plate',count=200} inv.insert{name='iron-plate',count=got} end "
        "local secs=p.hub.get_logistic_sections() local mine={} for _,se in pairs(secs.sections) do for _,fl in pairs(se.filters) do if fl.value then mine[fl.value.name]=true end end end "
        "for _,se in pairs(old.hub.get_logistic_sections().sections) do if se.group==nil or se.group=='' then for _,fl in pairs(se.filters) do if fl.value and not mine[fl.value.name] and string.find(fl.value.name,'science') then local ns=secs.add_section() "
        "ns.set_slot(1,{value={name=fl.value.name,quality='normal'},min=fl.min,import_from=fl.import_from,minimum_delivery_count=fl.minimum_delivery_count}) mine[fl.value.name]=true end end end end "
        "local junk=0 for _,b in pairs(p.surface.find_entities_filtered{type={'transport-belt','underground-belt'}}) do for l=1,2 do local tl=b.get_transport_line(l) for _,it in pairs(tl.get_contents()) do if it.name~='firearm-magazine' and not string.find(it.name,'chunk') then local r=tl.remove_item{name=it.name,count=it.count} junk=junk+r inv.insert{name=it.name,count=r} end end end end "
        "local sch=p.schedule or {} sch.records=old.schedule.records sch.current=1 p.schedule=sch p.paused=false "
        "o[#o+1]=q[1]..': schedule copied ('..#p.schedule.records..' stops), belt junk cleared '..junk..', paused '..tostring(p.paused) end end rcon.print(table.concat(o,' | '))")

if __name__ == "__main__":
    step = sys.argv[1]
    lua = CREATE.replace("APPLY", "true" if "--apply" in sys.argv else "false") if step == "create" else {"twin": TWIN}[step]
    print(tools["run_lua"](lua))
