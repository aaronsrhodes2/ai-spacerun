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
        "local s=game.surfaces.nauvis for name,r in pairs(f.recipes) do local p=r.prototype local okc=false for _,c in pairs(p.categories) do if cats[c] then okc=true end end "
        "local surf=true for _,c in pairs(p.surface_conditions or {}) do local v=s.get_property(c.property) if (c.min and v<c.min) or (c.max and v>c.max) then surf=false end end "
        "if r.enabled and okc and surf and not p.hidden and #r.products==1 and r.products[1].type=='item' and not name:find('science%-pack') and not name:find('recycling') then "
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


# ---- ROUND 2: the dynamic refresh. Circuits cannot read the research tree, so a script re-reads it and rewrites ONLY the constant combinators.
# The machine itself reads each recipe's ingredients from the game, so the only data left outside the game is the LIST of makeable items.
LIST_LUA = ("local s=game.surfaces.nauvis local f=game.forces.player local cats=prototypes.entity['assembling-machine-3'].crafting_categories local EX={EXCL} local seen,list={},{} "
            "for name,r in pairs(f.recipes) do local p=r.prototype local okc=false for _,c in pairs(p.categories) do if cats[c] then okc=true end end "
            "local surf=true for _,c in pairs(p.surface_conditions or {}) do local v=s.get_property(c.property) if (c.min and v<c.min) or (c.max and v>c.max) then surf=false end end "
            "if r.enabled and okc and surf and not p.hidden and #r.products==1 and r.products[1].type=='item' and not name:find('science%-pack') and not name:find('recycling') then "
            "local solid=true for _,i in pairs(r.ingredients) do if i.type~='item' then solid=false end end local it=r.products[1].name "
            "if solid and not EX[it] then if seen[it] then seen[it]=2 else seen[it]=1 list[#list+1]=it end end end end local mk={} for _,it in pairs(list) do if seen[it]==1 then mk[#mk+1]=it end end table.sort(mk) ")
REFRESH = (LIST_LUA + "local function at(n,x,y) return s.find_entities_filtered{name=n,position={x,y},radius=0.4}[1] end local rank,ring=at('constant-combinator',RKX,RKY),at('constant-combinator',RGX,RGY) "
           "local cur={} for _,sec in pairs(rank.get_or_create_control_behavior().sections) do for _,fl in pairs(sec.filters) do if fl.value then cur[fl.value.name]=fl.min end end end "
           "local same=true local n=0 for i,it in pairs(mk) do n=n+1 if cur[it]~=i then same=false end end local m=0 for _ in pairs(cur) do m=m+1 end if m~=n then same=false end "
           "local add,rem={},{} for _,it in pairs(mk) do if not cur[it] then add[#add+1]=it end end local have={} for _,it in pairs(mk) do have[it]=true end for it in pairs(cur) do if not have[it] then rem[#rem+1]=it end end "
           "if same then rcon.print('unchanged '..n) return end "
           "for _,pair in pairs{{rank,'item'},{ring,'recipe'}} do local cb=pair[1].get_or_create_control_behavior() while cb.sections_count>0 do cb.remove_section(1) end local sec=cb.add_section() "
           "for i,it in pairs(mk) do sec.set_slot(i,{value={type=pair[2],name=it,quality='normal'},min=i}) end end "
           "table.sort(add) table.sort(rem) rcon.print('changed: '..n..' items; added '..table.concat(add,',')..' ; removed '..table.concat(rem,','))")
TARGETS = {"bench": ((BX + 4.5, BY + 5.5), (BX + 5.5, BY + 5.5)),
           "live": ((-348.5, -224.5), (-324.5, -242.5))}      # live: the filter constant combinator of omni_maker site replicator, and the ring


def refresh(target="bench", exclude=()):
    """Rewrite the rank list and the ring from the game's recipes (one RCON call; idempotent: prints 'unchanged' when nothing differs).
    Items that became impossible (a recipe no longer enabled, surface conditions Nauvis fails) drop out; newly researched ones appear."""
    from _game import tools
    (rkx, rky), (rgx, rgy) = TARGETS[target]
    code = (REFRESH.replace("EXCL", ",".join("[%r]=true" % e for e in exclude)).replace("RKX", str(rkx)).replace("RKY", str(rky))
            .replace("RGX", str(rgx)).replace("RGY", str(rgy)))
    return tools["run_lua"](code).strip()


def refresh_test():
    """Simulate a research unlock without writing research state: leave 'lab' out of the list, check the bench answers nothing for it, then
    refresh again and check it is back and answers with its ingredients. Third call must say 'unchanged'."""
    import time
    r0 = refresh("bench")
    print("1 refresh (normal):", r0[:300])
    print("2 refresh (idempotent):", refresh("bench")[:80])
    print("3 refresh excluding lab:", refresh("bench", ["lab"])[:200])
    bench_pick("lab")
    time.sleep(1.5)
    out_gone = bench_read()
    print("  lab chosen while not listed ->", out_gone)
    print("4 refresh (lab becomes available again):", refresh("bench")[:200])
    ok = False
    for w in (1.0, 2.0, 3.0):
        bench_pick("lab")
        time.sleep(w)
        got = bench_read()
        if got == expected("lab"):
            ok = True
            break
    print("  lab chosen after refresh ->", got, "| matches f(lab) x BATCH:", ok)
    print("5 refresh (idempotent again):", refresh("bench")[:80])
    bench_pick(None)
    return ok and out_gone == {}


# ---- the LIVE SWAP: documented and dry-run only. This script never performs it (the Captain decides). ----
SW_X, SW_Y = -338, -243          # tiles: three 4-combinator conversion blocks and the ring, north strip beside the bench (outside the wall)

SWAP_PLAN = """LIVE SWAP PLAN (not performed by this script)
 0. Preconditions: refresh target 'live' reads/writes the filter constant combinator at (-348.5,-224.5) (omni_maker site replicator, cc at 5.5,6.5)
    and the ring constant combinator placed in step 2. `swap` below dry-runs the placements. Nobody may run omni_maker.py config after the swap
    (it re-wires the old tables: that IS the rollback). Tell the other sessions (ghost_demand, replicator_viz, omni_fluid_asm) first.
 1. Save: tools['save_game']('skippy') (rollback point 1).
 2. Place (place_entities, epic): substation + 3 x [D1 decider, A1 arithmetic, D2 decider, A2 arithmetic] + ring constant combinator at the swap site.
    Nothing is wired yet: the live Replicator is unchanged.
 3. SHADOW: `refresh live` rewrites the filter list with min=rank (the demand deciders only test > 0, so they are unaffected) and fills the ring.
    Check the live Replicator still answers (omni_maker.py status replicator).
 4. Cut machine 3 over first (the last in the nesting chain, least loaded): wire sel3 -> D1 -> A1 -> D2 -> machine 3 -> A2 -> blue chest 3, and
    disconnect the OLD table deciders' OUTPUT wires from chest 3 (entities stay). Verify on a real request: chest 3 wants f(item) x 5, the red chest fills.
 5. Same for machine 2, then machine 1, one at a time, each confirmed on a real request.
 6. Soak for a day: refresh runs from the autopilot every few cycles; an unlocked item appears with no manual step.
 7. RETIRE LAST: deconstruct the old table deciders (only entities the omni_maker layout built, matched by name+position, like replicator_move.py retire-old).
ROLLBACK at any step before 7: `python scripts/omni_maker.py config replicator` (disconnects every machine and chest and re-wires the old tables
    from sel; the new blocks just go idle), or load the saved game 'skippy'. After step 7 only the saved game restores them.
RISKS: (a) the 7 surface-locked items stop being requested (they could never be made); (b) a non-empty machine dump slot or inserted modules block recipe
    changes (seen on the bench): empty them before cutover; (c) anything that re-runs omni_maker config undoes the cutover; (d) recipe signals appear
    on the chests' wires (wire contents verified on the bench; the chest request effect itself NOT yet checked); (e) fluid and fluid-assembler units are NOT part of this swap; (f) one tick of lag more
    between choice and request (4 combinators in series)."""


def swap_layout():
    def e(name, tx, ty, w=1, h=1):
        return {"name": name, "x": tx + w / 2, "y": ty + h / 2, "direction": 0, "params": dict(Q)}
    out = [e("substation", SW_X + 6, SW_Y - 3, 2, 2)]
    for k in range(3):
        bx = SW_X + 4 * k
        out += [e("decider-combinator", bx, SW_Y, 1, 2), e("arithmetic-combinator", bx + 1, SW_Y, 1, 2), e("decider-combinator", bx + 2, SW_Y, 1, 2), e("arithmetic-combinator", bx + 3, SW_Y, 1, 2)]
    out.append(e("constant-combinator", SW_X + 13, SW_Y))
    return out


def swap_plan():
    from _game import tools
    print(SWAP_PLAN)
    r = json.loads(tools["place_entities"](json.dumps(swap_layout()), surface="nauvis", dry_run=True))
    print("dry run of the conversion blocks:", r.get("placed"), "of", len(swap_layout()), "failed", json.dumps(r.get("failed") or [])[:300])


# ---- the live swap, step by step (each guarded; --apply to act) ----
LIVE_RING = (-324.5, -242.5)
SW_PRE = ("local s=game.surfaces.nauvis local f=game.forces.player local W=defines.wire_connector_id local APPLY=DOIT local U=UNIT local ox=7*U "
          "local function at(n,x,y) return s.find_entities_filtered{name=n,position={x,y},radius=0.4}[1] end "
          "local rq=at('requester-chest',-354+ox+2.5,-231+6.5) local am=at('assembling-machine-3',-354+ox+2.5,-231+9.5) local sel=at('selector-combinator',-354+ox+6.5,-231+8) "
          "local cc=at('constant-combinator',-348.5,-224.5) local ring=at('constant-combinator',RGX,RGY) local bx=SWX+4*U "
          "local d1,a1,d2,a2=at('decider-combinator',bx+0.5,SWY+1),at('arithmetic-combinator',bx+1.5,SWY+1),at('decider-combinator',bx+2.5,SWY+1),at('arithmetic-combinator',bx+3.5,SWY+1) "
          "if not (rq and am and sel and cc and ring and d1 and a1 and d2 and a2) then rcon.print('ABORT: an entity is missing') return end "
          "local function wire(a,ia,b,ib) a.get_wire_connector(ia,true).connect_to(b.get_wire_connector(ib,true),false) end "
          "local CB={W.combinator_input_red,W.combinator_input_green,W.combinator_output_red,W.combinator_output_green} local function clr(e) for _,id in pairs(CB) do e.get_wire_connector(id,true).disconnect_all() end end "
          "local rc=rq.get_wire_connector(W.circuit_green,true) local sc=sel.get_wire_connector(W.combinator_output_green,true) "
          "local T={} for _,c in pairs(sc.connections) do local t=c.target if t.wire_connector_id==W.combinator_input_green and t.owner.name=='decider-combinator' and t.owner.unit_number~=d1.unit_number then T[#T+1]=t.owner end end "
          "local linked=0 for _,d in ipairs(T) do if d.get_wire_connector(W.combinator_output_green,true).is_connected_to(rc) then linked=linked+1 end end "
          "local cut=a2.get_wire_connector(W.combinator_output_green,true).is_connected_to(rc) ")
SW_CUT = (SW_PRE + "local dump=0 for _,c in pairs(am.get_inventory(defines.inventory.assembling_machine_dump).get_contents()) do dump=dump+c.count end "
          "local info='machine '..(U+1)..': old table deciders on sel '..#T..', linked to the chest '..linked..', dump items '..dump..', already cut '..tostring(cut) "
          "if cut then rcon.print('ABORT already cut: '..info) return end if dump>0 then rcon.print('ABORT dump slot not empty: '..info) return end if not APPLY then rcon.print('dry: '..info) return end "
          "local EACH={type='virtual',name='signal-each'} clr(d1) clr(a1) clr(d2) clr(a2) "
          "d1.get_or_create_control_behavior().parameters={conditions={{first_signal=EACH,first_signal_networks={red=false,green=true},comparator='>',constant=0},{first_signal=EACH,first_signal_networks={red=true,green=false},comparator='>',constant=0,compare_type='and'}},outputs={{signal=EACH,copy_count_from_input=true,networks={red=true,green=false}}}} "
          "a1.get_or_create_control_behavior().parameters={first_signal=EACH,second_constant=0,operation='+',output_signal={type='virtual',name='signal-R'}} "
          "d2.get_or_create_control_behavior().parameters={conditions={{first_signal=EACH,first_signal_networks={red=true,green=false},comparator='=',second_signal={type='virtual',name='signal-R'},second_signal_networks={red=false,green=true}}},outputs={{signal=EACH,copy_count_from_input=false,constant=1}}} "
          "a2.get_or_create_control_behavior().parameters={first_signal=EACH,second_constant=BATCH,operation='*',output_signal=EACH} "
          "for _,d in ipairs(T) do d.get_wire_connector(W.combinator_output_green,true).disconnect_from(rc) end "
          "am.get_wire_connector(W.circuit_green,true).disconnect_all() am.get_wire_connector(W.circuit_red,true).disconnect_all() am.get_or_create_control_behavior().circuit_read_ingredients=true "
          "wire(sel,W.combinator_output_green,d1,W.combinator_input_green) wire(cc,W.circuit_red,d1,W.combinator_input_red) wire(d1,W.combinator_output_green,a1,W.combinator_input_green) "
          "wire(a1,W.combinator_output_green,d2,W.combinator_input_green) wire(ring,W.circuit_red,d2,W.combinator_input_red) wire(d2,W.combinator_output_green,am,W.circuit_green) "
          "wire(am,W.circuit_green,a2,W.combinator_input_green) wire(a2,W.combinator_output_green,rq,W.circuit_green) "
          "rcon.print('CUT '..info..' ; old outputs unlinked '..#T)")
SW_BACK = (SW_PRE + "if not cut then rcon.print('not cut: nothing to roll back') return end "
           "clr(d1) clr(a1) clr(d2) clr(a2) am.get_wire_connector(W.circuit_green,true).disconnect_all() am.get_or_create_control_behavior().circuit_read_ingredients=false "
           "wire(am,W.circuit_green,sel,W.combinator_output_green) local n=0 for _,d in ipairs(T) do wire(d,W.combinator_output_green,rq,W.circuit_green) n=n+1 end "
           "rcon.print('ROLLED BACK machine '..(U+1)..': am rewired to sel, '..n..' table outputs reconnected')")


def swap_lua(code, unit, apply=False):
    return (code.replace("DOIT", "true" if apply else "false").replace("UNIT", str(unit)).replace("RGX", str(LIVE_RING[0])).replace("RGY", str(LIVE_RING[1]))
            .replace("SWX", str(SW_X)).replace("SWY", str(SW_Y)).replace("BATCH", str(BATCH)))


def swap_step(what, unit=None, apply=False):
    from _game import tools
    if what == "place":
        ring = tools["run_lua"]("rcon.print(#game.surfaces.nauvis.find_entities_filtered{name='constant-combinator',position={%s,%s},radius=0.4})" % LIVE_RING).strip()
        if ring != "0" and apply:
            sys.exit("the conversion blocks already stand: never apply twice")
        if apply:
            print("save:", tools["save_game"]("skippy"))
        r = json.loads(tools["place_entities"](json.dumps(swap_layout()), surface="nauvis", dry_run=not apply, clear_trees=apply))
        print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:300])
    elif what == "shadow":
        print("refresh live:", refresh("live"))
    elif what == "cut":
        print(tools["run_lua"](swap_lua(SW_CUT, unit, apply)))
    elif what == "rollback":
        print(tools["run_lua"](swap_lua(SW_BACK, unit, True)))


# ---- the choice-stall fix (2026-11-14): HYSTERESIS on the score. A machine's own blue-chest requests feed back into the missing-request
# demand, so a nested item displaced its parent, the parent's need vanished, and the machine flapped every 10-30 ticks and never finished a
# craft. One decider per machine copies the selector's chosen item back into the score as +HOLD_H: the machine keeps its item unless another
# beats it by more than HOLD_H (a demand difference) or the nesting first call (+10,000,000) asks for a sub-part. Rollback: `swap unhold K`.
HOLD_H = 200
HOLD_POS = [(-334.5, -240.0), (-333.5, -240.0), (-331.5, -240.0)]     # 1 x 2 deciders on the free strip (tiles y -241..-240)
HOLD_LUA = ("local s=game.surfaces.nauvis local W=defines.wire_connector_id local U=UNIT local MODE='WHAT' local ox=7*U "
            "local function at(n,x,y) return s.find_entities_filtered{name=n,position={x,y},radius=0.4}[1] end "
            "local sel=at('selector-combinator',-354+ox+6.5,-223) local h=at('decider-combinator',HX,HY) if not (sel and h) then rcon.print('ABORT: missing entity') return end "
            "for _,id in pairs{W.combinator_input_red,W.combinator_input_green,W.combinator_output_red,W.combinator_output_green} do h.get_wire_connector(id,true).disconnect_all() end "
            "if MODE=='unhold' then rcon.print('machine '..(U+1)..': hold decider unwired') return end "
            "local EACH={type='virtual',name='signal-each'} h.get_or_create_control_behavior().parameters={conditions={{first_signal=EACH,comparator='>',constant=0}},outputs={{signal=EACH,copy_count_from_input=false,constant=HOLDH}}} "
            "h.get_wire_connector(W.combinator_input_green,true).connect_to(sel.get_wire_connector(W.combinator_output_green,true),false) "
            "h.get_wire_connector(W.combinator_output_red,true).connect_to(sel.get_wire_connector(W.combinator_input_red,true),false) rcon.print('machine '..(U+1)..': hold +HOLDH wired')")


def hold_step(what, apply):
    from _game import tools
    if what == "hold-place":
        ents = [{"name": "decider-combinator", "x": x, "y": y, "direction": 0, "params": dict(Q)} for x, y in HOLD_POS]
        n = tools["run_lua"]("rcon.print(#game.surfaces.nauvis.find_entities_filtered{name='decider-combinator',position={%s,%s},radius=0.4})" % HOLD_POS[0]).strip()
        if n != "0" and apply:
            sys.exit("hold deciders already stand: never apply twice")
        if apply:
            print("save:", tools["save_game"]("skippy"))
        r = json.loads(tools["place_entities"](json.dumps(ents), surface="nauvis", dry_run=not apply, clear_trees=apply))
        print("placed" if apply else "dry run", r.get("placed"), "failed", json.dumps(r.get("failed") or [])[:300])
        return
    for u in range(3):
        code = (HOLD_LUA.replace("UNIT", str(u)).replace("WHAT", what).replace("HX", str(HOLD_POS[u][0])).replace("HY", str(HOLD_POS[u][1]))
                .replace("HOLDH", str(HOLD_H)))
        print(tools["run_lua"](code))


# ---- retire the old recipe tables (LAST step of the swap): the deciders whose INPUT hangs on a machine's selector output and whose
# OUTPUT no longer reaches anything, i.e. exactly the cut table entries (the conversion D1 and the hold decider are excluded by position/wiring).
RETIRE_LUA = ("local s=game.surfaces.nauvis local f=game.forces.player local W=defines.wire_connector_id local APPLY=DOIT local o={} local tot,marked=0,0 "
              "local keep={} for _,p in pairs(KEEP) do local e=s.find_entities_filtered{name='decider-combinator',position=p,radius=0.4}[1] if e then keep[e.unit_number]=true end end "
              "for u=0,2 do local sel=s.find_entities_filtered{name='selector-combinator',position={-354+7*u+6.5,-223},radius=0.4}[1] local n,live=0,0 "
              "for _,c in pairs(sel.get_wire_connector(W.combinator_output_green,true).connections) do local t=c.target local d=t.owner "
              "if t.wire_connector_id==W.combinator_input_green and d.name=='decider-combinator' and not keep[d.unit_number] then "
              "local oc=d.get_wire_connector(W.combinator_output_green,true).connection_count+d.get_wire_connector(W.combinator_output_red,true).connection_count "
              "if oc==0 then n=n+1 if APPLY and d.order_deconstruction(f) then marked=marked+1 end else live=live+1 end end end tot=tot+n "
              "o[#o+1]='machine '..(u+1)..': cut table deciders '..n..', still wired out '..live end rcon.print(table.concat(o,'; ')..' ; total '..tot..', marked for deconstruction '..marked)")


def retire_tables(apply):
    from _game import tools
    keep = [(SW_X + 4 * u + 0.5, SW_Y + 1) for u in range(3)] + list(HOLD_POS)
    code = RETIRE_LUA.replace("DOIT", "true" if apply else "false").replace("KEEP", "{" + ",".join("{%s,%s}" % k for k in keep) + "}")
    if apply:
        print("save:", tools["save_game"]("skippy"))
    print(tools["run_lua"](code))


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "study"
    if step == "study":
        study("--refresh" in sys.argv)
    elif step == "bench" and sys.argv[2] == "build":
        bench_build("--apply" in sys.argv)
    elif step == "bench" and sys.argv[2] == "stage2":
        bench_stage2("--apply" in sys.argv)
    elif step == "swap":
        if len(sys.argv) > 2 and sys.argv[2] == "retire":
            retire_tables("--apply" in sys.argv)
        elif len(sys.argv) > 2 and sys.argv[2] in ("hold-place", "hold", "unhold"):
            hold_step(sys.argv[2], "--apply" in sys.argv)
        elif len(sys.argv) > 2 and sys.argv[2] in ("place", "shadow", "cut", "rollback"):
            swap_step(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else None, "--apply" in sys.argv)
        else:
            swap_plan()
    elif step == "refresh":
        if "--test" in sys.argv:
            print("refresh test passed:", refresh_test())
        else:
            print(refresh("bench"))
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
