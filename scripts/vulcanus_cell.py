#!/usr/bin/env python3
"""Vulcanus science cell in the free band y -58.5..-41.5 (between the lattice rows y -60 and y -40; the band south of it is the base's solar field).
  foundries   lava pump (46.5,-43.5) -> lava main along y -43.5 -> six columns 9 apart. Each column: a lava foundry at y -46.5
              (molten copper or molten iron, calcite in from the west chest, stone out to the east chest), one link pipe at (x-1,-49.5),
              and below it at y -52.5 a foundry making science packs (copper columns) or tungsten plate (iron columns).
  unload      three red chests at the end of the tungsten belt (-117.5,-70.5)
  coal        big drills on the coal field; carbide = acid wells, carbon plants and carbide assemblers
Usage: vulcanus_cell.py foundries|unload|coal|carbide|calcite|dump|silo|space [--apply]"""
import json
import sys

from _game import tools

PACK_X = (36.5, 27.5, 18.5)
PLATE_X = (9.5, -7.5, -16.5)


def column(x, top, bottom):
    e = [{"name": "foundry", "x": x, "y": -46.5, "direction": 0, "recipe": top}, {"name": "pipe", "x": x - 1, "y": -49.5},
         {"name": "foundry", "x": x, "y": -52.5, "direction": 0, "recipe": bottom}]
    for y in (-46.5, -52.5):
        e += [{"name": "requester-chest", "x": x - 4, "y": y}, {"name": "bulk-inserter", "x": x - 3, "y": y, "direction": 12},
              {"name": "bulk-inserter", "x": x + 3, "y": y, "direction": 12}, {"name": "passive-provider-chest", "x": x + 4, "y": y}]
    return e


def foundries():
    e = [{"name": "offshore-pump", "x": 46.5, "y": -43.5, "direction": 4}]
    e += [{"name": "pipe", "x": x + 0.5, "y": -43.5} for x in range(-18, 46)]
    for x in PACK_X:
        e += column(x, "molten-copper-from-lava", "metallurgic-science-pack")
    for x in PLATE_X:
        e += column(x, "molten-iron-from-lava", "tungsten-plate")
    e += [{"name": "substation", "x": x, "y": y} for x in (-10, 10, 30) for y in (-57, -42)]
    return e


REQ = ("local s=game.surfaces.vulcanus local n=0 local function req(x,y,t) local c=s.find_entities_filtered{name='requester-chest',position={x,y},radius=0.3}[1] if not c then return end "
       "local ss=c.get_logistic_sections() local se=ss.sections[1] or ss.add_section() local i=0 for name,ct in pairs(t) do i=i+1 se.set_slot(i,{value={name=name,quality='normal'},min=ct}) end n=n+1 end "
       "for _,x in pairs{%s} do req(x-4,-46.5,{calcite=20}) req(x-4,-52.5,{['tungsten-carbide']=60,['tungsten-plate']=40}) end "
       "for _,x in pairs{%s} do req(x-4,-46.5,{calcite=20}) req(x-4,-52.5,{['tungsten-ore']=100}) end "
       "for _,f in pairs(s.find_entities_filtered{name='foundry',area={{-22,-56},{44,-43}}}) do f.direction=0 end rcon.print('requests set on '..n..' chests')") % (
           ",".join(str(x) for x in PACK_X), ",".join(str(x) for x in PLATE_X))

def unload():
    return [{"name": "bulk-inserter", "x": -118.5, "y": -70.5, "direction": 4}, {"name": "passive-provider-chest", "x": -119.5, "y": -70.5},
            {"name": "bulk-inserter", "x": -116.5, "y": -70.5, "direction": 12}, {"name": "passive-provider-chest", "x": -115.5, "y": -70.5},
            {"name": "bulk-inserter", "x": -117.5, "y": -69.5, "direction": 0}, {"name": "passive-provider-chest", "x": -117.5, "y": -68.5}]


def coal():
    """Six big mining drills on the coal field, each dropping straight into a red chest."""
    e = []
    for x in (-80.5, -72.5, -66.5, -58.5, -52.5, -46.5):
        e += [{"name": "big-mining-drill", "x": x, "y": -68.5, "direction": 0}, {"name": "passive-provider-chest", "x": x, "y": -71.5}]
    return e


def calcite():
    """One big drill on the calcite patch dropping into a red chest; a roboport and substation extend the base network to it."""
    return [{"name": "substation", "x": -132, "y": 104}, {"name": "roboport", "x": -130, "y": 110},
            {"name": "big-mining-drill", "x": -140.5, "y": 108.5, "direction": 4}, {"name": "passive-provider-chest", "x": -137.5, "y": 108.5}]


def dump():
    """Stone from the lava foundries is this planet's surplus: two blue chests on the shore, each with an inserter that throws stone into the lava,
    switched on only while the network holds more than 2,000 stone."""
    e = []
    for y in (-50.5, -51.5):
        e += [{"name": "requester-chest", "x": 43.5, "y": y}, {"name": "bulk-inserter", "x": 44.5, "y": y, "direction": 12}]
    return e


DUMP_CFG = ("local s=game.surfaces.vulcanus local n=0 for _,y in pairs{-50.5,-51.5} do local c=s.find_entities_filtered{name='requester-chest',position={43.5,y},radius=0.3}[1] local i=s.find_entities_filtered{type='inserter',position={44.5,y},radius=0.3}[1] "
            "if c and i then local ss=c.get_logistic_sections() local se=ss.sections[1] or ss.add_section() se.set_slot(1,{value={name='stone',quality='normal'},min=400}) "
            "local cb=i.get_or_create_control_behavior() cb.connect_to_logistic_network=true cb.logistic_condition={first_signal={type='item',name='stone'},comparator='>',constant=2000} n=n+1 end end "
            "rcon.print('stone dumps configured '..n..' drop tile '..s.get_tile(45.5,-50.5).name)")


def silo():
    """Rocket silo at (-30.5,-50.5) with three blue chests for rocket part ingredients on its north side."""
    cx, cy = -30.5, -50.5
    e = [{"name": "rocket-silo", "x": cx, "y": cy}]
    for dx in (-1, 0, 1):
        e += [{"name": "bulk-inserter", "x": cx + dx, "y": cy - 5, "direction": 0}, {"name": "requester-chest", "x": cx + dx, "y": cy - 6}]
    return e


SPACE = ("local f=game.forces.player local s=game.surfaces.vulcanus local o={} local sil=s.find_entities_filtered{name='rocket-silo'}[1] sil.use_transitional_requests=true "
         "for i,item in pairs{'processing-unit','low-density-structure','rocket-fuel'} do local c=s.find_entities_filtered{name='requester-chest',position={-32.5+i,-56.5},radius=0.3}[1] local ss=c.get_logistic_sections() local se=ss.sections[1] or ss.add_section() se.set_slot(1,{value={name=item,quality='normal'},min=100}) end "
         "local p=f.platforms[7] local secs=p.hub.get_logistic_sections() local have=false for _,sec in pairs(secs.sections) do for _,fl in pairs(sec.filters) do if fl.value and fl.value.name=='metallurgic-science-pack' then have=true end end end "
         "if not have then local sec=secs.add_section() sec.set_slot(1,{value={name='metallurgic-science-pack',quality='normal'},min=4000,import_from='vulcanus'}) end "
         "local sch=p.schedule local w=sch.records[2].wait_conditions local has=false for _,c in pairs(w) do if c.condition and c.condition.first_signal and c.condition.first_signal.name=='metallurgic-science-pack' then has=true end end "
         "if not has then w[#w+1]={type='circuit',compare_type='and',condition={first_signal={type='item',name='metallurgic-science-pack'},comparator='>=',constant=8000}} sch.records[2].wait_conditions=w p.schedule=sch end "
         "o[#o+1]='silo answers platform requests '..tostring(sil.use_transitional_requests)..'; shuttle 7 requests 4000 packs from Vulcanus and waits for them there (stop '..sch.records[2].station..')' rcon.print(table.concat(o,' | '))")


CARB_X = (10.5, 14.5, 18.5)


def carbide():
    """Acid block in the band y 84..96: acid main along y 90.5 (x 4.5..19.5) fed by four wells; carbon plants north of it, carbide assemblers south."""
    e = [{"name": "pumpjack", "x": 2.5, "y": 91.5, "direction": 0}, {"name": "pumpjack", "x": -0.5, "y": 89.5, "direction": 0},
         {"name": "pumpjack", "x": -3.5, "y": 89.5, "direction": 0}, {"name": "pumpjack", "x": 7.5, "y": 94.5, "direction": 0}]
    pts = [(-2.5, 87.5), (-1.5, 87.5), (-0.5, 87.5), (0.5, 87.5), (1.5, 87.5), (2.5, 87.5), (2.5, 88.5), (2.5, 89.5), (3.5, 89.5), (4.5, 89.5),
           (8.5, 92.5), (8.5, 91.5)] + [(x + 0.5, 90.5) for x in range(4, 20)]
    e += [{"name": "pipe", "x": x, "y": y} for x, y in pts]
    for x in CARB_X:
        e += [{"name": "chemical-plant", "x": x, "y": 88.5, "direction": 8, "recipe": "carbon"},
              {"name": "bulk-inserter", "x": x - 1, "y": 86.5, "direction": 0}, {"name": "requester-chest", "x": x - 1, "y": 85.5},
              {"name": "bulk-inserter", "x": x + 1, "y": 86.5, "direction": 8}, {"name": "passive-provider-chest", "x": x + 1, "y": 85.5},
              {"name": "assembling-machine-3", "x": x, "y": 92.5, "direction": 0, "recipe": "tungsten-carbide"},
              {"name": "bulk-inserter", "x": x - 1, "y": 94.5, "direction": 8}, {"name": "requester-chest", "x": x - 1, "y": 95.5},
              {"name": "bulk-inserter", "x": x + 1, "y": 94.5, "direction": 0}, {"name": "passive-provider-chest", "x": x + 1, "y": 95.5}]
    return e


CARB_REQ = ("local s=game.surfaces.vulcanus local n=0 local function req(x,y,t) local c=s.find_entities_filtered{name='requester-chest',position={x,y},radius=0.3}[1] if not c then return end "
            "local ss=c.get_logistic_sections() local se=ss.sections[1] or ss.add_section() local i=0 for name,ct in pairs(t) do i=i+1 se.set_slot(i,{value={name=name,quality='normal'},min=ct}) end n=n+1 end "
            "for _,x in pairs{%s} do req(x-1,85.5,{coal=100}) req(x-1,95.5,{carbon=50,['tungsten-ore']=100}) "
            "local c=s.find_entities_filtered{name='chemical-plant',position={x,88.5},radius=0.5}[1] if c then c.direction=8 end local a=s.find_entities_filtered{name='assembling-machine-3',position={x,92.5},radius=0.5}[1] if a then a.direction=0 end end "
            "rcon.print('carbide requests set on '..n..' chests')") % ",".join(str(x) for x in CARB_X)


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    if step == "foundries":
        print(tools["place_entities"](json.dumps(foundries()), surface="vulcanus", dry_run=not apply)[:1500])
        if apply:
            print(tools["run_lua"](REQ))
    elif step == "calcite":
        print(tools["place_entities"](json.dumps(calcite()), surface="vulcanus", dry_run=not apply)[:800])
    elif step == "dump":
        print(tools["place_entities"](json.dumps(dump()), surface="vulcanus", dry_run=not apply)[:800])
        if apply:
            print(tools["run_lua"](DUMP_CFG))
    elif step == "silo":
        print(tools["place_entities"](json.dumps(silo()), surface="vulcanus", dry_run=not apply)[:800])
    elif step == "space":
        print(tools["run_lua"](SPACE))
    elif step == "coal":
        print(tools["place_entities"](json.dumps(coal()), surface="vulcanus", dry_run=not apply)[:800])
    elif step == "carbide":
        print(tools["place_entities"](json.dumps(carbide()), surface="vulcanus", dry_run=not apply)[:1200])
        if apply:
            print(tools["run_lua"](CARB_REQ))
    elif step == "unload":
        print(tools["place_entities"](json.dumps(unload()), surface="vulcanus", dry_run=not apply)[:800])


if __name__ == "__main__":
    main()
