#!/usr/bin/env python3
"""Rebuild an old-hull inner shuttle in place as the prototype (the Captain, 2026-11-17: "Upgrade all of the inner shuttle designs with the
newer prototype"). The prototype is Nauvis-Proto 1 Shuttle: the inner_shuttle.py hull, seven bays (409 slots), eight thrusters, four collectors.
The ship keeps its platform, name, hub, cargo, requests and schedule: nothing is created except placed entities and deck.
  1  pause; read the tanks
  2  clear what stands where the new bays go (items go into the hub), lay the new deck, place the bays: the hub only ever grows.
     The old bays stand at (0,-6) and (0,-10), where the new hull has bays too, so they stay.
  3  clear the rest of the old hull into the hub, cut the deck to the new outline, place the new hull, configure it
  4  pour the tank contents back, put the old machines' modules into the new ones, lower the schedule's propellant marks to the
     prototype's (one tank of three is on the wire: 14,000 at Nauvis, 22,000 away), restore the pause state
Usage: inner_upgrade.py list | NAME [--apply]      (NAME as in "Nauvis-Gleba 2 Shuttle"; the ship must be in an orbit)"""
import json
import sys
import time

import inner_shuttle as I
from _game import tools
from _wheels import place_all

A = I.A
L = tools["run_lua"]
PROTO = "Nauvis-Proto 1 Shuttle"
TANKS = {"water": [(-1.5, 11.5), (1.5, 11.5)], "thruster-oxidizer": [(-7.5, 11.5), (-7.5, 14.5), (-4.5, 14.5)], "thruster-fuel": [(5.5, 11.5), (5.5, 14.5), (10.5, 14.5)]}
MARKS = {20000: I.HOME["fuel"], 32000: I.AWAY["fuel"]}

LIST = ("local o={} for _,p in pairs(game.forces.player.platforms) do if p.name:find('Nauvis%-%a+ %d+ Shuttle') then local s=p.surface "
        "o[#o+1]=p.name:gsub('^%[.-%]%s*','')..' | '..(p.space_location and p.space_location.name or 'in transit')..' | thrusters '..s.count_entities_filtered{name='thruster'}..' bays '..s.count_entities_filtered{name='cargo-bay'}"
        "..' collectors '..s.count_entities_filtered{name='asteroid-collector'}..' slots '..#p.hub.get_inventory(defines.inventory.hub_main) end end rcon.print(table.concat(o,string.char(10)))")
READ = ("local s=game.surfaces['SURF'] local p=s.platform local fl={} for _,t in pairs(s.find_entities_filtered{type='storage-tank'}) do for k,v in pairs(t.get_fluid_contents()) do fl[k]=(fl[k] or 0)+v end end "
        "local md={} for _,e in pairs(s.find_entities_filtered{type={'assembling-machine','furnace'}}) do local m=e.get_module_inventory() if m then for _,it in pairs(m.get_contents()) do local k=it.name..'|'..it.quality md[k]=(md[k] or 0)+it.count end end end "
        "local was=p.paused p.paused=true rcon.print(helpers.table_to_json({mods=md,loc=p.space_location and p.space_location.name or 'none',paused=was,fluids=fl,thrusters=s.count_entities_filtered{name='thruster'},bays=s.count_entities_filtered{name='cargo-bay'}}))")
# zone: 1 = only what touches the new bays' ground (x -6..6, y -16..-4), 0 = everything. The hub and cargo bays are never touched.
STRIP = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local inv=hub.get_inventory(defines.inventory.hub_main) local kept,lost,n=0,0,0 "
         "local function save(st) if st and st.valid_for_read then local c=st.count local put=inv.insert(st) kept=kept+put lost=lost+c-put end end "
         "for _,e in pairs(s.find_entities_filtered{force='player'}) do if e.valid and e.name~='space-platform-hub' and e.name~='cargo-bay' then local b=e.bounding_box "
         "if ZONE==0 or (b.right_bottom.x>-6 and b.left_top.x<6 and b.right_bottom.y>-16 and b.left_top.y<-4) then "
         "if e.type=='item-request-proxy' then e.destroy() else "
         "for i=1,e.get_max_inventory_index() do local v=e.get_inventory(i) if v then for k=1,#v do save(v[k]) end end end "
         "if e.type=='inserter' then save(e.held_stack) end "
         "if e.type=='transport-belt' or e.type=='underground-belt' then for i=1,e.get_max_transport_line_index() do for _,it in pairs(e.get_transport_line(i).get_contents()) do "
         "local put=inv.insert{name=it.name,count=it.count,quality=it.quality} kept=kept+put lost=lost+it.count-put end end end "
         "e.destroy() n=n+1 end end end end rcon.print('cleared '..n..' entities, items into the hub '..kept..', lost '..lost)")
POUR = ("local s=game.surfaces['SURF'] local o={} for fn,spec in pairs(FL) do local done=0 for _,q in pairs(spec.at) do local t=s.find_entities_filtered{name='storage-tank',position=q,radius=0.5}[1] "
        "if t and spec.n-done>1 then done=done+t.insert_fluid{name=fn,amount=spec.n-done} end end o[#o+1]=fn..' '..string.format('%.0f',done)..' of '..string.format('%.0f',spec.n) end rcon.print('poured back: '..table.concat(o,', '))")
# Modules are goods, so only what the old machines held goes in. Productivity first where the recipe takes it, then speed, then efficiency.
MODS = ("local s=game.surfaces['SURF'] local inv=s.platform.hub.get_inventory(defines.inventory.hub_main) local n=0 "
        "for _,a in pairs(ALLOW) do local left=a[3] for _,e in pairs(s.find_entities_filtered{type={'assembling-machine','furnace'}}) do local m=e.get_module_inventory() if m then "
        "while left>0 and m.count_empty_stacks()>0 and inv.get_item_count{name=a[1],quality=a[2]}>0 and m.can_insert{name=a[1],count=1,quality=a[2]} do if m.insert{name=a[1],count=1,quality=a[2]}==0 then break end "
        "inv.remove{name=a[1],count=1,quality=a[2]} n=n+1 left=left-1 end end end end rcon.print('modules fitted from the hub '..n)")
ORDER = ["productivity", "speed", "efficiency", "quality"]


def allow(mods):
    """The old machines' modules as a Lua list, productivity first (it only goes where the recipe takes it), higher tiers first."""
    rows = sorted(((k.split("|")[0], k.split("|")[1], int(v)) for k, v in (mods or {}).items()),
                  key=lambda r: (ORDER.index(r[0].split("-")[0]) if r[0].split("-")[0] in ORDER else 9, r[0].endswith("module"), -ord(r[0][-1])))
    return "{" + ",".join("{'%s','%s',%d}" % r for r in rows) + "}"


SCHED = ("local p=game.surfaces['SURF'].platform local sc=p.schedule local n=0 local M=MARKS if sc then for _,r in pairs(sc.records) do for _,c in pairs(r.wait_conditions or {}) do local cd=c.condition "
         "if c.type=='circuit' and cd and cd.first_signal and cd.first_signal.type=='fluid' and M[cd.constant] then cd.constant=M[cd.constant] n=n+1 end end end p.schedule=sc end p.paused=PAUSED "
         "rcon.print('schedule propellant marks lowered '..n..', paused='..tostring(p.paused))")
ARMED = "local n=0 for _,t in pairs(game.surfaces['SURF'].find_entities_filtered{name='gun-turret'}) do if t.get_inventory(defines.inventory.turret_ammo).is_empty() then n=n+1 end end rcon.print(n)"
ADD = "local s=game.surfaces['SURF'] local add={} for _,p in pairs(LIST) do add[#add+1]={name='space-platform-foundation',position=p} end s.set_tiles(add) rcon.print('deck laid '..#add)"


def upgrade(name, apply):
    A.NAME = name
    found = A.surface()
    if not found:
        return print("no platform named", name)
    sf = found[0]
    print(A.layout())
    if not apply:                                                         # the dry run cannot see through the old hull: it only reads the ship
        st = json.loads(L(READ.replace("SURF", sf).replace("p.paused=true", "")))
        return print("==", name, sf, st, "(nothing changed; --apply rebuilds)")
    st = json.loads(L(READ.replace("SURF", sf)))
    print("==", name, sf, st)
    if st["loc"] == "none" or st["thrusters"] != 4 or st["bays"] > 2:
        L("game.surfaces['%s'].platform.paused=%s" % (sf, "true" if st["paused"] else "false"))
        return print("in transit" if st["loc"] == "none" else "not an old hull (thrusters %s, bays %s): left alone" % (st["thrusters"], st["bays"]))
    lst = "{" + ",".join("{%d,%d}" % t for t in sorted(A.tiles)) + "}"
    bays = [e for e in A.ents if e["name"] == "cargo-bay"]
    rest = [e for e in A.ents if e["name"] != "cargo-bay"]
    print(L(ADD.replace("SURF", sf).replace("LIST", lst)))
    place_all(bays, sf, True)                                             # the bays whose ground is already free go up first, so a full hub has room for what is cleared
    print(L(STRIP.replace("SURF", sf).replace("ZONE", "1")))
    ok, bad = place_all(bays, sf, True)
    have = int(L("rcon.print(game.surfaces['%s'].count_entities_filtered{name='cargo-bay'})" % sf))
    print("bays placed", ok, "already there", bad, "standing", have)
    if have != 7:
        return print("STOP: expected 7 bays; ship left paused for a look")
    print(L(STRIP.replace("SURF", sf).replace("ZONE", "0")))
    print(L(A.TILES.replace("SURF", sf).replace("LIST", lst)))
    ok, bad = place_all(rest, sf, True)
    print("hull placed", ok, "failed", bad)
    if bad:
        return print("STOP: hull incomplete; ship left paused for a look")
    A.configure(sf)
    fl = ",".join("['%s']={n=%f,at={%s}}" % (k, v, ",".join("{%s,%s}" % q for q in TANKS[k])) for k, v in (st["fluids"] or {}).items() if k in TANKS)
    print(L(POUR.replace("SURF", sf).replace("FL", "{" + fl + "}")))
    print(L(MODS.replace("SURF", sf).replace("ALLOW", allow(st["mods"]))))
    for _ in range(30):                                                   # held until every gun is loaded: a rebuilt ship left at once with empty turrets
        if L(ARMED.replace("SURF", sf)).strip() == "0":
            break
        time.sleep(5)
    print(L(SCHED.replace("SURF", sf).replace("MARKS", "{" + ",".join("[%d]=%d" % kv for kv in MARKS.items()) + "}").replace("PAUSED", "true" if st["paused"] else "false")))
    print(L(A.STATUS.replace("SURF", sf)).replace(" ; ", "\n"))


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "list":
        print(L(LIST))
    else:
        upgrade(sys.argv[1], "--apply" in sys.argv)
