#!/usr/bin/env python3
"""Aquilo power (2026-11-14): more steam power so the cryogenic science line stops running at low_power and has room for 10x/20x.

THE NUMBERS (read from the game's prototypes, epic quality; all measured the same day):
  steam turbine   11.06 MW, 1.9 steam/tick = 114 steam/s;  heat exchanger 19.0 MW (316,667 J/tick), water 15 -> steam 500 C
  water has 2 kJ/degree, steam 0.2 kJ/degree: 1 water = 10 steam = 970 kJ.  So 1 MW = 1.03 water/s = 0.052 ice/s (1 ice = 20 water):
  60 MW is only 3.1 ice/s (186 a minute).  Ice is NOT the limit; the melter (ice-melting, epic chem plant speed 1.9 = 38 water/s) carries 37 MW.
  one exchanger feeds 1.7 turbines, so the pair is "exchanger + 2 turbines" = 19 MW (the turbines could do 22).
  heat: a tower or reactor delivers heat 1:1 to the exchanger (turbine efficiency 1.0): 1 MW electric = 1 MW heat = 5 solid fuel a minute.
  Towers follow the demand (burn what is drawn).  The REACTOR does not: with a fuel cell in it and the network at 1,000 C it burned 77 MW
  (770 MJ per 10 s) while the base drew about 24 MW (tested 2026-11-14, `_aq_rtest.py`); solid fuel use fell only 238 -> 211 a minute.
  So a reactor only pays when the base draws about 76 MW; below that it burns cells for nothing.
  1 heat pipe = 1 MJ/degree: a new pipe soaks 985 MJ = 82 solid fuel from the 1,000 C network; keep new pipes few.

Built (2026-11-14), both sets east of the base heat row (pipe end (31,-14)/(31,-13)), +38 MW, total 60 MW with the two old sets:
  A (E1)  exchanger tiles 34..35 x -14..-12 facing east, heat tile (33,-13); melter (34..36,-17..-15) facing north meets its north water port directly;
          turbines 36..40 and 41..45 x -14..-12 lie on the standing hot ring (38..43,-11).  chest (32,-16) + inserter (33,-16) feed ice.
  B (E2)  exchanger 32..33 x -21..-19, melter (32..34,-24..-22), turbines x 34..43 x -21..-19, heat column x=31 (y -22..-15), row y=-18 under the turbines;
          chest (30,-23) + inserter (31,-23).  The chest must be inside a roboport's logistic area (y >= -23).
  modules speed-module-3 into the fuel works (pumpjack 2, solid fuel plant 3, separation plant 3): solid fuel 228 -> 570 a minute.
Heat pipe soak: every pipe takes 985 MJ (82 solid fuel) when joined, so halos are replaced by explicit tiles (Plan.nohalo + extra).

Usage: aquilo_power.py status | measure [seconds] | plan [MW] | build A|B [--apply] | config | modules [--apply] [--no-sep] | sink2 [--apply] | fixb
"""
import json
import sys
import time

from _game import tools
import aquilo_cryo as C
from aquilo_cryo import Plan, fetch, heat_tiles, build, lua, N, E, S, W

BOX = (20, -34, 52, -5)


def block_a():
    """E1: exchanger tiles 34..35 x -14..-12 (east facing), melter above it, two turbines along the standing hot ring (38..43,-11)."""
    P = Plan()
    P.add("heat-exchanger", 34, -14, 2, 3, E)           # heat tile (33,-13); north water port meets the melter, steam leaves east
    P.add("steam-turbine", 36, -14, 5, 3, E)            # bottom row touches the ring pipes (38..43,-11): no heat pipes of its own
    P.add("steam-turbine", 41, -14, 5, 3, E)
    P.add("chemical-plant", 34, -17, 3, 3, N, recipe="ice-melting")     # output tile (34,-15) meets the exchanger's tile (34,-14)
    P.add("fast-inserter", 33, -16, d=W)                # picks up from the chest to its west
    P.add("requester-chest", 32, -16)
    P.add("substation", 38, -17, 2, 2)
    P.nohalo = set().union(*[e["tiles"] for e in P.ents if e["name"] not in C.NOHEAT])
    extra = [(32, -13), (33, -13), (33, -14), (33, -15)]
    return P, extra


def block_b():
    """E2 north of E1: exchanger tiles 32..33 x -21..-19 (east facing, heat tile (31,-20)), melter above it (output meets its north port), turbines along
    x 34..43. Heat: column x=31 from the row end up to the melter's inserter, and a row y=-18 under the turbines (20 pipes in all, about 1,700 solid fuel of soak)."""
    P = Plan()
    P.add("heat-exchanger", 32, -21, 2, 3, E)
    P.add("steam-turbine", 34, -21, 5, 3, E)
    P.add("steam-turbine", 39, -21, 5, 3, E)
    P.add("chemical-plant", 32, -24, 3, 3, N, recipe="ice-melting")
    P.add("fast-inserter", 31, -23, d=W)                # picks up from the chest to its west (that chest must be inside the logistic area: y >= -23)
    P.add("requester-chest", 30, -23)
    P.nohalo = set().union(*[e["tiles"] for e in P.ents if e["name"] not in C.NOHEAT])
    extra = [(31, y) for y in range(-15, -23, -1)] + [(x, -18) for x in range(32, 44)]
    return P, extra


def sink2():
    """Second ice sink (the fuel works' ice by-product filled the first one's chest at 4,550 and throttled the fuel plant): a recycler under the hot row y=-1,
    fed by a requester chest (19,1) and a fast inserter that runs only while the network holds more than 4,200 ice (the first sink works at 4,000);
    the quarter that comes back leaves by an inserter into a provider chest (14,1)."""
    P = Plan()
    C.SIZE_RECYCLER = True
    P.add("recycler", 16, 0, 2, 4, S)
    P.add("fast-inserter", 18, 1, d=E)
    P.add("requester-chest", 19, 1)
    P.add("fast-inserter", 15, 1, d=E)
    P.add("passive-provider-chest", 14, 1)
    P.nohalo = set().union(*[e["tiles"] for e in P.ents if e["name"] not in C.NOHEAT])
    return P, [(18, 0), (15, 0)]


def sink2_config():
    code = "local s=game.surfaces.aquilo local o={} " + C.ask(19.5, 1.5, {"ice": 400}) + C.cond(18.5, 1.5, "ice", ">", 4200) + " rcon.print(table.concat(o,' | '))"
    print(lua(code))


def status():
    print(lua(
        "local s=game.surfaces.aquilo local function st(e) for a,v in pairs(defines.entity_status) do if v==e.status then return a end end return '?' end local o={} "
        "local c={} for _,e in pairs(s.find_entities_filtered{name={'steam-turbine','heat-exchanger'}}) do local k=e.name..' '..st(e)..' net'..tostring(e.electric_network_id) c[k]=(c[k] or 0)+1 end for k,v in pairs(c) do o[#o+1]=k..' x'..v end "
        "for _,e in pairs(s.find_entities_filtered{name={'heating-tower','nuclear-reactor'}}) do o[#o+1]=e.name..' '..e.position.x..','..e.position.y..' '..st(e)..' '..string.format('%.0f',e.temperature)..'C' end "
        "local n=s.find_entities_filtered{name='roboport'}[1].logistic_network local sf,ice,rf=n.get_item_count('solid-fuel'),n.get_item_count('ice'),n.get_item_count('rocket-fuel') o[#o+1]='network: solid fuel '..sf..' ice '..ice..' rocket fuel '..rf "
        "for _,e in pairs(s.find_entities_filtered{name='cryogenic-plant'}) do local r=e.get_recipe() o[#o+1]='cryo '..(r and r.name or '-')..' '..st(e) end rcon.print(table.concat(o,' || '))").replace(" || ", "\n"))


def sample(secs):
    code = ("local s=game.surfaces.aquilo local p=s.find_entities_filtered{type='electric-pole',limit=1}[1] local st=p.electric_network_statistics local f=game.forces.player local fi=f.get_item_production_statistics(s) "
            "local o={game.tick,'fuel_made|'..fi.get_input_count('solid-fuel'),'fuel_used|'..fi.get_output_count('solid-fuel')} "
            "for n,v in pairs(st.input_counts) do o[#o+1]='i '..n..'|'..string.format('%.0f',v) end for n,v in pairs(st.output_counts) do o[#o+1]='o '..n..'|'..string.format('%.0f',v) end rcon.print(table.concat(o,'  '))")
    def snap():
        parts = lua(code).split("  ")
        return int(parts[0]), {k: float(v) for k, v in (p.rsplit("|", 1) for p in parts[1:])}
    t0, a = snap()
    time.sleep(secs)
    t1, b = snap()
    dt = (t1 - t0) / 60.0
    out = {}
    for k in b:
        d = b[k] - a.get(k, 0)
        out[k] = d / dt / 1e6 if k[:2] in ("i ", "o ") else d / dt * 60
    return dt, out


def measure(secs):
    dt, d = sample(secs)
    print("game seconds", round(dt, 1))
    prod = sum(v for k, v in d.items() if k.startswith("o ") and "solar" not in k and "accumulator" not in k)
    print("steam turbines %.2f MW | solar %.2f | accumulators out %.2f in %.2f" % (d.get("o steam-turbine", 0), d.get("o solar-panel", 0), d.get("o accumulator", 0), d.get("i accumulator", 0)))
    print("cryogenic plants draw %.2f MW, roboports %.2f, assemblers %.2f, chemical %.2f" % (d.get("i cryogenic-plant", 0), d.get("i roboport", 0), d.get("i assembling-machine-3", 0), d.get("i chemical-plant", 0)))
    print("solid fuel made %.0f/min, used %.0f/min" % (d.get("fuel_made", 0), d.get("fuel_used", 0)))


def config():
    code = "local s=game.surfaces.aquilo local o={} " + C.ask(32.5, -15.5, {"ice": 400})
    code += ("for _,q in pairs({{'heat-exchanger',35,-12.5},{'heat-exchanger',33,-19.5}}) do local e=s.find_entities_filtered{name=q[1],position={q[2],q[3]},radius=0.6}[1] if e then e.direction=defines.direction.east o[#o+1]=q[1]..' faces '..e.direction end end "
             "for _,e in pairs(s.find_entities_filtered{name='steam-turbine',area={{36,-22},{46,-12}}}) do e.direction=defines.direction.east o[#o+1]='turbine '..e.position.x..','..e.position.y..' '..e.direction end rcon.print(table.concat(o,' | '))")
    print(lua(code))


FUEL_MODULES = [("pumpjack", 35.5, -2.5, 2), ("chemical-plant", 32.5, -3.5, 3), ("chemical-plant", 28.5, -3.5, 3)]      # name, x, y, speed-module-3 count


def modules(apply, only=None):
    """Speed-module-3 (normal) into the fuel works: pumpjack 2 slots, solid fuel plant 3, separation plant 3.  The modules are factory-made items moved by
    Lua from Nauvis passive-provider chests (a move, not a spawn); the result line says what moved."""
    want = ",".join("{'%s',%s,%s,%d}" % t for t in FUEL_MODULES if only is None or (t[1], t[2]) in only)
    code = ("local a=game.surfaces.aquilo local n=game.surfaces.nauvis local o={} local apply=%s "
            "local function take(k) local got=0 for _,c in pairs(n.find_entities_filtered{type={'container','logistic-container'}}) do local inv=c.get_inventory(defines.inventory.chest) local have=inv.get_item_count({name='speed-module-3',quality='normal'}) "
            "if have>0 and got<k then local r=math.min(have,k-got) if apply then r=inv.remove({name='speed-module-3',quality='normal',count=r}) end got=got+r o[#o+1]='from nauvis chest '..c.position.x..','..c.position.y..' '..r end end return got end "
            "for _,q in pairs({%s}) do local e=a.find_entities_filtered{name=q[1],position={q[2],q[3]},radius=0.6}[1] if e then local mi=e.get_module_inventory() local have=mi.get_item_count('speed-module-3') local need=q[4]-have if need>0 then "
            "local g=take(need) if apply and g>0 then mi.insert({name='speed-module-3',quality='normal',count=g}) end o[#o+1]=e.name..' '..q[2]..','..q[3]..' +'..g..' speed-module-3' end end end rcon.print(table.concat(o,' | '))"
            % ("true" if apply else "false", want))
    print(lua(code))


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    apply = "--apply" in sys.argv
    if step == "status":
        status()
    elif step == "measure":
        measure(float(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 30)
    elif step == "config":
        config()
    elif step == "sink2":
        grid = fetch((8, -4, 30, 10))
        net = heat_tiles((8, -4, 30, 10))
        P, extra = sink2()
        build(P, grid, net, apply, extra)
        if apply:
            sink2_config()
    elif step == "fixb":
        # the first B build put the melter's chest at y=-26, outside every roboport: take out those pieces (all built by this script)
        print(lua("local s=game.surfaces.aquilo local o={} for _,q in pairs({{'fast-inserter',33.5,-24.5},{'requester-chest',33.5,-25.5},{'heat-pipe',31.5,-22.5},{'heat-pipe',31.5,-23.5},{'heat-pipe',31.5,-24.5},{'heat-pipe',32.5,-24.5}}) do "
                  "for _,e in pairs(s.find_entities_filtered{name=q[1],position={q[2],q[3]},radius=0.3}) do o[#o+1]='removed '..e.name..' '..e.position.x..','..e.position.y e.destroy() end end rcon.print(table.concat(o,' | '))"))
    elif step == "modules":
        modules(apply, {(35.5, -2.5), (32.5, -3.5)} if "--no-sep" in sys.argv else None)
    elif step == "plan":
        mw = float(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].replace(".", "").isdigit() else 60.0
        print("target %.0f MW electric: turbines %.1f (11.06 MW), exchangers %.1f (19.0 MW), heat %.0f MW = solid fuel %.0f a minute (+90 for rocket fuel, +heating)" % (mw, mw / 11.06, mw / 19.0, mw, mw * 5))
        print("water %.1f/s = ice %.0f a minute; melters %.1f (38 water/s each); ammonia for that fuel %.0f a minute, crude %.0f a minute, ice by-product %.0f a minute" % (mw * 1.03, mw * 3.1, mw * 1.03 / 38, mw * 75, mw * 30, mw * 7.5))
        print("fuel works now (3+3+2 speed-module-3): 570 a minute max = %.0f MW of heat" % (570 / 5.0))
    elif step == "build":
        which = sys.argv[2] if len(sys.argv) > 2 else "A"
        grid = fetch(BOX)
        net = heat_tiles(BOX)
        P, extra = (block_a if which == "A" else block_b)()
        build(P, grid, net, apply, extra)
        if apply:
            config()
            if which == "B":
                print(lua("local s=game.surfaces.aquilo local o={} " + C.ask(30.5, -22.5, {"ice": 400}) + " rcon.print(table.concat(o,' | '))"))


if __name__ == "__main__":
    main()
