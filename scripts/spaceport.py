#!/usr/bin/env python3
"""The standard spaceport (the Captain, 2026-11-16: "a standardized space port area for each planet: lots of storage, the landing pad, launch pad,
drone ports connected to the logistics network, rocket part inputs ... make it a standard unit"). Choices made with the Captain: a NEW block on free
ground with the planet's one landing pad moved into it, and 4 rocket silos. Sized with headroom (expand-with-headroom rule), not to today's need.

One block, 60 x 44 tiles, the same on every planet (offsets from the top-left tile):
  y  0-10   4 rocket silos (9 x 9) at x 2, 16, 30, 44; under each: 3 bulk inserters (y 9) fed by 3 requester chests (y 10) asking for
            low density structure, processing units and rocket fuel, PARTS of each (10 rockets' worth: the rocket part is 1 + 1 + 1)
  y 14-33   storage fields, 10 x 20 storage chests on each side (x 2-11 and x 48-57): 400 chests
  y 16-31   the landing pad (8 x 8 at x 26, y 20) with 24 cargo bays (4 x 4) in three columns on each side (x 14, 18, 22 and x 34, 38, 42)
  y 37-40   4 roboports at x 6, 22, 34, 50, and 3 more between the silos (x 11, 25, 39, y 3): they join the planet's logistic network when the site touches its coverage
  substations at (15,11), (43,11), (15,33), (43,33): legendary supply reaches the whole block
Built: Vulcanus at (-43,-135) on 2026-11-16 (odd origin, so its pad sits at tiles -16..-9 and the bays were placed by hand on the snapped grid).
Also built 2026-11-16: Gleba at (58,-66) and Nauvis at (-344,-194), both even origins, 24 bays, pad moved in (lattice pieces in the way were removed with power checks).
Aquilo is NOT covered by this layout: everything there needs heat pipes and ice platform under it. It gets its own variant, built last and by hand.

Steps (read-only unless --apply):
  plan PLANET                 find the nearest free 62 x 46 rectangle that touches the pad's logistic network; dry-run the block there
  build PLANET X Y [--apply]  place the block WITHOUT the pad at top-left tile (X, Y), set the chest requests, chart the area
  status PLANET X Y           what stands, power, logistic network, silo state
  wall-floor PLANET X Y       the Captain's style for containerized blocks: a legendary stone-wall ring one tile outside the block and striped floor
                              (refined hazard concrete) as TILE GHOSTS under it: robots lay it from stock, nothing is spawned
  --variant compact           the 44 x 34 block (Fulgora); give it on every step for that site
  move-pad PLANET X Y [--apply]   move the landing pad into the block: copies its request sections and inventory, removes the old pad and its bays.
                              Circuit wires on the old pad are re-attached to the new one (script wires, any distance). Bays only attach to a pad that stands, so run `build --apply` again after the move to fill in the bays.
Usage: scripts/spaceport.py plan vulcanus | build vulcanus X Y --apply | status vulcanus X Y | move-pad vulcanus X Y --apply"""
import json
import sys

from _game import tools

W, H = 60, 44
Q = {"quality": "legendary"}
PARTS = 500                      # each requester chest: 10 rockets' worth of one ingredient
SILOS_X = (2, 16, 30, 44)
STORAGE = [(2, 14, 10, 20), (48, 14, 10, 20)]            # (x0, y0, columns, rows) of storage chests
CHESTS = [(3, {"low-density-structure": 500}), (4, {"processing-unit": 500}), (5, {"rocket-fuel": 500})]   # under each silo: (x offset, requests); an inserter above each
HEAT = []                                                # heat-pipe tiles (Aquilo variant only)
BAYS = [(x, y) for x in (14, 18, 22, 34, 38, 42) for y in (16, 20, 24, 28)]      # 24 bays: 80 + 24 x 50 = 1,280 slots (16 gave 880, less than Gleba's old pad had)
PAD = (26, 20)
ROBOPORTS = [(6, 37), (22, 37), (34, 37), (50, 37), (11, 3), (25, 3), (39, 3)]      # south row + three in the gaps between the silos (the south row's range stops short of the part chests)
SUBS = ((15, 11), (43, 11), (15, 33), (43, 33))
PART_ITEMS = ("low-density-structure", "processing-unit", "rocket-fuel")
L = tools["run_lua"]


def use_variant(name):
    """compact (2026-11-16, Fulgora: the only free 60 x 44 ground is the accumulator field): 44 x 34, the four silos two tiles apart, 28 bays around the
    pad (1,480 slots), 128 storage chests, roboports in one south row. Same parts, same wiring, less storage."""
    global W, H, SILOS_X, BAYS, PAD, ROBOPORTS, SUBS, STORAGE, CHESTS, HEAT
    if name == "aquilo":
        # 48 x 30 (2026-11-16, the Captain: "carefully"): the only free ground is the east end of the prepared south area. What freezes there: silos (300 kW),
        # roboports (300 kW), inserters (50 kW); pad, bays, chests, substations and walls do not. So: two inserters a silo, each beside a heat pipe, a heat line
        # under the silos (y 11) and above the roboports (y 24), joined at both ends, fed through the gap between silos 2 and 3 (x 23) from the base's hot pipes.
        W, H = 48, 30
        SILOS_X = (3, 14, 25, 36)
        CHESTS = [(3, {"low-density-structure": 500, "processing-unit": 250}), (5, {"rocket-fuel": 500, "processing-unit": 250})]
        BAYS = [(x, y) for x in (8, 12, 16, 28, 32, 36) for y in (12, 16, 20)]
        PAD = (20, 14)
        STORAGE = [(2, 12, 4, 12), (42, 12, 4, 12)]
        ROBOPORTS = [(6, 25), (16, 25), (28, 25), (38, 25)]
        SUBS = ((12, 9), (34, 9), (12, 26), (34, 26))
        HEAT = ([(sx + d, y) for sx in SILOS_X for d in (2, 4, 6) for y in (9, 10)] + [(x, 11) for x in range(48)] + [(x, 24) for x in range(48)]
                + [(x, y) for x in (0, 47) for y in range(12, 24)] + [(23, y) for y in range(0, 11)])
        return
    if name == "compact":
        W, H = 44, 34
        SILOS_X = (1, 12, 23, 34)
        BAYS = [(x, y) for x in (6, 10, 14, 26, 30, 34) for y in (12, 16, 20, 24)] + [(18, 12), (22, 12), (18, 24), (22, 24)]
        PAD = (18, 16)
        STORAGE = [(1, 12, 4, 16), (39, 12, 4, 16)]
        ROBOPORTS = [(4, 29), (14, 29), (26, 29), (36, 29)]
        SUBS = ((10, 9), (32, 9), (9, 28), (33, 28))
    if name not in ("standard", "compact"):
        sys.exit("variants: standard, compact")


def lua(code, planet, ox, oy):
    """Fill a Lua template with the site and the current variant's numbers."""
    spec = ",".join("{%d,{%s}}" % (dx, ",".join("{'%s',%d}" % kv for kv in req.items())) for dx, req in CHESTS)
    code = code.replace("CHESTSPEC", spec)
    return L(code.replace("SILOSX", ",".join(str(x) for x in SILOS_X)).replace("WW", str(W)).replace("HH", str(H)).replace("PCX", str(PAD[0] + 4)).replace("PCY", str(PAD[1] + 4))
             .replace("NBAYS", str(len(BAYS))).replace("SURFACE", planet).replace("OX", str(ox)).replace("OY", str(oy)).replace("PARTSN", str(PARTS)))


WALL_FLOOR = ("local s=game.surfaces['SURFACE'] local f=game.forces.player local ox,oy=OX,OY local n,m,k=0,0,0 "
              "for x=ox-1,ox+WW do for _,y in pairs({oy-1,oy+HH}) do if s.can_place_entity{name='stone-wall',position={x+0.5,y+0.5},force=f,build_check_type=defines.build_check_type.manual} then s.create_entity{name='stone-wall',position={x+0.5,y+0.5},force=f,quality='legendary',raise_built=true} n=n+1 else m=m+1 end end end "
              "for y=oy,oy+HH-1 do for _,x in pairs({ox-1,ox+WW}) do if s.can_place_entity{name='stone-wall',position={x+0.5,y+0.5},force=f,build_check_type=defines.build_check_type.manual} then s.create_entity{name='stone-wall',position={x+0.5,y+0.5},force=f,quality='legendary',raise_built=true} n=n+1 else m=m+1 end end end "
              "for x=ox,ox+WW-1 do for y=oy,oy+HH-1 do local t=s.get_tile(x,y) if not t.name:find('refined%-hazard%-concrete') and #s.find_entities_filtered{type='tile-ghost',position={x+0.5,y+0.5},radius=0.3}==0 then "
              "if s.create_entity{name='tile-ghost',inner_name='refined-hazard-concrete-left',position={x+0.5,y+0.5},force=f} then k=k+1 end end end end "
              "rcon.print('walls placed '..n..' (blocked or already there '..m..'), striped floor ghosts laid '..k)")


def ent(name, tx, ty, w, h, d=0):
    return {"name": name, "x": tx + w / 2, "y": ty + h / 2, "direction": d, "params": dict(Q)}


def layout(ox, oy, pad=False):
    out = []
    for sx in SILOS_X:
        out.append(ent("rocket-silo", ox + sx, oy, 9, 9))
        for dx, _ in CHESTS:
            out.append(ent("bulk-inserter", ox + sx + dx, oy + 9, 1, 1, 8))             # direction = the side it picks from (south: the chest)
            out.append(ent("requester-chest", ox + sx + dx, oy + 10, 1, 1))
    for hx, hy in HEAT:
        out.append(ent("heat-pipe", ox + hx, oy + hy, 1, 1))
    for bx, by in BAYS:
        out.append(ent("cargo-bay", ox + bx, oy + by, 4, 4))
    for x0, y0, cols, rows in STORAGE:
        for cx in range(cols):
            for cy in range(rows):
                out.append(ent("storage-chest", ox + x0 + cx, oy + y0 + cy, 1, 1))
    for rx, ry in ROBOPORTS:
        out.append(ent("roboport", ox + rx, oy + ry, 4, 4))
    for sx, sy in SUBS:
        out.append(ent("substation", ox + sx, oy + sy, 2, 2))
    if pad:
        out.append(ent("cargo-landing-pad", ox + PAD[0], oy + PAD[1], 8, 8))
    return out


def place(planet, ox, oy, apply):
    ents = layout(ox, oy)
    done, failed = 0, []
    for i in range(0, len(ents), 250):
        r = json.loads(tools["place_entities"](json.dumps(ents[i:i + 250]), surface=planet, dry_run=not apply, clear_trees=apply))
        done += r.get("placed") or 0
        failed += r.get("failed") or []
    return len(ents), done, failed


FIND = ("local s=game.surfaces['%s'] local f=game.forces.player local pad=s.find_entities_filtered{type='cargo-landing-pad',force=f}[1] local px,py=math.floor(pad.position.x),math.floor(pad.position.y) "
        "local net=s.find_logistic_network_by_position(pad.position,f) local W,H=62,46 local best={} for dx=-200,200,4 do for dy=-200,200,4 do local x,y=px+dx,py+dy local a={{x,y},{x+W,y+H}} "
        "if s.count_entities_filtered{area=a,type={'tree','simple-entity','resource','fish','logistic-robot','construction-robot'},invert=true}==0 and s.count_tiles_filtered{area=a,collision_mask='water_tile'}==0 and s.count_tiles_filtered{area=a,collision_mask='lava_tile'}==0 then local inside=0 "
        "for _,c in pairs({{x+1,y+1},{x+W-1,y+1},{x+1,y+H-1},{x+W-1,y+H-1},{x+W/2,y+H/2}}) do local n=s.find_logistic_network_by_position(c,f) if n and net and n.network_id==net.network_id then inside=inside+1 end end "
        "if inside>=1 then best[#best+1]={d=math.abs(dx+W/2)+math.abs(dy+H/2),x=x,y=y,i=inside} end end end end table.sort(best,function(a,b) return a.d<b.d end) local o={'pad '..px..','..py..' candidates '..#best} "
        "for i=1,math.min(5,#best) do o[#o+1]=(best[i].x+1)..' '..(best[i].y+1)..' dist '..best[i].d..' corners in network '..best[i].i end rcon.print(table.concat(o,';'))")

CONFIG = ("local s=game.surfaces['SURFACE'] local f=game.forces.player local ox,oy=OX,OY local n,m=0,0 "
          "for _,sx in pairs({SILOSX}) do for _,cs in pairs({CHESTSPEC}) do local c=s.find_entities_filtered{name='requester-chest',position={ox+sx+cs[1]+0.5,oy+10.5},radius=0.4}[1] if c then local pt=c.get_logistic_point(defines.logistic_member_index.logistic_container) "
          "for i=#pt.sections,1,-1 do pt.remove_section(i) end local sec=pt.add_section() for k,it in ipairs(cs[2]) do sec.set_slot(k,{value={type='item',name=it[1],quality='normal'},min=it[2]}) end n=n+1 end end "
          "local si=s.find_entities_filtered{type='rocket-silo',position={ox+sx+4.5,oy+4.5},radius=1}[1] if si then pcall(function() si.use_transitional_requests=true end) m=m+1 end end "
          "f.chart(s,{{ox-8,oy-8},{ox+WW+8,oy+HH+8}}) rcon.print('requester chests set '..n..', silos '..m)")

STATUS = ("local s=game.surfaces['SURFACE'] local f=game.forces.player local ox,oy=OX,OY local A={{ox,oy},{ox+WW,oy+HH}} local m={} for k,v in pairs(defines.entity_status) do m[v]=k end local c={} "
          "for _,e in pairs(s.find_entities_filtered{area=A,force=f}) do if e.type~='logistic-robot' and e.type~='construction-robot' then local k=e.name..' '..tostring(m[e.status] or '-') c[k]=(c[k] or 0)+1 end end "
          "local o={} for k,v in pairs(c) do o[#o+1]=k..' x'..v end table.sort(o) local pad=s.find_entities_filtered{type='cargo-landing-pad',force=f}[1] local net=s.find_logistic_network_by_position(pad.position,f) "
          "local rp=s.find_entities_filtered{type='roboport',area=A,force=f} local same=0 for _,r in pairs(rp) do local n=s.find_logistic_network_by_position(r.position,f) if n and net and n.network_id==net.network_id then same=same+1 end end "
          "local sub=s.find_entities_filtered{name='substation',area=A,force=f} local pole=s.find_entities_filtered{type='electric-pole',position=pad.position,radius=30,force=f}[1] local conn=0 "
          "for _,x in pairs(sub) do if pole and x.electric_network_id==pole.electric_network_id then conn=conn+1 end end "
          "rcon.print(table.concat(o,'\\n')..'\\nroboports in the pad network '..same..' of '..#rp..' | substations on the main grid '..conn..' of '..#sub..' | pad at '..pad.position.x..','..pad.position.y..' slots '..#pad.get_inventory(defines.inventory.cargo_landing_pad_main))")

MOVE = ("local s=game.surfaces['SURFACE'] local f=game.forces.player local ox,oy=OX,OY local APPLY=APPLYFLAG local W=defines.wire_connector_id local old=s.find_entities_filtered{type='cargo-landing-pad',force=f}[1] "
        "local np={ox+PCX,oy+PCY} if math.abs(old.position.x-np[1])<1 and math.abs(old.position.y-np[2])<1 then rcon.print('the pad already stands in the block') return end "
        "local wires={} for _,id in pairs({W.circuit_red,W.circuit_green}) do for _,cn in pairs(old.get_wire_connector(id,true).connections) do wires[#wires+1]={id=id,ent=cn.target.owner,tid=cn.target.wire_connector_id} end end "
        "if s.count_entities_filtered{area={{ox+PCX-3.9,oy+PCY-3.9},{ox+PCX+3.9,oy+PCY+3.9}},type={'resource','logistic-robot','construction-robot','fish'},invert=true}>0 then rcon.print('REFUSED: the pad site is not empty') return end "
        "local inv=old.get_inventory(defines.inventory.cargo_landing_pad_main) local items={} local stacks=0 for _,i in pairs(inv.get_contents()) do items[#items+1]=i stacks=stacks+math.ceil(i.count/prototypes.item[i.name].stack_size) end "
        "local secs={} for _,pt in pairs(old.get_logistic_point()) do if pt.mode==defines.logistic_mode.requester then for _,sec in pairs(pt.sections) do local sl={} for i,fl in pairs(sec.filters) do if fl.value then sl[#sl+1]={value=fl.value,min=fl.min,max=fl.max,import_from=fl.import_from and fl.import_from.name,minimum_delivery_count=fl.minimum_delivery_count} end end "
        "secs[#secs+1]={group=sec.group,active=sec.active,mult=sec.multiplier,slots=sl} end end end local oldbays=s.find_entities_filtered{name='cargo-bay',force=f} local ob=0 for _,b in pairs(oldbays) do if not (b.position.x>ox and b.position.x<ox+WW and b.position.y>oy and b.position.y<oy+HH) then ob=ob+1 end end "
        "if stacks>80+50*NBAYS then rcon.print('REFUSED: the old pad holds '..stacks..' stacks, more than the new one') return end "
        "if not APPLY then rcon.print('dry run: would move '..#items..' item kinds ('..stacks..' stacks), '..#secs..' request sections, re-attach '..#wires..' circuit wires, and remove the old pad and '..ob..' old bays') return end "
        "local q=old.quality.name old.destroy() for _,b in pairs(oldbays) do if b.valid and not (b.position.x>ox and b.position.x<ox+WW and b.position.y>oy and b.position.y<oy+HH) then b.destroy() end end "
        "local pad=s.create_entity{name='cargo-landing-pad',position=np,force=f,quality=q,raise_built=true} if not pad then rcon.print('FAILED to place the new pad: reload the save') return end "
        "local ni=pad.get_inventory(defines.inventory.cargo_landing_pad_main) local lost=0 for _,i in pairs(items) do local ins=ni.insert{name=i.name,count=i.count,quality=i.quality} lost=lost+(i.count-ins) end "
        "local done=0 for _,pt in pairs(pad.get_logistic_point()) do if pt.mode==defines.logistic_mode.requester then for i=#pt.sections,1,-1 do pt.remove_section(i) end for _,sc in ipairs(secs) do local sec=(sc.group and sc.group~='') and pt.add_section(sc.group) or pt.add_section() "
        "if sec then for k,sl in ipairs(sc.slots) do pcall(function() sec.set_slot(k,sl) end) end sec.active=sc.active if sc.mult then sec.multiplier=sc.mult end done=done+1 end end end end "
        "local rw=0 for _,w in ipairs(wires) do if w.ent.valid then pad.get_wire_connector(w.id,true).connect_to(w.ent.get_wire_connector(w.tid,true),false,defines.wire_origin.script) rw=rw+1 end end "
        "rcon.print('circuit wires re-attached '..rw..' | pad moved to '..np[1]..','..np[2]..': slots '..#ni..', item kinds '..#items..' (lost '..lost..'), sections restored '..done..' of '..#secs..', old bays removed '..ob)")


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        sys.exit(__doc__)
    step, planet = a[0], a[1]
    if "--variant" in a:
        use_variant(a[a.index("--variant") + 1])
    if planet == "aquilo" and "--variant" not in a:
        sys.exit("Aquilo: give --variant aquilo (heat pipes; build it by the careful steps in the docstring)")
    if step == "plan":
        res = L(FIND % planet)
        print(res.replace(";", "\n"))
        parts = res.split(";")
        if len(parts) > 1:
            x, y = (int(v) for v in parts[1].split()[:2])
            x, y = x + x % 2, y + y % 2                       # even origin (pad and bays snap to a 2-tile grid); the search box has a 1-tile margin
            n, done, failed = place(planet, x, y, False)
            print("dry run at %d %d: %d entities, would place %d, failed %s" % (x, y, n, done, json.dumps(failed)[:400]))
        return
    ox, oy = int(a[2]), int(a[3])
    if step == "build" and (ox % 2 or oy % 2) and "--odd-ok" not in a:
        sys.exit("the top-left tile must be EVEN in x and y: the landing pad and cargo bays snap to a 2-tile grid (found on Vulcanus, 2026-11-16: an odd origin shifted them one tile and only 4 of 16 bays fitted)")
    apply = "--apply" in a
    if step == "build":
        if apply:
            print("save:", tools["save_game"]("pre-spaceport-" + planet))
        n, done, failed = place(planet, ox, oy, apply)
        print(("placed" if apply else "dry run:"), done, "of", n, "failed", json.dumps(failed)[:600])
        if apply:
            print(lua(CONFIG, planet, ox, oy))
    elif step == "status":
        print(lua(STATUS, planet, ox, oy))
    elif step == "move-pad":
        if apply:
            print("save:", tools["save_game"]("pre-padmove-" + planet))
        print(lua(MOVE.replace("APPLYFLAG", "true" if apply else "false"), planet, ox, oy))
    elif step == "wall-floor":
        print(lua(WALL_FLOOR, planet, ox, oy))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
