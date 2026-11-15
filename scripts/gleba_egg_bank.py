#!/usr/bin/env python3
"""Gleba egg bank: a small self-sustaining egg breeder (the Captain, 2026-11-15: "a fully self-sufficient egg reproducer that only lets eggs out
when it is self-sustainable").

Why it exists: a pentapod egg hatches 15 minutes after it was last crafted, so eggs cannot be stored; the main loop's eggs die whenever science
pauses for a quarter of an hour (packs at their cap, labs idle) or the cell stalls. The bank keeps a handful of eggs alive by re-crafting them on
a heartbeat, from its own bioflux, and lends eggs to the main loop only while it is healthy.

        pipes (water) ------------------------------
          E1  <==ring==>  E2  --tap--> [egg chest, provider]
           ^               ^
           +----- N -------+       N = nutrients-from-bioflux chamber, bioflux from a requester chest (gated by the cell's own bioflux stock)
        fuel loop: N -> Cn -> Cm -> N  (Cm also asks the network for 8 nutrients: that is the cold start)

Heartbeat: a combinator clock counts ticks; every PERIOD ticks it opens a WINDOW-tick window. Only inside the window do nutrients move (N -> E1/E2) and
bioflux move (chest -> N), so each chamber crafts about once per period and every egg is re-crafted (and so made fresh) well inside its 15 minutes.
Population cap: the feed also needs eggs in the ring < EGG_MAX, so the ring cannot grow without limit.
Release: the tap opens only while the ring holds >= KEEP_EGGS+1 eggs, bioflux for the next beats is on hand, and the network wants eggs.

Usage: gleba_egg_bank.py dry | build | circuit | seed | status
"""
import json
import sys

from _game import tools
import gleba_cell as G

L = G.L
O = (82, 44)                 # top-left tile of the bank
PERIOD = 36000               # ticks between heartbeats: 10 minutes, inside the 15 minute hatch time
WINDOW = 900                 # ticks the window stays open (15 s: N needs two crafts to make the 60 nutrients both chambers need, and nutrients rot in 5 minutes so each heartbeat must finish in one window)
EGG_MAX = 30                 # the feed stops only on real overgrowth (6 and then 10 both deadlocked a ring whose eggs sat idle for want of nutrients: the cap shut the very feed they needed)
KEEP_EGGS = 2                # the tap never takes the ring below this
NET_EGG_WANT = 30            # the tap is open while the network holds fewer eggs than this: the main loop always wants eggs, so the breeder lends its surplus instead of letting it age
BIOFLUX_BUFFER = 100         # about 10 heartbeats = 100 minutes of life if the whole cell is dead
BIOFLUX_HEALTHY = 150        # the bioflux inserter refills the buffer only while the cell holds more than this
NEED_BIOFLUX_IN_BANK = 10    # the tap stays shut when the bank holds less bioflux than this (N input + chest)


def w(tx, ty):
    return (O[0] + tx + 0.5, O[1] + ty + 0.5)


def plan():
    P = G.Plan()
    E1, E2, N = w(1, 1), w(5, 1), w(3, 5)
    P.add("biochamber", E1[0], E1[1], 0, "pentapod-egg", G.Q)
    P.add("biochamber", E2[0], E2[1], 0, "pentapod-egg", G.Q)
    P.add("biochamber", N[0], N[1], 0, "nutrients-from-bioflux", G.Q)
    # ring (E1 <-> E2)
    P.add("bulk-inserter", *w(3, 0), 4, None, G.Q)
    P.add("bulk-inserter", *w(3, 2), 12, None, G.Q)
    # N feeds both egg chambers (gated by the heartbeat: circuit set in circuit())
    P.add("bulk-inserter", *w(2, 3), 8, None, G.Q, feed=True)
    P.add("bulk-inserter", *w(4, 3), 8, None, G.Q, feed=True)
    # fuel loop for N: I1 N->Cn, I3 Cn->Cm, I2 Cm->N
    P.add("bulk-inserter", *w(1, 4), 4, None, G.Q, loop=True)         # gated in circuit(): open only while the heartbeat window is CLOSED, so the egg chambers are fed first # inserter direction = the side it PICKS UP from (E=4: picks east, drops west)
    P.add("steel-chest", *w(0, 4))
    P.add("bulk-inserter", *w(0, 5), 0, None, G.Q)
    P.add("requester-chest", *w(0, 6), request={"nutrients": 8})
    P.add("bulk-inserter", *w(1, 6), 12, None, G.Q)
    # bioflux for N
    P.add("requester-chest", *w(3, 8), request={"bioflux": BIOFLUX_BUFFER})
    P.add("bulk-inserter", *w(3, 7), 8, None, G.Q, feed=True, cond=("bioflux", ">", BIOFLUX_HEALTHY))
    # tap: E2 -> provider chest
    P.add("bulk-inserter", *w(7, 1), 12, None, G.Q, tap=True, cond=("pentapod-egg", "<", NET_EGG_WANT))
    P.add("passive-provider-chest", *w(8, 1), bar=3)
    # poles
    P.add("medium-electric-pole", *w(3, 1))
    P.add("medium-electric-pole", *w(0, 7))
    P.add("medium-electric-pole", *w(7, 3))
    P.add("medium-electric-pole", *w(-1, 2))
    # combinators (1 x 2, standing in the free column west of the bank)
    for i, nm in enumerate(("arithmetic-combinator", "arithmetic-combinator", "decider-combinator", "decider-combinator")):
        P.add(nm, O[0] - 1.5, O[1] + 1.0 + 2 * i, 0, None, None)
    # water: from the hub's vertical pipe (93.5, 39.5) down and west along the row above the chambers
    for y in (40.5, 41.5, 42.5):
        P.add("pipe", 93.5, y)
    for x in range(O[0], O[0] + 12):
        P.add("pipe", x + 0.5, O[1] - 0.5)
    return P


def build(apply):
    P = plan()
    for e in P.ents:
        e["cfg"] = dict(e["cfg"])
    G.SIZE.update({"biochamber": 1.5, "arithmetic-combinator": 1, "decider-combinator": 1, "steel-chest": .5})
    print("entities", len(P.ents))
    print(G.clear_plants(P, apply))
    if not apply:
        placed, failed = G.place(P, True)
        print("dry run", placed, json.dumps(failed)[:1500])
        return
    tools["save_game"]("skippy")
    placed, failed = G.place(P, False)
    print("placed", placed, "failed", json.dumps(failed)[:1500])
    for r in G.cfg_lua(P):
        print(r)


CIRCUIT = """
local s=game.surfaces.gleba local f=game.forces.player
local function at(name,x,y) return s.find_entities_filtered{name=name,position={x,y},radius=0.9,force=f}[1] end
local R=defines.wire_connector_id local WO=defines.wire_origin.script
local function con(e,id) return e.get_wire_connector(id,true) end
local E1=at('biochamber',%(e1x)s,%(e1y)s) local E2=at('biochamber',%(e2x)s,%(e2y)s) local Nn=at('biochamber',%(nx)s,%(ny)s)
local cs={} for _,e in pairs(s.find_entities_filtered{name={'arithmetic-combinator','decider-combinator'},area={{%(cx0)s,%(cy0)s},{%(cx1)s,%(cy1)s}},force=f}) do cs[#cs+1]=e end
table.sort(cs,function(a,b) return a.position.y<b.position.y end)
local C,M,D1,D2=cs[1],cs[2],cs[3],cs[4]
if not(E1 and E2 and Nn and C and M and D1 and D2) then rcon.print('missing parts') return end
local T={type='virtual',name='signal-T'} local MM={type='virtual',name='signal-M'} local G1={type='virtual',name='signal-G'} local G2={type='virtual',name='signal-H'} local EGG={type='item',name='pentapod-egg'} local BF={type='item',name='bioflux'}
C.get_or_create_control_behavior().parameters={first_signal=T,second_constant=1,operation='+',output_signal=T}
M.get_or_create_control_behavior().parameters={first_signal=T,second_constant=%(period)d,operation='%%',output_signal=MM}
D1.get_or_create_control_behavior().parameters={conditions={{first_signal=MM,comparator='<',constant=%(window)d},{first_signal=EGG,comparator='<',constant=%(emax)d,compare_type='and'}},outputs={{signal=G1,copy_count_from_input=false}}}
D2.get_or_create_control_behavior().parameters={conditions={{first_signal=EGG,comparator='>',constant=%(keep)d},{first_signal=BF,comparator='>',constant=%(needbf)d,compare_type='and'}},outputs={{signal=G2,copy_count_from_input=false}}}
con(C,R.combinator_output_red).connect_to(con(C,R.combinator_input_red),false,WO)
con(C,R.combinator_output_red).connect_to(con(M,R.combinator_input_red),false,WO)
con(M,R.combinator_output_red).connect_to(con(D1,R.combinator_input_red),false,WO)
for _,e in pairs({E1,E2}) do e.get_or_create_control_behavior().circuit_read_contents=true con(e,R.circuit_red).connect_to(con(D1,R.combinator_input_red),false,WO) con(e,R.circuit_red).connect_to(con(D2,R.combinator_input_red),false,WO) end
Nn.get_or_create_control_behavior().circuit_read_contents=true con(Nn,R.circuit_red).connect_to(con(D2,R.combinator_input_red),false,WO)
local function gate(e,sig,wire_from)
  local cb=e.get_or_create_control_behavior() cb.circuit_enable_disable=true cb.circuit_condition={first_signal=sig,comparator='>',constant=0}
  con(wire_from,R.combinator_output_red).connect_to(con(e,R.circuit_red),false,WO) end
local n=0
for _,p in pairs({{%(f1)s},{%(f2)s},{%(f3)s}}) do local e=at('bulk-inserter',p[1],p[2]) if e then gate(e,G1,D1) n=n+1 end end
local tap=at('bulk-inserter',%(tapx)s,%(tapy)s) if tap then gate(tap,G2,D2) n=n+1 end
local loop=at('bulk-inserter',%(lx)s,%(ly)s) if loop then local lcb=loop.get_or_create_control_behavior() lcb.circuit_enable_disable=true lcb.circuit_condition={first_signal=G1,comparator='<',constant=1} con(D1,R.combinator_output_red).connect_to(con(loop,R.circuit_red),false,WO) n=n+1 end
rcon.print('circuit built, gated inserters '..n)
"""


def circuit():
    E1, E2, N = w(1, 1), w(5, 1), w(3, 5)
    f1, f2, f3 = w(2, 3), w(4, 3), w(3, 7)
    tap = w(7, 1)
    code = CIRCUIT % dict(e1x=E1[0], e1y=E1[1], e2x=E2[0], e2y=E2[1], nx=N[0], ny=N[1], cx0=O[0] - 3, cy0=O[1], cx1=O[0] - 0.5, cy1=O[1] + 9,
                          period=PERIOD, window=WINDOW, emax=EGG_MAX, keep=KEEP_EGGS, needbf=NEED_BIOFLUX_IN_BANK,
                          f1="%s,%s" % f1, f2="%s,%s" % f2, f3="%s,%s" % f3, tapx=tap[0], tapy=tap[1], lx=w(1, 4)[0], ly=w(1, 4)[1])
    print(L(code))


def seed(n=2):
    """Two eggs moved from the main loop into the ring (moving factory-made eggs between inventories; nothing is spawned)."""
    E1, E2 = w(1, 1), w(5, 1)
    code = ("local s=game.surfaces.gleba local got=0 "
            "for _,e in pairs(s.find_entities_filtered{name='biochamber',area={{89,35},{110,41}}}) do if got>=%d then break end local inv=e.get_inventory(defines.inventory.crafter_input) local c=inv.get_item_count('pentapod-egg') "
            "if c>0 then got=got+inv.remove{name='pentapod-egg',count=math.min(c,%d-got)} end end "
            "local a=s.find_entities_filtered{name='biochamber',position={%s,%s},radius=0.5}[1] local b=s.find_entities_filtered{name='biochamber',position={%s,%s},radius=0.5}[1] "
            "local put=0 if got>0 then put=put+a.get_inventory(defines.inventory.crafter_input).insert{name='pentapod-egg',count=1} end if got>1 then put=put+b.get_inventory(defines.inventory.crafter_input).insert{name='pentapod-egg',count=1} end "
            "rcon.print('took '..got..' eggs from the main loop, put '..put..' into the bank ring')") % (n, n, E1[0], E1[1], E2[0], E2[1])
    print(L(code))


def status():
    E1, E2, N = w(1, 1), w(5, 1), w(3, 5)
    code = ("local m={} for k,v in pairs(defines.entity_status) do m[v]=k end local s=game.surfaces.gleba local o={} "
            "for nm,p in pairs({E1={%s,%s},E2={%s,%s},N={%s,%s}}) do local e=s.find_entities_filtered{name='biochamber',position=p,radius=0.5}[1] if e then "
            "o[#o+1]=nm..' '..m[e.status]..' in '..serpent.line(e.get_inventory(defines.inventory.crafter_input).get_contents())..' out '..serpent.line(e.get_inventory(defines.inventory.crafter_output).get_contents()) end end "
            "local c=s.find_entities_filtered{name='arithmetic-combinator',position={%s,%s},radius=3}[1] if c then local sg=c.get_signal({type='virtual',name='signal-T'},defines.wire_connector_id.combinator_output_red) o[#o+1]='clock T='..tostring(sg) end "
            "rcon.print(table.concat(o,'\\n'))") % (E1 + E2 + N + (O[0] - 1.5, O[1] + 1.0))
    print(L(code))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    {"dry": lambda: build(False), "build": lambda: build(True), "circuit": circuit, "seed": seed, "status": status}[cmd]()
