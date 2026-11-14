#!/usr/bin/env python3
"""Nauvis (surface `nauvis`) belt and inserter upgrade. Re-runnable; dry run by default.

  upgrade_belts_nauvis.py                 dry run: counts, power decision, saturated-inserter candidates
  upgrade_belts_nauvis.py --apply         express belts/undergrounds/splitters -> turbo (whole surface, in 100x100 cells),
                                          then the saturated-inserter upgrades (see below)
  upgrade_belts_nauvis.py --apply-belts   belts only
  upgrade_belts_nauvis.py --apply-inserters   inserters only
  upgrade_belts_nauvis.py status          counts by name, no_power / low_power machines, plate rates

Belts, undergrounds and splitters draw no power: the whole surface goes turbo so no trunk is left with mixed speeds.
Undergrounds are replaced together with their partner (a turbo end does not connect to an express end).
Splitter filter and priorities are read back after replacement and re-applied if lost.

Inserters draw power, so only measured bottlenecks are upgraded: an inserter that was `working` in nearly every one of
SAMPLES status samples spread over SPAN_S seconds (it never waits, so it is the limit of its line). fast -> stack,
bulk -> stack. Filters, stack-size override, control behaviour and wires are read back on the new entity.
Power: Nauvis is one network; the decision is printed from the generators and accumulators (see power())."""
import sys
import time

from _game import tools

APPLY_B = "--apply" in sys.argv or "--apply-belts" in sys.argv
APPLY_I = "--apply" in sys.argv or "--apply-inserters" in sys.argv
STATUS = "status" in sys.argv
CELL = 100
SAMPLES = 8
SPAN_S = 24
HOT = 7  # working in at least this many of SAMPLES

NAMES = ["express-transport-belt", "express-underground-belt", "express-splitter"]


def lua(code):
    code = " ".join(code.split("\n"))
    return tools["run_lua"](code)


def counts():
    return lua(r"""local s=game.surfaces.nauvis local o={} for _,n in ipairs{'express-transport-belt','turbo-transport-belt','express-underground-belt','turbo-underground-belt','express-splitter','turbo-splitter','fast-inserter','bulk-inserter','stack-inserter'} do o[#o+1]=n..'='..s.count_entities_filtered{name=n} end rcon.print(table.concat(o,' '))""")


def power():
    return lua(r"""local s=game.surfaces.nauvis local g,n=0,0 for _,e in pairs(s.find_entities_filtered{type='generator'}) do n=n+1 g=g+e.energy_generated_last_tick end
local ch,cap=0,0 for _,a in pairs(s.find_entities_filtered{type='accumulator'}) do ch=ch+a.energy cap=cap+a.electric_buffer_size end
local E=defines.entity_status local low,nop=0,0 for _,e in pairs(s.find_entities_filtered{type={'assembling-machine','furnace','lab','inserter','mining-drill','chemical-plant','oil-refinery','roboport','beacon'}}) do if e.status==E.low_power then low=low+1 elseif e.status==E.no_power then nop=nop+1 end end
local cap_t=0 for _,e in pairs(s.find_entities_filtered{type='generator'}) do cap_t=cap_t+e.prototype.get_max_power_output(e.quality)*60 end
rcon.print('turbines '..n..' generating '..string.format('%.0f',g*60/1e6)..' MW of nameplate '..string.format('%.0f',cap_t/1e6)..' MW; accumulators '..string.format('%.1f',ch/1e9)..' of '..string.format('%.1f',cap/1e9)..' GJ; low_power '..low..' no_power '..nop)""")


def bounds():
    r = lua(r"""local s=game.surfaces.nauvis local x0,x1,y0,y1=1e9,-1e9,1e9,-1e9 for _,e in pairs(s.find_entities_filtered{name={'express-transport-belt','express-underground-belt','express-splitter','fast-inserter','bulk-inserter'}}) do local p=e.position if p.x<x0 then x0=p.x end if p.x>x1 then x1=p.x end if p.y<y0 then y0=p.y end if p.y>y1 then y1=p.y end end rcon.print(x0..' '..x1..' '..y0..' '..y1)""")
    return [float(v) for v in r.split()]


REPL_BELTS = r"""local s=game.surfaces.nauvis local A={{%f,%f},{%f,%f}} local n=0 local u=0 local sp=0 local bad=0
for _,e in ipairs(s.find_entities_filtered{area=A,name='express-transport-belt',limit=3000}) do local p=e.position if p.x>=%f and p.x<%f and p.y>=%f and p.y<%f then local r=s.create_entity{name='turbo-transport-belt',position=p,direction=e.direction,force=e.force,fast_replace=true,spill=false,quality=e.quality,raise_built=true} if r then n=n+1 else bad=bad+1 end end end
for _,e in ipairs(s.find_entities_filtered{area=A,name='express-underground-belt',limit=1500}) do if e.valid then local p=e.position if p.x>=%f and p.x<%f and p.y>=%f and p.y<%f then local nb=e.underground_belt_neighbour local np=nb and {position=nb.position,direction=nb.direction,type=nb.belt_to_ground_type,quality=nb.quality,force=nb.force} local r=s.create_entity{name='turbo-underground-belt',position=p,direction=e.direction,type=e.belt_to_ground_type,force=e.force,fast_replace=true,spill=false,quality=e.quality,raise_built=true} if r then u=u+1 else bad=bad+1 end
 if np then local nn=s.find_entities_filtered{position=np.position,name='express-underground-belt',limit=1}[1] if nn then local r2=s.create_entity{name='turbo-underground-belt',position=np.position,direction=np.direction,type=np.type,force=np.force,fast_replace=true,spill=false,quality=np.quality,raise_built=true} if r2 then u=u+1 else bad=bad+1 end end end end end end
for _,e in ipairs(s.find_entities_filtered{area=A,name='express-splitter',limit=500}) do local p=e.position if p.x>=%f and p.x<%f and p.y>=%f and p.y<%f then local f,ip,op=e.splitter_filter,e.splitter_input_priority,e.splitter_output_priority local r=s.create_entity{name='turbo-splitter',position=p,direction=e.direction,force=e.force,fast_replace=true,spill=false,quality=e.quality,raise_built=true} if r then sp=sp+1 if f and not r.splitter_filter then r.splitter_filter=f end if r.splitter_input_priority~=ip then r.splitter_input_priority=ip end if r.splitter_output_priority~=op then r.splitter_output_priority=op end else bad=bad+1 end end end
rcon.print(n..' '..u..' '..sp..' '..bad)"""


def cell_remaining(x0, y0):
    return int(lua(f"rcon.print(game.surfaces.nauvis.count_entities_filtered{{area={{{{{x0},{y0}}},{{{x0+CELL},{y0+CELL}}}}},name={{'express-transport-belt','express-underground-belt','express-splitter'}}}})"))


def upgrade_belts():
    x0, x1, y0, y1 = bounds()
    tot = [0, 0, 0, 0]
    cx = int(x0 // CELL) * CELL
    while cx <= x1:
        cy = int(y0 // CELL) * CELL
        while cy <= y1:
            if cell_remaining(cx, cy):
                for _ in range(4):  # a cell may exceed the per-call limit
                    r = lua(REPL_BELTS % ((cx - 1, cy - 1, cx + CELL + 1, cy + CELL + 1)
                                          + (cx, cx + CELL, cy, cy + CELL) * 3)).split()
                    r = [int(v) for v in r]
                    tot = [a + b for a, b in zip(tot, r)]
                    if sum(r[:3]) == 0:
                        break
                print(f"cell {cx},{cy} done; totals belts/ug/splitters/bad {tot}", flush=True)
            cy += CELL
        cx += CELL
    print("belts/undergrounds/splitters replaced, failures:", tot)


SAMPLE = r"""local s=game.surfaces.nauvis local t={} for _,e in ipairs(s.find_entities_filtered{name={'fast-inserter','bulk-inserter'}}) do t[#t+1]=(e.status==defines.entity_status.working) and 1 or 0 end rcon.print(table.concat(t))"""
LIST = r"""local s=game.surfaces.nauvis local t={} for _,e in ipairs(s.find_entities_filtered{name={'fast-inserter','bulk-inserter'}}) do t[#t+1]=e.position.x..','..e.position.y..','..e.name end rcon.print(table.concat(t,';'))"""


def hot_inserters():
    pos = lua(LIST).split(";")
    score = [0] * len(pos)
    for i in range(SAMPLES):
        s = lua(SAMPLE)
        if len(s) != len(pos):
            print("inserter list changed during sampling, aborting")
            sys.exit(1)
        for j, ch in enumerate(s):
            score[j] += int(ch)
        if i < SAMPLES - 1:
            time.sleep(SPAN_S / SAMPLES)
    return [p for p, sc in zip(pos, score) if sc >= HOT]


REPL_INS = r"""local s=game.surfaces.nauvis local ok,bad,out=0,0,{} for _,k in ipairs({%s}) do local x,y,nm=k[1],k[2],k[3] local e=s.find_entities_filtered{position={x,y},name=nm,limit=1}[1] if e then
 local uf=e.use_filters local fl={} if uf then for i=1,e.filter_slot_count do fl[i]=e.get_filter(i) end end local fm=e.inserter_filter_mode local ov=e.inserter_stack_size_override local cb=e.get_control_behavior() local hasW=false for _,c in pairs(e.get_wire_connectors(false)) do if c.connection_count>0 then hasW=true end end
 local en=e.inserter_stack_size_override local d=e.direction local pd,pu=e.drop_position,e.pickup_position
 local r=s.create_entity{name='stack-inserter',position=e.position,direction=d,force=e.force,fast_replace=true,spill=false,quality=e.quality,raise_built=true}
 if r then ok=ok+1 if uf then r.use_filters=true for i,f in pairs(fl) do r.set_filter(i,f) end end r.inserter_stack_size_override=ov
  local good=(r.direction==d) if hasW or cb or uf or ov>0 then out[#out+1]=x..','..y..' wired='..tostring(hasW)..' cb='..tostring(cb~=nil)..' filt='..tostring(r.use_filters)..' ov='..r.inserter_stack_size_override..' dir_ok='..tostring(good) end
 else bad=bad+1 end end end rcon.print(ok..' '..bad..' '..table.concat(out,' | '))"""


def upgrade_inserters(hot):
    ok = bad = 0
    for i in range(0, len(hot), 100):
        chunk = hot[i:i + 100]
        items = ",".join("{%s,%s,'%s'}" % tuple(p.split(",")) for p in chunk)
        r = lua(REPL_INS % items)
        a, b, rest = (r.split(" ", 2) + [""])[:3]
        ok += int(a)
        bad += int(b)
        if rest.strip():
            print("  special:", rest[:500])
    print("inserters -> stack:", ok, "failed:", bad)


def plates():
    return lua(r"""local f=game.forces.player local st=f.get_item_production_statistics(game.surfaces.nauvis) local P=defines.flow_precision_index.ten_minutes local o={} for _,n in ipairs{'iron-plate','copper-plate','steel-plate','plastic-bar','electronic-circuit'} do o[#o+1]=n..' made '..string.format('%.1f',st.get_flow_count{name=n,category='input',precision_index=P}/ 1)..'/min used '..string.format('%.1f',st.get_flow_count{name=n,category='output',precision_index=P})..'/min' end rcon.print(table.concat(o,'; '))""")


def furn():
    return lua(r"""local c={} for _,f in pairs(game.surfaces.nauvis.find_entities_filtered{type='furnace'}) do local k=tostring(f.status) c[k]=(c[k] or 0)+1 end local SN={} for k,v in pairs(defines.entity_status) do SN[v]=k end local o={} for k,v in pairs(c) do o[#o+1]=(SN[tonumber(k)] or k)..'='..v end rcon.print(table.concat(o,' '))""")


def main():
    print("power:", power())
    print("counts:", counts())
    if STATUS:
        print("furnaces:", furn())
        print("plates (10 min window):", plates())
        return
    if not (APPLY_B or APPLY_I):
        print("dry run. Would replace every express belt/underground/splitter with turbo (power-free).")
        hot = hot_inserters()
        print(f"saturated fast/bulk inserters (working in >= {HOT}/{SAMPLES} samples): {len(hot)}")
        return
    if APPLY_B:
        upgrade_belts()
        print("counts:", counts())
    if APPLY_I:
        hot = hot_inserters()
        print("saturated inserters:", len(hot))
        upgrade_inserters(hot)
        print("counts:", counts())
        print("power after:", power())


main()
