#!/usr/bin/env python3
"""Vulcanus big-mining-drill unit (2026-11-20, the Captain: Fulgora ghosts ask for big mining drills; recipe is METALLURGY with 200 molten iron, so no Replicator could make it).
Two foundries stacked 5 tiles apart, both facing north: the caster C (recipe iron-ore-melting: 50 iron ore + 1 calcite -> 500 molten iron) stands SOUTH of the maker P
(recipe big-mining-drill). C's output port (-1,-2) touches P's input port (-1,+2) directly, so the molten iron needs no pipe.
West of each foundry: inserter + requester chest (P: advanced circuit, electric engine unit, tungsten carbide, electric mining drill; C: iron ore, calcite).
East of P: inserter + passive provider chest (output bar 1 slot, so at most one stack of drills is ever made without an order). Robots carry the goods.
Electric engine units and electric mining drills are NOT made on Vulcanus: they must be carried in (Nauvis has them); until then P waits with its requests open.
Usage: big_drill_unit.py [find|build [--apply]|status]"""
import sys

from _game import tools

ROB = (95, -97)
BATCH = 5   # drills' worth of solids a request holds
PREQ = [("advanced-circuit", 10 * BATCH), ("electric-engine-unit", 10 * BATCH), ("tungsten-carbide", 20 * BATCH), ("electric-mining-drill", BATCH)]
CREQ = [("iron-ore", 100), ("calcite", 4)]

COMMON = ("local s=game.surfaces.vulcanus local f=game.forces.player "
          "local function spots(px,py) return {{'foundry',px,py},{'foundry',px,py+5},{'requester-chest',px-4,py},{'fast-inserter',px-3,py},{'requester-chest',px-4,py+5},{'fast-inserter',px-3,py+5},"
          "{'fast-inserter',px+3,py},{'passive-provider-chest',px+4,py},{'substation',px+6,py+3}} end "
          "local function fits(px,py) for _,t in ipairs(spots(px,py)) do if not s.can_place_entity{name=t[1],position={t[2],t[3]},force=f} then return false end end return true end ")
FIND = COMMON + ("local best,bd=nil,1e9 for px=80.5,125.5 do for py=-125.5,-84.5 do local d=(px-%d)^2+(py-(%d))^2 if d<bd and fits(px,py) then best={px,py} bd=d end end end "
                 "rcon.print(best and (best[1]..','..best[2]..' dist '..math.sqrt(bd)) or 'none')") % ROB


def fill_code(chest, items):
    return ("local c=s.find_entities_filtered{name='requester-chest',position={%s},radius=0.4}[1] local sec=nil for _,pt in pairs(c.get_logistic_point()) do sec=pt.add_section() break end "
            "local i=0 for _,q in ipairs({%s}) do i=i+1 sec.set_slot(i,{value={type='item',name=q[1],quality='normal'},min=q[2]}) end ") % (
        chest, ",".join("{'%s',%d}" % kv for kv in items))


def build(px, py, apply):
    code = COMMON + ("local px,py=%s,%s local o={} if not fits(px,py) then rcon.print('does not fit') return end local APPLY=%s "
                     "for _,t in ipairs(spots(px,py)) do if APPLY then local d=defines.direction.north if t[1]=='fast-inserter' then d=defines.direction.west end "
                     "local e=s.create_entity{name=t[1],position={t[2],t[3]},direction=d,force=f,raise_built=true} o[#o+1]=t[1]..(e and ' ok' or ' FAILED') end end "
                     "if APPLY then local P=s.find_entities_filtered{name='foundry',position={px,py},radius=0.5}[1] local C=s.find_entities_filtered{name='foundry',position={px,py+5},radius=0.5}[1] "
                     "P.set_recipe('big-mining-drill') C.set_recipe('iron-ore-melting') "
                     "local out=s.find_entities_filtered{name='passive-provider-chest',position={px+4,py},radius=0.4}[1] out.get_inventory(defines.inventory.chest).set_bar(2) end rcon.print(#o..' made ; '..table.concat(o,','))") % (
        px, py, "true" if apply else "false")
    print(tools["run_lua"](code.replace("\n", " ")))
    if apply:
        c1 = COMMON + fill_code("%s,%s" % (px - 4, py), PREQ) + fill_code("%s,%s" % (px - 4, py + 5), CREQ) + "rcon.print('requests set')"
        print(tools["run_lua"](c1.replace("\n", " ")))


STATUS = COMMON + ("local o={} local nm={} for k,v in pairs(defines.entity_status) do nm[v]=k end for _,e in pairs(s.find_entities_filtered{name='foundry',area={{75,-130},{130,-80}}}) do local r=e.get_recipe() if r and (r.name=='big-mining-drill' or r.name=='iron-ore-melting') then "
                   "o[#o+1]=r.name..' '..e.position.x..','..e.position.y..' '..nm[e.status]..' made '..e.products_finished..' fluid '..serpent.line(e.get_fluid_contents()) end end rcon.print(table.concat(o,' ; '))")

if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    if step == "find":
        print(tools["run_lua"](FIND.replace("\n", " ")))
    elif step == "build":
        r = tools["run_lua"](FIND.replace("\n", " ")).strip()
        if r == "none":
            sys.exit("no clean site")
        x, y = r.split(" ")[0].split(",")
        print("site", x, y)
        build(float(x), float(y), "--apply" in sys.argv)
    else:
        print(tools["run_lua"](STATUS.replace("\n", " ")).replace(" ; ", "\n"))
