#!/usr/bin/env python3
"""Stock that travels without touching a planet's ground (the Captain, 2026-11-14: "a rich planet ships lots of goods up to space, then we move
those in space"). Factorio 2.1 lets a hub ask other platforms in the same orbit (`request_from='platforms'`) and a hub gives items away only when
`providing_to_other_platforms` is true. So:
  source wheel (Nauvis)  provides              the shuttle asks it for the packs the far wheel lacks (while both are in Nauvis orbit)
  shuttle                provides              flies; at the far planet the wheel asks the shuttle for the same packs
  far wheel              requests from platforms   (never from the planet: the pad is not involved)
The section carrying this on each hub is the one whose `group` is 'orbit-ferry <platform index>' (a group name is shared by every hub that uses it, so each hub needs its own); running again rewrites it (idempotent).
Tested 2026-11-14: Nauvis Wheel -> Nauvis-Gleba 1 Shuttle moved 21 production science packs in under a minute.
Steps: status | apply | off.   Usage: orbit_ferry.py apply"""
import sys

from _game import tools

GROUP = "orbit-ferry"
# (shuttle, far wheel, items {name: amount the far wheel keeps})
FERRIES = [
    ("Nauvis-Gleba 1 Shuttle", "Gleba Wheel", {"logistic-science-pack": 2000, "chemical-science-pack": 2000, "military-science-pack": 300, "production-science-pack": 80}),
    ("Nauvis-Fulgora 1 Shuttle", "Fulgora Wheel", {"military-science-pack": 300, "production-science-pack": 80}),
    ("Nauvis-Vulcanus 1 Shuttle", "Vulcanus Wheel", {"military-science-pack": 300, "production-science-pack": 80}),
]
SOURCE = "Nauvis Wheel"

LUA = ("local function plat(n) for _,p in pairs(game.forces.player.platforms) do if p.name:find(n,1,true) then return p end end end "
       "local function sec(p) local pt for _,q in pairs(p.hub.get_logistic_point()) do if q.mode==defines.logistic_mode.requester then pt=q end end for i,s in pairs(pt.sections) do if s.group==('%(g)s '..p.index) then return pt,s,i end end return pt,nil,nil end "
       "local function put(p,items,imp) local pt,s,i=sec(p) if s then pt.remove_section(i) end if not items then return 0 end s=pt.add_section('%(g)s '..p.index) local k=0 for n,c in pairs(items) do k=k+1 s.set_slot(k,{value={type='item',name=n,quality='normal'},min=c,max=c,import_from=imp,request_from='platforms'}) end return k end "
       "local o={} %(body)s rcon.print(table.concat(o,'\\n'))")


def run(body):
    return tools["run_lua"](LUA % {"g": GROUP, "body": body})


def lua_items(d):
    return "{" + ",".join("['%s']=%d" % (k, v) for k, v in d.items()) + "}"


def apply(on=True):
    body = "plat('%s').hub.providing_to_other_platforms=%s " % (SOURCE, "true" if on else "false")
    for ship, wheel, items in FERRIES:
        it = lua_items(items) if on else "nil"
        body += ("plat('%s').hub.providing_to_other_platforms=%s put(plat('%s'),%s,'nauvis') put(plat('%s'),%s,nil) o[#o+1]='%s -> %s: '..%s "
                 % (ship, "true" if on else "false", ship, it, wheel, it, ship, wheel, "'on'" if on else "'off'"))
    print(run(body))


def status():
    body = ""
    for ship, wheel, items in FERRIES:
        for p in (ship, wheel):
            body += ("do local p=plat('%s') local pt,s=sec(p) local t={} if s then for _,f in pairs(s.filters) do if f.value then t[#t+1]=f.value.name:gsub('%%-science%%-pack','')..' '..f.min end end end "
                     "local inv=p.hub.get_inventory(defines.inventory.hub_main) local h={} for _,n in pairs{'logistic-science-pack','chemical-science-pack','military-science-pack','production-science-pack'} do h[#h+1]=n:gsub('%%-science%%-pack','')..' '..inv.get_item_count(n) end "
                     "o[#o+1]='%s @'..tostring(p.space_location and p.space_location.name)..' provides '..tostring(p.hub.providing_to_other_platforms)..' | asks '..table.concat(t,', ')..' | holds '..table.concat(h,', ') end " % (p, p[-22:]))
    print(run(body))


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    if step == "apply":
        apply(True)
    elif step == "off":
        apply(False)
    status()
