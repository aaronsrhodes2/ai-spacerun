#!/usr/bin/env python3
"""Gleba, first steps: the trigger techs. The base (solar, substations pitch 20, roboports pitch 48, trash yard chest at 2.5,2.5) was
prepared on 2026-11-10 with planet_base.py. Yumako trees are north-west (x -200..-130, y -160..-100), jellystems east (x 197..205,
y 64..112) across wetland, egg rafts from 240 tiles out (nearest small raft -135,199).
  east     two roboports (131,71) (160,86) and three substations along the land strip toward the jellystems
  jelly    order one jellystem deconstructed (robot mining earns the jellynut trigger); fruit goes to the trash yard
  boot     50 logistic robots; assembler (5.5,8.5) making nutrients from the spoilage in the trash yard (10 crafts earn biochamber, 500 artificial soil);
           a second assembler turns the mined jellynut into jelly, which spoils in its red chest and feeds the first
  trunks   the two fruit belts from docs/gleba_routes.json (found with a tile search around everything built): yumako from the north-west farm,
           jellynut from the east farm, meeting at (126,-4) where each side-loads onto its own lane of the core's fruit belt. Wetland under
           them is landfilled first.
  farms    one agricultural tower on each natural soil field (it harvests the wild plants in reach and replants), an inserter onto the trunk,
           a blue chest asking for seeds with an inserter into the tower, a roboport and substations for each
  farmjunk the towers also harvest the wild trees in reach (wood, stone, spoilage). The trunk inserter takes fruit and spoilage only; a second
           inserter takes everything else into a red chest. Wood and stone already on the belts are moved to the trash yard chest.
  water    offshore pump (156.5,26.5) and a pipe west along y 26, north along x 150, west along y 12 (under the jellynut trunk at x 136)
           into the egg chambers' water main at (123.5,12.5)
  raid     the first eggs: a small solar outpost (substation, four panels, two accumulators) on the land north-east of the lone small egg
           raft at (-134,199); with --turrets also two laser turrets, which shoot the raft (no ammunition involved)
  loot     picks the eggs up off the ground there: one (with five nutrients off the belt) into the assembler at (5.5,13.5) that crafts the
           one biochamber the bioflux research asks for, one into each egg chamber
  soil     artificial soil (researched) on every wetland tile of the matching kind inside each tower's reach, so the tower has more cells to plant
  seed     gives one egg off the egg belt (surplus on its way to the burner) to every egg chamber that has none, so every pair runs
Usage: gleba.py STEP [--apply] [--turrets]"""
import json
import sys

from _game import tools

REQ = ("local s=game.surfaces.gleba local n=0 for _,q in pairs(SPEC) do local c=s.find_entities_filtered{name='requester-chest',position={q[1],q[2]},radius=0.3}[1] if c then "
       "local ss=c.get_logistic_sections() local se=ss.sections[1] or ss.add_section() local i=0 for name,ct in pairs(q[3]) do i=i+1 se.set_slot(i,{value={name=name,quality='normal'},min=ct}) end n=n+1 end end "
       "rcon.print('requests set on '..n..' chests')")

JELLY = ("local s=game.surfaces.gleba local f=game.forces.player local best,bd for _,e in pairs(s.find_entities_filtered{name='jellystem',area={{190,60},{214,115}}}) do "
         "local d=(e.position.x-160)^2+(e.position.y-86)^2 if not bd or d<bd then best=e bd=d end end "
         "if not best then rcon.print('no jellystem in range') return end local ok=best.order_deconstruction(f) "
         "rcon.print('jellystem '..best.position.x..','..best.position.y..' ordered '..tostring(ok)..' in construction range '..tostring(#s.find_logistic_networks_by_construction_area(best.position,f)>0))")

ROBOTS = ("local s=game.surfaces.gleba local rp=s.find_entities_filtered{name='roboport',position={-3,-3},radius=3}[1] "
          "local need=50-rp.logistic_network.all_logistic_robots local a=need>0 and rp.insert{name='logistic-robot',count=need} or 0 rcon.print('logistic robots added '..a)")


def east():
    return ([{"name": "substation", "x": x, "y": y, "quality": "epic"} for x, y in ((130, 74), (148, 76), (164, 84))]
            + [{"name": "roboport", "x": x, "y": y, "quality": "epic"} for x, y in ((131, 71), (160, 86))])


def boot():
    return [{"name": "assembling-machine-3", "x": 5.5, "y": 8.5, "recipe": "nutrients-from-spoilage"},
            {"name": "requester-chest", "x": 2.5, "y": 8.5, "req": {"spoilage": 50}},
            {"name": "bulk-inserter", "x": 3.5, "y": 8.5, "direction": 12},
            {"name": "bulk-inserter", "x": 7.5, "y": 8.5, "direction": 12},
            {"name": "passive-provider-chest", "x": 8.5, "y": 8.5},
            {"name": "assembling-machine-3", "x": 5.5, "y": 13.5, "recipe": "jellynut-processing"},
            {"name": "requester-chest", "x": 2.5, "y": 13.5, "req": {"jellynut": 50}},
            {"name": "bulk-inserter", "x": 3.5, "y": 13.5, "direction": 12},
            {"name": "bulk-inserter", "x": 7.5, "y": 13.5, "direction": 12},
            {"name": "passive-provider-chest", "x": 8.5, "y": 13.5}]


LANDFILL = ("local s=game.surfaces.gleba local f=game.forces.player if not f.recipes['landfill'].enabled then rcon.print('landfill not researched') return end local t={} "
            "for _,q in pairs(SPEC) do local tl=s.get_tile(q[1],q[2]) if tl.collides_with('water_tile') then t[#t+1]={name='landfill',position={q[1],q[2]}} end end "
            "if APPLY then s.set_tiles(t) end rcon.print('landfill tiles '..#t)")

RARE = {"quality": "epic"}


def landfill(tiles, apply):
    spec = "{" + ",".join("{%d,%d}" % t for t in tiles) + "}"
    print(tools["run_lua"](LANDFILL.replace("SPEC", spec).replace("APPLY", "true" if apply else "false")))


def trunks():
    import os
    routes = json.load(open(os.path.join(os.path.dirname(__file__), "..", "docs", "gleba_routes.json")))
    ents, tiles = [], []
    dirs = {(1, 0): 4, (-1, 0): 12, (0, 1): 8, (0, -1): 0}
    for name, p in routes.items():
        for i, (x, y) in enumerate(p):
            nx, ny = p[i + 1] if i + 1 < len(p) else (x + (x - p[i - 1][0]), y + (y - p[i - 1][1]))
            ents.append({"name": "turbo-transport-belt", "x": x + 0.5, "y": y + 0.5, "direction": dirs[(nx - x, ny - y)], "params": dict(RARE)})
            tiles.append((x, y))
    return ents, tiles


def box(cx, cy, half):
    return [(x, y) for x in range(int(cx - half), int(cx + half)) for y in range(int(cy - half), int(cy + half))]


def farms():
    e = [  # yumako, north-west
        {"name": "substation", "x": -139, "y": -113}, {"name": "roboport", "x": -132, "y": -106},
        {"name": "agricultural-tower", "x": -150.5, "y": -115.5},
        {"name": "bulk-inserter", "x": -148.5, "y": -115.5, "direction": 12},
        {"name": "bulk-inserter", "x": -149.5, "y": -113.5, "direction": 8},
        {"name": "requester-chest", "x": -149.5, "y": -112.5, "req": {"yumako-seed": 10}},
        # jellynut, east
        {"name": "substation", "x": 176, "y": 89}, {"name": "substation", "x": 190, "y": 97}, {"name": "roboport", "x": 187, "y": 84},
        {"name": "agricultural-tower", "x": 195.5, "y": 100.5},
        {"name": "bulk-inserter", "x": 193.5, "y": 100.5, "direction": 4},
        {"name": "bulk-inserter", "x": 195.5, "y": 98.5, "direction": 0},
        {"name": "requester-chest", "x": 195.5, "y": 97.5, "req": {"jellynut-seed": 10}}]
    for x in e:
        x["params"] = dict(RARE)
    tiles = box(176, 89, 1) + box(190, 97, 1) + box(187, 84, 2)
    return e, tiles


FARMJUNK = ("local s=game.surfaces.gleba local o={} local function cfg(x,y,mode,items) local i=s.find_entities_filtered{type='inserter',position={x,y},radius=0.3}[1] i.use_filters=true i.inserter_filter_mode=mode "
            "for k,n in pairs(items) do i.set_filter(k,n) end o[#o+1]=mode..' at '..x..','..y end "
            "cfg(-148.5,-115.5,'whitelist',{'yumako','spoilage'}) cfg(193.5,100.5,'whitelist',{'jellynut','spoilage'}) "
            "cfg(-148.5,-116.5,'blacklist',{'yumako','spoilage'}) cfg(193.5,99.5,'blacklist',{'jellynut','spoilage'}) "
            "local yard=s.find_entities_filtered{name='storage-chest',position={2.5,2.5},radius=0.3}[1] local moved={} "
            "for _,b in pairs(s.find_entities_filtered{type='transport-belt'}) do for l=1,2 do local tl=b.get_transport_line(l) for _,it in pairs(tl.get_contents()) do "
            "if it.name~='yumako' and it.name~='jellynut' and it.name~='spoilage' and it.name~='nutrients' and it.name~='bioflux' and it.name~='pentapod-egg' and it.name~='agricultural-science-pack' and it.name~='yumako-seed' and it.name~='jellynut-seed' then "
            "local n=tl.remove_item{name=it.name,count=it.count} if n>0 then yard.insert{name=it.name,count=n} moved[it.name]=(moved[it.name] or 0)+n end end end end end "
            "rcon.print(table.concat(o,' | ')..' | moved to the trash yard '..helpers.table_to_json(moved))")


def farmjunk():
    e = [{"name": "bulk-inserter", "x": -148.5, "y": -116.5, "direction": 12}, {"name": "passive-provider-chest", "x": -147.5, "y": -116.5},
         {"name": "bulk-inserter", "x": 193.5, "y": 99.5, "direction": 4}, {"name": "passive-provider-chest", "x": 192.5, "y": 99.5}]
    for x in e:
        x["params"] = dict(RARE)
    return e, [(192, 99)]


def water():
    e = []
    for x in range(124, 151):
        if x == 135:
            e.append({"name": "pipe-to-ground", "x": x + .5, "y": 12.5, "direction": 12})
        elif x == 137:
            e.append({"name": "pipe-to-ground", "x": x + .5, "y": 12.5, "direction": 4})
        elif x != 136:
            e.append({"name": "pipe", "x": x + .5, "y": 12.5})
    e += [{"name": "pipe", "x": 150.5, "y": y + .5} for y in range(13, 27)]
    e += [{"name": "pipe", "x": x + .5, "y": 26.5} for x in range(151, 156)]
    e.append({"name": "offshore-pump", "x": 156.5, "y": 26.5, "direction": 4})
    for x in e:
        x["params"] = dict(RARE)
    return e


def raid(turrets):
    e = [{"name": "substation", "x": -126, "y": 193},
         {"name": "solar-panel", "x": -123.5, "y": 192.5}, {"name": "solar-panel", "x": -128.5, "y": 190.5},
         {"name": "solar-panel", "x": -129.5, "y": 196.5}, {"name": "solar-panel", "x": -126.5, "y": 196.5},
         {"name": "accumulator", "x": -124, "y": 195}, {"name": "accumulator", "x": -122, "y": 195}]
    tiles = box(-126, 193, 1) + box(-124, 195, 1) + box(-122, 195, 1)
    for x, y in ((-123.5, 192.5), (-128.5, 190.5), (-129.5, 196.5), (-126.5, 196.5)):
        tiles += [(int(x - 1.5) + i, int(y - 1.5) + j) for i in range(3) for j in range(3)]
    if turrets:
        e += [{"name": "laser-turret", "x": -131, "y": 194}, {"name": "laser-turret", "x": -128, "y": 194}]
        tiles += box(-131, 194, 1) + box(-128, 194, 1)
    for x in e:
        x["params"] = dict(RARE)
    return e, tiles


LOOT = ("local s=game.surfaces.gleba local o={} local eggs={} for _,it in pairs(s.find_entities_filtered{type='item-entity',area={{-150,185},{-118,215}}}) do if it.stack.valid_for_read and it.stack.name=='pentapod-egg' then eggs[#eggs+1]=it end end "
        "o[#o+1]='eggs on the ground '..#eggs if #eggs==0 then rcon.print(o[1]) return end "
        "local function takeegg() local it=table.remove(eggs) if not it then return false end if it.stack.count>1 then it.stack.count=it.stack.count-1 eggs[#eggs+1]=it else it.destroy() end return true end "
        "local B=s.find_entities_filtered{type='assembling-machine',position={5.5,13.5},radius=0.3}[1] local need=5 "
        "for _,b in pairs(s.find_entities_filtered{type='transport-belt',area={{76,9},{124,10}}}) do for l=1,2 do if need>0 then need=need-b.get_transport_line(l).remove_item{name='nutrients',count=need} end end end "
        "if need==0 and takeegg() then B.insert{name='nutrients',count=5} B.insert{name='pentapod-egg',count=1} o[#o+1]='crafter loaded' else o[#o+1]='crafter NOT loaded, nutrients short by '..need end "
        "local n=0 for _,m in pairs(s.find_entities_filtered{name='biochamber',area={{92,13},{124,16}}}) do if takeegg() then m.insert{name='pentapod-egg',count=1} n=n+1 end end o[#o+1]='egg chambers seeded '..n "
        "local left=0 for _,it in pairs(eggs) do left=left+it.stack.count end o[#o+1]='eggs left on the ground '..left rcon.print(table.concat(o,' | '))")


SEED = ("local s=game.surfaces.gleba local o={} local belts=s.find_entities_filtered{type='transport-belt',area={{68,17},{123,18}}} local n,short=0,0 "
        "for _,m in pairs(s.find_entities_filtered{name='biochamber',area={{92,13},{124,16}}}) do local has=m.get_inventory(defines.inventory.crafter_input).get_item_count('pentapod-egg')+m.get_output_inventory().get_item_count('pentapod-egg') "
        "if has==0 and not m.is_crafting() then local got=0 for _,b in pairs(belts) do for l=1,2 do if got==0 then got=b.get_transport_line(l).remove_item{name='pentapod-egg',count=1} end end end "
        "if got>0 then m.insert{name='pentapod-egg',count=1} n=n+1 else short=short+1 end end end rcon.print('egg chambers seeded '..n..', still without an egg '..short)")


SOIL = ("local s=game.surfaces.gleba local f=game.forces.player local o={} for _,q in pairs{{-150.5,-115.5,'yumako'},{195.5,100.5,'jellynut'}} do local art='artificial-'..q[3]..'-soil' "
        "if f.recipes[art].enabled then local a={{q[1]-10.5,q[2]-10.5},{q[1]+10.5,q[2]+10.5}} local t={} for _,tl in pairs(s.find_tiles_filtered{area=a,name='wetland-'..q[3]}) do t[#t+1]={name=art,position=tl.position} end "
        "if APPLY then s.set_tiles(t) end o[#o+1]=q[3]..': '..#t..' wetland tiles to artificial soil; soil tiles in reach now '..s.count_tiles_filtered{area=a,name={art,'natural-'..q[3]..'-soil'}} else o[#o+1]=art..' not researched' end end rcon.print(table.concat(o,' | '))")


def place(ents, apply):
    reqs = [(x["x"], x["y"], x.pop("req")) for x in ents if x.get("req")]
    print(tools["place_entities"](json.dumps(ents), surface="gleba", dry_run=not apply)[:900])
    if apply and reqs:
        spec = "{" + ",".join("{%s,%s,{%s}}" % (x, y, ",".join("['%s']=%d" % kv for kv in r.items())) for x, y, r in reqs) + "}"
        print(tools["run_lua"](REQ.replace("SPEC", spec)))


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    if step == "east":
        place(east(), apply)
    elif step == "jelly":
        print(tools["run_lua"](JELLY) if apply else "(dry run) would order the nearest jellystem deconstructed")
    elif step == "trunks":
        ents, tiles = trunks()
        landfill(tiles, apply)
        for i in range(0, len(ents), 400):
            print(tools["place_entities"](json.dumps(ents[i:i + 400]), surface="gleba", dry_run=not apply)[:600])
    elif step == "farms":
        ents, tiles = farms()
        landfill(tiles, apply)
        place(ents, apply)
    elif step == "farmjunk":
        ents, tiles = farmjunk()
        landfill(tiles, apply)
        place(ents, apply)
        if apply:
            print(tools["run_lua"](FARMJUNK))
    elif step == "water":
        place(water(), apply)
    elif step == "raid":
        ents, tiles = raid("--turrets" in sys.argv)
        landfill(tiles, apply)
        place(ents, apply)
    elif step == "loot":
        print(tools["run_lua"](LOOT) if apply else "(dry run) would collect eggs")
    elif step == "seed":
        print(tools["run_lua"](SEED) if apply else "(dry run) would seed empty egg chambers from the egg belt")
    elif step == "soil":
        print(tools["run_lua"](SOIL.replace("APPLY", "true" if apply else "false")))
    elif step == "boot":
        place(boot(), apply)
        if apply:
            print(tools["run_lua"](ROBOTS))


if __name__ == "__main__":
    main()
