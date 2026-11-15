"""Soak 2 (after the hold fix): every ~100 s: per machine recipe/made, choice changes over 12 back-to-back reads, bad requests, other units' entity
counts. At +5 game minutes a one-item request (1 cargo-wagon) is placed in a temporary requester chest; the tick when a machine picks it and when it
arrives are logged. Read only, except that one chest (placed via place_entities, deconstructed at the end)."""
import json
import time

import replicator_compress as r
from _game import tools

TARGET = 108000
TEST_ITEM, POS = "flamethrower-turret", (-337.5, -239.5)
d = r.game_recipes()
ING = sorted({i for v in d.values() for i in v["ing"]})
BOXES = {"fluid unit": (-310, -233, -290, -215), "fluid-asm": (-342, -190, -316, -165), "buffer field": (-346, -233, -334, -222)}
boxes = "".join("do local c=0 for _,e in pairs(s.find_entities_filtered{area={{%d,%d},{%d,%d}},force='player'}) do if e.type~='logistic-robot' and e.type~='construction-robot' then c=c+1 end end b[#b+1]='%s '..c end " % (v + (k,)) for k, v in BOXES.items())
SAMPLE = ("local s=game.surfaces.nauvis local W=defines.wire_connector_id local ING={%s} local ok={} for _,n in pairs(ING) do ok[n]=true end local o={} "
          "local function at(n,x,y) return s.find_entities_filtered{name=n,position={x,y},radius=0.4}[1] end "
          "for u=0,2 do local ox=7*u local am=at('assembling-machine-3',-354+ox+2.5,-221.5) local rq=at('requester-chest',-354+ox+2.5,-224.5) local rr=am.get_recipe() "
          "local n=rq.get_circuit_network(W.circuit_green) local bad={} local items=0 if n and n.signals then for _,x in pairs(n.signals) do if (x.signal.type==nil or x.signal.type=='item') then items=items+1 if not ok[x.signal.name] then bad[#bad+1]=x.signal.name end end end end "
          "o[#o+1]='m'..(u+1)..' '..(rr and rr.name or 'none')..' made '..am.products_finished..' reqs '..items..(#bad>0 and (' BAD:'..table.concat(bad,'/')) or '') end "
          "local b={} BOXES rcon.print(game.tick..' '..table.concat(o,' | ')..' || '..table.concat(b,' ; '))").replace("BOXES", boxes) % ",".join("'%s'" % i for i in ING)
PROBE = ("local s=game.surfaces.nauvis local W=defines.wire_connector_id local o={} for u=0,2 do local sel=s.find_entities_filtered{name='selector-combinator',position={-354+7*u+6.5,-223},radius=0.4}[1] "
         "local n=sel.get_circuit_network(W.combinator_output_green) o[#o+1]=(n and n.signals and n.signals[1]) and n.signals[1].signal.name or '-' end rcon.print(table.concat(o,' '))")
FIND = "local s=game.surfaces.nauvis local c=s.find_entities_filtered{name='requester-chest',position={%s,%s},radius=0.4}[1] " % POS
start, placed, picked, arrived = None, None, None, None
while True:
    out = tools["run_lua"](SAMPLE)
    tick = int(out.split()[0])
    start = start or tick
    seqs = [tools["run_lua"](PROBE).split() for _ in range(12)]
    changes = [sum(1 for a, b in zip(seqs, seqs[1:]) if a[u] != b[u]) for u in range(3)]
    msg = "[+%5.1f min] %s || choice changes in 12 reads %s" % ((tick - start) / 3600.0, out, changes)
    if placed is None and tick - start >= 18000:
        if tools["run_lua"](FIND + "rcon.print(c and 1 or 0)").strip() == "0":
            tools["place_entities"](json.dumps([{"name": "requester-chest", "x": POS[0], "y": POS[1], "direction": 0, "params": {"quality": "epic"}}]), surface="nauvis", dry_run=False)
        tools["run_lua"](FIND + "local lp=c.get_logistic_point(defines.logistic_member_index.logistic_container) local se=lp.get_section(1) or lp.add_section() se.set_slot(3,{value={type='item',name='%s',quality='normal'},min=1}) rcon.print('ok')" % TEST_ITEM)
        placed = tick
        msg += " || TEST: requested 1 %s" % TEST_ITEM
    if placed and picked is None and any(TEST_ITEM in s_ for s_ in seqs):
        picked = tick
        msg += " || TEST: picked after %d ticks" % (picked - placed)
    if placed and arrived is None:
        have = tools["run_lua"](FIND + "rcon.print(c and c.get_item_count('%s') or 0)" % TEST_ITEM).strip()
        if have not in ("0", ""):
            arrived = tick
            msg += " || TEST: arrived after %d ticks" % (arrived - placed)
    print(msg, flush=True)
    if tick - start >= TARGET:
        tools["run_lua"](FIND + "if c then c.order_deconstruction(game.forces.player) end rcon.print('x')")
        print("soak finished; test placed %s picked %s arrived %s" % (placed, picked, arrived), flush=True)
        break
    time.sleep(60 if placed and arrived is None else 100)
