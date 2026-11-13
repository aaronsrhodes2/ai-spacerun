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
Usage: wheel.py create | build [--apply] | outer [--apply] | config | arm | stock | status"""
import json
import sys

from _game import tools

NAME = "Gleba Wheel"
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
    for x in range(-29, 28):                         # ammunition loop, with a hop under the spoke
        if x == -1:
            put(k, "express-underground-belt", x, -29, d=E, type="input")
        elif x == 1:
            put(k, "express-underground-belt", x, -29, d=E, type="output")
        elif x != 0:
            put(k, "express-transport-belt", x, -29, d=E)
    for tx in (-24, -14, -6, 6, 14, 22):             # gun turrets
        put(k, "gun-turret", tx, -27, 2, 2, N)
        put(k, "fast-inserter", tx, -28, d=N, filt=["firearm-magazine"])
    # no substations: a space platform powers everything standing on it (the Captain, 2026-11-13)
    for tx in (-10, -6, 5, 9):                       # solar
        for ty in (-25, -22, -19, -16):
            if not (tx == -6 and ty == -19):         # the spoke substation stands at -3..-2, keep its neighbour clear
                put(k, "solar-panel", tx, ty, 3, 3)
    if k == 0:                                       # ammunition feed from the hub, north spoke only
        put(k, "fast-inserter", 3, -5, d=S, filt=["firearm-magazine"])
        for y in (-6, -7, -8):
            put(k, "express-transport-belt", 3, y, d=N)
        put(k, "express-underground-belt", 3, -9, d=N, type="input")
        put(k, "express-underground-belt", 3, -11, d=N, type="output")
        for y in range(-12, -29, -1):
            put(k, "express-transport-belt", 3, y, d=N)


R2 = 130                                             # outer ring: collector row 130 tiles out, grabbers 20 tiles apart (the Captain: bigger, spread out)


def outer(k):
    R = R2
    found(k, -R, -(R - 1), R - 1, -(R - 8))          # ring band
    found(k, -3, -(R - 9), 9, -34)                   # spoke band, wide enough for a row of panels
    for tx in range(-110, 111, 20):
        put(k, "asteroid-collector", tx, -R, 3, 3, N)
        put(k, "fast-inserter", tx + 1, -(R - 3), d=N)
    for x in range(-(R - 5), 0):
        put(k, "express-transport-belt", x, -(R - 4), d=E)
    for x in range(1, R - 4):
        put(k, "express-transport-belt", x, -(R - 4), d=W)
    for y in range(-(R - 4), -30):                   # outer spoke, through the inner ring where its middle collector stood
        put(k, "express-transport-belt", 0, y, d=S)
    for x in range(-(R - 5), R - 6):                 # ammunition loop
        if x == -1:
            put(k, "express-underground-belt", x, -(R - 5), d=E, type="input")
        elif x == 1:
            put(k, "express-underground-belt", x, -(R - 5), d=E, type="output")
        elif x != 0:
            put(k, "express-transport-belt", x, -(R - 5), d=E)
    for tx in range(-100, 101, 20):
        if tx != 0:                                  # the spoke runs there
            put(k, "gun-turret", tx, -(R - 7), 2, 2, N)
            put(k, "fast-inserter", tx, -(R - 6), d=N, filt=["firearm-magazine"])
    for tx in range(-116, 105, 20):
        put(k, "substation", tx, -(R - 7), 2, 2)
    for ty in (-112, -94, -76, -58, -40):
        put(k, "substation", 4, ty, 2, 2)
    for ty in range(-118, -36, 3):
        put(k, "solar-panel", 6, ty, 3, 3)
    if k == 0:                                       # ammunition for the outer loop: hub -> x -1 -> under the inner loop -> x -2 -> under the inner ring's belts -> north
        put(k, "fast-inserter", -1, -5, d=S, filt=["firearm-magazine"])
        for y in (-6, -7, -8):
            put(k, "express-transport-belt", -1, y, d=N)
        put(k, "express-underground-belt", -1, -9, d=N, type="input")
        put(k, "express-underground-belt", -1, -11, d=N, type="output")
        for y in range(-12, -28, -1):
            put(k, "express-transport-belt", -1, y, d=N)
        put(k, "express-transport-belt", -1, -28, d=W)
        put(k, "express-underground-belt", -2, -28, d=N, type="input")
        put(k, "express-underground-belt", -2, -31, d=N, type="output")
        for y in range(-32, -(R - 5), -1):
            put(k, "express-transport-belt", -2, y, d=N)


def layout_outer():
    for k in range(4):
        outer(k)


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


ARM = ("local f=game.forces.player local s=game.surfaces['SURF'] local p for i,q in pairs(f.platforms) do if q.surface==s then p=q end end local hub=p.hub.get_inventory(defines.inventory.hub_main) local n,a=0,0 "
       "for _,t in pairs(s.find_entities_filtered{type='ammo-turret'}) do local inv=t.get_inventory(defines.inventory.turret_ammo) local need=25-inv.get_item_count() if need>0 then local got=hub.remove{name='firearm-magazine',count=need} "
       "if got>0 then inv.insert{name='firearm-magazine',count=got} a=a+got end end n=n+1 end local g=0 for pass=1,3 do for _,e in pairs(s.find_entities_filtered{type='entity-ghost'}) do if e.revive() then g=g+1 end end end "
       "rcon.print('turrets '..n..', magazines handed out '..a..', ghosts revived '..g..', hub magazines left '..hub.get_item_count('firearm-magazine'))")
CREATE = ("local f=game.forces.player for i,p in pairs(f.platforms) do if p.name=='" + NAME + "' then rcon.print(i..' '..p.surface.name..' exists') return end end "
          "local p=f.create_space_platform{name='" + NAME + "',planet='gleba',starter_pack='space-platform-starter-pack'} p.apply_starter_pack() rcon.print(p.index..' '..p.surface.name..' created')")
WHERE = "local f=game.forces.player for i,p in pairs(f.platforms) do if p.name=='" + NAME + "' then rcon.print(i..' '..p.surface.name) return end end rcon.print('none')"
CONFIG = ("local s=game.surfaces['SURF'] local n,r=0,0 for _,q in pairs(FILT) do local i=s.find_entities_filtered{type='inserter',position={q[1],q[2]},radius=0.3}[1] if i then i.use_filters=true i.inserter_filter_mode='whitelist' "
          "for k,name in pairs(q[3]) do i.set_filter(k,name) end n=n+1 end end for _,q in pairs(REC) do local m=s.find_entities_filtered{name='crusher',position={q[1],q[2]},radius=0.5}[1] if m then m.set_recipe(q[3]) r=r+1 end end "
          "rcon.print('inserters filtered '..n..', crusher recipes '..r)")
STOCK = ("local f=game.forces.player local p for i,q in pairs(f.platforms) do if q.name=='" + NAME + "' then p=q end end local best,bn=nil,0 for _,net in pairs(f.logistic_networks.nauvis or {}) do if net.all_logistic_robots>bn then best=net bn=net.all_logistic_robots end end "
         "local inv=p.hub.get_inventory(defines.inventory.hub_main) local want=2000-inv.get_item_count('firearm-magazine') local got=0 if want>0 then got=best.remove_item{name='firearm-magazine',count=want} if got>0 then inv.insert{name='firearm-magazine',count=got} end end "
         "rcon.print('magazines moved from Nauvis '..got..', hub now '..inv.get_item_count('firearm-magazine'))")
STATUS = ("local f=game.forces.player local p for i,q in pairs(f.platforms) do if q.name=='" + NAME + "' then p=q end end local s=p.surface local st=f.get_item_production_statistics(s) local o={} "
          "for _,n in pairs{'iron-ore','carbon','ice','metallic-asteroid-chunk','carbonic-asteroid-chunk','oxide-asteroid-chunk'} do o[#o+1]=n..' made '..string.format('%.1f',st.get_flow_count{name=n,category='input',precision_index=defines.flow_precision_index.ten_minutes})"
          "..' used '..string.format('%.1f',st.get_flow_count{name=n,category='output',precision_index=defines.flow_precision_index.ten_minutes}) end "
          "local inv=p.hub.get_inventory(defines.inventory.hub_main) local c={} for _,it in pairs(inv.get_contents()) do c[#c+1]=it.name..' '..it.count end o[#o+1]='hub ('..inv.count_empty_stacks()..' free): '..table.concat(c,', ') "
          "local held=0 for _,e in pairs(s.find_entities_filtered{name='asteroid-collector'}) do held=held+e.get_output_inventory().get_item_count() end local onbelt=0 for _,b in pairs(s.find_entities_filtered{type='transport-belt'}) do for l=1,2 do onbelt=onbelt+b.get_transport_line(l).get_item_count() end end "
          "local armed,tur=0,0 for _,t in pairs(s.find_entities_filtered{type='ammo-turret'}) do tur=tur+1 if t.get_inventory(defines.inventory.turret_ammo).get_item_count()>0 then armed=armed+1 end end "
          "local dmg=0 for _,e in pairs(s.find_entities_filtered{force=f}) do if e.health and e.max_health and e.health<e.max_health then dmg=dmg+1 end end "
          "local ac,acap=0,0 for _,a in pairs(s.find_entities_filtered{name='accumulator'}) do ac=ac+a.energy acap=acap+a.electric_buffer_size end local use,make=ac/60,acap/60 "
          "o[#o+1]='chunks held in collectors '..held..', items on belts '..onbelt..', turrets armed '..armed..'/'..tur..', lasers '..s.count_entities_filtered{name='laser-turret'}..', damaged '..dmg..', ghosts '..s.count_entities_filtered{type='entity-ghost'}..string.format(', accumulators %.0f of %.0f MJ',use*60/1e6,make*60/1e6)..', asteroids near '..s.count_entities_filtered{type='asteroid'} "
          "rcon.print(table.concat(o,' | '))")


def lua_tiles(surface, part=None):
    want = ",".join("{%d,%d}" % t for t in (part if part is not None else sorted(tiles)))
    return ("local s=game.surfaces['%s'] local add={} for _,p in pairs({%s}) do add[#add+1]={name='space-platform-foundation',position=p} end s.set_tiles(add) rcon.print('foundation '..#add)" % (surface, want))


def main():
    step = sys.argv[1]
    if step == "create":
        print(tools["run_lua"](CREATE))
        return
    where = tools["run_lua"](WHERE).strip()
    if where == "none":
        raise SystemExit("no platform named " + NAME)
    surface = where.split()[1]
    if step == "outer":                              # only the outer ring's entities and tiles (the inner wheel already stands)
        layout_outer()
        step = "build"
    elif step == "config":
        layout()
        layout_outer()
    else:
        layout()
    apply = "--apply" in sys.argv
    if step == "build":
        print("plan: %d entities, %d foundation tiles on %s" % (len(ents), len(tiles), surface))
        if apply:
            ts = sorted(tiles)
            for i in range(0, len(ts), 4000):        # an RCON command is limited to 65,535 characters
                print(tools["run_lua"](lua_tiles(surface, ts[i:i + 4000])))
        for i in range(0, len(ents), 400):
            r = tools["place_entities"](json.dumps(ents[i:i + 400]), surface=surface, dry_run=not apply)
            print(r[:400])
    elif step == "config":
        filt = "{" + ",".join("{%s,%s,{%s}}" % (x, y, ",".join("'%s'" % f for f in fl)) for x, y, fl in cfg) + "}"
        rec = "{" + ",".join("{%s,%s,'%s'}" % r for r in recipes) + "}"
        print(tools["run_lua"](CONFIG.replace("SURF", surface).replace("FILT", filt).replace("REC", rec)))
    elif step == "arm":
        print(tools["run_lua"](ARM.replace("SURF", surface)))
    elif step == "stock":
        print(tools["run_lua"](STOCK))
    elif step == "status":
        print(tools["run_lua"](STATUS).replace(" | ", "\n"))


if __name__ == "__main__":
    main()
