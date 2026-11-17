#!/usr/bin/env python3
"""Request tidy (2026-11-17, from the factory check): three request faults that filled hubs and the Aquilo pad.

  floors   The `floor-hub-ng|nv|nf` groups made nine Nauvis shuttles carry 1,000 to 2,000 refined hazard concrete each for the block floors.
           Gleba, Vulcanus and Fulgora have no tile ghost left, so the cargo was dead weight (Nauvis-Gleba 2 Shuttle: 0 of 109 slots free,
           game alert "no platform storage"). The groups become drops (min = max = 0, import_from the destination): the concrete goes down
           to that planet's pad on the next visit and nothing new is lifted. A group name is shared, so one write changes every shuttle.
  aquilo   Fulgora-Aquilo 5 Shuttle lifted 500 holmium plate, 600 tungsten plate and 500 tungsten carbide every trip and dropped all of it
           (`aq-drop-39`), whatever Aquilo held: the pad reached 26,594 / 7,800 / 15,204 and 82% full. Those three leave the drop group and the
           Aquilo pad asks for a keep level instead (group `aq-keep`), so the shuttle only unloads what the pad is short of.
  tiles    Aquilo's floor ghosts: 1,534 refined hazard concrete and 7,848 refined concrete, zero stock there. Gleba holds 2,640 unused hazard
           concrete, Fulgora makes refined concrete from its surplus concrete. Gleba-Aquilo 1 Shuttle lifts hazard concrete at Gleba
           (`floor-hub-ga`), Fulgora-Aquilo 5 Shuttle lifts refined concrete at Fulgora (`floor-hub-fa`), and the Aquilo pad asks for what the
           ghosts still need (group `aq-floor`, rewritten from the live ghost count on every run: 0 ghosts = no request, shuttle groups removed).
Nothing is created: requests only. Usage: request_tidy.py status | apply      (apply is safe to repeat; the autopilot may call tiles())"""
import sys

from _game import tools

L = tools["run_lua"]
KEEP = {"holmium-plate": 2000, "tungsten-plate": 1000, "tungsten-carbide": 1000}
UNDROP = list(KEEP) + ["refined-concrete"]                                               # refined concrete is unloaded by the pad's own request (aq-floor), never dumped      # Aquilo pad keep levels (fusion cells, cryogenic plants)
FLOORS = {"floor-hub-ng": "gleba", "floor-hub-nv": "vulcanus", "floor-hub-nf": "fulgora"}
SHIP_FA, SHIP_GA = "Fulgora-Aquilo 5 Shuttle", "Gleba-Aquilo 1 Shuttle"
HEAD = 1.1                                                                               # tiles: ask for 10% over the ghost count

HELP = (
    "local f=game.forces.player local NL=string.char(10) local o={} "
    "local function hubpt(p) return p.hub.get_logistic_point(defines.logistic_member_index.space_platform_hub_requester) end "
    "local function ship(n) for _,p in pairs(f.platforms) do if p.hub and p.hub.valid and string.find(p.name,n,1,true) then return p end end end "
    "local function padpt(sn) local pad=game.surfaces[sn].find_entities_filtered{type='cargo-landing-pad',force=f}[1] "
    "  local pt=pad.get_logistic_point(defines.logistic_member_index.cargo_landing_pad_requester) return pt,pad end "
    "local function drop(pt,g) for i=pt.sections_count,1,-1 do if pt.sections[i].group==g then pt.remove_section(i) end end end "
    "local function sec(pt,g) for _,s in pairs(pt.sections) do if s.group==g then return s end end return pt.add_section(g) end "
    "local function show(tag,pt,pat) for _,s in pairs(pt.sections) do if s.group and string.find(s.group,pat) then for _,fl in pairs(s.filters) do if fl.value then "
    "  o[#o+1]=tag..' ['..s.group..'] '..fl.value.name..' '..tostring(fl.min)..'..'..tostring(fl.max)..' from '..tostring(fl.import_from and fl.import_from.name) end end end end end "
    "local function ghosts(n) local c=0 for _,g in pairs(game.surfaces.aquilo.find_entities_filtered{type='tile-ghost'}) do if g.ghost_name==n then c=c+1 end end return c end "
)

STATUS = HELP + (
    "for _,p in pairs(f.platforms) do if p.hub and p.hub.valid then show(p.name,hubpt(p),'^floor%-hub') show(p.name,hubpt(p),'^aq%-drop') "
    " o[#o+1]=p.name..' free slots '..p.hub.get_inventory(defines.inventory.hub_main).count_empty_stacks()..' hazard aboard '..p.hub.get_item_count('refined-hazard-concrete')..' refined aboard '..p.hub.get_item_count('refined-concrete') end end "
    "local pt,pad=padpt('aquilo') show('aquilo pad',pt,'^aq%-') show('aquilo pad',pt,'^ghost%-auto') "
    "o[#o+1]='aquilo pad free '..pad.get_inventory(defines.inventory.cargo_landing_pad_main).count_empty_stacks()..' holmium '..pad.get_item_count('holmium-plate')..' tungsten '..pad.get_item_count('tungsten-plate')..' carbide '..pad.get_item_count('tungsten-carbide') "
    "o[#o+1]='aquilo ghosts: refined '..ghosts('refined-concrete')..' hazard '..(ghosts('refined-hazard-concrete-left')+ghosts('refined-hazard-concrete-right')) "
    "rcon.print(table.concat(o,NL))"
)


def floors():
    code = HELP
    for g, dest in FLOORS.items():
        code += ("for _,p in pairs(f.platforms) do if p.hub and p.hub.valid then for _,s in pairs(hubpt(p).sections) do if s.group=='%s' then "
                 "s.set_slot(1,{value={type='item',name='refined-hazard-concrete',quality='normal'},min=0,max=0,import_from='%s'}) o[#o+1]=p.name..' %s -> drop at %s' end end end end "
                 % (g, dest, g, dest))
    return L(code + "rcon.print(table.concat(o,NL))")


def aquilo():
    keep = ",".join("{'%s',%d}" % kv for kv in KEEP.items())
    und = ",".join("'%s'" % n for n in UNDROP)
    return L(HELP + (
        "local K={%s} local U={%s} local p=ship('%s') local pt=hubpt(p) local n=0 "
        "for _,s in pairs(pt.sections) do if s.group and string.find(s.group,'^aq%%-drop') then for i,fl in pairs(s.filters) do if fl.value then for _,k in pairs(U) do "
        " if fl.value.name==k then s.clear_slot(i) n=n+1 end end end end end end "
        "local ppt=padpt('aquilo') drop(ppt,'aq-keep') local ks=ppt.add_section('aq-keep') "
        "for i,k in ipairs(K) do ks.set_slot(i,{value={type='item',name=k[1],quality='normal'},min=k[2],max=k[2]}) end "
        "rcon.print('drop slots cleared '..n..', pad keep levels '..#K)") % (keep, und, SHIP_FA))


def tiles():
    """Rewrites the floor requests from the live ghost count. Safe to call every cycle."""
    return L(HELP + (
        "local r=ghosts('refined-concrete') local h=ghosts('refined-hazard-concrete-left')+ghosts('refined-hazard-concrete-right') "
        "local net=game.surfaces.aquilo.find_logistic_network_by_position(select(2,padpt('aquilo')).position,f) "
        "local hr=net and net.get_item_count('refined-concrete') or 0 local hh=net and net.get_item_count('refined-hazard-concrete') or 0 "
        "local nr=math.max(0,math.ceil(r*%s)-hr) local nh=math.max(0,math.ceil(h*%s)-hh) "
        "local ppt,pad=padpt('aquilo') drop(ppt,'aq-floor') local pr,ph=nr,nh "
        "for _,s in pairs(ppt.sections) do if s.group=='ghost-auto-aquilo' then for _,fl in pairs(s.filters) do if fl.value then "
        " if fl.value.name=='refined-concrete' then pr=math.max(0,pr-math.max(0,fl.min-pad.get_item_count('refined-concrete'))) end "
        " if fl.value.name=='refined-hazard-concrete' then ph=math.max(0,ph-math.max(0,fl.min-pad.get_item_count('refined-hazard-concrete'))) end end end end end "
        "if pr+ph>0 then local s=ppt.add_section('aq-floor') local i=0 "
        " if pr>0 then i=i+1 local c=pad.get_item_count('refined-concrete')+pr s.set_slot(i,{value={type='item',name='refined-concrete',quality='normal'},min=c,max=c}) end "
        " if ph>0 then i=i+1 local c=pad.get_item_count('refined-hazard-concrete')+ph s.set_slot(i,{value={type='item',name='refined-hazard-concrete',quality='normal'},min=c,max=c}) end end "
        "local function lift(name,g,item,need,from) local p=ship(name) if not p then o[#o+1]='no ship '..name return end local pt=hubpt(p) drop(pt,g) "
        " if need>0 then local s=pt.add_section(g) s.set_slot(1,{value={type='item',name=item,quality='normal'},min=need,max=100000,import_from=from}) end o[#o+1]=name..' ['..g..'] '..item..' '..need end "
        "lift('%s','floor-hub-fa','refined-concrete',nr,'fulgora') lift('%s','floor-hub-ga','refined-hazard-concrete',nh,'gleba') "
        "o[#o+1]='ghosts refined '..r..' hazard '..h..'; on Aquilo refined '..hr..' hazard '..hh rcon.print(table.concat(o,NL))") % (HEAD, HEAD, SHIP_FA, SHIP_GA))


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    if step == "apply":
        print(floors())
        print(aquilo())
        print(tiles())
    print(L(STATUS))
