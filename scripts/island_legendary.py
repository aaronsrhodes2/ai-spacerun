#!/usr/bin/env python3
"""Fulgora home island: scrap -> legendary goods by vanilla upcycling (2026-11-20, the Captain: "work on creating the quality sub-products in Fulgora's legendary island").
Design: docs/fulgora-legendary-workshop.md stage S3. Four nodes in a row at the free strip x 24..35, y -124..-116 (island robot network 4669):
  N1, N2  R1 nodes: requester chest (scrap) -> inserter -> recycler with 4 quality module 3 -> inserter -> passive provider chest
  N3, N4  R2 nodes: the same, but the requester chest asks every NON-legendary tier of the recyclable intermediates
          (processing unit, advanced circuit, low density structure, battery, electronic circuit, gear, cable), so what scrap gave comes round again until it is legendary
  export  a requester chest (30.5,-109.5) that asks for the LEGENDARY tier of everything the chain makes; this is the island's order shelf
Scrap comes from two of the island's drill chests turned into passive provider chests (fast replace, same legendary 120 slots, drills and the train inserters keep working).
Junk (stone, ice, solid fuel, concrete, holmium ore, non-legendary plates and steel) piles up in the provider chests and would stop the recyclers: `trim` voids it (reported).
Steps: build [--apply] | swap [--apply] | modules [--apply] | config | trim [--apply] | status"""
import sys

from _game import tools

NODES = [(24, "r1"), (27, "r1"), (30, "r2"), (33, "r2")]
EXPORT = (30.5, -109.5)
SUBS = [(36, -120), (22, -117)]
SWAP = [(34.5, -102.5), (26.5, -102.5)]
RECYCLABLE = ["processing-unit", "advanced-circuit", "low-density-structure", "accumulator", "electronic-circuit", "iron-gear-wheel", "copper-cable"]
LEGENDARY = RECYCLABLE + ["battery", "iron-plate", "copper-plate", "steel-plate", "plastic-bar", "holmium-plate"]
TIERS = ["normal", "uncommon", "rare", "epic"]
S = "local s=game.surfaces.fulgora local f=game.forces.player "


def spots(c):
    return [("requester-chest", c + 0.5, -123.5), ("fast-inserter", c + 0.5, -122.5), ("recycler", c + 1, -120), ("fast-inserter", c + 0.5, -117.5), ("passive-provider-chest", c + 0.5, -116.5)]


def lua_list(rows):
    return "{" + ",".join("{'%s',%s,%s}" % r for r in rows) + "}"


def build(apply):
    rows = [r for c, _ in NODES for r in spots(c)] + [("requester-chest",) + EXPORT] + [("substation", x, y) for x, y in SUBS]
    code = S + ("local L=%s local o={} local bad=0 for _,t in ipairs(L) do local ok=s.can_place_entity{name=t[1],position={t[2],t[3]},force=f,direction=defines.direction.north} if not ok and not s.find_entities_filtered{name=t[1],position={t[2],t[3]},radius=0.3}[1] then bad=bad+1 o[#o+1]='BLOCKED '..t[1]..' '..t[2]..','..t[3] end end "
                "if bad>0 then rcon.print(table.concat(o,' ; ')) return end "
                "if %s then for _,t in ipairs(L) do if not s.find_entities_filtered{name=t[1],position={t[2],t[3]},radius=0.3}[1] then local d=defines.direction.north local e=s.create_entity{name=t[1],position={t[2],t[3]},direction=d,force=f,raise_built=true} o[#o+1]=t[1]..(e and ' ok' or ' FAILED') end end end rcon.print(#L..' entities, '..bad..' blocked, '..#o..' made') ") % (
        lua_list(rows), "true" if apply else "false")
    print(tools["run_lua"](code).replace(" ; ", "\n"))


def config():
    def fill(pos, items):
        its = ",".join("{'%s','%s',%d}" % i for i in items)
        return ("do local c=s.find_entities_filtered{name='requester-chest',position={%s,%s},radius=0.4}[1] if c then for _,pt in pairs(c.get_logistic_point()) do local sec=pt.sections[1] or pt.add_section() local i=0 "
                "for _,q in ipairs({%s}) do i=i+1 sec.set_slot(i,{value={type='item',name=q[1],quality=q[2]},min=q[3]}) end break end end end ") % (pos[0], pos[1], its)
    code = S
    for c, kind in NODES:
        pos = (c + 0.5, -123.5)
        if kind == "r1":
            code += fill(pos, [("scrap", "normal", 1500)])
        else:
            code += fill(pos, [(it, q, 50) for it in RECYCLABLE for q in TIERS])
    code += fill(EXPORT, [(it, "legendary", 200) for it in LEGENDARY])
    code += "rcon.print('requests set')"
    print(tools["run_lua"](code))


def swap(apply):
    code = S + ("local o={} for _,p in ipairs({%s}) do local c=s.find_entities_filtered{name='steel-chest',position=p,radius=0.4}[1] if c then local n=c.get_inventory(defines.inventory.chest).get_item_count('scrap') "
                "if %s then local e=s.create_entity{name='passive-provider-chest',position=c.position,force=f,quality=c.quality.name,fast_replace=true,player=nil,spill=false,raise_built=true} "
                "o[#o+1]=p[1]..','..p[2]..' replaced '..tostring(e~=nil)..' scrap before '..n..' after '..(e and e.get_inventory(defines.inventory.chest).get_item_count('scrap') or -1) else o[#o+1]=p[1]..','..p[2]..' scrap '..n end "
                "else o[#o+1]=p[1]..','..p[2]..' already done or missing' end end rcon.print(table.concat(o,' ; '))") % (
        ",".join("{%s,%s}" % p for p in SWAP), "true" if apply else "false")
    print(tools["run_lua"](code).replace(" ; ", "\n"))


def modules(apply):
    code = S + ("local o={} local src=nil for _,c in pairs(s.find_entities_filtered{type='logistic-container',area={{100,-70},{150,-20}}}) do local n=c.get_inventory(defines.inventory.chest).get_item_count('quality-module-3') if n>=16 then src=c break end end "
                "if not src then rcon.print('no source chest with 16 quality module 3') return end local srcinv=src.get_inventory(defines.inventory.chest) o[#o+1]='source '..src.position.x..','..src.position.y..' has '..srcinv.get_item_count('quality-module-3') "
                "local done=0 for _,r in pairs(s.find_entities_filtered{name='recycler',area={{20,-125},{40,-114}}}) do local mi=r.get_module_inventory() local have=mi.get_item_count('quality-module-3') if have<4 then "
                "if %s then local took=srcinv.remove{name='quality-module-3',count=4-have} local put=mi.insert{name='quality-module-3',count=took} if put<took then srcinv.insert{name='quality-module-3',count=took-put} end done=done+put else done=done+(4-have) end end end "
                "rcon.print(table.concat(o,' ; ')..' ; modules '..(%s and 'moved ' or 'would move ')..done)") % ("true" if apply else "false", "true" if apply else "false")
    print(tools["run_lua"](code).replace(" ; ", "\n"))


KEEP = RECYCLABLE + ["scrap", "battery", "iron-plate"]


def trim(apply):
    keep = ",".join("['%s']=true" % k for k in KEEP)
    code = S + ("local KEEP={%s} local o={} local tot=0 for _,c in pairs(s.find_entities_filtered{name='passive-provider-chest',area={{20,-120},{40,-114}}}) do local inv=c.get_inventory(defines.inventory.chest) "
                "for _,it in pairs(inv.get_contents()) do local junk=(it.quality~='legendary' and not KEEP[it.name]) if junk and it.count>200 then "
                "local rm=it.count-200 if %s then rm=inv.remove{name=it.name,quality=it.quality,count=rm} end tot=tot+rm o[#o+1]=it.name..' '..it.quality..' '..rm end end end rcon.print((%s and 'voided ' or 'would void ')..tot..' : '..table.concat(o,', '))") % (
        keep, "true" if apply else "false", "true" if apply else "false")
    return tools["run_lua"](code).strip()


def cycle():
    """Autopilot hook: void the junk in the node provider chests so the scrap recyclers never stall on a full chest."""
    return trim(True)[:200]


STATUS = S + ("local o={} local nm={} for k,v in pairs(defines.entity_status) do nm[v]=k end for _,r in pairs(s.find_entities_filtered{name='recycler',area={{20,-125},{40,-114}}}) do o[#o+1]='recycler '..r.position.x..' '..nm[r.status]..' qm3 '..r.get_module_inventory().get_item_count('quality-module-3')..' made '..r.products_finished end "
              "local leg={} for _,c in pairs(s.find_entities_filtered{name='passive-provider-chest',area={{20,-120},{40,-114}}}) do for _,it in pairs(c.get_inventory(defines.inventory.chest).get_contents()) do if it.quality~='normal' then local k=it.name..' '..it.quality leg[k]=(leg[k] or 0)+it.count end end end "
              "local t={} for k,v in pairs(leg) do t[#t+1]=k..'='..v end table.sort(t) o[#o+1]='bumped items in provider chests: '..table.concat(t,', ') "
              "local ex=s.find_entities_filtered{name='requester-chest',position={%s,%s},radius=0.4}[1] if ex then local e={} for _,it in pairs(ex.get_inventory(defines.inventory.chest).get_contents()) do e[#e+1]=it.name..' '..it.quality..'='..it.count end o[#o+1]='export shelf: '..table.concat(e,', ') end "
              "rcon.print(table.concat(o,' ; '))") % EXPORT

if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    ap = "--apply" in sys.argv
    if step == "build":
        build(ap)
    elif step == "swap":
        swap(ap)
    elif step == "modules":
        modules(ap)
    elif step == "config":
        config()
    elif step == "trim":
        print(trim(ap))
    else:
        print(tools["run_lua"](STATUS).replace(" ; ", "\n"))
