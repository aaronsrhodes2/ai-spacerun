"""
Refined hazard concrete on Nauvis, made by drones (the Captain, 2026-11-14): 3,432 tile ghosts of refined-hazard-concrete-left at the
Replicator site (x -365.5..-288.5, y -233.5..-190.5) are built by the construction robots once the network holds the item.

Chain (recipes read from the game, Factorio 2.1):
    concrete               10 s  crafting-with-fluid  5 stone-brick + 1 iron-ore + 100 water        -> 10 concrete
    refined-concrete       15 s  crafting-with-fluid  20 concrete + 1 steel-plate + 8 iron-stick + 100 water -> 10 refined concrete
    refined-hazard-concrete 0.25 s crafting           10 refined-concrete                           -> 10 refined hazard concrete
  so 10 tiles = 10 refined = 20 concrete (10 bricks, 2 ore, 2000 water) + 1 steel + 8 sticks (4 plates) + 100 water; 5,000 tiles = 5,000 bricks, 1,000 ore, 500 steel.

What this builds (all drone fed: requester chest -> bulk inserter -> machine -> bulk inserter -> passive provider chest, nothing belted):
  WATER BLOCK   x -433..-394, y -191..-183, beside the lake: one offshore pump, a pipe main along y -190.5 with a drop to the east port of each
                of 8 epic assembling-machine-3 (direction east: water port east, output port west left unconnected, pitch 5). 4 make concrete, 4 refined.
  SIDE CELLS    x -390..-383, y -191..-176: 3 electric furnaces (stone brick), 1 iron-stick assembler, 1 refined-hazard-concrete assembler.
  ORE           3 electric mining drills on the Iron patch at (-362..-355, -372) each straight into a passive provider chest (iron ore is the
                one input the network lacked: 145 in stock, 1 per 10 concrete).
  Speed modules (speed-module-2, factory made, moved out of network stock) in the water machines and furnaces.

Usage: scripts/nauvis_hazard_concrete.py check | build [--apply] | status
"""
import json
import sys

import build_cells as bc
import fx
from _game import tools

from bridge.factorio.planner import batches

Q = {"quality": "epic"}
BOX = (-365.5, -233.5, -288.5, -190.5)  # the floor site
GHOST = "refined-hazard-concrete-left"

PUMP = (-437.5, -186.5)  # shore tile, faces west (water), pipe leaves east
CX0, PITCH, N_CON, N_REF = -431.5, 5, 4, 4
YC = -186.5
MAIN_Y = -190.5
SIDE_X0, SIDE_Y0 = -390, -191  # plain cells: 3 brick, 1 stick, 1 hazard
DRILLS = [(-361.5, -371.5), (-358.5, -371.5), (-355.5, -371.5)]
SUB = (-358.0, -375.0)

REQ_CON = [("stone-brick", 250), ("iron-ore", 40)]
REQ_REF = [("concrete", 600), ("steel-plate", 30), ("iron-stick", 240)]
GROUP_CON, GROUP_REF = "Hazard: Concrete", "Hazard: Refined Concrete"

bc.KINDS["hazard"] = {"machine": "assembling-machine-3", "recipe": "refined-hazard-concrete", "bar": 6, "req": [("refined-concrete", 300)]}
bc.GROUPS.update({"hazard": "Hazard: Refined Hazard Concrete", "brick": "Hazard: Stone Brick", "stick": "Hazard: Iron Stick"})
bc.KINDS["brick"] = dict(bc.KINDS["brick"], req=[("stone", 300)])
bc.KINDS["stick"] = dict(bc.KINDS["stick"], req=[("iron-plate", 400)])
SIDE = [("brick", 3), ("stick", 1), ("hazard", 1)]


def cxs():
    return [CX0 + PITCH * i for i in range(N_CON + N_REF)]


def water_block():
    e = [{"name": "offshore-pump", "x": PUMP[0], "y": PUMP[1], "direction": 12, "params": {}}]
    pipes = [(PUMP[0] + 1, y) for y in (-186.5, -187.5, -188.5, -189.5, -190.5)]
    last = cxs()[-1] + 2
    x = PUMP[0] + 2
    while x <= last:
        pipes.append((x, MAIN_Y))
        x += 1
    for cx in cxs():
        pipes += [(cx + 2, y) for y in (-189.5, -188.5, -187.5, -186.5)]
    e += [{"name": "pipe", "x": x, "y": y, "direction": 0, "params": {}} for x, y in pipes]
    for cx in cxs():
        e += [
            {"name": "requester-chest", "x": cx, "y": YC - 3, "params": {}},
            {"name": "bulk-inserter", "x": cx, "y": YC - 2, "direction": 0, "params": Q},
            {"name": "assembling-machine-3", "x": cx, "y": YC, "direction": 4, "params": Q},
            {"name": "bulk-inserter", "x": cx, "y": YC + 2, "direction": 0, "params": Q},
            {"name": "passive-provider-chest", "x": cx, "y": YC + 3, "params": {}},
        ]
    return e


def side_cells():
    ents, y = [], SIDE_Y0
    for kind, n in SIDE:
        for d in bc.plan(kind, SIDE_X0, y, n):
            if d["name"] in ("electric-furnace", "assembling-machine-3", "bulk-inserter"):
                d["params"] = Q
            ents.append(d)
        y += 3 * n
    return ents


def ore_site():
    e = [{"name": "substation", "x": SUB[0], "y": SUB[1], "direction": 0, "params": {}}]
    for x, y in DRILLS:
        e += [{"name": "electric-mining-drill", "x": x, "y": y, "direction": 0, "params": Q},
              {"name": "passive-provider-chest", "x": x, "y": y - 2, "params": {}}]
    return e


def dry(ents, surface="nauvis"):
    r = json.loads(tools["place_entities"](json.dumps(ents), surface=surface, dry_run=True))
    return r


def stock():
    return fx.lua(
        "local s=game.surfaces.nauvis local n=s.find_logistic_network_by_position({-330,-210},game.forces.player) local o={} "
        "for _,k in ipairs({'concrete','refined-concrete','hazard-concrete','refined-hazard-concrete','stone-brick','stone','steel-plate','iron-plate','iron-stick','iron-ore','speed-module-2'}) do o[#o+1]=k..'='..n.get_item_count(k) end "
        "rcon.print(table.concat(o,' '))")


def ghost_count():
    a, b, c, d = BOX
    return fx.lua("local s=game.surfaces.nauvis local n,t=0,0 for _,g in pairs(s.find_entities_filtered{area={{%s,%s},{%s,%s}},type='tile-ghost'}) do t=t+1 if g.ghost_name=='%s' then n=n+1 end end rcon.print(n..' of '..t..' tile ghosts')" % (a, b, c, d, GHOST))


def configure_water():
    cons, refs = cxs()[:N_CON], cxs()[N_CON:]
    out = []
    for xs, recipe, req, grp in ((cons, "concrete", REQ_CON, GROUP_CON), (refs, "refined-concrete", REQ_REF, GROUP_REF)):
        R = ",".join("{'%s',%d}" % r for r in req)
        X = ",".join(str(x) for x in xs)
        out.append(fx.lua(
            f"local s=game.surfaces.nauvis local R={{{R}}} local n,m=0,0 for _,cx in ipairs({{{X}}}) do "
            f"local c=s.find_entities_filtered{{name='requester-chest',position={{cx,{YC - 3}}},radius=0.4}}[1] "
            f"if c then local sec=c.get_logistic_sections().add_section() for j,r in ipairs(R) do sec.set_slot(j,{{value={{name=r[1],quality='normal'}},min=r[2]}}) end sec.group='{grp}' n=n+1 end "
            f"local e=s.find_entities_filtered{{name='assembling-machine-3',position={{cx,{YC}}},radius=0.4}}[1] "
            f"if e then e.set_recipe('{recipe}') e.direction=defines.direction.east m=m+1 end "
            f"local o=s.find_entities_filtered{{name='passive-provider-chest',position={{cx,{YC + 3}}},radius=0.4}}[1] if o then o.get_inventory(defines.inventory.chest).set_bar(9) end end "
            "rcon.print('" + recipe + " requests '..n..' machines '..m)"))
    return out


def modules():
    """Fill empty module slots of our machines with speed-module-2 taken out of the network (factory made)."""
    head = ("local s=game.surfaces.nauvis local n=s.find_logistic_network_by_position({-330,-210},game.forces.player) local t,miss=0,0 "
            "local function fill(e) local inv=e.get_module_inventory() if not inv then return end for i=1,#inv do if inv[i].count==0 then "
            "if n.get_item_count('speed-module-2')>0 and n.remove_item{name='speed-module-2',count=1}==1 then inv[i].set_stack{name='speed-module-2',count=1} t=t+1 else miss=miss+1 end end end end ")
    a = ("for _,e in pairs(s.find_entities_filtered{type='assembling-machine',area={{%s,%s},{%s,%s}}}) do fill(e) end " % (CX0 - 3, YC - 3, cxs()[-1] + 3, YC + 3))
    b = ("for _,e in pairs(s.find_entities_filtered{name='electric-furnace',area={{%s,%s},{%s,%s}}}) do fill(e) end " % (SIDE_X0, SIDE_Y0, SIDE_X0 + 7, SIDE_Y0 + 9))
    return fx.lua(head + a + b + "rcon.print('modules placed '..t..' unfilled '..miss)")


def chart():
    return fx.lua("local f=game.forces.player local s=game.surfaces.nauvis f.chart(s,{{-445,-196},{-375,-170}}) f.chart(s,{{-375,-382},{-345,-362}}) rcon.print('charted')")


def exists(name, x, y):
    return fx.lua(f"rcon.print(#game.surfaces.nauvis.find_entities_filtered{{name='{name}',position={{{x},{y}}},radius=0.6}})") != "0"


def check():
    print("stock:", stock())
    print("ghosts left:", ghost_count())
    for label, ents in (("water block", water_block()), ("side cells", side_cells()), ("ore site", ore_site())):
        r = dry(ents)
        print(label, len(ents), "entities; dry run:", {k: v for k, v in r.items() if k in ("placed", "failed")})


def build(apply):
    if not apply:
        return check()
    print(tools["save_game"]("skippy"))
    print(chart())
    parts = [("water", water_block(), exists("offshore-pump", *PUMP)), ("side", side_cells(), exists("electric-furnace", SIDE_X0 + 3.5, SIDE_Y0 + 1.5)),
             ("ore", ore_site(), exists("electric-mining-drill", *DRILLS[0]))]
    for label, ents, done in parts:
        if done:
            print(label, "already stands, skipped")
            continue
        if label == "side":
            print(bc.clear_box(SIDE_X0, SIDE_Y0, 3 + 1 + 1))
        if label == "water":
            print(fx.lua(f"local s=game.surfaces.nauvis local t=0 for _,e in pairs(s.find_entities_filtered{{area={{{{{CX0 - 4},{MAIN_Y - 1}}},{{{cxs()[-1] + 4},{YC + 4}}}}},type={{'tree','cliff','simple-entity','item-entity','corpse'}}}}) do if e.force.name~='player' then e.destroy() t=t+1 end end rcon.print('cleared '..t)"))
        if label == "ore":
            print(fx.lua("local s=game.surfaces.nauvis local t=0 for _,e in pairs(s.find_entities_filtered{area={{-364,-377},{-353,-369}},type={'tree','cliff','simple-entity','item-entity','corpse'}}) do if e.force.name~='player' then e.destroy() t=t+1 end end rcon.print('cleared '..t)"))
        for part in batches(ents):
            r = json.loads(tools["place_entities"](json.dumps(part), surface="nauvis"))
            print(label, "placed", r.get("placed"), "failed", r.get("failed"))
    for line in configure_water():
        print(line)
    y = SIDE_Y0
    for kind, n in SIDE:
        print(kind, bc.configure(kind, SIDE_X0, y, n))
        y += 3 * n
    print(modules())
    status()


def status():
    cons, refs = cxs()[:N_CON], cxs()[N_CON:]
    s = fx.lua(
        "local s=game.surfaces.nauvis local o={} local st={} for k,v in pairs(defines.entity_status) do st[v]=k end "
        "for _,e in pairs(s.find_entities_filtered{type={'assembling-machine','furnace'},area={{-440,-192},{-380,-175}}}) do local r=e.get_recipe() "
        "o[#o+1]=e.name..' '..(r and r.name or 'furnace')..' @'..e.position.x..','..e.position.y..' '..tostring(st[e.status])..' made='..e.products_finished..' speed='..string.format('%%.2f',e.crafting_speed) end "
        "for _,e in pairs(s.find_entities_filtered{name='electric-mining-drill',area={{-364,-376},{-353,-369}}}) do o[#o+1]='drill '..e.position.x..' '..tostring(st[e.status])..' ore '..e.mining_target.name end "
        "for _,e in pairs(s.find_entities_filtered{name='offshore-pump',position={%s,%s},radius=1}) do o[#o+1]='pump '..tostring(st[e.status]) end "
        "rcon.print(table.concat(o,'|'))" % PUMP)
    print(s.replace("|", "\n"))
    print("stock:", stock())
    print("ghosts left:", ghost_count())


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "check":
        check()
    elif cmd == "build":
        build("--apply" in sys.argv)
    elif cmd == "status":
        status()
    else:
        sys.exit(__doc__)
