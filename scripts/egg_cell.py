#!/usr/bin/env python3
"""Biter-egg cell on Nauvis: a captive biter spawner fed with bioflux, its eggs going straight into a productivity-module-3 assembler
(the Captain, 2026-11-20: "Yes, with bioflux"). Why: `alert_trace.py` showed every productivity module 3 request in the game waiting
on biter eggs, and Nauvis had no captive spawner.

RULES OF THE THING (read from the prototypes)
  * the spawner burns bioflux (food, 100 kW = 1 a minute); UNFED it turns back into a hostile nest. So `spawner` refuses to place it
    until the feed chest holds bioflux, and bioflux comes by shuttle from Gleba (ghost_carriers.py: 200 a ship, pad slot 400).
  * it makes 5 eggs every 10 s; an egg hatches into a biter after 30 minutes wherever it lies. So eggs NEVER enter the logistic
    network: one inserter hands them from the spawner to the assembler, and the spawner is switched off by circuit while the output
    chest holds STOCK modules or more. Four laser turrets stand by for whatever hatches anyway.
  * the spawner is a placed entity (free once researched, as every building); nothing else is created: circuits, processing units and
    productivity modules 2 come from the network by requester chest.
LAYOUT (tiles from the site's top-left, 18 x 13)
  feed chest (6,1) -> inserter (6,2) -> spawner (4..8, 3..7) -> inserter (9,5) -> assembler (10..12, 4..6) -> inserter (13,5) -> red chest (14,5)
  parts chest (11,2) -> inserter (11,3) -> assembler; substation (9,9); laser turrets at the four corners
Steps: plan | build [--apply] | spawner [--apply] | status
Usage: egg_cell.py build --apply ; egg_cell.py spawner --apply ; egg_cell.py status"""
import json
import sys

from _game import tools

L = tools["run_lua"]
OX, OY = -365, -187
STOCK = 100
Q = {"quality": "legendary"}


def at(tx, ty, w=1):
    return OX + tx + w / 2, OY + ty + w / 2


def ents():
    e = []

    def add(name, tx, ty, w=1, d=0, **kw):
        x, y = at(tx, ty, w)
        r = {"name": name, "x": x, "y": y, "direction": d, "params": dict(Q)}
        r.update(kw)
        e.append(r)

    add("substation", 9, 9, 2)
    add("requester-chest", 6, 1)
    add("bulk-inserter", 6, 2, d=0)             # direction = pick-up side
    add("assembling-machine-3", 10, 4, 3, recipe="productivity-module-3")
    add("bulk-inserter", 9, 5, d=12)
    add("requester-chest", 11, 2)
    add("bulk-inserter", 11, 3, d=0)
    add("bulk-inserter", 13, 5, d=12)
    add("passive-provider-chest", 14, 5)
    for tx, ty in ((1, 1), (15, 1), (1, 10), (15, 10)):
        add("laser-turret", tx, ty, 2)
    return e


CONFIG = ("local s=game.surfaces.nauvis local function one(n,x,y) return s.find_entities_filtered{name=n,position={x,y},radius=0.4}[1] end "
          "local feed=one('requester-chest',%s,%s) local parts=one('requester-chest',%s,%s) local out=one('passive-provider-chest',%s,%s) local o={} "
          "local function req(ch,rows) local pt=ch.get_logistic_point(defines.logistic_member_index.logistic_container) for k=#pt.sections,1,-1 do pt.remove_section(k) end local sec=pt.add_section() for i,r in pairs(rows) do sec.set_slot(i,{value={type='item',name=r[1],quality='normal'},min=r[2]}) end end "
          "if feed then req(feed,{{'bioflux',10}}) o[#o+1]='feed chest asks 10 bioflux' end if parts then req(parts,{{'advanced-circuit',20},{'processing-unit',20},{'productivity-module-2',16}}) o[#o+1]='parts chest set' end "
          "local sp=s.find_entities_filtered{name='captive-biter-spawner',position={%s,%s},radius=1}[1] if sp and out then local a=sp.get_wire_connector(defines.wire_connector_id.circuit_red,true) local b=out.get_wire_connector(defines.wire_connector_id.circuit_red,true) a.connect_to(b,false,defines.wire_origin.script) "
          "local cb=sp.get_or_create_control_behavior() cb.circuit_enable_disable=true cb.circuit_condition={first_signal={type='item',name='productivity-module-3'},comparator='<',constant=%d} o[#o+1]='spawner runs while the chest holds under %d modules' end rcon.print(table.concat(o,'; '))")

STATUS = ("local s=game.surfaces.nauvis local f=game.forces.player local m={} for k,v in pairs(defines.entity_status) do m[v]=k end local o={} local a={{%s,%s},{%s,%s}} "
          "for _,e in pairs(s.find_entities_filtered{area=a,force=f}) do if e.type=='assembling-machine' or e.type=='container' or e.type=='logistic-container' then local c={} local inv=e.get_output_inventory() or e.get_inventory(defines.inventory.chest) "
          "if e.type=='assembling-machine' then for _,it in pairs(e.get_inventory(defines.inventory.crafter_input) and e.get_inventory(defines.inventory.crafter_input).get_contents() or {}) do c[#c+1]='in '..it.name..' '..it.count end end "
          "if inv then for _,it in pairs(inv.get_contents()) do c[#c+1]=it.name..' '..it.count end end local fu='' if e.burner then fu=' fuel '..e.burner.inventory.get_item_count()..' heat '..math.floor(e.burner.remaining_burning_fuel/1000)..'kJ' end o[#o+1]=e.name..' '..tostring(m[e.status])..fu..' ['..table.concat(c,', ')..'] made '..tostring(e.type=='assembling-machine' and e.products_finished or '') end end "
          "o[#o+1]='enemies within 60 tiles: '..s.count_entities_filtered{force='enemy',position={%s,%s},radius=60}..' | bioflux in the Nauvis networks '..(function() local c=0 for _,nw in pairs(f.logistic_networks.nauvis or {}) do c=c+nw.get_item_count('bioflux') end return c end)() rcon.print(table.concat(o,string.char(10)))")


def feed_has():
    x, y = at(6, 1)
    r = L("local s=game.surfaces.nauvis local ch=s.find_entities_filtered{name='requester-chest',position={%s,%s},radius=0.4}[1] rcon.print(ch and ch.get_inventory(defines.inventory.chest).get_item_count('bioflux') or -1)" % (x, y)).strip()
    return int(r)


def config():
    f, p, o, sp = at(6, 1), at(11, 2), at(14, 5), at(4, 3, 5)
    print("   " + L(CONFIG % (f[0], f[1], p[0], p[1], o[0], o[1], sp[0], sp[1], STOCK, STOCK)).strip())


def main():
    a = sys.argv[1:]
    step = a[0] if a else "plan"
    apply = "--apply" in a
    if step in ("plan", "build"):
        r = tools["place_entities"](json.dumps(ents()), surface="nauvis", dry_run=not (apply and step == "build"))
        print(str(r)[:400])
        if apply and step == "build":
            config()
    elif step == "spawner":
        n = feed_has()
        print("bioflux in the feed chest: %d" % n)
        if n < 5:
            print("not placed: the spawner would starve and turn hostile. Wait for the shuttle.")
            return
        x, y = at(4, 3, 5)
        r = tools["place_entities"](json.dumps([{"name": "captive-biter-spawner", "x": x, "y": y}]), surface="nauvis", dry_run=not apply)
        print(str(r)[:300])
        if apply:
            config()
    elif step == "status":
        print(L(STATUS % (OX, OY, OX + 18, OY + 13, OX + 9, OY + 6)))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
