#!/usr/bin/env python3
"""Low density structure from the Vulcanus Wheel to the planets (the Captain, 2026-11-14: "make the Vulcanus Wheel's LDS stock available
for pickup in the logistics network").

Design (nothing but request sections, no circuits, no change to the wheel):
  wheel   Vulcanus Wheel hub has providing_to_other_platforms = true and holds the stock (cap 4,000, wheel_export_vulcanus.py). It
          is left exactly as it is.
  ship    each Nauvis-Vulcanus N Shuttle gets ONE more request section, group 'lds-<platform index>':
              low-density-structure  min = max = AMOUNT   request_from = 'platforms'   import_from = 'vulcanus'
          `import_from` makes a request live only while the ship orbits THAT planet (the same way the ships' express-belt requests
          are import_from nauvis and only fill at Nauvis). At Vulcanus the ship pulls AMOUNT from the wheel, in orbit, without
          touching the ground. At Nauvis the request is dormant, so the LDS is an unrequested item and the hub drops it to the
          Nauvis landing pad by cargo pod within about 30 s, into the network. The ships' old rule (they carry metallurgic packs
          from Vulcanus to Nauvis the same way) is unchanged.
  no trash: min = max, and the only way LDS gets aboard is this request, so the stock never exceeds max (hub_trash stays empty).
Fulgora and Aquilo follow from the Nauvis network (see the end of the docstring of the `report` text in `status`): Nauvis-Fulgora ships
add LDS with import_from nauvis, Fulgora-Aquilo 4 Shuttle adds LDS with import_from fulgora. Not done here (other agents' ships).
The ships' hubs have 97 slots; LDS stacks 10, so AMOUNT 200 = 20 slots. Free slots at the start: V1 42, V2 24, V3 58.
Steps: status | apply [--amount N] | off | test3 (one ship, 500, for the proof)   Usage: lds_pickup.py apply"""
import sys

from _game import tools

GROUP = "lds"
ITEM = "low-density-structure"
SHIPS = {"Nauvis-Vulcanus 1 Shuttle": 200, "Nauvis-Vulcanus 2 Shuttle": 200, "Nauvis-Vulcanus 3 Shuttle": 200}
WHEEL = "Vulcanus Wheel"

LUA = ("local function plat(n) for _,p in pairs(game.forces.player.platforms) do if p.name:find(n,1,true) then return p end end end "
       "local function sec(p) local pt for _,q in pairs(p.hub.get_logistic_point()) do if q.mode==defines.logistic_mode.requester then pt=q end end for i,s in pairs(pt.sections) do if s.group==('%(g)s-'..p.index) then return pt,s,i end end return pt,nil,nil end "
       "local function put(p,amt) local pt,s,i=sec(p) if s then pt.remove_section(i) end if not amt then return 'removed' end s=pt.add_section('%(g)s-'..p.index) "
       "s.set_slot(1,{value={type='item',name='%(item)s',quality='normal'},min=amt,max=amt,import_from='vulcanus',request_from='platforms'}) "
       "local _,s2=sec(p) local f=s2.filters[1] return 'set '..f.value.name..' '..f.min..'/'..f.max..' from '..tostring(f.request_from)..' import_from '..tostring(f.import_from and f.import_from.name or f.import_from) end "
       "local o={} %(body)s rcon.print(table.concat(o,' ;; '))")

STATUS = ("local w=plat('%s') w.hub.providing_to_other_platforms=true local wi=w.hub.get_inventory(defines.inventory.hub_main) "
          "o[#o+1]='wheel @'..w.space_location.name..' provides '..tostring(w.hub.providing_to_other_platforms)..' LDS '..wi.get_item_count('%s')..' trash '..#w.hub.get_inventory(defines.inventory.hub_trash).get_contents() "
          % (WHEEL, ITEM))


def run(body):
    out = tools["run_lua"](LUA % {"g": GROUP, "item": ITEM, "body": body})
    return out.replace(" ;; ", "\n")


def apply(amounts):
    body = ""
    for ship, amt in amounts.items():
        body += "do local p=plat('%s') o[#o+1]=p.name:sub(-22)..': '..put(p,%s) end " % (ship, amt if amt else "nil")
    print(run(body))


def status():
    body = STATUS
    for ship in SHIPS:
        body += ("do local p=plat('%s') local pt,s=sec(p) local inv=p.hub.get_inventory(defines.inventory.hub_main) local tr=p.hub.get_inventory(defines.inventory.hub_trash) "
                 "o[#o+1]=p.name:sub(-22)..' @'..tostring(p.space_location and p.space_location.name)..' state '..p.state..' section '..(s and (s.filters[1].min..'/'..s.filters[1].max) or 'none')..' | LDS aboard '..inv.get_item_count('%s')..' | free slots '..inv.count_empty_stacks()..' | trash '..#tr.get_contents() end "
                 % (ship, ITEM))
    body += ("local net=game.forces.player.logistic_networks.nauvis local bn=0 local bc=0 for _,n in pairs(net or {}) do local c=n.get_item_count('%s') if c>bc then bc=c end end "
             "o[#o+1]='Nauvis network LDS (best network) '..bc" % ITEM)
    print(run(body))


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    if step == "apply":
        amt = int(sys.argv[sys.argv.index("--amount") + 1]) if "--amount" in sys.argv else None
        apply({s: (amt or a) for s, a in SHIPS.items()})
    elif step == "test3":
        apply({"Nauvis-Vulcanus 3 Shuttle": 500})
    elif step == "off":
        apply({s: None for s in SHIPS})
    status()
