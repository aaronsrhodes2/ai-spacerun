#!/usr/bin/env python3
"""The compact Replicator CELL (the Captain, 2026-11-14: "compress it, squish it of unused space and get it all small, then we just multiply
that block and we have many replicators"). The logic is the compact lookup of scripts/replicator_compress.py (the machine reads its own
recipe's ingredients; 4 combinators a machine instead of a 178-decider table) plus the stall fix (own-request penalty, +10 hold).

FOOTPRINT 21 x 11 tiles (the large Replicator's machines+tables filled ~78 x 44). Tile offsets from the cell's top-left (X, Y):
  row 0-3   demand roboport (0,0) 4x4 | [stock roboport (4,0) 4x4, only with --silos] | substation (8,0) | rank list (8,2) | ring (9,2)
            | [stock negate (10,0), stock gate (11,0), only with --silos] | substation (19,0)
  row 4-10  three machine columns, 7 wide (ox = 7k): blue chest (ox+1,4), inserter (ox+1,5), assembler 3 (ox,6) 3x3, inserter (ox+1,9),
            red chest (ox+1,10); combinators 1x2 at (ox+3..6, 4|6|8): dec sel ar [first-call] / D1 A1 D2 A2 / penalty hold
CHOICE per machine (as omni_maker): dec = demanded AND on the rank list -> 1e6; ar = -demand; first-call (machines 2,3) = +1e7 for what the
  previous blue chest asks for and the network lacks; selector picks the max. PENALTY: -1e6 on the selector's green input for what the
  machine's own blue chest asks for; HOLD: +10 for the item already chosen (also on the green input: on the red score net it fed
  the first-call decider and kept an item of ANOTHER partition chosen while its demand was under 10). LOOKUP: D1 (chosen AND rank) -> A1 (sum to signal-R) -> D2 (ring
  of RECIPE signals, value = rank, == R) -> assembler (set recipe, read ingredients) -> A2 (x BATCH) -> blue chest requests.
PARTITION (multiply without coordination): a cell with index p of n keeps on its RANK LIST only the items whose rank mod n == p (the ring
  keeps all). Its dec then never passes the other cells' items, so two cells never make the same item; a sub-part of another partition is
  requested by this cell's blue chest and the owning cell sees it as ordinary demand. Data only: no extra combinator.
DEMAND: the cell's own roboport reads the missing requests of the network it stands in (any surface), or --demand RX RY: the dec/ar read a
  shared HUB roboport instead (on Nauvis the old Replicator's roboport at (-352,-229) with its stock stage + silos, which the fluid, fluid-assembler
  and furnace units also read: orbital demand then counts once for everyone). Only ONE cell per surface may read the
  silos' orbital requests (--silos), or the orbital demand is counted twice. Optional modules attach to the demand roboport's red wire:
  furnace unit, fluid unit (omni_fluid.py), fluid-assembler unit (omni_fluid_asm.py), buffer field.
Registry: snapshots/replicator_cells.json (name -> surface, rank/ring positions, n, p, menu); `refresh` rewrites every registered list.
Steps: plan NAME X Y [--surface S] [--silos] [--part P/N] [--demand RX RY] | build NAME [--apply] | config NAME | refresh [NAME] | status NAME | verify NAME
  `plan` registers the cell (no game change) and dry-runs it; `build --apply` saves, places (never twice), wires and refreshes."""
import json
import sys
import time
from pathlib import Path

from _game import tools

REG = Path(__file__).resolve().parent.parent / "snapshots" / "replicator_cells.json"
W_, H_ = 21, 11
BATCH, HOLD = 5, 10
Q = {"quality": "epic"}


def reg():
    return json.loads(REG.read_text(encoding="utf-8")) if REG.exists() else {}


def save_reg(r):
    REG.write_text(json.dumps(r, indent=1, sort_keys=True), encoding="utf-8")


def layout(c):
    X, Y, silos = c["x"], c["y"], c.get("silos", False)

    def e(name, tx, ty, w=1, h=1):
        return {"name": name, "x": X + tx + w / 2, "y": Y + ty + h / 2, "direction": 0, "params": dict(Q)}
    out = [e("roboport", 0, 0, 4, 4), e("substation", 8, 0, 2, 2), e("constant-combinator", 8, 2), e("constant-combinator", 9, 2), e("substation", 19, 0, 2, 2)]
    if silos:
        out += [e("roboport", 4, 0, 4, 4), e("arithmetic-combinator", 10, 0, 1, 2), e("decider-combinator", 11, 0, 1, 2)]
    for k in range(3):
        ox = 7 * k
        out += [e("requester-chest", ox + 1, 4), e("fast-inserter", ox + 1, 5), e("assembling-machine-3", ox, 6, 3, 3), e("fast-inserter", ox + 1, 9),
                e("passive-provider-chest", ox + 1, 10),
                e("decider-combinator", ox + 3, 4, 1, 2), e("selector-combinator", ox + 4, 4, 1, 2), e("arithmetic-combinator", ox + 5, 4, 1, 2),
                e("decider-combinator", ox + 3, 6, 1, 2), e("arithmetic-combinator", ox + 4, 6, 1, 2), e("decider-combinator", ox + 5, 6, 1, 2),
                e("arithmetic-combinator", ox + 6, 6, 1, 2), e("decider-combinator", ox + 3, 8, 1, 2), e("decider-combinator", ox + 4, 8, 1, 2)]
        if k > 0:
            out.append(e("decider-combinator", ox + 6, 4, 1, 2))
            out.append(e("decider-combinator", ox + 5, 8, 1, 2))          # cross-penalty (2026-11-16): see SPREAD below
    return out


# SPREAD (2026-11-16, found by the parity test): all three machines of a cell chose the same top order. When that order could not be made (efficiency module 3
# waits for spoilage on Nauvis) the whole partition hung: cell2 never made the shotgun shells cell1 was waiting for. Machines 2 and 3 now subtract SPREAD from
# the score of what the earlier machines have chosen: another demanded item always wins, but with nothing else to do they still join in on the big order.
SPREAD = 500000


def spread_entities(c):
    X, Y = c["x"], c["y"]
    return [{"name": "decider-combinator", "x": X + 7 * k + 5.5, "y": Y + 9.0, "direction": 0, "params": dict(Q)} for k in (1, 2)]


def rank_ring(c):
    return (c["x"] + 8.5, c["y"] + 2.5), (c["x"] + 9.5, c["y"] + 2.5)


CONFIG = ("local s=game.surfaces['SURF'] local f=game.forces.player local W=defines.wire_connector_id local X,Y=CX,CY local SILOS=SIL local o={} "
          "local function at(n,dx,dy) return s.find_entities_filtered{name=n,position={X+dx,Y+dy},radius=0.4}[1] end "
          "local function wire(a,ia,b,ib) a.get_wire_connector(ia,true).connect_to(b.get_wire_connector(ib,true),false) end "
          "local CB={W.combinator_input_red,W.combinator_input_green,W.combinator_output_red,W.combinator_output_green} local CC={W.circuit_red,W.circuit_green} "
          "local function clr(e,ids) for _,id in pairs(ids) do e.get_wire_connector(id,true).disconnect_all() end end "
          "local EACH={type='virtual',name='signal-each'} local function dp(e,conds,outs) e.get_or_create_control_behavior().parameters={conditions=conds,outputs=outs} end "
          "local function C(net,cmp,k) return {first_signal=EACH,first_signal_networks=net,comparator=cmp,constant=k} end local RED,GRN={red=true,green=false},{red=false,green=true} "
          "local rp,rank,ring=at('roboport',2,2),at('constant-combinator',8.5,2.5),at('constant-combinator',9.5,2.5) local DEM=DEMT if not (rank and ring and (rp or DEM)) then rcon.print('ABORT: cell not built') return end "
          "clr(rank,CC) clr(ring,CC) if rp then clr(rp,CC) local rc=rp.get_or_create_control_behavior() rc.read_items_mode=defines.control_behavior.roboport.read_items_mode.missing_requests rc.read_robot_stats=false end local dem=rp if DEM then dem=s.find_entities_filtered{name='roboport',position=DEM,radius=0.6}[1] if not dem then rcon.print('ABORT: demand roboport missing') return end o[#o+1]='demand from the hub roboport at '..DEM[1]..','..DEM[2] end "
          "if SILOS then local rp2,neg,gate=at('roboport',6,2),at('arithmetic-combinator',10.5,1),at('decider-combinator',11.5,1) clr(rp2,CC) clr(neg,CB) clr(gate,CB) "
          "rp2.get_or_create_control_behavior().read_items_mode=defines.control_behavior.roboport.read_items_mode.logistics rp2.get_or_create_control_behavior().read_robot_stats=false "
          "wire(neg,W.combinator_input_red,rp2,W.circuit_red) neg.get_or_create_control_behavior().parameters={first_signal=EACH,second_constant=-1,operation='*',output_signal=EACH} "
          "wire(gate,W.combinator_input_green,neg,W.combinator_output_green) dp(gate,{C(nil,'>',0)},{{signal=EACH,copy_count_from_input=true}}) wire(gate,W.combinator_output_red,rp,W.circuit_red) local ns=0 "
          "for _,si in pairs(s.find_entities_filtered{type='rocket-silo',force=f}) do si.get_or_create_control_behavior().read_mode=defines.control_behavior.rocket_silo.read_mode.orbital_requests "
          "si.get_wire_connector(W.circuit_green,true).connect_to(gate.get_wire_connector(W.combinator_input_green,true),false) ns=ns+1 end o[#o+1]='silos '..ns end "
          "local prev,sel1,psel=nil,nil,nil for k=0,2 do local ox=7*k local rq,am,pv=at('requester-chest',ox+1.5,4.5),at('assembling-machine-3',ox+1.5,7.5),at('passive-provider-chest',ox+1.5,10.5) "
          "local dec,sel,ar=at('decider-combinator',ox+3.5,5),at('selector-combinator',ox+4.5,5),at('arithmetic-combinator',ox+5.5,5) "
          "local d1,a1,d2,a2=at('decider-combinator',ox+3.5,7),at('arithmetic-combinator',ox+4.5,7),at('decider-combinator',ox+5.5,7),at('arithmetic-combinator',ox+6.5,7) "
          "local pen,hold=at('decider-combinator',ox+3.5,9),at('decider-combinator',ox+4.5,9) local bo=k>0 and at('decider-combinator',ox+6.5,5) or nil local xp=k>0 and at('decider-combinator',ox+5.5,9) or nil "
          "for _,e in pairs{dec,sel,ar,d1,a1,d2,a2,pen,hold} do clr(e,CB) end if bo then clr(bo,CB) end if xp then clr(xp,CB) end clr(rq,CC) clr(am,CC) "
          "wire(dec,W.combinator_input_red,dem,W.circuit_red) wire(dec,W.combinator_input_green,rank,W.circuit_green) dp(dec,{C(RED,'>',0),{first_signal=EACH,first_signal_networks=GRN,comparator='>',constant=0,compare_type='and'}},{{signal=EACH,copy_count_from_input=false,constant=1000000}}) "
          "wire(ar,W.combinator_input_red,dem,W.circuit_red) ar.get_or_create_control_behavior().parameters={first_signal=EACH,second_constant=-1,operation='*',output_signal=EACH} wire(ar,W.combinator_output_red,dec,W.combinator_output_red) "
          "wire(sel,W.combinator_input_red,dec,W.combinator_output_red) sel.get_or_create_control_behavior().parameters={operation='select',select_max=true,index_constant=0} "
          "if bo then wire(bo,W.combinator_input_red,dec,W.combinator_output_red) wire(bo,W.combinator_input_green,prev,W.circuit_green) "
          "dp(bo,{C(RED,'>',0),{first_signal=EACH,first_signal_networks=GRN,comparator='>',constant=0,compare_type='and'}},{{signal=EACH,copy_count_from_input=false,constant=10000000}}) wire(bo,W.combinator_output_red,dec,W.combinator_output_red) end "
          "dp(d1,{C(GRN,'>',0),{first_signal=EACH,first_signal_networks=RED,comparator='>',constant=0,compare_type='and'}},{{signal=EACH,copy_count_from_input=true,networks=RED}}) "
          "a1.get_or_create_control_behavior().parameters={first_signal=EACH,second_constant=0,operation='+',output_signal={type='virtual',name='signal-R'}} "
          "dp(d2,{{first_signal=EACH,first_signal_networks=RED,comparator='=',second_signal={type='virtual',name='signal-R'},second_signal_networks=GRN}},{{signal=EACH,copy_count_from_input=false,constant=1}}) "
          "a2.get_or_create_control_behavior().parameters={first_signal=EACH,second_constant=BATCH,operation='*',output_signal=EACH} "
          "wire(sel,W.combinator_output_green,d1,W.combinator_input_green) wire(rank,W.circuit_red,d1,W.combinator_input_red) wire(d1,W.combinator_output_green,a1,W.combinator_input_green) "
          "wire(a1,W.combinator_output_green,d2,W.combinator_input_green) wire(ring,W.circuit_red,d2,W.combinator_input_red) wire(d2,W.combinator_output_green,am,W.circuit_green) "
          "wire(am,W.circuit_green,a2,W.combinator_input_green) wire(a2,W.combinator_output_green,rq,W.circuit_green) "
          "local ab=am.get_or_create_control_behavior() ab.circuit_set_recipe=true ab.circuit_read_ingredients=true "
          "local qb=rq.get_or_create_control_behavior() qb.set_requests=true qb.read_contents=false rq.get_logistic_point(defines.logistic_member_index.logistic_container).trash_not_requested=true "
          "dp(pen,{C(nil,'>',0)},{{signal=EACH,copy_count_from_input=false,constant=-1000000}}) wire(pen,W.combinator_input_green,rq,W.circuit_green) wire(pen,W.combinator_output_green,sel,W.combinator_input_green) "
          "dp(hold,{C(nil,'>',0)},{{signal=EACH,copy_count_from_input=false,constant=HOLD}}) wire(hold,W.combinator_input_green,sel,W.combinator_output_green) wire(hold,W.combinator_output_green,sel,W.combinator_input_green) "
          "if xp then dp(xp,{C(nil,'>',0)},{{signal=EACH,copy_count_from_input=false,constant=-SPREAD}}) wire(xp,W.combinator_input_red,sel1,W.combinator_output_red) "
          "if k==2 then wire(xp,W.combinator_input_green,psel,W.combinator_output_green) end wire(xp,W.combinator_output_green,sel,W.combinator_input_green) o[#o+1]='spread m'..(k+1) end "
          "if k==0 then sel1=sel end psel=sel "
          "prev=rq end o[#o+1]='3 machines wired' rcon.print(table.concat(o,', '))")

# Doctrine (the Captain, 2026-11-14): the Replicator grid serves building items and special orders; goods with a continuous need run on
# dedicated lines and stay OFF the menus. Each item here had its own line on Nauvis when listed (lines/stock/made checked 2026-11-14).
# Occasional ammunition with no line (cannon/artillery/shotgun shells, atomic bomb) and landfill stay on the menu as special orders.
CONSUMABLES = ["advanced-circuit", "electronic-circuit", "copper-cable", "iron-gear-wheel", "iron-stick", "engine-unit", "flying-robot-frame",
               "low-density-structure", "barrel", "explosive-rocket", "firearm-magazine", "piercing-rounds-magazine", "rocket",
               "uranium-rounds-magazine", "uranium-fuel-cell", "repair-pack", "space-platform-foundation"]
EXT = "{" + ",".join("['%s']=true" % c for c in CONSUMABLES) + "}"

# The list refresh, generalised: surface conditions of the cell's surface, an optional menu, and the partition p of n.
LIST = ("local s=game.surfaces['SURF'] local f=game.forces.player local cats=prototypes.entity['assembling-machine-3'].crafting_categories local MENU=MENUT local EX=" + EXT + " local seen,list={},{} "
        "for name,r in pairs(f.recipes) do local p=r.prototype local okc=false for _,c in pairs(p.categories) do if cats[c] then okc=true end end "
        "local surf=true for _,c in pairs(p.surface_conditions or {}) do local v=s.get_property(c.property) if (c.min and v<c.min) or (c.max and v>c.max) then surf=false end end "
        "if r.enabled and okc and surf and not p.hidden and #r.products==1 and r.products[1].type=='item' and not name:find('science%-pack') and not name:find('recycling') then "
        "local solid=true for _,i in pairs(r.ingredients) do if i.type~='item' then solid=false end end local it=r.products[1].name "
        "if solid and not EX[it] and (not MENU or MENU[it]) then if seen[it] then seen[it]=2 else seen[it]=1 list[#list+1]=it end end end end local mk={} for _,it in pairs(list) do if seen[it]==1 then mk[#mk+1]=it end end table.sort(mk) ")
REFRESH = (LIST + "local function at(x,y) return s.find_entities_filtered{name='constant-combinator',position={x,y},radius=0.4}[1] end local rank,ring=at(RKX,RKY),at(RGX,RGY) "
           "if not (rank and ring) then rcon.print('missing constant combinators') return end local N,P=NN,PP local want,nw={},0 for i,it in ipairs(mk) do if (i-1)%N==P then want[it]=i nw=nw+1 end end "
           "local cur,nc={},0 for _,sec in pairs(rank.get_or_create_control_behavior().sections) do for _,fl in pairs(sec.filters) do if fl.value then cur[fl.value.name]=fl.min nc=nc+1 end end end "
           "local nr=0 for _,sec in pairs(ring.get_or_create_control_behavior().sections) do nr=nr+#sec.filters end "
           "local same=(nc==nw and nr==#mk) if same then for it,i in pairs(want) do if cur[it]~=i then same=false end end end if same then rcon.print('unchanged '..nw..' of '..#mk) return end "
           "local add,rem={},{} for it in pairs(want) do if not cur[it] then add[#add+1]=it end end for it in pairs(cur) do if not want[it] then rem[#rem+1]=it end end "
           "local cb=rank.get_or_create_control_behavior() while cb.sections_count>0 do cb.remove_section(1) end local sec=cb.add_section() local j=0 for i,it in ipairs(mk) do if want[it] then j=j+1 sec.set_slot(j,{value={type='item',name=it,quality='normal'},min=i}) end end "
           "cb=ring.get_or_create_control_behavior() while cb.sections_count>0 do cb.remove_section(1) end sec=cb.add_section() for i,it in ipairs(mk) do sec.set_slot(i,{value={type='recipe',name=it,quality='normal'},min=i}) end "
           "table.sort(add) table.sort(rem) rcon.print('changed: '..nw..' of '..#mk..' items; added '..table.concat(add,',')..' ; removed '..table.concat(rem,','))")


def refresh_one(c):
    (rkx, rky), (rgx, rgy) = (c["rank"], c["ring"]) if "rank" in c else rank_ring(c)
    menu = c.get("menu")
    code = (REFRESH.replace("SURF", c.get("surface", "nauvis")).replace("MENUT", "{" + ",".join("[%r]=true" % m for m in menu) + "}" if menu else "nil")
            .replace("RKX", str(rkx)).replace("RKY", str(rky)).replace("RGX", str(rgx)).replace("RGY", str(rgy)).replace("NN", str(c.get("n", 1))).replace("PP", str(c.get("p", 0))))
    return tools["run_lua"](code).strip()


def refresh_all():
    """Every registered list (the autopilot calls this). Returns {name: result}."""
    return {name: refresh_one(c) for name, c in reg().items()}


def standing(c):
    # the rank list marks a standing cell: a cell that reads a shared hub (--demand) may have had its own roboport removed (2026-11-16, overlap thinning)
    r = tools["run_lua"]("rcon.print(#game.surfaces['%s'].find_entities_filtered{name='constant-combinator',position={%s,%s},radius=0.4})" % (c.get("surface", "nauvis"), c["x"] + 8.5, c["y"] + 2.5))
    return r.strip() != "0"


def config(c):
    code = (CONFIG.replace("SURF", c.get("surface", "nauvis")).replace("CX", str(c["x"])).replace("CY", str(c["y"])).replace("SIL", "true" if c.get("silos") else "false")
            .replace("BATCH", str(BATCH)).replace("HOLD", str(HOLD)).replace("SPREAD", str(SPREAD))
            .replace("DEMT", "{%s,%s}" % tuple(c["demand"]) if c.get("demand") else "nil"))
    placed = json.loads(tools["place_entities"](json.dumps(spread_entities(c)), surface=c.get("surface", "nauvis"), dry_run=False)).get("placed") or 0      # a cell built before 2026-11-16 lacks them
    return ("spread deciders placed %d, " % placed if placed else "") + tools["run_lua"](code)


PROBE = ("local s=game.surfaces['SURF'] local W=defines.wire_connector_id local o={} for k=0,2 do local sel=s.find_entities_filtered{name='selector-combinator',position={CX+7*k+4.5,CY+5},radius=0.4}[1] "
         "local am=s.find_entities_filtered{name='assembling-machine-3',position={CX+7*k+1.5,CY+7.5},radius=0.4}[1] local n=sel.get_circuit_network(W.combinator_output_green) "
         "local r=am.get_recipe() o[#o+1]=((n and n.signals and n.signals[1]) and n.signals[1].signal.name or '-')..'/'..(r and r.name or 'none')..'/'..am.products_finished end rcon.print(game.tick..' '..table.concat(o,' '))")


def probe(c, n=12):
    code = PROBE.replace("SURF", c.get("surface", "nauvis")).replace("CX", str(c["x"])).replace("CY", str(c["y"]))
    rows = [tools["run_lua"](code).split() for _ in range(n)]
    out = []
    for k in range(3):
        seq = [r[1 + k].split("/") for r in rows]
        out.append({"changes": sum(1 for a, b in zip(seq, seq[1:]) if a[0] != b[0]), "chosen": seq[-1][0], "recipe": seq[-1][1], "made": int(seq[-1][2])})
    return out


def main():
    a = sys.argv[1:]
    step = a[0] if a else ""
    r = reg()
    if step == "plan":
        name, x, y = a[1], int(a[2]), int(a[3])
        part = a[a.index("--part") + 1] if "--part" in a else "0/1"
        c = {"x": x, "y": y, "surface": a[a.index("--surface") + 1] if "--surface" in a else "nauvis", "silos": "--silos" in a,
             "demand": [float(a[a.index("--demand") + 1]), float(a[a.index("--demand") + 2])] if "--demand" in a else None,
             "p": int(part.split("/")[0]), "n": int(part.split("/")[1])}
        if name in r and standing(r[name]):
            sys.exit("cell %s already stands; registry kept" % name)
        r[name] = c
        save_reg(r)
        res = json.loads(tools["place_entities"](json.dumps(layout(c)), surface=c["surface"], dry_run=True))
        print("cell %s at (%d,%d) %s: footprint %d x %d tiles, %d entities; dry run placed %s, failed %s" % (
            name, x, y, c["surface"], W_, H_, len(layout(c)), res.get("placed"), json.dumps(res.get("failed") or [])[:300]))
    elif step == "build":
        c = r[a[1]]
        apply = "--apply" in a
        if apply and standing(c):
            sys.exit("cell already built: never apply twice (use config)")
        if apply:
            print("save:", tools["save_game"]("skippy"))
        res = json.loads(tools["place_entities"](json.dumps(layout(c)), surface=c["surface"], dry_run=not apply, clear_trees=apply))
        print("placed" if apply else "dry run", res.get("placed"), "failed", json.dumps(res.get("failed") or [])[:300])
        if apply and not res.get("failed"):
            time.sleep(1)
            print(config(c))
            print("refresh:", refresh_one(c))
    elif step == "config":
        print(config(r[a[1]]))
        print("refresh:", refresh_one(r[a[1]]))
    elif step == "refresh":
        for name, c in r.items():
            if len(a) < 2 or a[1] == name:
                print(name, refresh_one(c))
    elif step in ("status", "verify"):
        c = r[a[1]]
        for k, m in enumerate(probe(c, 12 if step == "status" else 30)):
            print("machine %d: chosen %s, recipe %s, made %d, choice changes %d" % (k + 1, m["chosen"], m["recipe"], m["made"], m["changes"]))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
