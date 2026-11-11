"""
Fulgora main base on the open land of the big island (x 116..200, y -128..-88), fed with raw scrap by the elevated-rail train.
Everything inside the base moves by logistic robots (the Captain's order 2026-11-11: "sort it using drones"); only fluids use pipes.

  unload     north of the track at stop `Scrap Base Unload`: bulk inserters lift scrap from the 4 wagons into red (passive provider) chests
  recyclers  row of 34 recyclers: blue chest (requests scrap) -> inserter -> recycler -> purple (active provider) chest
  yard       the trash yard south of the track: yellow storage chest -> inserter -> recycler -> purple chest. Robots carry to blue chests
             first; what nobody wants lands in yellow chests and is recycled away (25% comes back as its ingredients each pass)
  ports      8 more roboports; `robots N` moves N logistic robots from Nauvis' roboports (factory-made, moved)

Usage: scripts/fulgora_base.py STEP [--apply]
"""
import json
import sys

from _game import tools

WAGONS = (148, 155, 162, 169)
REC_X = list(range(126, 194, 2))
YARD_X = list(range(124, 136, 2)) + list(range(146, 158, 2)) + list(range(166, 178, 2)) + list(range(184, 198, 2))


def lua(code):
    out = tools["run_lua"](code).strip()
    try:
        d = json.loads(out)
        return d["result"] if isinstance(d, dict) and "result" in d else d
    except Exception:
        return out


def place(ents, apply, group=1):
    """Dry run first; a group of `group` consecutive entities (one machine with its chests) is dropped whole if any part fails."""
    res = json.loads(tools["place_entities"](json.dumps(ents), surface="fulgora", dry_run=True))
    res = json.loads(res["result"]) if "result" in res else res
    bad = {(f["i"] - 1) // group for f in (res.get("failed") or [])}
    good = [e for i, e in enumerate(ents) if i // group not in bad]
    print(f"{len(ents)} entities, {len(bad)} group(s) dropped for collisions, placing {len(good)}")
    if apply and good:
        print(tools["place_entities"](json.dumps(good), surface="fulgora", dry_run=False)[:1500])


def unload():
    e = []
    for c in WAGONS:
        for t in range(c - 3, c + 3):
            e.append({"name": "bulk-inserter", "x": t + 0.5, "y": -106.5, "direction": 8})
            e.append({"name": "passive-provider-chest", "x": t + 0.5, "y": -107.5})
    return e


def bank(xs, top, feeder):
    """Recyclers facing north. top = row (min y) of the output chests."""
    e = []
    for cx in xs:
        e.append({"name": "active-provider-chest", "x": cx - 0.5, "y": top + 0.5})
        e.append({"name": "recycler", "x": cx, "y": top + 3, "direction": 0})
        e.append({"name": "bulk-inserter", "x": cx - 0.5, "y": top + 5.5, "direction": 8})
        e.append({"name": feeder, "x": cx - 0.5, "y": top + 6.5})
    return e


REQUEST = ("local s=game.surfaces.fulgora local n=0 for _,c in pairs(s.find_entities_filtered{name='requester-chest',area={{120,-110},{196,-109}}}) do "
           "local secs=c.get_logistic_sections() local sec=secs.sections[1] or secs.add_section() sec.set_slot(1,{value={name='scrap',quality='normal'},min=100}) n=n+1 end rcon.print('scrap requests set '..n)")

ROBOTS = ("local f=game.forces.player local s=game.surfaces.fulgora local need=%d local got={} for _,rp in pairs(game.surfaces.nauvis.find_entities_filtered{type='roboport',force=f}) do if need<=0 then break end "
          "local inv=rp.get_inventory(defines.inventory.roboport_robot) for i=1,#inv do local st=inv[i] if need>0 and st.valid_for_read and st.name=='logistic-robot' then local t=math.min(need,st.count) "
          "got[#got+1]={name='logistic-robot',count=t,quality=st.quality.name} st.count=st.count-t need=need-t end end end "
          "local ports=s.find_entities_filtered{type='roboport',force=f,area={{116,-128},{200,-88}}} local put=0 local i=0 for _,g in pairs(got) do local left=g.count local tries=0 while left>0 and tries<#ports do i=i%%#ports+1 tries=tries+1 "
          "local d=ports[i].get_inventory(defines.inventory.roboport_robot).insert{name=g.name,count=math.min(left,25),quality=g.quality} left=left-d put=put+d if d>0 then tries=0 end end end "
          "rcon.print('robots moved '..put..' short '..need..' ports '..#ports)")


def pipes(pts):
    return [{"name": "pipe", "x": x, "y": y} for x, y in pts]


def hline(y, x0, x1):
    return [(x + 0.5, y) for x in range(int(x0 - 0.5), int(x1 - 0.5) + 1)]


def vline(x, y0, y1):
    return [(x, y + 0.5) for y in range(int(y0 - 0.5), int(y1 - 0.5) + 1)]


def cell():
    """Science cell, x 105..200, y -162..-129. Electromagnetic plants face east: fluid input 1 on the north side, input 2 on the south,
    output 1 on the west (led under the south main by an underground pipe to the electrolyte main)."""
    e = []
    # heavy oil: pump on the west shore, trunk along y -155.5 = north main of the electrolyte row
    e.append({"name": "offshore-pump", "x": 105.5, "y": -151.5, "direction": 12})
    e += pipes(vline(106.5, -155.5, -151.5) + hline(-155.5, 107.5, 139.5))
    # light oil unit: ice melter -> water under the trunk -> cracker (heavy from the trunk) -> superconductor plant
    e.append({"name": "chemical-plant", "x": 112.5, "y": -160.5, "direction": 0, "recipe": "ice-melting"})
    e += [{"name": "bulk-inserter", "x": 110.5, "y": -160.5, "direction": 12}, {"name": "requester-chest", "x": 109.5, "y": -160.5, "req": {"ice": 20}}]
    e += pipes([(111.5, -158.5), (111.5, -152.5), (113.5, -153.5), (113.5, -154.5), (113.5, -152.5), (111.5, -148.5)])
    e += [{"name": "pipe-to-ground", "x": 111.5, "y": -157.5, "direction": 0}, {"name": "pipe-to-ground", "x": 111.5, "y": -153.5, "direction": 8}]
    e.append({"name": "chemical-plant", "x": 112.5, "y": -150.5, "direction": 0, "recipe": "heavy-oil-cracking"})
    e.append({"name": "electromagnetic-plant", "x": 112, "y": -146, "direction": 4, "recipe": "superconductor"})
    e += [{"name": "requester-chest", "x": 108.5, "y": -147.5, "req": {"copper-plate": 10, "plastic-bar": 10, "holmium-plate": 10}}, {"name": "bulk-inserter", "x": 109.5, "y": -147.5, "direction": 12},
          {"name": "passive-provider-chest", "x": 108.5, "y": -146.5}, {"name": "bulk-inserter", "x": 109.5, "y": -146.5, "direction": 4}]
    # row A: electrolyte (north main heavy oil, south main holmium solution, output to the electrolyte main)
    for k in range(4):
        cx, cy = 122 + 6 * k, -153
        e.append({"name": "electromagnetic-plant", "x": cx, "y": cy, "direction": 4, "recipe": "electrolyte"})
        e += [{"name": "requester-chest", "x": cx - 3.5, "y": cy - 1.5, "req": {"stone": 20}}, {"name": "bulk-inserter", "x": cx - 2.5, "y": cy - 1.5, "direction": 12}]
        e += pipes([(cx - 2.5, cy + 0.5)])
        e += [{"name": "pipe-to-ground", "x": cx - 2.5, "y": cy + 1.5, "direction": 0}, {"name": "pipe-to-ground", "x": cx - 2.5, "y": cy + 3.5, "direction": 8}]
    e += pipes(hline(-150.5, 117.5, 140.5))                       # solution main 1
    e += pipes(hline(-148.5, 119.5, 163.5))                       # electrolyte main
    # row B: science packs (north electrolyte, south solution) and supercapacitors (north electrolyte only)
    for k in range(8):
        cx, cy = 122 + 6 * k, -146
        pack = k < 5
        e.append({"name": "electromagnetic-plant", "x": cx, "y": cy, "direction": 4, "recipe": "electromagnetic-science-pack" if pack else "supercapacitor"})
        req = {"supercapacitor": 10, "accumulator": 10} if pack else {"battery": 10, "electronic-circuit": 40, "holmium-plate": 20, "superconductor": 20}
        e += [{"name": "requester-chest", "x": cx - 3.5, "y": cy - 1.5, "req": req}, {"name": "bulk-inserter", "x": cx - 2.5, "y": cy - 1.5, "direction": 12},
              {"name": "passive-provider-chest", "x": cx - 3.5, "y": cy - 0.5}, {"name": "bulk-inserter", "x": cx - 2.5, "y": cy - 0.5, "direction": 4}]
    e += pipes(hline(-143.5, 116.5, 146.5))                       # solution main 2
    e += pipes(vline(117.5, -149.5, -144.5))                      # main 1 to main 2
    e += pipes(vline(116.5, -142.5, -131.5))                      # main 2 to main 3
    e += pipes(hline(-130.5, 116.5, 154.5))                       # solution main 3 (chem row output, plate assemblers' input)
    # chem row: holmium solution plants under a water main, ice melter above it, plate assemblers at the east end
    for k in range(5):
        cx, cy = 124.5 + 5 * k, -132.5
        e.append({"name": "chemical-plant", "x": cx, "y": cy, "direction": 0, "recipe": "holmium-solution"})
        e += [{"name": "bulk-inserter", "x": cx - 2, "y": cy, "direction": 12}, {"name": "requester-chest", "x": cx - 3, "y": cy, "req": {"stone": 10, "holmium-ore": 20}}]
    e += pipes(hline(-134.5, 123.5, 145.5))                       # water main
    e.append({"name": "chemical-plant", "x": 134.5, "y": -136.5, "direction": 0, "recipe": "ice-melting"})
    e += [{"name": "bulk-inserter", "x": 132.5, "y": -136.5, "direction": 12}, {"name": "requester-chest", "x": 131.5, "y": -136.5, "req": {"ice": 20}}]
    for cx in (149.5, 154.5):
        e.append({"name": "assembling-machine-3", "x": cx, "y": -132.5, "direction": 8, "recipe": "holmium-plate"})
        e += [{"name": "bulk-inserter", "x": cx - 2, "y": -132.5, "direction": 4}, {"name": "passive-provider-chest", "x": cx - 3, "y": -132.5}]
    # robot-only assemblers: accumulators and electronic circuits
    for k in range(6):
        cx, cy = 160.5 + 7 * k, -132.5
        acc = k < 5
        e.append({"name": "assembling-machine-3", "x": cx, "y": cy, "direction": 0, "recipe": "accumulator" if acc else "electronic-circuit"})
        req = {"iron-plate": 20, "battery": 50} if acc else {"iron-plate": 20, "copper-cable": 60}
        e += [{"name": "requester-chest", "x": cx - 3, "y": cy, "req": req}, {"name": "bulk-inserter", "x": cx - 2, "y": cy, "direction": 12},
              {"name": "bulk-inserter", "x": cx + 2, "y": cy, "direction": 12}, {"name": "passive-provider-chest", "x": cx + 3, "y": cy}]
    e += [{"name": "roboport", "x": x, "y": -162} for x in (130, 150, 170)]
    return e


def place_with_requests(ents, apply):
    reqs = [(x["x"], x["y"], x.pop("req")) for x in ents if "req" in x]
    res = tools["place_entities"](json.dumps(ents), surface="fulgora", dry_run=not apply)
    print(len(ents), "entities:", res[:3000])
    if apply:
        spec = "{" + ",".join("{%s,%s,{%s}}" % (x, y, ",".join("['%s']=%d" % kv for kv in r.items())) for x, y, r in reqs) + "}"
        print(lua("local s=game.surfaces.fulgora local n=0 for _,q in pairs(" + spec + ") do local c=s.find_entities_filtered{name='requester-chest',position={q[1],q[2]},radius=0.4}[1] if c then "
                  "local secs=c.get_logistic_sections() local sec=secs.sections[1] or secs.add_section() local i=0 for name,ct in pairs(q[3]) do i=i+1 sec.set_slot(i,{value={name=name,quality='normal'},min=ct}) end n=n+1 end end rcon.print('requests set on '..n..' chests')"))


MODULES = ("local f=game.forces.player local s=game.surfaces.fulgora local put=0 local short=0 "
           "for _,e in pairs(s.find_entities_filtered{area={{104,-164},{202,-128}},force=f,type='assembling-machine'}) do local r=e.get_recipe() local inv=e.get_module_inventory() "
           "if r and inv and r.prototype.allowed_effects and r.prototype.allowed_effects.productivity then local room=#inv-inv.get_item_count() while room>0 do local got=0 "
           "for _,net in pairs(f.logistic_networks.nauvis) do if got==0 then got=net.remove_item({name='productivity-module',count=1,quality='normal'}) end end "
           "if got==0 then short=short+room break end inv.insert{name='productivity-module',count=1} put=put+1 room=room-1 end end end rcon.print('productivity modules moved from Nauvis '..put..' short '..short)")


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    if step == "unload":
        place(unload(), apply, 2)
    elif step == "recyclers":
        place(bank(REC_X, -116, "requester-chest"), apply, 4)
        if apply:
            print(lua(REQUEST))
    elif step == "yard":
        place(bank(YARD_X, -102, "storage-chest"), apply, 4)
    elif step == "ports":
        place([{"name": "roboport", "x": x, "y": y} for y in (-126, -92) for x in (130, 150, 170, 190)], apply)
    elif step == "cell":
        if apply:
            print(lua("local s=game.surfaces.fulgora local n=0 for _,e in pairs(s.find_entities_filtered{type='roboport',position={144,-144},radius=1}) do e.destroy() n=n+1 end rcon.print('roboport in the way removed '..n)"))
        place_with_requests(cell(), apply)
    elif step == "modules":
        print(lua(MODULES))
    elif step == "robots":
        print(lua(ROBOTS % int(sys.argv[2])))


if __name__ == "__main__":
    main()
