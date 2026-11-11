"""
Fulgora home island (scrap patch around 22,-95): mine raw scrap and load it on the train to the base (the Captain's order 2026-11-11:
processing happens at the base, scrap travels by elevated rail).

Track: y -105, stop `Scrap Home Load` at (1,-107). Train: locomotive, 4 cargo wagons, locomotive. Wagons stop centred on x 11, 18, 25, 32.
South of the track, per wagon (6 tiles):  inserter row -104 (chest to wagon), steel chests row -103, inserter row -102 (belt to chest), belt row -101.
Each wagon has its own belt: it rises north through the drill field in the column under the wagon's east end and turns west along row -101.
Field: per belt, electric mining drills on both sides facing it, 5 down (rows -100..-84 with a 2-row gap at -94/-93 for a substation and a rod).

Steps: teardown (old drill-and-recycler block, old train, lattice pieces in the way), build [--apply], modules, train
"""
import json
import sys

from _game import tools

WAGONS = (11, 18, 25, 32)
DRILL_Y = (-98.5, -95.5, -90.5, -87.5, -84.5)


def lua(code):
    out = tools["run_lua"](code).strip()
    try:
        d = json.loads(out)
        return d["result"] if isinstance(d, dict) and "result" in d else d
    except Exception:
        return out


TEARDOWN = (
    "local s=game.surfaces.fulgora local f=game.forces.player local n=0 local mods=0 local fuel=0 if s.count_entities_filtered{name='steel-chest',position={10.5,-118.5},radius=0.4}==0 then s.create_entity{name='steel-chest',position={10.5,-118.5},force=f} end local keepers=s.find_entities_filtered{name='steel-chest',area={{7,-120},{12,-117}}} table.sort(keepers,function(x,y) return x.position.x>y.position.x end) "
    "for _,e in pairs(s.find_entities_filtered{area={{9.5,-99},{46.5,-81.5}},force=f,type={'mining-drill','furnace','transport-belt','underground-belt'}}) do "
    "if e.type=='mining-drill' then for _,m in pairs(e.get_module_inventory().get_contents()) do mods=mods+m.count for _,c in pairs(keepers) do if m.count>0 then m.count=m.count-c.insert{name=m.name,count=m.count,quality=m.quality} end end end end e.destroy() n=n+1 end "
    "for _,e in pairs(s.find_entities_filtered{area={{9.5,-99},{46.5,-81.5}},force=f,name='medium-electric-pole'}) do e.destroy() n=n+1 end "
    "for _,e in pairs(s.find_entities_filtered{area={{16,-104},{25,-96.5}},force=f,name={'substation','accumulator','lightning-rod'}}) do e.destroy() n=n+1 end "
    "for _,e in pairs(s.find_entities_filtered{area={{36.5,-101.5},{38.9,-99.5}},force=f,name='accumulator'}) do e.destroy() n=n+1 end "
    "for _,e in pairs(s.find_entities_filtered{area={{-2,-108},{46,-103}},force=f,type={'locomotive','cargo-wagon','train-stop'}}) do "
    "if e.type=='locomotive' then fuel=fuel+e.get_fuel_inventory().get_item_count('solid-fuel') end e.destroy() n=n+1 end "
    "local g=0 for _,e in pairs(s.find_entities_filtered{area={{7,-104.5},{39,-83}},type='item-entity'}) do local st=e.stack if st.valid_for_read then for _,c in pairs(keepers) do if st.valid_for_read then local d=c.insert(st) if d>=st.count then break else st.count=st.count-d end end end end e.destroy() g=g+1 end "
    "local c=s.find_entities_filtered{name='steel-chest',position={8.5,-118.5},radius=1.6} if fuel>0 and c[1] then c[1].insert{name='solid-fuel',count=fuel} end "
    "rcon.print(helpers.table_to_json({removed=n,drill_modules=mods,fuel_returned=fuel,ground_items_removed=g}))"
)


def entities():
    e = [{"name": "straight-rail", "x": x, "y": -105, "direction": 4} for x in (1, 3, 5)]
    e.append({"name": "train-stop", "x": 1, "y": -107, "direction": 12})
    for c in WAGONS:
        xr = c + 2
        for t in range(c - 3, c + 3):
            e.append({"name": "bulk-inserter", "x": t + 0.5, "y": -103.5, "direction": 8})
            e.append({"name": "steel-chest", "x": t + 0.5, "y": -102.5})
            e.append({"name": "bulk-inserter", "x": t + 0.5, "y": -101.5, "direction": 8})
            e.append({"name": "express-transport-belt", "x": t + 0.5, "y": -100.5, "direction": 12})
        for row in range(-100, -83):
            e.append({"name": "express-transport-belt", "x": xr + 0.5, "y": row + 0.5, "direction": 0})
        e.append({"name": "substation", "x": xr - 2, "y": -93})
        e.append({"name": "lightning-rod", "x": xr - 0.5, "y": -93.5})
        e.append({"name": "lightning-rod", "x": xr + 1.5, "y": -93.5})
    return e


def drills():
    d = []
    for c in WAGONS:
        xr = c + 2
        for y in DRILL_Y:
            d.append((xr - 1.5, y, 4))
            d.append((xr + 2.5, y, 12))
    spec = "{" + ",".join(f"{{{x},{y},{dr}}}" for x, y, dr in d) + "}"
    ok = lua("local s=game.surfaces.fulgora local o={} for i,u in pairs(" + spec + ") do o[i]=s.count_entities_filtered{name='scrap',area={{u[1]-2.49,u[2]-2.49},{u[1]+2.49,u[2]+2.49}}} end rcon.print(helpers.table_to_json(o))")
    ok = json.loads(ok) if isinstance(ok, str) else ok
    return [{"name": "electric-mining-drill", "x": x, "y": y, "direction": dr} for (x, y, dr), n in zip(d, ok) if n > 0], len(d)


MODULES = (
    "local f=game.forces.player local s=game.surfaces.fulgora local want=%d local put=0 local have=0 "
    "local chest=s.find_entities_filtered{name='steel-chest',position={8.5,-118.5},radius=1.6} "
    "for _,d in pairs(s.find_entities_filtered{name='electric-mining-drill',area={{9,-101},{39,-83}}}) do local inv=d.get_module_inventory() local room=#inv-inv.get_item_count() "
    "while room>0 do local got=0 for _,c in pairs(s.find_entities_filtered{name='steel-chest',area={{7,-120},{12,-117}}}) do if got==0 and c.remove_item{name='speed-module-2',count=1,quality='rare'}>0 then got=2 end end if got==2 then inv.insert{name='speed-module-2',count=1,quality='rare'} room=room-1 end if got~=2 then for _,net in pairs(f.logistic_networks.nauvis) do if got==0 then got=net.remove_item({name='speed-module-2',count=1,quality='normal'}) end end "
    "if got==0 then break end inv.insert{name='speed-module-2',count=1} put=put+1 room=room-1 end end have=have+inv.get_item_count() end rcon.print('modules moved from Nauvis '..put..' in drills now '..have)"
)

TRAIN = (
    "local s=game.surfaces.fulgora local f=game.forces.player local o={} local a=s.find_entities_filtered{name='train-stop',position={1,-107},radius=1.5}[1] a.backer_name='Scrap Home Load' a.trains_limit=1 "
    "local chest=s.find_entities_filtered{name='steel-chest',position={8.5,-118.5},radius=1.6} local locos=s.find_entities_filtered{name='locomotive',area={{-2,-107},{45,-103}}} "
    "for _,l in pairs(locos) do local want=50 for _,c in pairs(chest) do if want>0 then local g=c.remove_item{name='solid-fuel',count=want} if g>0 then l.get_fuel_inventory().insert{name='solid-fuel',count=g} want=want-g end end end o[#o+1]='fuel '..l.get_fuel_inventory().get_item_count('solid-fuel') end "
    "local t=locos[1].train o[#o+1]='carriages '..#t.carriages "
    "t.schedule={current=1,records={{station='Scrap Home Load',wait_conditions={{type='full',compare_type='or'},{type='inactivity',ticks=600,compare_type='or'}}},{station='Scrap Base Unload',wait_conditions={{type='empty',compare_type='or'},{type='inactivity',ticks=600,compare_type='or'}}}}} "
    "t.group='Scrap Home' rcon.print(table.concat(o,' | '))"
)


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    if step == "teardown":
        print(lua(TEARDOWN))
    elif step == "build":
        d, total = drills()
        ents = entities() + d
        print(f"drills with scrap in reach: {len(d)} of {total}; entities {len(ents)}")
        print(tools["place_entities"](json.dumps(ents), surface="fulgora", dry_run=not apply)[:2000])
    elif step == "modules":
        print(lua(MODULES % 3))
    elif step == "train":
        ents = [{"name": "locomotive", "x": 4, "y": -105, "direction": 12}, {"name": "locomotive", "x": 39, "y": -105, "direction": 4}]
        ents += [{"name": "cargo-wagon", "x": c, "y": -105, "direction": 12} for c in WAGONS]
        ents.sort(key=lambda e: e["x"])
        print(tools["place_entities"](json.dumps(ents), surface="fulgora", dry_run=False)[:800])
        print(lua(TRAIN))


if __name__ == "__main__":
    main()
