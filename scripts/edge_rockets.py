#!/usr/bin/env python3
"""Edgerunner ROCKET WORKS (the Captain, 2026-11-18: "Yes, build both" to an on-board works of about 60 explosive rockets a minute).

WHY. Big asteroids (the Aquilo legs) take no damage from guns: only rockets. The hub works make explosives on one chain (about 130 a
minute when nothing is wedged) and the two railgun assemblers stand first on that bus, so rockets got about 8 a minute.

WHERE. East of the SOUTH SPOKE (the chunk belt, x = 0, flowing north to the hub), rows R-17 .. R+13 with R = 70, on new deck. The works take
chunks straight off the spoke belt, before the station ring. At rest the belt is nearly empty (measured: 14 chunks on rows 44..150), in
flight it carries the whole catch and the surplus used to go overboard at row 258: this works is a flight-time works, and the hub is its store.

LAYOUT (tiles; x east of the spoke, rows south positive). Every crusher is 2 x 3 on x 2..3 with its intake and hand-back inserters on x 1
(intake on its southern row = upstream, hand-back north of it), its product inserters on x 4, the plants on x 5..7, the water main on x 8.
  row R        belt X, flowing east from x 5 to 33. SOUTH lane explosives, NORTH lane iron plate: one kind a lane, so the dead end cannot clog.
  chain B      north of X: explosives plant rows R-4..R-2, carbonic crusher R-6..R-4, coal plant R-8..R-6. Its plant's inserter (6,R-1)
               drops on X from the north (far lane = south).
  chain A      south of X: explosives plant R+3..R+5, crusher R+5..R+7, coal plant R+7..R+9. Its inserter (6,R+2) drops on a one-tile
               stub (6,R+1) that joins X from the south (near lane = south).
  water        oxide crusher R+9..R+11, melter R+11..R+13; main x 8 from R+13 to R-8, under belt X by pipe to ground.
  plates       metallic crusher R-12..R-10 with a furnace east of it (rows R-12..R-10) and one north of it (x 1..3, rows R-16..R-14);
               their plates ride belt P (row R-15, then x 9 south) and join X from the north (near lane = north).
  assembly     north of X, two triples from x 11 and x 23: explosive rocket | rocket | explosive rocket, the rocket assembler handing a
               rocket to each neighbour; one inserter each from X on row R-1.
  output       belt O: row R-6 west, x 10 north, row R-17 west, then up the spoke's free deck column x 1 to row 11, under the reprocessing
               crusher (3 -> 7), under the ring's south row (7,9 -> 7,7) and the plate belt (7,6 -> 7,4), to the free hub face tile (4,2).
               The hub is the store (it takes rockets while it holds fewer than CAP); the existing outlet (4,0) puts them on the feed in flight.
CONTROL (the same relief as the hub works, edge_works.RELIEF): per carbonic crusher two decider combinators on the spoke's west deck set the
chute inserter's filter (carbon > 9 and sulfur < 2: drop carbon; sulfur > 3 and carbon < 5: drop sulfur), and the explosives plant takes
sulfur one at a time while it holds fewer than 2. No rule depends on which modules the autopilot fits.
The request `edge-ammo 37` kept explosive rockets at exactly 1,000: its maximum is lifted, or the hub would send the works' rockets down.

Steps: plan | deck | build [--apply] | config | status | rates [SECONDS]
Usage: edge_rockets.py plan ; edge_rockets.py deck ; edge_rockets.py build --apply ; edge_rockets.py config ; edge_rockets.py rates 120"""
import json
import sys
import time

import triangle_miner as TM
from _game import tools
from edge_works import T

L = tools["run_lua"]
R = 70
CAP = 20000
N, E, S, W = 0, 4, 8, 12
BELT, UG, PIPE, PTG = "express-transport-belt", "express-underground-belt", "pipe", "pipe-to-ground"
ASM, CHEM, FUR, CRUSH, FAST, BULK, DEC = "assembling-machine-3", "chemical-plant", "electric-furnace", "crusher", "fast-inserter", "bulk-inserter", "decider-combinator"
TRIPLES = (11, 23)
X_END = 33
# (crusher top row, explosives plant top row, coal plant top row, chute row, guard row, coal-feed row, coal->plant inserter (row, pick-up side))
CHAINS = {"A": dict(k=R + 5, ex=R + 3, cs=R + 7, intake=R + 7, back=R + 6, guard=R + 5, chute=R + 6, feed=R + 7, link=(R + 6, S)),
          "B": dict(k=R - 6, ex=R - 4, cs=R - 8, intake=R - 4, back=R - 5, guard=R - 4, chute=R - 5, feed=R - 6, link=(R - 5, N))}
KO, KM = R + 9, R - 12


def layout():
    e = []
    for c in CHAINS.values():
        e += [T(CRUSH, 2, c["k"], N, 2, 3, "advanced-carbonic-asteroid-crushing"), T(CHEM, 5, c["ex"], E, 3, 3, "explosives"), T(CHEM, 5, c["cs"], E, 3, 3, "coal-synthesis"),
              T(FAST, 1, c["intake"], W), T(FAST, 1, c["back"], E), T(FAST, 4, c["guard"], W), T(FAST, 4, c["chute"], W), T(FAST, 4, c["feed"], W),
              T(FAST, 6, c["link"][0], c["link"][1])]
    e += [T(FAST, 6, R - 1, N), T(FAST, 6, R + 2, S), T(BELT, 6, R + 1, N)]                       # explosives onto belt X
    e += [T(BELT, x, R, E) for x in range(5, X_END + 1)]
    # water
    e += [T(CRUSH, 2, KO, N, 2, 3, "oxide-asteroid-crushing"), T(FAST, 1, KO + 2, W), T(FAST, 1, KO + 1, E), T(FAST, 4, KO + 2, W), T(CHEM, 5, KO + 2, W, 3, 3, "ice-melting")]
    e += [T(PIPE, 8, y) for y in range(R + 2, R + 14)] + [T(PTG, 8, R + 1, S), T(PTG, 8, R - 1, N)] + [T(PIPE, 8, y) for y in range(R - 8, R - 1)]
    # plates
    e += [T(CRUSH, 2, KM, N, 2, 3, "metallic-asteroid-crushing"), T(FAST, 1, KM + 2, W), T(FAST, 1, KM + 1, E),
          T(FAST, 4, KM + 1, W), T(FUR, 5, KM, N, 3, 3), T(FAST, 8, KM + 1, W),
          T(FAST, 2, KM - 1, S), T(FUR, 1, KM - 4, N, 3, 3), T(FAST, 4, KM - 3, W)]
    e += [T(BELT, x, R - 15, E) for x in range(5, 9)] + [T(BELT, 9, y, S) for y in range(R - 15, R)]
    # assembly
    for a in TRIPLES:
        e += [T(ASM, a, R - 4, N, 3, 3, "explosive-rocket"), T(FAST, a + 3, R - 3, E), T(ASM, a + 4, R - 4, N, 3, 3, "rocket"), T(FAST, a + 7, R - 3, W),
              T(ASM, a + 8, R - 4, N, 3, 3, "explosive-rocket"), T(FAST, a + 1, R - 1, S), T(FAST, a + 5, R - 1, S), T(FAST, a + 9, R - 1, S),
              T(FAST, a + 1, R - 5, S), T(FAST, a + 9, R - 5, S)]
    # returned chunks overboard: with the spoke belt packed and standing (docked, ring full) a hand-back inserter finds no room, the
    # crusher keeps its returned chunk and stops. One more inserter per crusher drops that chunk into open space (tile beyond it has no deck).
    e += [T(FAST, 3, R - 9, N), T(FAST, 3, R - 7, S), T(FAST, 3, R + 4, S), T(FAST, 3, R + 12, N)]
    # output belt O
    e += [T(BELT, x, R - 6, W) for x in range(X_END, 10, -1)] + [T(BELT, 10, y, N) for y in range(R - 6, R - 17, -1)] + [T(BELT, x, R - 17, W) for x in range(10, 1, -1)]
    e += [T(BELT, 1, y, N) for y in range(R - 17, 11, -1)]
    e += [T(BELT, 1, 11, E), T(BELT, 2, 11, E), T(UG, 3, 11, E, type="input"), T(UG, 7, 11, E, type="output"), T(BELT, 8, 11, N), T(BELT, 8, 10, W), T(BELT, 7, 10, N),
          T(UG, 7, 9, N, type="input"), T(UG, 7, 7, N, type="output"), T(UG, 7, 6, N, type="input"), T(UG, 7, 4, N, type="output"), T(BELT, 7, 3, N), T(BELT, 7, 2, W),
          T(BELT, 6, 2, W), T(BELT, 5, 2, W)]
    return e


def deciders():
    out = []
    for c in CHAINS.values():
        for row in (c["k"], c["k"] + 1):
            out.append({"name": DEC, "x": -1.0, "y": row + 0.5, "direction": E, "params": {"quality": "normal"}})
    return out


def tiles_of(ents):
    out = set()
    for e in ents:
        w = h = 1
        if e["name"] in (ASM, CHEM, FUR):
            w = h = 3
        elif e["name"] == CRUSH:
            w, h = 2, 3
        x0, y0 = round(e["x"] - w / 2), round(e["y"] - h / 2)
        out |= {(x0 + i, y0 + j) for i in range(w) for j in range(h)}
    return out


def cells(ts):
    return "{" + ",".join("{%d,%d}" % c for c in sorted(ts)) + "}"


def plan():
    ents = layout()
    ts = tiles_of(ents)
    print(len(ents), "entities on", len(ts), "tiles; deciders", len(deciders()))
    print(L(TM.AT + "local need,gh=0,0 local blk={} for _,q in pairs(" + cells(ts) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' then need=need+1 if s.count_entities_filtered{type='tile-ghost',position={q[1]+0.5,q[2]+0.5},radius=0.3}>0 then gh=gh+1 end end "
            "for _,e in pairs(s.find_entities_filtered{area={{q[1]+0.1,q[2]+0.1},{q[1]+0.9,q[2]+0.9}}}) do if e.type~='tile-ghost' then blk[e.name..' @'..e.position.x..','..e.position.y]=true end end end "
            "local t={} for k in pairs(blk) do t[#t+1]=k end rcon.print('tiles without deck '..need..' (ghosts '..gh..') | hub foundations '..p.hub.get_inventory(defines.inventory.hub_main).get_item_count('space-platform-foundation')..' | standing in the way: '..(#t>0 and table.concat(t,'; '):sub(1,900) or 'nothing'))"))
    return ents, ts


# the hub inserter is created with its filter in the same tick (an unfiltered one on a hub face moves whatever the hub holds)
CONFIG = (TM.AT + "local W=defines.wire_connector_id local o={} local hub=p.hub local function at(t,x,y) return s.find_entities_filtered{type=t,position={x+0.5,y+0.5},radius=0.3}[1] end "
          "local function filt(e,names,mode) e.use_filters=true e.inserter_filter_mode=mode or 'whitelist' for i=1,e.filter_slot_count do e.set_filter(i,nil) end for i,n in pairs(names) do e.set_filter(i,{name=n,quality='normal',comparator='='}) end end "
          "local function I(n) return {type='item',name=n} end "
          "for _,c in pairs(CHAINLIST) do local kc=s.find_entities_filtered{name='crusher',position={3,c.k+1.5},radius=0.6}[1] local ex=s.find_entities_filtered{name='chemical-plant',position={6.5,c.ex+1.5},radius=0.6}[1] "
          "local intake,back,guard,chute=at('inserter',1,c.intake),at('inserter',1,c.back),at('inserter',4,c.guard),at('inserter',4,c.chute) "
          "local da=s.find_entities_filtered{name='decider-combinator',position={-1,c.k+0.5},radius=0.4}[1] local db=s.find_entities_filtered{name='decider-combinator',position={-1,c.k+1.5},radius=0.4}[1] "
          "if not (kc and ex and intake and back and guard and chute and da and db) then o[#o+1]='chain '..c.name..' INCOMPLETE' else "
          "filt(intake,{'carbonic-asteroid-chunk'}) filt(back,{'carbonic-asteroid-chunk'}) "
          "da.get_or_create_control_behavior().parameters={conditions={{first_signal=I('carbon'),comparator='>',constant=9},{first_signal=I('sulfur'),comparator='<',constant=2,compare_type='and'}},outputs={{signal=I('carbon'),copy_count_from_input=false,constant=1}}} "
          "db.get_or_create_control_behavior().parameters={conditions={{first_signal=I('sulfur'),comparator='>',constant=3},{first_signal=I('carbon'),comparator='<',constant=5,compare_type='and'}},outputs={{signal=I('sulfur'),copy_count_from_input=false,constant=1}}} "
          "kc.get_or_create_control_behavior().circuit_read_contents=true local kg=kc.get_wire_connector(W.circuit_green,true) local cr=chute.get_wire_connector(W.circuit_red,true) "
          "for _,d in pairs({da,db}) do local di=d.get_wire_connector(W.combinator_input_green,true) if not di.is_connected_to(kg) then di.connect_to(kg) end local dout=d.get_wire_connector(W.combinator_output_red,true) if not dout.is_connected_to(cr) then dout.connect_to(cr) end end "
          "chute.use_filters=true chute.inserter_filter_mode='whitelist' for i=1,chute.filter_slot_count do chute.set_filter(i,nil) end chute.inserter_stack_size_override=1 "
          "local cb=chute.get_or_create_control_behavior() cb.circuit_set_filters=true cb.circuit_enable_disable=true cb.circuit_condition={first_signal={type='virtual',name='signal-anything'},comparator='>',constant=0} "
          "local eb=ex.get_or_create_control_behavior() eb.circuit_read_contents=true eb.circuit_read_ingredients=false local er,gr=ex.get_wire_connector(W.circuit_red,true),guard.get_wire_connector(W.circuit_red,true) if not er.is_connected_to(gr) then er.connect_to(gr) end "
          "filt(guard,{'sulfur'}) guard.inserter_stack_size_override=1 local gb=guard.get_or_create_control_behavior() gb.circuit_enable_disable=true gb.circuit_condition={first_signal=I('sulfur'),comparator='<',constant=2} "
          "o[#o+1]='chain '..c.name..' wired' end end "
          "for _,q in pairs({{RROW-9,'metallic-asteroid-chunk'},{RROW-7,'carbonic-asteroid-chunk'},{RROW+4,'carbonic-asteroid-chunk'},{RROW+12,'oxide-asteroid-chunk'}}) do local i=at('inserter',3,q[1]) if i then filt(i,{q[2]}) else o[#o+1]='NO overboard inserter at row '..q[1] end end "
          "for _,q in pairs({{KOROW,'oxide-asteroid-chunk'},{KMROW,'metallic-asteroid-chunk'}}) do local a,b=at('inserter',1,q[1]+2),at('inserter',1,q[1]+1) if a and b then filt(a,{q[2]}) filt(b,{q[2]}) else o[#o+1]='NO chunk inserters at row '..q[1] end end "
          "pcall(function() hub.get_or_create_control_behavior().read_contents=true end) "
          "local hi=at('inserter',4,2) if not hi then hi=s.create_entity{name='bulk-inserter',position={4.5,2.5},direction=4,quality='legendary',force='player'} end "
          "if hi then filt(hi,{'explosive-rocket'}) local a,b=hub.get_wire_connector(W.circuit_green,true),hi.get_wire_connector(W.circuit_green,true) if not a.is_connected_to(b) then a.connect_to(b) end "
          "local hb=hi.get_or_create_control_behavior() hb.circuit_enable_disable=true hb.circuit_condition={first_signal=I('explosive-rocket'),comparator='<',constant=CAPV} "
          "o[#o+1]='hub inserter drops '..hi.drop_position.x..','..hi.drop_position.y..' into '..(hi.drop_target and hi.drop_target.name or 'NOTHING') else o[#o+1]='NO hub inserter' end "
          "for _,pt in pairs(hub.get_logistic_point()) do for _,sec in pairs(pt.sections) do if sec.is_manual and sec.group=='edge-ammo 37' then for i=1,sec.filters_count do local f=sec.get_slot(i) "
          "if f and f.value and f.value.name=='explosive-rocket' and f.max then f.max=nil sec.set_slot(i,f) o[#o+1]='request maximum for explosive rockets lifted' end end end end end "
          "rcon.print(table.concat(o,' | '))")

STATUS = (TM.AT + "local m={} for k,v in pairs(defines.entity_status) do m[v]=k end local o={} "
          "for _,e in pairs(s.find_entities_filtered{type={'assembling-machine','furnace'},area={{1,Y0},{35,Y1}}}) do local rc=e.get_recipe() if not rc and e.type=='furnace' then rc=e.previous_recipe end local nm=rc and rc.name or e.name if type(nm)~='string' then nm=nm.name end "
          "local out={} local inv=e.get_output_inventory() if inv then for _,i in pairs(inv.get_contents()) do out[#out+1]=i.name..' '..i.count end end local mods={} local mi=e.get_module_inventory() if mi then for _,i in pairs(mi.get_contents()) do mods[#mods+1]=i.count..' '..i.name:gsub('-module','') end end "
          "local fl={} for i=1,4 do local ok,x=pcall(function() return e.get_fluid(i) end) if ok and x then fl[#fl+1]=x.name..' '..math.floor(x.amount) end end "
          "o[#o+1]=string.format('%-36s @%5.1f,%5.1f %-26s made %-6d out[%s] %s [%s]',nm,e.position.x,e.position.y,tostring(m[e.status]),e.products_finished,table.concat(out,', '),table.concat(fl,', '),table.concat(mods,', ')) end table.sort(o) "
          "local function belt(cs) local c={} for _,q in pairs(cs) do local b=s.find_entities_filtered{type={'transport-belt','underground-belt'},position={q[1]+0.5,q[2]+0.5},radius=0.3}[1] if b then for li=1,2 do for _,i in pairs(b.get_transport_line(li).get_contents()) do local k=i.name..' lane'..li c[k]=(c[k] or 0)+i.count end end end end "
          "local t={} for k,v in pairs(c) do t[#t+1]=k..' '..v end table.sort(t) return #t>0 and table.concat(t,', ') or 'empty' end "
          "local xs={} for x=5,XEND do xs[#xs+1]={x,RROW} end o[#o+1]='belt X: '..belt(xs) local os={} for x=11,XEND do os[#os+1]={x,RROW-6} end for y=12,RROW-17 do os[#os+1]={1,y} end o[#o+1]='belt O: '..belt(os) "
          "local inv=p.hub.get_inventory(defines.inventory.hub_main) o[#o+1]='hub: explosive rockets '..inv.get_item_count('explosive-rocket')..', free slots '..inv.count_empty_stacks() "
          "local np=0 for _,e in pairs(s.find_entities_filtered{area={{1,Y0},{35,Y1}}}) do if e.status==defines.entity_status.no_power or e.status==defines.entity_status.low_power then np=np+1 end end o[#o+1]='without power: '..np "
          "rcon.print(table.concat(o,string.char(10)))")

MADE = (TM.AT + "local t={} for _,e in pairs(s.find_entities_filtered{type={'assembling-machine','furnace'},area={{1,Y0},{35,Y1}}}) do local rc=e.get_recipe() if not rc and e.type=='furnace' then rc=e.previous_recipe end "
        "local k=rc and rc.name or e.name if type(k)~='string' then k=k.name end t[k]=(t[k] or 0)+e.products_finished end local o={} for k,v in pairs(t) do o[#o+1]=k..'='..v end "
        "local st=p.force.get_item_production_statistics(s) rcon.print(game.tick..'|'..table.concat(o,';')..'|'..st.get_input_count('explosive-rocket')..'|'..p.hub.get_inventory(defines.inventory.hub_main).get_item_count('explosive-rocket'))")


def sub(code):
    chains = "{" + ",".join("{name='%s',k=%d,ex=%d,intake=%d,back=%d,guard=%d,chute=%d}" % (n, c["k"], c["ex"], c["intake"], c["back"], c["guard"], c["chute"]) for n, c in CHAINS.items()) + "}"
    return (code.replace("CHAINLIST", chains).replace("KOROW", str(KO)).replace("KMROW", str(KM)).replace("CAPV", str(CAP)).replace("XEND", str(X_END))
            .replace("RROW", str(R)).replace("Y0", str(R - 18)).replace("Y1", str(R + 15)))


def made():
    t, body, total, hub = L(sub(MADE)).split("|")
    return int(t), {k: int(v) for k, v in (kv.split("=") for kv in body.split(";") if "=" in kv)}, int(float(total)), int(hub)


def main():
    a = sys.argv[1:]
    step = a[0] if a else "status"
    if step == "plan":
        ents, ts = plan()
        ok, bad = TM.place(ents, False)
        print("dry run: would place", ok, "of", len(ents), "failed", bad)
    elif step == "deck":
        ts = tiles_of(layout())
        print(L(TM.AT + "local n=0 for _,q in pairs(" + cells(ts) + ") do if s.get_tile(q[1],q[2]).name~='space-platform-foundation' and s.count_entities_filtered{type='tile-ghost',position={q[1]+0.5,q[2]+0.5},radius=0.3}==0 then "
                "if s.create_entity{name='tile-ghost',inner_name='space-platform-foundation',position={q[1],q[2]},force='player'} then n=n+1 end end end rcon.print('tile ghosts laid '..n)").strip())
    elif step == "build":
        apply = "--apply" in a
        ents = layout() + deciders()
        if apply:
            print("save:", tools["save_game"]("pre-edge-rockets"))
        ok, bad = TM.place(ents, apply)
        print("placed" if apply else "dry run: would place", ok, "of", len(ents), "failed", bad)
        if apply:
            print(L(sub(CONFIG)))
    elif step == "config":
        print(L(sub(CONFIG)))
    elif step == "status":
        print(L(sub(STATUS)))
    elif step == "rates":
        secs = int(a[1]) if len(a) > 1 else 60
        t0, m0, tot0, hub0 = made()
        time.sleep(secs)
        t1, m1, tot1, hub1 = made()
        mins = (t1 - t0) / 3600.0
        if mins <= 0:
            sys.exit("the game did not advance")
        print("over %.2f game minutes, crafts finished a minute in the rocket works:" % mins)
        for k in sorted(m1):
            print("  %-38s %7.1f" % (k, (m1[k] - m0.get(k, 0)) / mins))
        print("explosive rockets made on the whole ship: %.1f a minute; hub stock %d -> %d" % ((tot1 - tot0) / mins, hub0, hub1))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
