#!/usr/bin/env python3
"""Gleba Wheel: a stationary asteroid factory in Gleba orbit (the Captain, 2026-11-13: a zero-waste space wagon wheel that makes space
science and the Nauvis packs from asteroids and drops them to the Gleba labs; stone comes up by rocket).

Stage 1 (this script): the frame and the asteroid stage, to measure real chunk income before the pack lines are sized.
  rim      a square ring, outer collector row at 34 tiles from the centre: 15 collectors a side facing outward, an inserter behind each
           onto the rim belt (row 30), which runs from both corners to the middle of the side and down the spoke
  spokes   four belts to the inner loop (a closed belt at 10 tiles round the hub); every chunk passes every crusher
  hub      two crushers a side between loop and hub (3 metallic, 3 carbonic, 2 oxide): filtered inserter in, products straight into the hub,
           the returned chunk back onto the loop. Nothing is thrown overboard: a full hub backs the belts up and the collectors stop.
  defence  an ammunition loop (row 29) all round the ring, fed from the hub up the north spoke, six gun turrets a side
  power    48 solar panels along the spokes, substations round the ring, on the spokes and at the hub
Coordinates are tiles; everything is written for the north side and turned three times.
Runs on every wheel in scripts/_wheels.py (Gleba Wheel, Nauvis Wheel); --only gleba|nauvis for one. Never run `build --apply` twice on
the same wheel: on a platform an identical entity is stacked a second time.
RETIRED LAYOUT: the square centre below (ring of 56 collectors, crushers against the hub) was removed from both wheels on 2026-11-13;
nothing reaches the inside of the round rim, so those collectors caught nothing. scripts/wheel_hub.py builds the round centre instead and
reuses the constants here. Still in use from this file: create and status.
Usage: wheel.py create | status  [--only PLANET]"""
import json
import sys

from _game import tools
from _wheels import create, lay_foundation, place_all, wheels

Q = {"quality": "rare"}
N, E, S, W = 0, 4, 8, 12
ents, tiles, cfg, recipes = [], set(), [], []          # cfg: (x, y, [filters]); recipes: (x, y, recipe)


def turn(tx, ty, w, h, d, k):
    for _ in range(k):
        tx, ty, w, h, d = -(ty + h), tx, h, w, (d + 4) % 16
    return tx, ty, w, h, d


def put(k, name, tx, ty, w=1, h=1, d=N, filt=None, recipe=None, **kw):
    tx, ty, w, h, d = turn(tx, ty, w, h, d, k)
    e = {"name": name, "x": tx + w / 2, "y": ty + h / 2, "direction": d, "params": dict(Q)}
    if "type" in kw:                                 # underground belt end: create_entity wants it among the extra arguments
        e["params"]["type"] = kw.pop("type")
    e.update(kw)
    ents.append(e)
    if filt:
        cfg.append((e["x"], e["y"], filt))
    if recipe:
        recipes.append((e["x"], e["y"], recipe))


def found(k, x0, y0, x1, y1):
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            tx, ty, _, _, _ = turn(x, y, 1, 1, 0, k)
            tiles.add((tx, ty))


CHUNKS = ["metallic-asteroid-chunk", "carbonic-asteroid-chunk", "oxide-asteroid-chunk"]
CRUSH = {"metallic": ("advanced-metallic-asteroid-crushing", "metallic-asteroid-chunk", ["iron-ore", "copper-ore"]),
         "carbonic": ("advanced-carbonic-asteroid-crushing", "carbonic-asteroid-chunk", ["carbon", "sulfur"]),
         "oxide": ("advanced-oxide-asteroid-crushing", "oxide-asteroid-chunk", ["ice", "calcite"])}
SIDES = [("metallic", "carbonic"), ("oxide", "metallic"), ("carbonic", "oxide"), ("metallic", "carbonic")]


def side(k):
    found(k, -34, -33, 33, -26)                      # ring band (the collectors' front row -34 stays open space)
    found(k, -11, -25, 11, -11)                      # spoke band
    for i in range(15):                              # collectors and their inserters
        tx = -29 + 4 * i
        if i == 7:                                   # the middle one made way for the outer ring's spoke
            continue
        put(k, "asteroid-collector", tx, -34, 3, 3, N)
        put(k, "fast-inserter", tx + 1, -31, d=N)
    for x in range(-29, 0):                          # rim belt to the middle, then the spoke
        put(k, "express-transport-belt", x, -30, d=E)
    for x in range(1, 30):
        put(k, "express-transport-belt", x, -30, d=W)
    for y in range(-30, -10):
        put(k, "express-transport-belt", 0, y, d=S)
    for x in range(-10, 9):                          # inner loop, this side's part
        put(k, "express-transport-belt", x, -10, d=E)
    for (tx, kind) in zip((-3, 1), SIDES[k]):        # two crushers
        rec, chunk, prods = CRUSH[kind]
        put(k, "crusher", tx, -8, 2, 3, N, recipe=rec)
        put(k, "fast-inserter", tx, -9, d=N, filt=[chunk])
        put(k, "fast-inserter", tx + 1, -9, d=S, filt=CHUNKS)
        put(k, "fast-inserter", tx, -5, d=N, filt=prods)
    for tx in (-24, -14, -6, 6, 14, 22):             # laser turrets, only where asteroids can hurt (Gleba); the first build had gun turrets on a belt loop
        put(k, "laser-turret", tx, -27, 2, 2, N)
    # no substations: a space platform powers everything standing on it (the Captain, 2026-11-13)
    for tx in (-10, -6, 5, 9):                       # solar
        for ty in (-25, -22, -19, -16):
            if not (tx == -6 and ty == -19):         # the spoke substation stands at -3..-2, keep its neighbour clear
                put(k, "solar-panel", tx, ty, 3, 3)


def layout():
    for x in range(-11, 11):
        for y in range(-11, 11):
            tiles.add((x, y))
    for k in range(4):
        side(k)
    for k in range(4):                               # a collector needs open space on its front row and three rows ahead: no ring foundation there
        for i in range(15):
            for x in range(-29 + 4 * i, -26 + 4 * i):
                for y in range(-37, -33):
                    tx, ty, _, _, _ = turn(x, y, 1, 1, 0, k)
                    tiles.discard((tx, ty))


CONFIG = ("local s=game.surfaces['SURF'] local n,r=0,0 for _,q in pairs(FILT) do local i=s.find_entities_filtered{type='inserter',position={q[1],q[2]},radius=0.3}[1] if i then i.use_filters=true i.inserter_filter_mode='whitelist' "
          "for k,name in pairs(q[3]) do i.set_filter(k,name) end n=n+1 end end for _,q in pairs(REC) do local m=s.find_entities_filtered{name='crusher',position={q[1],q[2]},radius=0.5}[1] if m then m.set_recipe(q[3]) r=r+1 end end "
          "rcon.print('inserters filtered '..n..', crusher recipes '..r)")
STATUS = ("local f=game.forces.player local p for i,q in pairs(f.platforms) do if q.name=='NAME' then p=q end end local s=p.surface local st=f.get_item_production_statistics(s) local o={} "
          "for _,n in pairs{'iron-ore','carbon','ice','metallic-asteroid-chunk','carbonic-asteroid-chunk','oxide-asteroid-chunk'} do o[#o+1]=n..' made '..string.format('%.1f',st.get_flow_count{name=n,category='input',precision_index=defines.flow_precision_index.ten_minutes})"
          "..' used '..string.format('%.1f',st.get_flow_count{name=n,category='output',precision_index=defines.flow_precision_index.ten_minutes}) end "
          "local inv=p.hub.get_inventory(defines.inventory.hub_main) local c={} for _,it in pairs(inv.get_contents()) do c[#c+1]=it.name..' '..it.count end o[#o+1]='hub ('..inv.count_empty_stacks()..' free): '..table.concat(c,', ') "
          "local held=0 for _,e in pairs(s.find_entities_filtered{name='asteroid-collector'}) do held=held+e.get_output_inventory().get_item_count() end local onbelt=0 local ch={0,0,0} local nm={'metallic-asteroid-chunk','carbonic-asteroid-chunk','oxide-asteroid-chunk'} "
          "for _,b in pairs(s.find_entities_filtered{type='transport-belt'}) do for l=1,2 do local tl=b.get_transport_line(l) onbelt=onbelt+tl.get_item_count() for k=1,3 do ch[k]=ch[k]+tl.get_item_count(nm[k]) end end end "
          "o[#o+1]='chunks waiting on belts: metallic '..ch[1]..' carbonic '..ch[2]..' oxide '..ch[3]..' at tick '..game.tick "
          "local armed,tur=0,0 for _,t in pairs(s.find_entities_filtered{type='ammo-turret'}) do tur=tur+1 if t.get_inventory(defines.inventory.turret_ammo).get_item_count()>0 then armed=armed+1 end end "
          "local dmg=0 for _,e in pairs(s.find_entities_filtered{force=f}) do if e.health and e.max_health and e.health<e.max_health then dmg=dmg+1 end end "
          "local ac,acap=0,0 for _,a in pairs(s.find_entities_filtered{name='accumulator'}) do ac=ac+a.energy acap=acap+a.electric_buffer_size end local use,make=ac/60,acap/60 "
          "o[#o+1]='chunks held in collectors '..held..', items on belts '..onbelt..', turrets armed '..armed..'/'..tur..', lasers '..s.count_entities_filtered{name='laser-turret'}..', damaged '..dmg..', ghosts '..s.count_entities_filtered{type='entity-ghost'}..string.format(', accumulators %.0f of %.0f MJ',use*60/1e6,make*60/1e6)..', asteroids near '..s.count_entities_filtered{type='asteroid'} "
          "rcon.print(table.concat(o,' | '))")


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    layout()
    for name, planet, surface, turrets in wheels():
        print("==", name, surface or "(not created)")
        if step == "create":
            print(create(name, planet))
            continue
        if not surface:
            continue
        mine = [e for e in ents if turrets or e["name"] != "laser-turret"]
        if step == "build":
            sys.exit("the square first centre is retired (removed on both wheels 2026-11-13): build a wheel with wheel.py create, wheel_round.py found + build, wheel_power.py, wheel_hub.py build + config, wheel_lights.py")
            if apply:
                print("foundation tiles", lay_foundation(tiles, surface))
            ok, bad = place_all(mine, surface, apply)
            print("placed" if apply else "dry run", ok, "failed", bad)
        elif step == "config":
            filt = "{" + ",".join("{%s,%s,{%s}}" % (x, y, ",".join("'%s'" % f for f in fl)) for x, y, fl in cfg) + "}"
            rec = "{" + ",".join("{%s,%s,'%s'}" % r for r in recipes) + "}"
            print(tools["run_lua"](CONFIG.replace("SURF", surface).replace("FILT", filt).replace("REC", rec)))
        elif step == "status":
            print(tools["run_lua"](STATUS.replace("NAME", name)).replace(" | ", "\n"))


if __name__ == "__main__":
    main()
