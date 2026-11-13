#!/usr/bin/env python3
"""Gleba as science central (the Captain, 2026-11-12): agricultural packs rot, so research happens where they are made and the other packs
are shipped in.
  build    nine labs either side of a pack belt running south along x 127 from the science buffer chest (128.5,20.5); each lab has an
           inserter from the belt (agricultural packs only), a spoilage inserter back onto the belt, and a blue chest on its far side
           asking for the eight packs that do not rot. The belt is a dead end with a spoilage-only inserter into a heating tower (127.5,45.5).
           Cargo landing pad (142,23) where the shuttles drop the other packs; substation (134,22).
  config   filters, chest requests (200 of each pack), landing pad requests (PAD of each)
  ships    the two Nauvis-Gleba shuttles stop asking Gleba for agricultural packs and instead ask Nauvis for 400 of each pack Nauvis has
           (all nine since 2026-11-13; a ship waits at Nauvis until every kind is aboard); they leave Nauvis fuelled, armed and loaded, and leave Gleba after 60 quiet seconds (10 was too short: the ship left with packs still aboard).
           The Nauvis landing pad no longer asks for agricultural packs.
Run 2026-11-13. The first version of `ships` had an unbounded `while` loop over hub sections and froze the server on 2026-11-12. No unbounded loops in RCON Lua.
Usage: gleba_labs.py build|config|ships [--apply]"""
import json
import sys

from _game import tools

R = {"quality": "epic"}
PACKS = ["automation-science-pack", "logistic-science-pack", "military-science-pack", "chemical-science-pack", "production-science-pack",
         "utility-science-pack", "space-science-pack", "metallurgic-science-pack", "electromagnetic-science-pack"]
PAD = 1200      # the pad has 80 slots: nine packs at 4,000 filled it
WEST = [24, 27, 30, 33, 36, 39]
EAST = [24, 27, 30]


def build():
    e = [{"name": "substation", "x": 134, "y": 22}, {"name": "cargo-landing-pad", "x": 142, "y": 23},
         {"name": "bulk-inserter", "x": 128.5, "y": 21.5, "direction": 0},
         {"name": "transport-belt", "x": 128.5, "y": 22.5, "direction": 12}]
    e += [{"name": "transport-belt", "x": 127.5, "y": y + 0.5, "direction": 8} for y in range(22, 43)]
    e += [{"name": "bulk-inserter", "x": 127.5, "y": 43.5, "direction": 0}, {"name": "heating-tower", "x": 127.5, "y": 45.5}]
    for y in WEST:
        e += [{"name": "lab", "x": 124.5, "y": y + 0.5}, {"name": "bulk-inserter", "x": 126.5, "y": y - 0.5, "direction": 4},
              {"name": "bulk-inserter", "x": 126.5, "y": y + 1.5, "direction": 12},
              {"name": "bulk-inserter", "x": 122.5, "y": y + 0.5, "direction": 12}, {"name": "requester-chest", "x": 121.5, "y": y + 0.5}]
    for y in EAST:
        e += [{"name": "lab", "x": 130.5, "y": y + 0.5}, {"name": "bulk-inserter", "x": 128.5, "y": y - 0.5, "direction": 12},
              {"name": "bulk-inserter", "x": 128.5, "y": y + 1.5, "direction": 4},
              {"name": "bulk-inserter", "x": 132.5, "y": y + 0.5, "direction": 4}, {"name": "requester-chest", "x": 133.5, "y": y + 0.5}]
    for x in e:
        x["params"] = dict(R)
    return e


def config():
    agri, rot, feed = [], [], []
    for y in WEST:
        agri.append((126.5, y - 0.5)); rot.append((126.5, y + 1.5)); feed.append((121.5, y + 0.5))
    for y in EAST:
        agri.append((128.5, y - 0.5)); rot.append((128.5, y + 1.5)); feed.append((133.5, y + 0.5))
    agri.append((128.5, 21.5)); rot.append((127.5, 43.5))
    L = lambda rows: "{" + ",".join("{%s,%s}" % r for r in rows) + "}"
    packs = "{" + ",".join("'%s'" % p for p in PACKS) + "}"
    return ("local s=game.surfaces.gleba local function at(t,x,y) return s.find_entities_filtered{type=t,position={x,y},radius=0.3}[1] end local n=0 "
            "local function filt(rows,item) for _,q in pairs(rows) do local i=at('inserter',q[1],q[2]) i.use_filters=true i.inserter_filter_mode='whitelist' i.set_filter(1,item) n=n+1 end end "
            "filt(" + L(agri) + ",'agricultural-science-pack') filt(" + L(rot) + ",'spoilage') "
            "local packs=" + packs + " for _,q in pairs(" + L(feed) + ") do local c=at('logistic-container',q[1],q[2]) local ss=c.get_logistic_sections() local se=ss.sections[1] or ss.add_section() "
            "for k,p in pairs(packs) do se.set_slot(k,{value={name=p,quality='normal'},min=200}) end end "
            "local pad=s.find_entities_filtered{name='cargo-landing-pad'}[1] local ps=pad.get_logistic_sections() local se=ps.sections[1] or ps.add_section() "
            "for k,p in pairs(packs) do se.set_slot(k,{value={name=p,quality='normal'},min=%d}) end "
            "rcon.print('inserters filtered '..n..', lab chests '..#" % PAD + L(feed) + "..', pad asks for %d of each of '..#packs..' packs')" % PAD)


SHIPS = ("local f=game.forces.player local o={} local packs=PACKS local nb,bn=nil,0 for _,net in pairs(f.logistic_networks.nauvis or {}) do if net.all_logistic_robots>bn then nb=net bn=net.all_logistic_robots end end "
         "for i,p in pairs(f.platforms) do if p.name:find('^Nauvis%-Gleba') then local secs=p.hub.get_logistic_sections() local se=nil for _,sec in pairs(secs.sections) do if sec.is_manual then for j=1,sec.filters_count do sec.clear_slot(j) end se=se or sec end end se=se or secs.add_section() local k=0 "
         "for _,n in pairs(packs) do if true then k=k+1 se.set_slot(k,{value={name=n,quality='normal'},min=400,import_from='nauvis'}) end end "
         "local sch=p.schedule local w1={} for _,c in pairs(sch.records[1].wait_conditions) do if c.type=='circuit' then w1[#w1+1]=c end end w1[#w1+1]={type='all_requests_satisfied',compare_type='and'} "
         "local w2={} for _,c in pairs(sch.records[2].wait_conditions) do if c.type=='circuit' and c.condition.first_signal.name~='agricultural-science-pack' and #w2<3 then c.compare_type='and' w2[#w2+1]=c end end w2[#w2+1]={type='inactivity',compare_type='and',ticks=3600} "
         "sch.records[1].wait_conditions=w1 sch.records[2].wait_conditions=w2 p.schedule=sch o[#o+1]=p.name..' asks Nauvis for '..k..' packs x400' end end "
         "local pad=game.surfaces.nauvis.find_entities_filtered{name='cargo-landing-pad'}[1] for _,sec in pairs(pad.get_logistic_sections().sections) do for k,fl in pairs(sec.filters) do if fl.value and fl.value.name=='agricultural-science-pack' then sec.clear_slot(k) o[#o+1]='Nauvis pad request for agricultural packs removed' end end end "
         "rcon.print(table.concat(o,' | '))")


def main():
    apply = "--apply" in sys.argv
    if sys.argv[1] == "build":
        print(tools["place_entities"](json.dumps(build()), surface="gleba", dry_run=not apply)[:900])
    elif sys.argv[1] == "ships":
        lua = SHIPS.replace("PACKS", "{" + ",".join("'%s'" % p for p in PACKS) + "}")
        print(tools["run_lua"](lua) if apply else "(dry run) ships")
    else:
        print(tools["run_lua"](config()) if apply else "(dry run) config")


if __name__ == "__main__":
    main()
