#!/usr/bin/env python3
"""Fulgora home island, stage S1: the accumulator loop (2026-11-20, docs/fulgora-legendary-workshop.md). Two assembling machine 3 with 4 quality module 3 each craft accumulators
(5 batteries + 2 iron plate) from batteries and plates of ANY tier; the product takes the ingredients' quality plus the module bump. Accumulators go to a provider chest; the R2 recycler nodes of
island_legendary.py ask for every non-legendary accumulator, recycle it (25% back, bumped) and the batteries/plates they return come round to these machines. Legendary accumulators go to the export shelf.
Batteries also arrive from the scrap recyclers; iron plate from the scrap chain too. Seed batteries are CARRIED by script from the main-land storage chests (a bounded one-off, not a train).
Layout (horizontal, y -108.5): requester chest -> inserter -> AM3 -> inserter -> passive provider chest, origins x 4.5 and 12.5. An inserter's `direction` is its PICKUP side (west = takes from the west).
Steps: build [--apply] | modules [--apply] | config | seed [--apply] | status"""
import sys

from _game import tools
from island_legendary import S, TIERS, lua_list

ORIGINS = [4.5, 12.5]
SEED_BATT = 2000


def spots(x):
    return [("requester-chest", x, -108.5), ("fast-inserter", x + 1, -108.5), ("assembling-machine-3", x + 3, -108.5), ("fast-inserter", x + 5, -108.5), ("passive-provider-chest", x + 6, -108.5)]


def build(apply):
    rows = [r for x in ORIGINS for r in spots(x)]
    code = S + ("local L=%s local o={} local bad=0 for _,t in ipairs(L) do local ok=s.can_place_entity{name=t[1],position={t[2],t[3]},force=f} if not ok and not s.find_entities_filtered{name=t[1],position={t[2],t[3]},radius=0.3}[1] then bad=bad+1 o[#o+1]='BLOCKED '..t[1]..' '..t[2] end end "
                "if bad>0 then rcon.print(table.concat(o,' ; ')) return end if %s then for _,t in ipairs(L) do if not s.find_entities_filtered{name=t[1],position={t[2],t[3]},radius=0.3}[1] then "
                "local d=defines.direction.north if t[1]=='fast-inserter' then d=defines.direction.west end local e=s.create_entity{name=t[1],position={t[2],t[3]},direction=d,force=f,raise_built=true} "
                "if e and t[1]=='assembling-machine-3' then e.set_recipe('accumulator') end o[#o+1]=t[1]..(e and ' ok' or ' FAILED') end end end rcon.print(#L..' spots, '..bad..' blocked, '..#o..' made') ") % (lua_list(rows), "true" if apply else "false")
    print(tools["run_lua"](code).replace(" ; ", "\n"))


def config():
    its = [("battery", q, 300 if q == "normal" else 150) for q in TIERS] + [("iron-plate", q, 100) for q in TIERS]
    sl = ",".join("{'%s','%s',%d}" % i for i in its)
    code = S
    for x in ORIGINS:
        code += ("do local c=s.find_entities_filtered{name='requester-chest',position={%s,-108.5},radius=0.4}[1] if c then for _,pt in pairs(c.get_logistic_point()) do local sec=pt.sections[1] or pt.add_section() local i=0 "
                 "for _,q in ipairs({%s}) do i=i+1 sec.set_slot(i,{value={type='item',name=q[1],quality=q[2]},min=q[3]}) end break end end end ") % (x, sl)
    print(tools["run_lua"](code + "rcon.print('requests set')"))


def modules(apply):
    code = S + ("local src=nil for _,c in pairs(s.find_entities_filtered{type='logistic-container',area={{100,-70},{150,-20}}}) do if c.get_inventory(defines.inventory.chest).get_item_count('quality-module-3')>=8 then src=c break end end "
                "if not src then rcon.print('no source') return end local si=src.get_inventory(defines.inventory.chest) local done=0 for _,r in pairs(s.find_entities_filtered{name='assembling-machine-3',area={{3,-111},{22,-106}}}) do local mi=r.get_module_inventory() local have=mi.get_item_count('quality-module-3') "
                "if have<4 then if %s then local took=si.remove{name='quality-module-3',count=4-have} local put=mi.insert{name='quality-module-3',count=took} if put<took then si.insert{name='quality-module-3',count=took-put} end done=done+put else done=done+4-have end end end "
                "rcon.print('modules '..(%s and 'moved ' or 'would move ')..done..' ; source left '..si.get_item_count('quality-module-3'))") % ("true" if apply else "false", "true" if apply else "false")
    print(tools["run_lua"](code))


def seed(apply):
    code = S + ("local want=%d local n=0 for _,c in pairs(s.find_entities_filtered{name='storage-chest',area={{100,-160},{230,-10}}}) do if n>=want then break end local inv=c.get_inventory(defines.inventory.chest) local have=inv.get_item_count('battery') if have>0 then "
                "local take=math.min(have,want-n) if %s then take=inv.remove{name='battery',count=take} end n=n+take end end local dst=s.find_entities_filtered{name='passive-provider-chest',position={%s,-108.5},radius=0.4}[1] "
                "if %s and dst then dst.get_inventory(defines.inventory.chest).insert{name='battery',count=n} end rcon.print((%s and 'carried ' or 'would carry ')..n..' batteries to the island provider chest')") % (
        SEED_BATT, "true" if apply else "false", ORIGINS[0] + 6, "true" if apply else "false", "true" if apply else "false")
    print(tools["run_lua"](code))


STATUS = S + ("local o={} local nm={} for k,v in pairs(defines.entity_status) do nm[v]=k end for _,r in pairs(s.find_entities_filtered{name='assembling-machine-3',area={{3,-111},{22,-106}}}) do local rc=r.get_recipe() o[#o+1]='am3 '..r.position.x..' '..nm[r.status]..' recipe '..tostring(rc and rc.name)..' qm3 '..r.get_module_inventory().get_item_count('quality-module-3')..' made '..r.products_finished end "
              "local t={} for _,c in pairs(s.find_entities_filtered{name='passive-provider-chest',area={{10,-110},{22,-107}}}) do for _,it in pairs(c.get_inventory(defines.inventory.chest).get_contents()) do t[#t+1]=it.name..' '..it.quality..'='..it.count end end o[#o+1]='accum provider chests: '..table.concat(t,', ') "
              "local ex=s.find_entities_filtered{name='requester-chest',position={30.5,-109.5},radius=0.4}[1] local e={} for _,it in pairs(ex.get_inventory(defines.inventory.chest).get_contents()) do e[#e+1]=it.name..' '..it.quality..'='..it.count end o[#o+1]='export shelf: '..table.concat(e,', ') rcon.print(table.concat(o,' ; '))")

if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    ap = "--apply" in sys.argv
    if step == "build":
        build(ap)
    elif step == "modules":
        modules(ap)
    elif step == "config":
        config()
    elif step == "seed":
        seed(ap)
    else:
        print(tools["run_lua"](STATUS).replace(" ; ", "\n"))
