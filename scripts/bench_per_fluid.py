#!/usr/bin/env python3
"""TEST BENCH (2026-11-16): the per-fluid table for the Replicator's fluid-assembler unit (docs/replicator-compaction-plan.md, research pattern 1).
The live unit (omni_fluid_asm.py) has 4 deciders a recipe (P recipe, P solids, E recipe, E barrels): 48 for 12 recipes. The bench tries:
  P       set recipe from the CHOSEN ITEM signal (selector output, red wire) and read its own ingredients (green wire)
  A       one arithmetic combinator: each x BATCH -> each, P's reading -> P's blue chest (set requests)
  a fluid one decider (fluid > 0 -> recipe empty-<fluid>-barrel = 1 -> E, red) and one arithmetic (fluid x BATCH / 50 -> <fluid>-barrel -> E's blue chest, green)
Demand is faked by a constant combinator (no roboport): set it with `demand ITEM N`.
Same geometry as the unit (omni_fluid_asm.layout); extra combinators: demand constant (-6.5,-5.5), A at tile (-6,+1), the fluid table from tile (-6,+4), 2 a fluid.
Usage: bench_per_fluid.py build [--apply] | config | demand ITEM N | demand none | status | remove [--apply]"""
import json
import sys

import omni_fluid_asm as fa
from _game import tools

CX, CY = -192, -250          # free ground north of the Nauvis landing pad, inside the robot network
BATCH = fa.BATCH
L = tools["run_lua"]
Q = dict(fa.Q)


def fluids():
    """Barrel fluids of the unit's recipes, sorted: [(fluid, barrel), ...]."""
    seen = {}
    for row in fa.recipes():
        key, name, fl, bar = row.split("|")
        if fl != "solid":
            seen[fl.split(" x")[0]] = bar
    return sorted(seen.items())


def extra(fl):
    out = [{"name": "constant-combinator", "x": CX - 6.5, "y": CY - 5.5, "direction": 0, "params": dict(Q)},
           {"name": "arithmetic-combinator", "x": CX - 5.5, "y": CY + 2.0, "direction": 0, "params": dict(Q)},
           # item -> recipe signal (the cells' lookup): ring constant, D1, A1, D2. Needed because P obeys its own ingredient ITEM signals on the set-recipe wire
           # unless a RECIPE-type signal is there (bench result 2026-11-16).
           {"name": "constant-combinator", "x": CX - 6.5, "y": CY - 4.5, "direction": 0, "params": dict(Q)},
           {"name": "decider-combinator", "x": CX - 6.5, "y": CY - 3.0, "direction": 0, "params": dict(Q)},
           {"name": "arithmetic-combinator", "x": CX - 3.5, "y": CY - 5.0, "direction": 0, "params": dict(Q)},
           {"name": "decider-combinator", "x": CX - 3.5, "y": CY + 3.0, "direction": 0, "params": dict(Q)}]
    for k in range(len(fl)):
        out.append({"name": "decider-combinator", "x": CX - 5.5 + 2 * k, "y": CY + 5.0, "direction": 0, "params": dict(Q)})
        out.append({"name": "arithmetic-combinator", "x": CX - 4.5 + 2 * k, "y": CY + 5.0, "direction": 0, "params": dict(Q)})
    return out


def P(key):
    return "{%s,%s}" % fa.pos(CX, CY, key)


CONFIG = fa.LIST + r'''
local s=game.surfaces.nauvis local W=defines.wire_connector_id
local CB={W.combinator_input_red,W.combinator_input_green,W.combinator_output_red,W.combinator_output_green} local CC={W.circuit_red,W.circuit_green}
local function wire(a,ia,b,ib) a.get_wire_connector(ia,true).connect_to(b.get_wire_connector(ib,true),false,defines.wire_origin.script) end
local function clr(e,ids) for _,id in pairs(ids) do local c=e.get_wire_connector(id,true) c.disconnect_all() c.disconnect_all(defines.wire_origin.script) end end
local function at(n,p) return s.find_entities_filtered{name=n,position=p,radius=0.4}[1] end
local Pm,Em,reqP,reqE,cc,dec,sel=at('assembling-machine-3',PP),at('assembling-machine-3',PE),at('requester-chest',PRP),at('requester-chest',PRE),at('constant-combinator',PCC),at('decider-combinator',PDEC),at('selector-combinator',PSEL)
local dm,A=at('constant-combinator',{CX-6.5,CY-5.5}),at('arithmetic-combinator',{CX-5.5,CY+2.0})
if not (Pm and Em and reqP and reqE and cc and dec and sel and dm and A) then rcon.print('bench incomplete') return end
local cb=cc.get_or_create_control_behavior() while cb.sections_count>0 do cb.remove_section(1) end local sec=cb.add_section()
for i,r in pairs(rs) do sec.set_slot(i,{value={type='item',name=r.key,quality='normal'},min=i}) end
local ring,D1,A1,D2=at('constant-combinator',{CX-6.5,CY-4.5}),at('decider-combinator',{CX-6.5,CY-3.0}),at('arithmetic-combinator',{CX-3.5,CY-5.0}),at('decider-combinator',{CX-3.5,CY+3.0})
if not (ring and D1 and A1 and D2) then rcon.print('lookup incomplete') return end
local rb=ring.get_or_create_control_behavior() while rb.sections_count>0 do rb.remove_section(1) end local rsec=rb.add_section()
for i,r in pairs(rs) do rsec.set_slot(i,{value={type='recipe',name=r.name,quality='normal'},min=i}) end
clr(ring,CC) clr(D1,CB) clr(A1,CB) clr(D2,CB)
local EACH={type='virtual',name='signal-each'}
clr(dec,CB) clr(sel,CB) clr(A,CB) clr(dm,CC) clr(cc,CC)
wire(dec,W.combinator_input_red,dm,W.circuit_red) wire(dec,W.combinator_input_green,cc,W.circuit_green)
dec.get_or_create_control_behavior().parameters={conditions={{first_signal=EACH,first_signal_networks={red=true,green=false},comparator='>',constant=0},{first_signal=EACH,first_signal_networks={red=false,green=true},comparator='>',constant=0,compare_type='and'}},outputs={{signal=EACH,copy_count_from_input=true,networks={red=true,green=false}}}}
wire(sel,W.combinator_input_red,dec,W.combinator_output_red) sel.get_or_create_control_behavior().parameters={operation='select',select_max=true,index_constant=0}
clr(Pm,CC) clr(Em,CC)
local b=Pm.get_or_create_control_behavior() b.circuit_set_recipe=true b.circuit_read_ingredients=true
b=Em.get_or_create_control_behavior() b.circuit_set_recipe=true b.circuit_read_ingredients=false
for _,q in pairs{reqP,reqE} do clr(q,CC) local qb=q.get_or_create_control_behavior() qb.set_requests=true qb.read_contents=false q.get_logistic_point(defines.logistic_member_index.logistic_container).trash_not_requested=true end
local RSIG={type='virtual',name='signal-R'}
wire(D1,W.combinator_input_red,sel,W.combinator_output_red) wire(D1,W.combinator_input_green,cc,W.circuit_green)
D1.get_or_create_control_behavior().parameters={conditions={{first_signal=EACH,first_signal_networks={red=true,green=false},comparator='>',constant=0},{first_signal=EACH,first_signal_networks={red=false,green=true},comparator='>',constant=0,compare_type='and'}},outputs={{signal=EACH,copy_count_from_input=true,networks={red=false,green=true}}}}
wire(A1,W.combinator_input_green,D1,W.combinator_output_green) A1.get_or_create_control_behavior().parameters={first_signal=EACH,second_constant=0,operation='+',output_signal=RSIG}
wire(D2,W.combinator_input_green,A1,W.combinator_output_green) wire(D2,W.combinator_input_red,ring,W.circuit_red)
D2.get_or_create_control_behavior().parameters={conditions={{first_signal=EACH,first_signal_networks={red=true,green=false},comparator='=',second_signal=RSIG,second_signal_networks={red=false,green=true}}},outputs={{signal=EACH,copy_count_from_input=false,constant=1}}}
wire(D2,W.combinator_output_red,Pm,W.circuit_red)                        -- a RECIPE signal sets P's recipe (red)
wire(A,W.combinator_input_green,Pm,W.circuit_green)                      -- P's own ingredients (green) ...
A.get_or_create_control_behavior().parameters={first_signal=EACH,second_constant=BATCHN,operation='*',output_signal=EACH}
wire(A,W.combinator_output_green,reqP,W.circuit_green)                   -- ... x BATCH -> P's blue chest
local FL=FLUIDS local n=0
for k,fb in ipairs(FL) do
  local d=at('decider-combinator',{CX-5.5+2*(k-1),CY+5.0}) local ar=at('arithmetic-combinator',{CX-4.5+2*(k-1),CY+5.0})
  if d and ar then clr(d,CB) clr(ar,CB)
    wire(d,W.combinator_input_green,Pm,W.circuit_green) wire(ar,W.combinator_input_green,Pm,W.circuit_green)
    d.get_or_create_control_behavior().parameters={conditions={{first_signal={type='fluid',name=fb[1]},comparator='>',constant=0}},outputs={{signal={type='recipe',name='empty-'..fb[2]},copy_count_from_input=false,constant=1}}}
    ar.get_or_create_control_behavior().parameters={first_signal={type='fluid',name=fb[1]},second_constant=DIVN,operation='/',output_signal={type='item',name=fb[2]}}
    wire(d,W.combinator_output_red,Em,W.circuit_red) wire(ar,W.combinator_output_green,reqE,W.circuit_green) n=n+1 end
end
rcon.print('bench wired: '..#rs..' items on the list, fluids '..n..' of '..#FL)
'''

STATUS = r'''
local s=game.surfaces.nauvis local W=defines.wire_connector_id local m={} for k,v in pairs(defines.entity_status) do m[v]=k end
local function at(n,p) return s.find_entities_filtered{name=n,position=p,radius=0.4}[1] end
local function sig(e,id) local t={} local n=e.get_circuit_network(id) if n and n.signals then for _,x in pairs(n.signals) do t[#t+1]=(x.signal.type or 'item')..':'..x.signal.name..' '..x.count end end return table.concat(t,', ') end
local function st(e) local r=e.get_recipe() local fl={} for n,v in pairs(e.get_fluid_contents()) do fl[#fl+1]=n..' '..math.floor(v) end return (r and r.name or 'no recipe')..', '..tostring(m[e.status])..', made '..e.products_finished..(#fl>0 and (' ['..table.concat(fl,', ')..']') or '') end
local function inv(e) local t={} for _,it in pairs(e.get_inventory(defines.inventory.chest).get_contents()) do t[#t+1]=it.name..' '..it.count end return table.concat(t,', ') end
local function req(e) local t={} local pt=e.get_logistic_point(defines.logistic_member_index.logistic_container) for _,f in pairs(pt.filters or {}) do t[#t+1]=(f.name or '?')..' '..tostring(f.count) end return table.concat(t,', ') end
local Pm,Em=at('assembling-machine-3',PP),at('assembling-machine-3',PE) if not (Pm and Em) then rcon.print('bench not built') return end
local reqP,reqE=at('requester-chest',PRP),at('requester-chest',PRE)
local o={}
o[#o+1]='P set-recipe wire (red): '..sig(Pm,W.circuit_red)
o[#o+1]='P read wire (green):     '..sig(Pm,W.circuit_green)
o[#o+1]='P: '..st(Pm)..' | blue asks: '..req(reqP)..' | blue holds: '..inv(reqP)..' | red: '..inv(at('passive-provider-chest',PCP))
o[#o+1]='E set-recipe wire (red): '..sig(Em,W.circuit_red)
o[#o+1]='E: '..st(Em)..' | blue asks: '..req(reqE)..' | blue holds: '..inv(reqE)..' | red: '..inv(at('passive-provider-chest',PCE))
rcon.print(table.concat(o,'\n'))
'''


def fill(code, fl=None):
    rep = {"PP": P("P"), "PE": P("E"), "PRP": P("reqP"), "PRE": P("reqE"), "PCC": P("cc"), "PDEC": P("dec"), "PSEL": P("sel"), "PCP": P("chP"), "PCE": P("chE")}
    import re
    for k, v in sorted(rep.items(), key=lambda kv: -len(kv[0])):
        code = re.sub(r"\b%s\b" % k, v, code)
    code = code.replace("CX", str(CX)).replace("CY", str(CY)).replace("BATCHN", str(BATCH)).replace("DIVN", str(50 // BATCH))
    if fl is not None:
        code = code.replace("FLUIDS", "{" + ",".join("{'%s','%s'}" % fb for fb in fl) + "}")
    return " ".join(line.split("--")[0] for line in code.split("\n"))


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    apply = "--apply" in sys.argv
    if step == "build":
        fl = fluids()
        ents = fa.layout(CX, CY) + extra(fl)
        if apply:
            print("save:", tools["save_game"]("pre-bench-per-fluid"))
        r = json.loads(tools["place_entities"](json.dumps(ents), surface="nauvis", dry_run=not apply, clear_trees=apply))
        print("fluids", fl)
        print(("placed" if apply else "dry run:"), r.get("placed"), "of", len(ents), "failed", json.dumps(r.get("failed") or [])[:500])
    elif step == "config":
        print(L(fill(CONFIG, fluids())))
    elif step == "demand":
        item = sys.argv[2]
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        slot = "" if item == "none" else "sec.set_slot(1,{value={type='item',name='%s',quality='normal'},min=%d})" % (item, n)
        print(L("local s=game.surfaces.nauvis local dm=s.find_entities_filtered{name='constant-combinator',position={%s,%s},radius=0.4}[1] local cb=dm.get_or_create_control_behavior() "
                "while cb.sections_count>0 do cb.remove_section(1) end local sec=cb.add_section() %s rcon.print('demand set: %s %d')" % (CX - 6.5, CY - 5.5, slot, item, n)))
    elif step == "status":
        print(L(fill(STATUS)))
    elif step == "remove":
        code = ("local s=game.surfaces.nauvis local n=0 for _,e in pairs(s.find_entities_filtered{area={{%d,%d},{%d,%d}},force='player'}) do "
                "if e.type~='logistic-robot' and e.type~='construction-robot' then if %s then e.order_deconstruction(game.forces.player) end n=n+1 end end rcon.print('bench entities '..n..(%s and ' marked for deconstruction' or ' (dry run)'))"
                % (CX - 8, CY - 7, CX + 9, CY + 8, "true" if apply else "false", "true" if apply else "false"))
        print(L(code))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
