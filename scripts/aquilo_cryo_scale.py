#!/usr/bin/env python3
"""Aquilo: scale the cryogenic science line (the Captain, 2026-11-14: "increase Aquilo science production by 20x").

Usage:  aquilo_cryo_scale.py status | plan N | build N [--apply] | measure [game_minutes] | holmium | gate

Baseline: ONE science plant (-24.5,-38.5) with its cooler (-24.5,-33.5) and fluoroketone plant (-32.5,-39.5) makes 11.4 packs a minute
(3 packs per 3.8-speed 20 s craft... 60/20*3.8). 20x = 228 packs/min.  The route that needs no land and no new machines is MODULES: a
cryogenic plant has 8 slots and no base effects; a speed-module-3 (normal) is +50% speed, +70% energy. The Nauvis mall chests hold
speed-module-3 (normal) x1,335, productivity-module-2 (normal) x4,500 (no productivity-module-3 exists anywhere). Moving factory-made
modules from a Nauvis passive-provider chest into a plant is allowed (it is a move, not a spawn); `build` does exactly that and says what moved.

What was found and fixed first (the "baseline" was not 11.4/min, it was 0):
  The hot-fluoroketone loop deadlocked at 379 packs. The fluoroketone plant keeps making 50 hot whenever its inserter has lithium, so the
  hot pipe column (16 pipes) sat at 100%; a pipe at 100% will not take the science plant's 3 hot output, the plant reports full_output,
  its inserter stops, the cooler cannot run (cold full) and nothing moves. `gate` wires the cooler to the fluoroketone plant's inserter
  (circuit_read_contents on the cooler, enable when fluoroketone-cold < 120): new hot is made only when the cold stock is low, so the
  hot column keeps head room. Clearing the stuck hot pipes once (clear_fluid_inside) restarted the line.

Model (per pack, productivity P of the science plant, Pl of the lithium plant):
  ice 3/(1+P); lithium plate 1/(1+P); cold fluoroketone 6/(1+P), hot returned 3/(1+P) => 3/(1+P) fluoroketone lost
  = 3/50/(1+P) synthesis: solid fuel, lithium, 50 fluorine, 50 ammonia per craft.  lithium craft = 1 holmium plate + 50 brine + 50 ammonia
  -> 5 lithium (x(1+Pl)).  Holmium per pack = lithium per pack /(5(1+Pl)).
"""
import sys
import time

from _game import tools

L = tools["run_lua"]
SCI = (-24.5, -38.5)
COOL = (-24.5, -33.5)
SYN = (-32.5, -39.5)
SYN_INS = (-32.5, -36.5)
LIT = (-21.5, -18.5)
BASE_PACKS = 11.4                      # per minute, one unmoduled epic science plant (60/20 * 3.8 * 1 pack)
SPEED3, PROD2 = 0.5, 0.06              # normal-quality module effects (speed-module-3 speed, productivity-module-2 productivity)
NAUVIS_MODULE_CHESTS = [(-138.5, -463.5), (-135.5, -463.5), (-132.5, -463.5), (-129.5, -463.5), (-126.5, -463.5), (53.5, -411.5)]
# stages: name -> (speed-module-3 in the science plant, in the lithium chem plant) ; kept simple, see plan()
STAGES = {2: 2, 5: 8}                  # target multiple -> speed-module-3 count in the science plant (8 slots = 5x)
# Brine: wells (x, y, amount 2026-11-14). The pumpjack at (-52.5,58.5) measured 113 brine/min at amount 167,369 => 6.75e-4 per minute per unit
WELLS = [(-53.5, 55.5, 93487), (-52.5, 58.5, 167369), (-44.5, 59.5, 286800), (-52.5, 66.5, 262652), (-52.5, 72.5, 213988),
         (-46.5, 73.5, 290949), (-35.5, 71.5, 212001)]
BRINE_PER_UNIT_MIN = 113.0 / 167369


def lua(code):
    return L(code)


def model(packs, speed_mods=0, prod_sci=0.0, prod_lit=0.0):
    """Material and machine bill per minute for `packs` packs/min."""
    ps, pl = prod_sci, prod_lit
    plates = packs / (1 + ps)
    ice = 3 * plates
    syn_crafts = 3 * plates / 50
    lith_for_syn = syn_crafts
    lith = plates + lith_for_syn                       # lithium (plates use 1 lithium each in a furnace)
    li_crafts = lith / (5 * (1 + pl))
    brine = 50 * li_crafts
    ammonia = 50 * li_crafts + 50 * syn_crafts
    fluorine = 50 * syn_crafts
    sci_speed = 3.8 * (1 + SPEED3 * speed_mods)
    per_plant = 3 * sci_speed * (1 + ps)
    return dict(packs=packs, plates=plates, ice=ice, solid_fuel=syn_crafts, lithium=lith, holmium=li_crafts, brine=brine,
                ammonia=ammonia, fluorine=fluorine, cold=6 * plates, plants=packs / per_plant,
                plant_mw=1.5 * (1 + 0.7 * speed_mods + 0.6 * round(ps / PROD2)))


def plan(n):
    n = int(n)
    packs = BASE_PACKS * n
    print("== plan %dx: %.0f packs/min (%.0f/hour) ==" % (n, packs, packs * 60))
    routes = [("A. modules only: speed-module-3 x8 in the science plant (5.0x = 57/min each), unmoduled elsewhere", 8, 0.0, 0.0),
              ("B. as A + 3 productivity-module-2 in the lithium chem plants (+18%)", 8, 0.0, 0.18),
              ("C. productivity route: 4 prod-2 + 4 speed-3 in each science plant (+24% prod, 2.6x speed)", 4, 0.24, 0.18)]
    for name, sm, ps, pl in routes:
        m = model(packs, sm, ps, pl)
        # recompute speed with prod modules slowing it: 4 prod-2 = -40% speed
        if ps:
            speed = 3.8 * (1 + SPEED3 * sm - 0.1 * round(ps / PROD2))
            m["plants"] = packs / (3 * speed * (1 + ps))
        print("\n" + name)
        print("  science plants %.1f (each %.1f MW with modules => %.1f MW)  cooler plants >= %.1f (456 cold/min each, unmoduled)" %
              (m["plants"], m["plant_mw"], m["plants"] * m["plant_mw"], m["cold"] / 456))
        print("  per minute: ice %.0f  lithium plate %.0f  solid fuel %.1f  fluorine %.0f  ammonia %.0f  brine %.0f  holmium plate %.1f (%.0f/hour)" %
              (m["ice"], m["plates"], m["solid_fuel"], m["fluorine"], m["ammonia"], m["brine"], m["holmium"], m["holmium"] * 60))
        lit_chem = m["lithium"] / (28.5 * (1 + pl))
        print("  lithium chem plants (unmoduled epic: 28.5 lithium/min) %.1f ; pumpjacks needed at 6.75e-4*amount brine/min: wells give %.0f/min total (7 wells), x2 with 2 speed-3 per pumpjack" %
              (lit_chem, sum(w[2] for w in WELLS) * BRINE_PER_UNIT_MIN))
    m = model(packs, 8, 0.0, 0.18)
    print("\nBinding checks (route B):")
    print("  brine: need %.0f/min, 7 wells at current pumpjacks give %.0f/min, with speed modules in 7 pumpjacks %.0f/min -> %s" %
          (m["brine"], sum(w[2] for w in WELLS) * BRINE_PER_UNIT_MIN, 2 * sum(w[2] for w in WELLS) * BRINE_PER_UNIT_MIN,
           "OK only with all 7 wells and modules" if m["brine"] <= 2 * sum(w[2] for w in WELLS) * BRINE_PER_UNIT_MIN else "NOT REACHABLE with the wells charted"))
    print("  one well pumpjack today: %.0f brine/min = %.1f packs/min (lithium plates only)" % (BRINE_PER_UNIT_MIN * 167369, BRINE_PER_UNIT_MIN * 167369 / 10))
    print("  holmium for 5,000 / 7,500 packs: %.0f / %.0f plates (route B, %.0f / %.0f without modules)" %
          (5000 * m["holmium"] / packs, 7500 * m["holmium"] / packs, 5000 * model(packs)["holmium"] / packs, 7500 * model(packs)["holmium"] / packs))
    power_report(m["plants"] * m["plant_mw"])
    delivery(n)


def power_report(added_mw):
    out = lua("local s=game.surfaces.aquilo local w=0 for _,g in pairs(s.find_entities_filtered{type='generator'}) do w=w+g.energy_generated_last_tick*60 end rcon.print(string.format('%.1f',w/1e6))")
    print("  power: turbines now deliver %s MW (cap 22 MW = 2 epic turbines); science adds ~%.1f MW (minus the %.1f MW of the plant that exists)" %
          (out.strip(), added_mw, 1.5))


def delivery(n):
    print("\nDELIVERY LIST (off-world -> Aquilo pad), stage %dx:" % n)
    print("  holmium plate: see `holmium` (stock lasts X minutes; ~%.0f per hour at %dx with route B)" % (model(BASE_PACKS * n, 8, 0, 0.18)["holmium"] * 60, n))
    if n >= 10:
        k = int(model(BASE_PACKS * n, 8, 0, 0.18)["plants"] + 0.999) - 1
        print("  cryogenic-plant (craft on Aquilo: 20 processing-unit, 20 superconductor, 20 lithium plate, 40 refined concrete):")
        print("    %d more science plants + 1 more cooler = %d plants -> %d processing units, %d superconductors, %d refined concrete (the lithium plates are on site)" %
              (k, k + 1, 20 * (k + 1), 20 * (k + 1), 40 * (k + 1)))
    print("  modules (move from Nauvis mall by Lua, or Replicator request): speed-module-3 x%d (8 per science plant/cooler, 2 per pumpjack, up to 3 per chem plant)," % (8 * (3 if n >= 10 else 1)))
    print("    productivity-module-2 x3 per lithium chem plant")
    print("  pumpjack x6 (more brine wells), chemical-plant x4+ (lithium), pipe, pipe-to-ground, heat-pipe x300, storage-tank x2, medium/big poles")
    print("  power for >= 10x: steam-turbine + heat-exchanger + heating-tower: 2 per 22 MW (Nauvis network has 3 turbines, 123 exchangers, 0 towers: Replicator)")
    print("  construction/logistic robots: +50 each if the robot network feeder is short")


def holmium():
    a = lua("local f=game.forces.player local s=game.surfaces.aquilo local net=s.find_logistic_network_by_position({4,-11},f) rcon.print(net.get_item_count('holmium-plate')..' '..net.get_item_count('lithium-plate')..' '..net.get_item_count('lithium'))").split()
    w = lua("local p=prototypes.item['holmium-plate'] rcon.print(p.weight..' '..p.stack_size)").split()
    hol, plates = int(a[0]), int(a[1])
    print("Aquilo network: holmium plate %d, lithium plate %d. One holmium makes 5 lithium (x1.18 with 3 prod-2), one lithium plate = one pack." % (hol, plates))
    print("Packs possible from stock without new holmium: %d (plates) + %d (holmium, no modules) = %d" % (plates, hol * 5, plates + hol * 5))
    print("holmium-plate weight %s kg, stack %s: a 1,000 kg rocket carries %d" % (w[0], w[1], 1000000 // int(float(w[0]))))
    for n, p in ((1, BASE_PACKS), (2, 22.8), (5, 57), (10, 114), (20, 228)):
        m = model(p, 8, 0, 0.18)
        print("  %2dx: %.1f holmium/min = %.0f/hour; stock lasts %.0f min after the %d lithium plates are used" % (n, m["holmium"], m["holmium"] * 60, hol / m["holmium"] if m["holmium"] else 0, plates))
    print("Fulgora source: holmium ore 81/min (1.0%% of scrap); holmium-solution = 2 ore + 1 stone + 10 water -> 100; plate = 20 solution -> so 2 ore = 5 plates, up to ~200 plates/min if all ore went here")
    print("Total need for the remaining research (5,000-7,500 packs) minus the 1,090 plates in stock: about %d to %d holmium plates (no prod modules), %d to %d with them" %
          (int((5000 - plates) / 5), int((7500 - plates) / 5), int((5000 - plates) / 5 / 1.18), int((7500 - plates) / 5 / 1.18)))


def gate(apply=True):
    """Idempotent: wire the cooler to the fluoroketone plant's inserter; enable only while cold fluoroketone is under 120."""
    if not apply:
        print("  gate: cooler -> fluoroketone inserter, enable while cold < 120 (would be set)")
        return
    print(lua("local s=game.surfaces.aquilo local W=defines.wire_connector_id local c=s.find_entities_filtered{name='cryogenic-plant',position={%s,%s},radius=1}[1] "
              "local i=s.find_entities_filtered{name='fast-inserter',position={%s,%s},radius=0.4}[1] c.get_or_create_control_behavior().circuit_read_contents=true "
              "local a=i.get_wire_connector(W.circuit_red,true) local b=c.get_wire_connector(W.circuit_red,true) a.connect_to(b,false) "
              "local cb=i.get_or_create_control_behavior() cb.circuit_enable_disable=true cb.circuit_condition={first_signal={type='fluid',name='fluoroketone-cold'},comparator='<',constant=120} "
              "rcon.print('gate on: fluoroketone plant inserter runs while cold fluoroketone < 120; fulfilled now '..tostring(cb.circuit_condition.fulfilled))" % (COOL + SYN_INS)))


def count_modules(pos, name="speed-module-3", ent="cryogenic-plant"):
    r = lua("local s=game.surfaces.aquilo local e=s.find_entities_filtered{name='%s',position={%s,%s},radius=1}[1] rcon.print(e.get_module_inventory().get_item_count('%s')..' '..#e.get_module_inventory())" % ((ent,) + pos + (name,)))
    a, b = r.split()
    return int(a), int(b)


def move_modules(pos, name, want, apply, ent="cryogenic-plant"):
    have, slots = count_modules(pos, name, ent)
    need = min(want, slots) - have
    if need <= 0:
        print("  %s at %s already holds %d %s" % ("plant", pos, have, name))
        return
    print("  %s: %d -> %d %s (move %d from a Nauvis passive-provider chest into the plant)" % (pos, have, have + need, name, need))
    if not apply:
        return
    chests = ",".join("{%s,%s}" % c for c in NAUVIS_MODULE_CHESTS)
    print("   ", lua("local nv=game.surfaces.nauvis local s=game.surfaces.aquilo local e=s.find_entities_filtered{name='%s',position={%s,%s},radius=1}[1] local mi=e.get_module_inventory() "
                     "local need=%d local moved=0 for _,p in pairs({%s}) do if moved<need then local c=nv.find_entities_filtered{name='passive-provider-chest',position=p,radius=0.4}[1] "
                     "if c then local inv=c.get_inventory(defines.inventory.chest) local got=inv.remove{name='%s',count=need-moved,quality='normal'} if got>0 then local put=mi.insert{name='%s',count=got,quality='normal'} "
                     "if put<got then inv.insert{name='%s',count=got-put,quality='normal'} end moved=moved+put end end end end rcon.print('moved '..moved..' %s from Nauvis chests into the plant; plant now has '..mi.get_item_count('%s'))"
                     % ((ent,) + pos + (need, chests, name, name, name, name, name))))


def build(n, apply):
    if str(n) == "brine":
        print("== build brine (APPLY) ==" if apply else "== build brine (dry run) ==")
        move_modules((-52.5, 58.5), "speed-module-3", 2, apply, "pumpjack")      # doubles the one brine well's output
        move_modules(LIT, "speed-module-3", 3, apply, "chemical-plant")           # lithium chem plant 28 -> 71 lithium/min capacity
        return
    n = int(n)
    print("== build %dx %s ==" % (n, "(APPLY)" if apply else "(dry run; add --apply)"))
    if n not in STAGES:
        print("Stage %dx cannot be built by modules alone (one plant tops out at 5x with normal speed-module-3, 7x with legendary speed-module-2 x8)." % n)
        print("It needs more cryogenic plants (see `plan %d` delivery list: processing units, superconductors) and land; NOT BUILT." % n)
        return
    cur = lua("local w=0 for _,g in pairs(game.surfaces.aquilo.find_entities_filtered{type='generator'}) do w=w+g.energy_generated_last_tick*60 end rcon.print(string.format('%.1f',w/1e6))")
    add = 1.5 * 0.7 * STAGES[n]
    print("power: turbines deliver %s MW now, cap 22 MW; this stage adds %.1f MW" % (cur.strip(), add))
    if apply:
        lua("game.auto_save('skippy_before_cryo_%d')" % n) if False else tools["save_game"]("skippy")
    gate(apply)
    move_modules(SCI, "speed-module-3", STAGES[n], apply)


def measure(minutes=3.0):
    """Packs made a game minute by the science plant (products_finished), plus brine, plates, and the loop state."""
    code = ("local s=game.surfaces.aquilo local p=s.find_entities_filtered{name='cryogenic-plant',position={%s,%s},radius=1}[1] local f=game.forces.player "
            "local fs=f.get_fluid_production_statistics(s) local ps=f.get_item_production_statistics(s) "
            "rcon.print(game.tick..' '..p.products_finished..' '..fs.get_input_count('lithium-brine')..' '..ps.get_input_count('lithium-plate')..' '..ps.get_output_count('lithium-plate')..' '..ps.get_input_count('lithium')..' '..p.get_module_inventory().get_item_count('speed-module-3')..' '..p.status)" % SCI)
    a = [float(v) for v in lua(code).split()]
    while True:
        time.sleep(15)
        b = [float(v) for v in lua(code).split()]
        if b[0] - a[0] >= minutes * 3600:
            break
    m = (b[0] - a[0]) / 3600
    print("%.1f game minutes: packs %.1f/min (baseline 11.4 -> %.1fx); brine %.0f/min; lithium plates made %.1f used %.1f/min; lithium made %.1f/min; speed modules %d; plant status %d" %
          (m, (b[1] - a[1]) / m, (b[1] - a[1]) / m / BASE_PACKS, (b[2] - a[2]) / m, (b[3] - a[3]) / m, (b[4] - a[4]) / m, (b[5] - a[5]) / m, b[6], b[7]))
    print(lua("local f=game.forces.player local s=game.surfaces.aquilo local net=s.find_logistic_network_by_position({4,-11},f) local w=0 for _,g in pairs(s.find_entities_filtered{type='generator'}) do w=w+g.energy_generated_last_tick*60 end "
              "rcon.print('network: lithium-plate '..net.get_item_count('lithium-plate')..' holmium '..net.get_item_count('holmium-plate')..' ice '..net.get_item_count('ice')..' solid-fuel '..net.get_item_count('solid-fuel')..' power '..string.format('%.1f',w/1e6)..' MW')"))


def status():
    print(lua("local s=game.surfaces.aquilo local st={} for k,v in pairs(defines.entity_status) do st[v]=k end local o={} for _,p in pairs({{%s,%s},{%s,%s},{%s,%s}}) do local e=s.find_entities_filtered{name='cryogenic-plant',position=p,radius=1}[1] "
              "local fl='' for i=1,e.fluids_count do local f=e.get_fluid(i) if f then fl=fl..f.name..'='..math.floor(f.amount)..' ' end end o[#o+1]=e.get_recipe().name..' '..(st[e.status] or e.status)..' made '..e.products_finished..' speed '..string.format('%%.2f',e.crafting_speed)..' modules '..serpent.line(e.get_module_inventory().get_contents())..' '..fl end "
              "local l=s.find_entities_filtered{name='chemical-plant',position={%s,%s},radius=1}[1] o[#o+1]='lithium plant '..(st[l.status] or l.status)..' made '..l.products_finished "
              "rcon.print(table.concat(o,' ## '))" % (SCI + COOL + SYN + LIT)).replace(" ## ", chr(10)))


def main():
    a = sys.argv[1:]
    step = a[0] if a else "status"
    apply = "--apply" in a
    rest = [x for x in a[1:] if not x.startswith("--")]
    if step == "status":
        status()
    elif step == "plan":
        plan(rest[0] if rest else 2)
    elif step == "build":
        build(rest[0] if rest else 2, apply)
    elif step == "measure":
        measure(float(rest[0]) if rest else 3.0)
    elif step == "holmium":
        holmium()
    elif step == "gate":
        gate()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
