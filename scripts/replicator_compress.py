#!/usr/bin/env python3
"""Replicator compression experiment (the Captain, 2026-11-14: "find a pattern, reduce it to a procedure, simplify, compress, repeat").

THE FUNCTION the recipe tables compute (scripts/omni_maker.py `rom`, one decider per makeable item per machine):
    f(item) = { ingredient: amount * BATCH }       (BATCH = 5; solid ingredients only; one recipe per item)
The 3 machines each hold a full copy, because a decider writes every output on both of its wires and so serves one requester chest.
The fluid unit (omni_fluid.py) holds 8 deciders per recipe, the furnace unit (omni_maker.py furnace) one per smeltable item.

THE TRICK THAT COMPRESSES IT: an assembling machine set to a recipe and told to read ingredients puts exactly f(item)/BATCH on its
circuit connection. So a 'lookup bench' (an assembler fed by nothing, set by circuit to the chosen item) IS the recipe table. The earlier
attempt slid down the recipe tree because the machine obeys the FIRST recipe signal in item order and reads its own ingredients back
onto the wire it takes the recipe from. `bench` below tests the way out empirically (quality of the chosen signal / recipe-type signal).

Steps: study | generate | verify | bench | status        (shell: bash, PYTHONPATH=scripts; PLATINUM 20)
  study     dumps the game's recipe data for the makeable items and prints the statistics (read only)
  generate  emits the compact design for the data (dry; prints counts, before/after)
  verify    proves, item by item, that the compact design gives the same ingredient set as the tables standing in the game (read only)
  bench     builds / drives / reads the lookup bench on a free strip (never applies twice; the live Replicator is not touched)
  status    entities and results of the bench
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE.parent / "snapshots" / "replicator_recipes.json"
BATCH = 5

# the same selection omni_maker.CONFIG uses: enabled, assembler-3 category, not hidden, single item product, solid ingredients only,
# not a science pack or recycling, and only items with exactly one such recipe
DUMP = ("local f=game.forces.player local cats=prototypes.entity['assembling-machine-3'].crafting_categories local seen,list,rec={},{},{} "
        "for name,r in pairs(f.recipes) do local p=r.prototype local okc=false for _,c in pairs(p.categories) do if cats[c] then okc=true end end "
        "if r.enabled and okc and not p.hidden and #r.products==1 and r.products[1].type=='item' and not name:find('science%-pack') and not name:find('recycling') then "
        "local solid=true for _,i in pairs(r.ingredients) do if i.type~='item' then solid=false end end local it=r.products[1].name "
        "if solid then if seen[it] then seen[it]=2 else seen[it]=1 list[#list+1]=it rec[it]=r end end end end local out={} "
        "for _,it in pairs(list) do if seen[it]==1 then local t={} for _,i in pairs(rec[it].ingredients) do t[#t+1]=i.name..':'..i.amount end "
        "out[#out+1]=rec[it].name..'|'..it..'|'..rec[it].products[1].amount..'|'..table.concat(t,',') end end rcon.print(table.concat(out,';'))")


def game_recipes(refresh=False):
    """{item: {'recipe': name, 'yield': n, 'ing': {ingredient: amount}}} for every item the Replicator can make (cached)."""
    if CACHE.exists() and not refresh:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    from _game import tools
    raw = tools["run_lua"](DUMP).strip()
    data = {}
    for row in raw.split(";"):
        rn, it, y, ing = row.split("|")
        data[it] = {"recipe": rn, "yield": int(float(y)), "ing": {k: int(float(v)) for k, v in (p.split(":") for p in ing.split(",") if p)}}
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(data, indent=0, sort_keys=True), encoding="utf-8")
    return data


def study(refresh=False):
    d = game_recipes(refresh)
    n = len(d)
    kinds = Counter(len(v["ing"]) for v in d.values())
    amts = [a for v in d.values() for a in v["ing"].values()]
    ing_all = Counter(i for v in d.values() for i in v["ing"])
    print("makeable items:", n)
    print("ingredient kinds per recipe (kinds: recipes):", dict(sorted(kinds.items())))
    print("amounts: min %d max %d, distinct %d, bits needed %d (x BATCH %d: max %d)" % (min(amts), max(amts), len(set(amts)), max(amts).bit_length(), BATCH, max(amts) * BATCH))
    print("distinct ingredients:", len(ing_all), "| items that are also ingredients:", len(set(ing_all) & set(d)))
    print("deciders in the tables now: 3 machines x %d = %d" % (n, 3 * n))
    print("recipe-name differs from item name:", [(k, v["recipe"]) for k, v in d.items() if k != v["recipe"]])
    print("recipes yielding more than 1:", {k: v["yield"] for k, v in d.items() if v["yield"] > 1})
    print("top ingredients:", ing_all.most_common(12))
    ids = sorted(set(d) | set(ing_all))
    print("id space (items + ingredients): %d -> %d bits; packed (id,amount) needs %d bits" % (len(ids), (len(ids) - 1).bit_length(), (len(ids) - 1).bit_length() + max(amts).bit_length()))


# ---- the bench: free strip north of the walled perimeter (tiles x -352..-343, y -246..-240, checked empty 2026-11-14) ----
BX, BY = -352, -246
Q = {"quality": "epic"}


def bench_layout():
    def e(name, tx, ty, w=1, h=1):
        return {"name": name, "x": BX + tx + w / 2, "y": BY + ty + h / 2, "direction": 0, "params": dict(Q)}
    return [e("substation", 6, 0, 2, 2), e("assembling-machine-3", 0, 3, 3, 3), e("constant-combinator", 4, 3), e("constant-combinator", 4, 5),
            e("assembling-machine-3", 0, 0, 3, 3)][:4]


def bench_build(apply):
    from _game import tools
    n = tools["run_lua"]("rcon.print(#game.surfaces.nauvis.find_entities_filtered{name='assembling-machine-3',position={%s,%s},radius=0.6})" % (BX + 1.5, BY + 4.5)).strip()
    if n != "0" and apply:
        sys.exit("bench already stands: never apply twice")
    if apply:
        print("save:", tools["save_game"]("skippy"))
    r = json.loads(tools["place_entities"](json.dumps(bench_layout()), surface="nauvis", dry_run=not apply, clear_trees=apply))
    print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:400])


def stage2_layout():
    """Round 1 compact lookup on the bench: D1 intersect, A1 sum, D2 ring decode, A2 times BATCH, a ring constant combinator and a requester chest.
    (Stand-in for the live selector's chosen item: constant combinator 1; rank list: constant combinator 2; both stage 1.)"""
    def e(name, tx, ty, w=1, h=1):
        return {"name": name, "x": BX + tx + w / 2, "y": BY + ty + h / 2, "direction": 0, "params": dict(Q)}
    return [e("decider-combinator", 6, 3, 1, 2), e("arithmetic-combinator", 7, 3, 1, 2), e("decider-combinator", 8, 3, 1, 2),
            e("arithmetic-combinator", 9, 3, 1, 2), e("constant-combinator", 5, 5), e("requester-chest", 10, 4)]


def bench_stage2(apply):
    from _game import tools
    n = tools["run_lua"]("rcon.print(#game.surfaces.nauvis.find_entities_filtered{name='requester-chest',position={%s,%s},radius=0.6})" % (BX + 10.5, BY + 4.5)).strip()
    if n != "0" and apply:
        sys.exit("bench stage 2 already stands: never apply twice")
    r = json.loads(tools["place_entities"](json.dumps(stage2_layout()), surface="nauvis", dry_run=not apply, clear_trees=apply))
    print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:400])


def ranks():
    d = game_recipes()
    return {it: i + 1 for i, it in enumerate(sorted(d))}


def slots_lua(kind):
    return "".join("sec.set_slot(%d,{value={type='%s',name='%s',quality='normal'},min=%d}) " % (r, kind, it, r) for it, r in ranks().items())


CFG2 = ("local s=game.surfaces.nauvis local W=defines.wire_connector_id local function at(n,x,y) return s.find_entities_filtered{name=n,position={BX+x,BY+y},radius=0.4}[1] end "
        "local function wire(a,ia,b,ib) a.get_wire_connector(ia,true).connect_to(b.get_wire_connector(ib,true),false) end "
        "local CB={W.combinator_input_red,W.combinator_input_green,W.combinator_output_red,W.combinator_output_green} local function clr(e) for _,id in pairs(CB) do e.get_wire_connector(id,true).disconnect_all() end end "
        "local am=at('assembling-machine-3',1.5,4.5) local ch=at('requester-chest',10.5,4.5) local pick=at('constant-combinator',4.5,3.5) local rank=at('constant-combinator',4.5,5.5) local ring=at('constant-combinator',5.5,5.5) "
        "local d1,a1,d2,a2=at('decider-combinator',6.5,4),at('arithmetic-combinator',7.5,4),at('decider-combinator',8.5,4),at('arithmetic-combinator',9.5,4) "
        "for _,e in pairs{pick,rank,ring} do for _,id in pairs{W.circuit_red,W.circuit_green} do e.get_wire_connector(id,true).disconnect_all() end end for _,e in pairs{am,ch} do for _,id in pairs{W.circuit_red,W.circuit_green} do e.get_wire_connector(id,true).disconnect_all() end end "
        "for _,e in pairs{d1,a1,d2,a2} do clr(e) end "
        "local cb=rank.get_or_create_control_behavior() while cb.sections_count>0 do cb.remove_section(1) end local sec=cb.add_section() RANKS "
        "cb=ring.get_or_create_control_behavior() while cb.sections_count>0 do cb.remove_section(1) end sec=cb.add_section() RING "
        "local EACH={type='virtual',name='signal-each'} "
        "d1.get_or_create_control_behavior().parameters={conditions={{first_signal=EACH,first_signal_networks={red=false,green=true},comparator='>',constant=0},"
        "{first_signal=EACH,first_signal_networks={red=true,green=false},comparator='>',constant=0,compare_type='and'}},outputs={{signal=EACH,copy_count_from_input=true,networks={red=true,green=false}}}} "
        "a1.get_or_create_control_behavior().parameters={first_signal=EACH,second_constant=0,operation='+',output_signal={type='virtual',name='signal-R'}} "
        "d2.get_or_create_control_behavior().parameters={conditions={{first_signal=EACH,first_signal_networks={red=true,green=false},comparator='=',second_signal={type='virtual',name='signal-R'},second_signal_networks={red=false,green=true}}},"
        "outputs={{signal=EACH,copy_count_from_input=false,constant=1}}} "
        "a2.get_or_create_control_behavior().parameters={first_signal=EACH,second_constant=BATCH,operation='*',output_signal=EACH} "
        "wire(pick,W.circuit_green,d1,W.combinator_input_green) wire(rank,W.circuit_red,d1,W.combinator_input_red) wire(d1,W.combinator_output_green,a1,W.combinator_input_green) "
        "wire(a1,W.combinator_output_green,d2,W.combinator_input_green) wire(ring,W.circuit_red,d2,W.combinator_input_red) wire(d2,W.combinator_output_green,am,W.circuit_green) "
        "wire(am,W.circuit_green,a2,W.combinator_input_green) wire(a2,W.combinator_output_green,ch,W.circuit_green) "
        "local ab=am.get_or_create_control_behavior() ab.circuit_set_recipe=true ab.circuit_read_ingredients=true "
        "local qb=ch.get_or_create_control_behavior() qb.set_requests=true qb.read_contents=false rcon.print('stage 2 wired')")


def run_cfg2():
    from _game import tools
    code = CFG2.replace("BX", str(BX)).replace("BY", str(BY)).replace("RANKS", slots_lua("item")).replace("RING", slots_lua("recipe")).replace("BATCH", str(BATCH))
    print(len(code), tools["run_lua"](code))


def bench_pick(item):
    from _game import tools
    tools["run_lua"]("local s=game.surfaces.nauvis local cc=s.find_entities_filtered{name='constant-combinator',position={%s,%s},radius=0.4}[1] local cb=cc.get_or_create_control_behavior() "
                     "while cb.sections_count>0 do cb.remove_section(1) end %s" % (BX + 4.5, BY + 3.5, ("local sec=cb.add_section() sec.set_slot(1,{value={type='item',name='%s',quality='normal'},min=1000000})" % item) if item else ""))


READ = ("local s=game.surfaces.nauvis local W=defines.wire_connector_id local ch=s.find_entities_filtered{name='requester-chest',position={%s,%s},radius=0.4}[1] "
        "local n=ch.get_circuit_network(W.circuit_green) local t={} if n and n.signals then for _,x in pairs(n.signals) do t[#t+1]=(x.signal.type or 'item')..':'..x.signal.name..'='..x.count end end rcon.print(table.concat(t,','))")


def bench_read():
    from _game import tools
    out = {}
    for p in tools["run_lua"](READ % (BX + 10.5, BY + 4.5)).strip().split(","):
        if p:
            k, v = p.rsplit("=", 1)
            out[k] = int(v)
    return out


def expected(item):
    d = game_recipes()[item]
    out = {"item:" + k: v * BATCH for k, v in d["ing"].items()}
    out["recipe:" + item] = BATCH
    return out


def verify_bench(items=None):
    """Drive the bench through every makeable item (or the given ones) and compare the requester chest's wire with f(item) x BATCH."""
    import time
    bad, ok = [], 0
    for it in (items or sorted(game_recipes())):
        want = expected(it)
        got = {}
        bench_pick(it)
        for wait in (0.4, 1.0, 2.0):
            time.sleep(wait)
            got = bench_read()
            if got == want:
                break
        if got == want:
            ok += 1
        else:
            bad.append((it, want, got))
    bench_pick(None)
    time.sleep(0.5)
    print("empty choice ->", bench_read())
    print("verified %d, mismatches %d" % (ok, len(bad)))
    for b in bad:
        print("  MISMATCH", b)
    return not bad


def generate():
    """Counts, before and after, for the compact design (the Lua that emits it is CFG2: one ring + one rank list, four combinators a machine)."""
    n = len(game_recipes())
    machines = 3
    before = machines * n
    after = machines * 4
    print("solid recipe tables: %d deciders (%d machines x %d items)" % (before, machines, n))
    print("compact: %d combinators (%d machines x [D1 intersect, A1 sum, D2 ring decode, A2 x BATCH]) + 1 ring constant combinator" % (after, machines))
    print("                the rank list is the demand-filter constant combinator that already exists (min=rank instead of min=1)")
    print("whole Replicator combinators: 653 deciders + 6 arithmetic -> %d deciders + %d arithmetic (fluid 112 and furnace 5 untouched)"
          % (653 - before + machines * 2, 6 + machines * 2))


def status():
    from _game import tools
    print(tools["run_lua"]("local s=game.surfaces.nauvis local c={} for _,e in pairs(s.find_entities_filtered{area={{%s,%s},{%s,%s}},force='player'}) do c[e.name]=(c[e.name] or 0)+1 end local t={} for k,v in pairs(c) do t[#t+1]=k..' '..v end rcon.print('bench: '..table.concat(t,', '))" % (BX, BY, BX + 12, BY + 7)))
    print("chest wire:", bench_read())


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "study"
    if step == "study":
        study("--refresh" in sys.argv)
    elif step == "bench" and sys.argv[2] == "build":
        bench_build("--apply" in sys.argv)
    elif step == "bench" and sys.argv[2] == "stage2":
        bench_stage2("--apply" in sys.argv)
    elif step == "generate":
        generate()
    elif step == "status":
        status()
    elif step == "verify":
        verify_bench()
    elif step == "bench" and sys.argv[2] == "config2":
        run_cfg2()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
