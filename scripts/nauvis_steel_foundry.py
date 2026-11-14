#!/usr/bin/env python3
"""Steel by foundry at the south-west iron mine on Nauvis (ore patch -464,284; furnace rows at y 305..313).

Why: an electric furnace makes 1 steel from 5 ore; a melting foundry plus a casting foundry make 0.75 steel from 1 ore (50 ore + 1 calcite
-> 750 molten iron, 30 molten iron -> 1.5 steel). The mine's ore trunk (x -438.5, flowing south) backs up because the furnace rows below it
stand with full chests, so the ore is there for the taking.

Layout (east of the trunk, y 273..301; all epic):
  trunk x -438.5 | ore inserters x -437.5 | melters (facing east) centre x -434.5 | molten iron main x -431.5
  | casters A (facing east) centre x -428.5 | inserter -425.5, steel chest -424.5, inserter -423.5 | casters B (facing west) centre x -420.5
  | molten iron main x -417.5, joined to the first along y 274.5 | roboport (-414,287) so the steel chests are in the logistic network.
  | casters C (facing east) centre x -414.5 at y 277.5, 282.5, 296.5, steel chests x -410.5.
  Calcite: requester chests at x -434.5 (y 265.5, 273.5, 286.5, 287.5, 300.5), one inserter into each melter. The Nauvis landing pad
  asks for 1,000 calcite (section "Nauvis Steel Foundry: Calcite"), which the Nauvis Wheel drops from orbit.
Foundry ports (read from the prototype): facing east the two outputs are on the east edge at y-1 and y+1, the inputs on the west edge;
facing west the inputs are on the east edge.

Usage: nauvis_steel_foundry.py            dry run
       nauvis_steel_foundry.py --apply    save, clear trees, build, set directions and calcite requests, chart
       nauvis_steel_foundry.py status     what every foundry is doing, molten iron, steel and calcite on site
       nauvis_steel_foundry.py furnacegate [RESERVE|off]  old furnace steel cells run only while network steel < RESERVE (default 20000)
       nauvis_steel_foundry.py modules [speed-module-2]   fill empty foundry module slots from the logistic network's own stock (no spawning)"""
import json
import sys

from _game import tools

Q = {"quality": "epic"}
MELT_X, MAIN1_X, CAST_A_X, CHEST_X, CAST_B_X, MAIN2_X = -434.5, -431.5, -428.5, -424.5, -420.5, -417.5
MELT_Y = [269.5, 277.5, 282.5, 291.5, 296.5]
CAST_Y = [277.5, 282.5, 287.5, 292.5, 297.5]
# calcite: (inserter y, direction = pickup side, chest y) per melter, in MELT_Y order
CALCITE = [(266.5, 0, 265.5), (274.5, 0, 273.5), (285.5, 8, 286.5), (288.5, 0, 287.5), (299.5, 8, 300.5)]
SUBSTATIONS = [(-433, 274), (-433, 287), (-433, 300), (-425, 280), (-425, 295), (-415, 291), (-411, 280)]
CAST_C_X, CAST_C_Y = -414.5, [277.5, 282.5, 296.5]
ROBOPORT = (-414, 287)
BOX = "{{-438,264},{-408,302}}"
CALCITE_REQUEST = 400


def e(name, x, y, direction=None, recipe=None):
    d = {"name": name, "x": x, "y": y, "params": dict(Q)}
    if direction is not None:
        d["direction"] = direction
    if recipe:
        d["recipe"] = recipe
    return d


def plan():
    ents = [e("substation", x, y) for x, y in SUBSTATIONS]
    ents.append(e("roboport", *ROBOPORT))
    for cy, (iy, idir, chy) in zip(MELT_Y, CALCITE):
        ents.append(e("foundry", MELT_X, cy, 4, "iron-ore-melting"))
        for dy in (-1, 0, 1):
            ents.append(e("bulk-inserter", -437.5, cy + dy, 12))
        ents.append(e("requester-chest", MELT_X, chy))
        ents.append(e("bulk-inserter", MELT_X, iy, idir))
    for cy in CAST_Y:
        ents.append(e("foundry", CAST_A_X, cy, 4, "casting-steel"))
        ents.append(e("foundry", CAST_B_X, cy, 12, "casting-steel"))
        ents.append(e("bulk-inserter", -425.5, cy, 12))
        ents.append(e("passive-provider-chest", CHEST_X, cy))
        ents.append(e("bulk-inserter", -423.5, cy, 4))
    for cy in CAST_C_Y:
        ents.append(e("foundry", CAST_C_X, cy, 4, "casting-steel"))
        ents.append(e("bulk-inserter", -411.5, cy, 12))
        ents.append(e("passive-provider-chest", -410.5, cy))
    y = 268.5
    while y <= 299.5:
        ents.append(e("pipe", MAIN1_X, y))
        if y >= 274.5:
            ents.append(e("pipe", MAIN2_X, y))
        y += 1
    x = MAIN1_X + 1
    while x < MAIN2_X:
        ents.append(e("pipe", x, 274.5))
        x += 1
    return ents


CLEAR = ("local s=game.surfaces.nauvis local t=0 for _,x in pairs(s.find_entities_filtered{area=" + BOX + ",type={'tree','simple-entity','item-entity','corpse','fish'}}) do "
         "if x.force.name~='player' then x.destroy() t=t+1 end end rcon.print('cleared '..t..' natural pieces')")

CONFIG = ("local s=game.surfaces.nauvis local f=game.forces.player local o={} "
          "for _,m in pairs(s.find_entities_filtered{name='foundry',area=" + BOX + "}) do local x=m.position.x "
          "if x<-432 then m.direction=defines.direction.east if not m.get_recipe() then m.set_recipe('iron-ore-melting') end "
          "elseif x<-426 then m.direction=defines.direction.east if not m.get_recipe() then m.set_recipe('casting-steel') end "
          "elseif x<-418 then m.direction=defines.direction.west if not m.get_recipe() then m.set_recipe('casting-steel') end "
          "else m.direction=defines.direction.east if not m.get_recipe() then m.set_recipe('casting-steel') end end end "
          "local n=0 for _,c in pairs(s.find_entities_filtered{name='requester-chest',area=" + BOX + "}) do local ss=c.get_logistic_sections() "
          "local se=ss.sections[1] or ss.add_section() se.set_slot(1,{value={name='calcite',quality='normal'},min=" + str(CALCITE_REQUEST) + "}) n=n+1 end "
          "f.chart(s," + BOX + ") rcon.print('directions set, calcite requests '..n..', charted')")

STATUS = ("local s=game.surfaces.nauvis local E=defines.entity_status local SN={} for k,v in pairs(E) do SN[v]=k end local o={} local fl=0 "
          "for _,m in pairs(s.find_entities_filtered{name='foundry',area=" + BOX + "}) do local r=m.get_recipe() "
          "o[#o+1]=string.format('%s %.1f,%.1f %s done %d net %d',r and r.name or '-',m.position.x,m.position.y,SN[m.status] or m.status,m.products_finished,m.electric_network_id or 0) "
          "if r and r.name=='iron-ore-melting' then fl=fl+(m.get_fluid_count('molten-iron') or 0) end end "
          "local st,ca=0,0 for _,c in pairs(s.find_entities_filtered{type='logistic-container',area=" + BOX + "}) do local inv=c.get_inventory(defines.inventory.chest) "
          "st=st+inv.get_item_count('steel-plate') ca=ca+inv.get_item_count('calcite') end "
          "local ins={} for _,i in pairs(s.find_entities_filtered{type='inserter',area=" + BOX + "}) do local k=SN[i.status] or i.status ins[k]=(ins[k] or 0)+1 end "
          "local it={} for k,v in pairs(ins) do it[#it+1]=k..'='..v end "
          "o[#o+1]='molten iron in melters '..math.floor(fl)..', steel in chests '..st..', calcite in chests '..ca..', inserters '..table.concat(it,' ') "
          "rcon.print(table.concat(o,'\\n'))")


MODULES = ("local s=game.surfaces.nauvis local ln=s.find_logistic_network_by_position({-424.5,287.5},game.forces.player) local put,short=0,0 "
           "for _,m in pairs(s.find_entities_filtered{name='foundry',area=" + BOX + "}) do local inv=m.get_module_inventory() "
           "for i=1,#inv do if not inv[i].valid_for_read then local got=ln.remove_item({name='MODULE',count=1,quality='normal'}) "
           "if got>0 then inv[i].set_stack({name='MODULE',count=1}) put=put+1 else short=short+1 end end end end "
           "rcon.print('modules moved from the network into foundries: '..put..', slots left empty for lack of stock: '..short)")


# The old steel cells (requester chest -> inserter -> electric furnace -> provider chest) burn 5 iron plates a steel. Their feeding inserters
# get a logistic condition: work only while the network holds fewer than RESERVE steel, so they are the backup, not the base load.
FGATE = ("local s=game.surfaces.nauvis local n,g=0,0 for _,m in pairs(s.find_entities_filtered{name='electric-furnace'}) do "
         "local r=m.get_recipe() local pr=m.previous_recipe local nm=r and r.name or (pr and (type(pr.name)=='string' and pr.name or pr.name.name)) "
         "if nm=='steel-plate' then n=n+1 for _,i in pairs(s.find_entities_filtered{type='inserter',area={{m.position.x-3,m.position.y-3},{m.position.x+3,m.position.y+3}}}) do "
         "local pt=i.pickup_target if i.drop_target==m and pt and pt.name=='requester-chest' then local cb=i.get_or_create_control_behavior() ACTION g=g+1 end end end end "
         "rcon.print('steel furnaces '..n..', chest-fed feeding inserters changed: '..g)")
FGATE_ON = "cb.connect_to_logistic_network=true cb.logistic_condition={first_signal={type='item',name='steel-plate'},comparator='<',constant=RESERVE}"
FGATE_OFF = "cb.connect_to_logistic_network=false"


def main():
    if "furnacegate" in sys.argv:
        arg = sys.argv[sys.argv.index("furnacegate") + 1] if len(sys.argv) > sys.argv.index("furnacegate") + 1 else "20000"
        act = FGATE_OFF if arg == "off" else FGATE_ON.replace("RESERVE", arg)
        print(tools["run_lua"](FGATE.replace("ACTION", act)))
        return
    if "modules" in sys.argv:
        name = sys.argv[sys.argv.index("modules") + 1] if len(sys.argv) > sys.argv.index("modules") + 1 else "speed-module-2"
        print(tools["run_lua"](MODULES.replace("MODULE", name)))
        return
    if "status" in sys.argv:
        print(tools["run_lua"](STATUS))
        return
    apply = "--apply" in sys.argv
    ents = plan()
    if not apply:
        r = json.loads(tools["place_entities"](json.dumps(ents), surface="nauvis", dry_run=True))
        print("dry run:", len(ents), "entities;", {k: v for k, v in r.items() if k in ("placed", "failed", "would_place", "ok")})
        for f in (r.get("failures") or r.get("errors") or [])[:20]:
            print("  ", f)
        return
    print(tools["save_game"]("skippy"))
    print(tools["run_lua"](CLEAR))
    r = json.loads(tools["place_entities"](json.dumps(ents), surface="nauvis", dry_run=False))
    print("placed", r.get("placed"), "failed", r.get("failed"))
    for f in (r.get("failures") or r.get("errors") or [])[:20]:
        print("  ", f)
    print(tools["run_lua"](CONFIG))


if __name__ == "__main__":
    main()
