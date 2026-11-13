#!/usr/bin/env python3
"""Gleba core: the block that turns fruit into agricultural science, laid out for spoilage first (the Captain's warning, 2026-11-12).

Rules of the layout
  * Only fruit (60 min), bioflux (120 min) and science (60 min) ride belts for long. Mash and jelly never touch a belt: the processors hand
    them straight to the bioflux chambers.
  * Every belt is a dead end with an inserter at the end that takes spoilage only and burns it in a heating tower. Whatever waits too long
    turns to spoilage at the front of the queue and leaves; nothing can fill a belt for good. The egg belt and the junk belt end in an
    inserter that burns everything, so eggs never wait.
  * Every machine has a junk inserter (spoilage only; seeds too on the processors) so spoiled ingredients or products never block it.
  * Restart from nothing: an electric assembler mashes yumako (needs no nutrients); its mash feeds a chamber making nutrients, and what spoils
    feeds an electric assembler making nutrients from spoilage. Both put nutrients at the head of the nutrient belt.
  * Egg chambers work in pairs that hand each other eggs directly, so they never depend on a belt; only the surplus goes on the egg belt.
  * Priority by position: nutrients pass the fruit line first, then the egg chambers, then science. Bioflux passes the nutrient chamber before science.

Rows (design y; the game y is one more, see DY): 1 junk belt K (west) | 2 fruit belt F (west; yumako and jellynut each on a lane) | 3 inserters |
4-6 line 1 | 7 inserters | 8 nutrient belt N, head (east; turns at x=124 and comes back as) 10 N, tail (west) | 9 bioflux belt B (west) |
11 inserters + water main | 12-14 line 2 | 15 inserters | 16 egg belt E (west) | 17 science belt S (east).
Line 1 (centre tile x): tower 74, AM3 nutrients-from-spoilage 77, AM3 yumako 81, mash nutrients 85, NU 89, YP 93, BF 97, JP 101, BF 105, YP 109,
YP 113, BF 117, JP 121.   Line 2: tower 65, SCI 69..85, EGG 93..121 (pairs 93+97, 101+105, 109+113, 117+121), all facing east for the water.

Usage: gleba_core.py build|config|throttle|recipes|status [--apply]
(throttle also turns a block built before 2026-11-12 evening, with four self-feeding pairs, into the keeper + production form)"""
import json
import sys

from _game import tools

Q = {"quality": "epic"}
YP, BF, JP = (93, 109, 113), (97, 105, 117), (101, 121)
SCI = (69, 73, 77, 81, 85)
EGG = (93, 97, 101, 105, 109, 113, 117, 121)
KEEPER = (117, 121)
DY = 1                                   # the whole block sits one tile lower than the row numbers above (roboport at 96,0 is in row 1)
ents, cfg, recipes = [], [], []          # cfg: (x, y, [filters], stack or 0)


def put(name, x, y, d=0, **kw):
    e = {"name": name, "x": x + 0.5, "y": y + 0.5 + DY, "direction": d, "params": dict(Q)}
    e.update(kw)
    ents.append(e)


def ins(x, y, d, filt=None, long=False, stack=0, kind=None):
    put(kind or ("long-handed-inserter" if long else "bulk-inserter"), x, y, d)
    if filt or stack:
        cfg.append((x + 0.5, y + 0.5 + DY, filt or [], stack))


def belt(x0, y0, x1, y1, d, name="turbo-transport-belt"):
    dx = (x1 > x0) - (x1 < x0)
    dy = (y1 > y0) - (y1 < y0)
    x, y = x0, y0
    while True:
        put(name, x, y, d)
        if (x, y) == (x1, y1):
            break
        x, y = x + dx, y + dy


N, E, S, W = 0, 4, 8, 12          # belt direction = flow; inserter direction = the side it picks up from


def layout():
    # belts
    belt(122, 1, 71, 1, W, "transport-belt")      # K junk
    belt(126, -5, 126, 1, S)
    belt(126, 2, 74, 2, W)                        # F
    belt(76, 8, 123, 8, E)
    belt(124, 8, 124, 9, S)
    belt(124, 10, 67, 10, W)                      # N head, turn, tail
    belt(116, 9, 67, 9, W)                        # B
    belt(122, 16, 68, 16, W, "transport-belt")    # E eggs
    belt(67, 16, 67, 18, S, "transport-belt")
    belt(67, 19, 61, 19, W, "transport-belt")     # E tail: ten tiles past the last science chamber, the surplus sensor
    belt(68, 17, 128, 17, E, "transport-belt")    # S science
    # towers and belt ends
    for cx, cy in ((68, 1), (74, 5), (64, 10), (61, 16), (131, 17)):
        put("heating-tower", cx, cy)
    ins(70, 1, E)                                 # K end: burn everything
    ins(72, 0, S, ["yumako-seed", "jellynut-seed"])
    put("passive-provider-chest", 72, -1)
    ins(74, 3, N, ["spoilage"])                   # F end
    ins(66, 10, E, ["spoilage"])                  # N end
    ins(66, 9, E, ["spoilage"])                   # B end
    ins(61, 18, S)                                # E end: burn every egg left over
    ins(129, 17, W, ["spoilage"])                 # S end
    # starters
    put("assembling-machine-3", 77, 5, recipe="nutrients-from-spoilage")
    ins(77, 3, N, ["spoilage"], long=True)
    ins(77, 7, N, ["nutrients"])
    put("assembling-machine-3", 81, 5, recipe="yumako-processing")
    ins(80, 3, N, ["yumako"])
    ins(82, 3, S, ["spoilage", "yumako-seed"], long=True)
    ins(83, 5, W, ["yumako-mash"])
    put("biochamber", 85, 5)
    recipes.append((85.5, 5.5 + DY, "nutrients-from-yumako-mash"))
    ins(85, 7, N, ["nutrients"])
    ins(86, 7, S, ["nutrients"])
    ins(85, 3, S, ["spoilage"], long=True)
    put("biochamber", 89, 5)
    recipes.append((89.5, 5.5 + DY, "nutrients-from-bioflux"))
    ins(88, 7, S, ["bioflux"], long=True)
    ins(89, 7, N, ["nutrients"])
    ins(90, 7, S, ["nutrients"])
    ins(89, 3, S, ["spoilage"], long=True)
    # line 1
    for c in YP + JP:
        fruit, seed, rec = ("yumako", "yumako-seed", "yumako-processing") if c in YP else ("jellynut", "jellynut-seed", "jellynut-processing")
        put("biochamber", c, 5)
        recipes.append((c + 0.5, 5.5 + DY, rec))
        ins(c - 1, 3, N, [fruit])
        ins(c + 1, 3, S, ["spoilage", seed], long=True)
        ins(c, 7, S, ["nutrients"])
    for c in BF:
        put("biochamber", c, 5)
        recipes.append((c + 0.5, 5.5 + DY, "bioflux"))
        ins(c, 3, S, ["spoilage"], long=True)
        ins(c - 1, 7, N, ["bioflux"], long=True)
        ins(c + 1, 7, S, ["nutrients"])
    for x, d, item in ((95, W, "yumako-mash"), (99, E, "jelly"), (103, W, "jelly"), (107, E, "yumako-mash"), (115, W, "yumako-mash"), (119, E, "jelly")):
        ins(x, 5, d, [item])
    # line 2
    # second nutrient chamber, just upstream of science on the nutrient tail: the single lane from the head (about 1,440 a minute) is
    # eaten by the egg chambers before it gets here, so science had no fuel
    put("biochamber", 89, 13)
    recipes.append((89.5, 13.5 + DY, "nutrients-from-bioflux"))
    ins(90, 11, N, ["bioflux"], long=True)
    ins(89, 11, S, ["nutrients"])
    ins(88, 11, N, ["nutrients"])
    ins(89, 15, N, ["spoilage"])
    for c in SCI:
        put("biochamber", c, 13)
        recipes.append((c + 0.5, 13.5 + DY, "agricultural-science-pack"))
        ins(c - 1, 11, N, ["bioflux"], long=True)
        ins(c + 1, 11, N, ["nutrients"])
        ins(c - 1, 15, S, ["pentapod-egg"], stack=2)
        ins(c, 15, N, ["spoilage"])
        ins(c + 1, 15, N, ["agricultural-science-pack"], long=True)
    for i, c in enumerate(EGG):
        put("biochamber", c, 13, E)
        recipes.append((c + 0.5, 13.5 + DY, "pentapod-egg"))
        ins(c, 11, N, ["nutrients"])
        ins(c, 15, N, ["pentapod-egg"], stack=1)
        ins(c + 1, 15, N, ["spoilage"])
        put("pipe", c + 2, 11)
        put("pipe", c + 2, 12)
        if c == KEEPER[0]:                       # the keeper pair hands eggs to each other and never stops
            ins(c + 2, 13, W, ["pentapod-egg"], stack=1)
            ins(c + 2, 14, E, ["pentapod-egg"], stack=1)
        if c not in KEEPER:                      # the others take one egg at a time off the belt, only while no egg reaches the burner
            ins(c - 1, 15, S, ["pentapod-egg"], stack=1)
        if i > 0:
            put("pipe-to-ground", c - 1, 11, W)
            put("pipe-to-ground", c + 1, 11, E)


# Egg throttle. The ten tiles of the egg belt after the last science chamber report what is on them; the six production chambers' egg
# inserters work only while that is zero eggs, i.e. while science takes everything. A chamber cut off finishes the eggs it holds and stops
# empty, so nothing hatches inside it; the keeper pair (117, 121) keeps the line alive and its surplus is what restarts the others.
THROTTLE = ("local s=game.surfaces.gleba local R=defines.wire_connector_id.circuit_red local function at(t,x,y) return s.find_entities_filtered{type=t,position={x,y},radius=0.3}[1] end "
            "local gone=0 for _,q in pairs(OLD) do local i=at('inserter',q[1],q[2]) if i then i.destroy() gone=gone+1 end end "
            "local chain={} for _,q in pairs(SENSE) do local b=at('transport-belt',q[1],q[2]) local cb=b.get_or_create_control_behavior() cb.read_contents=true cb.read_contents_mode=defines.control_behavior.transport_belt.content_read_mode.hold cb.circuit_enable_disable=false chain[#chain+1]=b end "
            "for _,x in pairs{68.5,69.5,70.5,76.5,82.5,88.5} do local b=at('transport-belt',x,EY) local cb=b.get_or_create_control_behavior() cb.read_contents=false cb.circuit_enable_disable=false chain[#chain+1]=b end "
            "local n=0 for _,q in pairs(NEW) do local i=at('inserter',q[1],q[2]) if i then local cb=i.get_or_create_control_behavior() cb.circuit_enable_disable=true "
            "cb.circuit_condition={first_signal={type='item',name='pentapod-egg'},comparator='=',constant=0} chain[#chain+1]=i n=n+1 end end "
            "local ok=0 for k=2,#chain do local a,b=chain[k-1].get_wire_connector(R,true),chain[k].get_wire_connector(R,true) if a.is_connected_to(b) or a.connect_to(b,false) then ok=ok+1 end end "
            "rcon.print('pair inserters removed '..gone..', sensor tiles '..#SENSE..', gated egg inserters '..n..', wires '..ok..' of '..(#chain-1))")


CONFIG = ("local s=game.surfaces.gleba local n,miss=0,0 for _,q in pairs(SPEC) do local i=s.find_entities_filtered{type='inserter',position={q[1],q[2]},radius=0.3}[1] if i then "
          "if #q[3]>0 then i.use_filters=true i.inserter_filter_mode='whitelist' for k,name in pairs(q[3]) do i.set_filter(k,name) end end "
          "if q[4]>0 then i.inserter_stack_size_override=q[4] end n=n+1 else miss=miss+1 end end rcon.print('inserters configured '..n..' missing '..miss)")

RECIPES = ("local s=game.surfaces.gleba local f=game.forces.player local set,wait=0,{} for _,q in pairs(SPEC) do local m=s.find_entities_filtered{type='assembling-machine',position={q[1],q[2]},radius=0.3}[1] "
           "if m and f.recipes[q[3]].enabled and not (SKIP and q[3]=='agricultural-science-pack') then if not (m.get_recipe() and m.get_recipe().name==q[3]) then m.set_recipe(q[3]) end "
           "if q[3]=='pentapod-egg' then m.direction=defines.direction.east end set=set+1 else wait[q[3]]=(wait[q[3]] or 0)+1 end end "
           "rcon.print('recipes set '..set..' not set '..helpers.table_to_json(wait))")

STATUS = ("local s=game.surfaces.gleba local f=game.forces.player local o={} local by={} "
          "for _,m in pairs(s.find_entities_filtered{type='assembling-machine',area={{56,0},{134,21}}}) do local r=m.get_recipe() local k=(r and r.name or 'no recipe') local st='?' for a,b in pairs(defines.entity_status) do if b==m.status then st=a end end "
          "by[k]=by[k] or {} by[k][st]=(by[k][st] or 0)+1 by[k].made=(by[k].made or 0)+m.products_finished end "
          "for k,v in pairs(by) do o[#o+1]=k..' '..helpers.table_to_json(v) end "
          "local function belts(name,x0,y0,x1,y1) local c={} for _,b in pairs(s.find_entities_filtered{type='transport-belt',area={{x0,y0},{x1+1,y1+1}}}) do for l=1,2 do for _,it in pairs(b.get_transport_line(l).get_contents()) do c[it.name]=(c[it.name] or 0)+it.count end end end o[#o+1]='belt '..name..' '..helpers.table_to_json(c) end "
          "belts('B',67,10,116,10) belts('K',71,2,122,2) belts('F',74,3,126,3) belts('N head',76,9,124,9) belts('N tail',67,11,124,11) belts('E',68,17,122,17) belts('E tail',61,17,67,20) belts('S',68,18,128,18) "
          "belts('yumako trunk',-150,-120,125,-4) belts('jellynut trunk',127,-5,195,102) "
          "for _,t in pairs(s.find_entities_filtered{name='heating-tower',area={{56,0},{134,21}}}) do o[#o+1]='tower '..t.position.x..','..t.position.y..' '..math.floor(t.temperature)..'C' end "
          "for _,t in pairs(s.find_entities_filtered{name='agricultural-tower'}) do local grown,young=0,0 for _,p in pairs(s.find_entities_filtered{type='plant',area={{t.position.x-10.5,t.position.y-10.5},{t.position.x+10.5,t.position.y+10.5}}}) do if game.tick>=p.tick_grown then grown=grown+1 else young=young+1 end end "
          "o[#o+1]='farm '..t.position.x..','..t.position.y..' plants ripe '..grown..' growing '..young..' seeds held '..t.get_inventory(defines.inventory.crafter_input).get_item_count() end "
          "local net=s.find_entities_filtered{name='roboport',position={-3,-3},radius=3}[1].logistic_network o[#o+1]='seeds in the network: yumako '..net.get_item_count('yumako-seed')..' jellynut '..net.get_item_count('jellynut-seed') "
          "local en=0 for _,u in pairs(s.find_entities_filtered{force='enemy',area={{30,-30},{160,50}}}) do en=en+1 end o[#o+1]='enemies near the core '..en "
          "rcon.print(table.concat(o,' | '))")


def lua_list(rows):
    out = []
    for r in rows:
        if len(r) == 4:
            out.append("{%s,%s,{%s},%d}" % (r[0], r[1], ",".join("'%s'" % f for f in r[2]), r[3]))
        else:
            out.append("{%s,%s,'%s'}" % r)
    return "{" + ",".join(out) + "}"


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    layout()
    if step == "build":
        seen = {}
        for e in ents:
            k = (e["x"], e["y"])
            if k in seen and e["name"].endswith("belt") and seen[k].endswith("belt"):
                print("belt overlap at", k)
            seen[k] = e["name"]
        for i in range(0, len(ents), 400):
            r = json.loads(tools["place_entities"](json.dumps(ents[i:i + 400]), surface="gleba", dry_run=not apply))
            r = r.get("result", r) if isinstance(r, dict) else r
            if isinstance(r, str):
                r = json.loads(r)
            print("placed", r.get("placed"), "failed", json.dumps(r.get("failed"))[:1500])
    elif step == "throttle":
        old = [(c + 2.5, y + 0.5 + DY) for c in (93, 101, 109) for y in (13, 14)]
        new = [(c - 0.5, 15.5 + DY) for c in EGG if c not in KEEPER]
        if apply:
            add = [e for e in ents if e["name"] == "bulk-inserter" and (e["x"], e["y"]) in new]
            print(tools["place_entities"](json.dumps(add), surface="gleba", dry_run=False)[:300])
            print(tools["run_lua"](CONFIG.replace("SPEC", lua_list([c for c in cfg if (c[0], c[1]) in new]))))
        sense = [(61.5 + i, 19.5 + DY) for i in range(7)][::-1] + [(67.5, y + 0.5 + DY) for y in (18, 17, 16)]
        sense = sense[::-1]
        lua = THROTTLE.replace("SENSE", "{" + ",".join("{%s,%s}" % q for q in sense) + "}").replace("OLD", "{" + ",".join("{%s,%s}" % q for q in old) + "}").replace("NEW", "{" + ",".join("{%s,%s}" % q for q in new) + "}").replace("EY", str(16.5 + DY))
        print(tools["run_lua"](lua) if apply else "(dry run) would rewire %d egg inserters" % len(new))
    elif step == "nu2":
        add = [e for e in ents if 88 <= e["x"] <= 91 and 12 <= e["y"] <= 17 and "belt" not in e["name"]]
        print(tools["place_entities"](json.dumps(add), surface="gleba", dry_run=not apply)[:300])
        if apply:
            print(tools["run_lua"](CONFIG.replace("SPEC", lua_list([c for c in cfg if 88 <= c[0] <= 91 and 12 <= c[1] <= 17]))))
            print(tools["run_lua"](RECIPES.replace("SPEC", lua_list([r for r in recipes if r[0] == 89.5])).replace("SKIP", "false")))
    elif step == "config":
        print(tools["run_lua"](CONFIG.replace("SPEC", lua_list(cfg))) if apply else "(dry run) %d inserters to configure" % len(cfg))
    elif step == "recipes":
        # science stays off unless --science is given: with no rocket silo yet the packs would only spoil on the belt
        print(tools["run_lua"](RECIPES.replace("SPEC", lua_list(recipes)).replace("SKIP", "false" if "--science" in sys.argv else "true")))
    elif step == "status":
        print(tools["run_lua"](STATUS).replace(" | ", "\n"))


if __name__ == "__main__":
    main()
