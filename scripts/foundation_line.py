#!/usr/bin/env python3
"""Foundation line (the Captain, 2026-11-20: "Yes, foundation line"; Fulgora waits for 3,892 foundation and nothing made it).
Foundation = 20 stone + 4 tungsten plate + 4 carbon fiber + 4 lithium plate + 20 COLD fluoroketone: four planets' goods. The maker
exists: the Nauvis Replicator's barrel-fed assembler unit lists foundation (omni_fluid_asm.py list) and makes it when a ship in orbit
asks Nauvis for it. What was missing is the supply into Nauvis, written by ghost_carriers.py:
  tungsten plate   Vulcanus -> Nauvis, the Nauvis-Vulcanus shuttles
  carbon fiber     Gleba -> Nauvis, the Nauvis-Gleba shuttles
  lithium plate, hot fluoroketone barrels   Aquilo -> Gleba (Gleba-Aquilo 1, Gleba pad as the relay) -> Nauvis (Nauvis-Gleba shuttles)
  foundation       Nauvis -> Fulgora, the Nauvis-Fulgora shuttles (50 a rocket)
and ONE new machine group, this script: the COOLER. Aquilo barrels only hot fluoroketone (the cold kind exists only inside its cryo
loop), so on Nauvis an emptier takes hot barrels, a cryogenic plant cools the fluid, a filler barrels it cold:
  filler F (assembler, facing south)   tiles (3..5, 1..3)    blue chest (1,2) empty barrels, red chest (7,2) COLD barrels
  cryogenic plant                      tiles (4..8, 4..8)    fluoroketone-cooling; its first input and output ports are its WEST column
  emptier E (assembler, facing south)  tiles (3..5, 9..11)   blue chest (1,10) hot barrels, red chest (7,10) empty barrels
The machines touch port to port (positions read from the prototypes): no pipes.
Steps: plan | build [--apply] | status      Usage: foundation_line.py build --apply ; foundation_line.py status"""
import json
import sys

from _game import tools

L = tools["run_lua"]
BX, BY = -383, -230
Q = {"quality": "legendary"}


def at(tx, ty, w=1):
    return BX + tx + w / 2, BY + ty + w / 2


def ents():
    e = []

    def add(name, tx, ty, w=1, d=0, **kw):
        x, y = at(tx, ty, w)
        r = {"name": name, "x": x, "y": y, "direction": d, "params": dict(Q)}
        r.update(kw)
        e.append(r)

    add("substation", 10, 6, 2)
    add("cryogenic-plant", 4, 4, 5, recipe="fluoroketone-cooling")
    add("assembling-machine-3", 3, 1, 3, d=8, recipe="fluoroketone-cold-barrel")
    add("assembling-machine-3", 3, 9, 3, d=8, recipe="empty-fluoroketone-hot-barrel")
    for ty in (2, 10):
        add("requester-chest", 1, ty)
        add("bulk-inserter", 2, ty, d=12)
        add("bulk-inserter", 6, ty, d=12)
        add("passive-provider-chest", 7, ty)
    return e


CONFIG = ("local s=game.surfaces.nauvis local function req(x,y,item,n) local ch=s.find_entities_filtered{name='requester-chest',position={x,y},radius=0.4}[1] local pt=ch.get_logistic_point(defines.logistic_member_index.logistic_container) "
          "for k=#pt.sections,1,-1 do pt.remove_section(k) end pt.add_section().set_slot(1,{value={type='item',name=item,quality='normal'},min=n}) end req(%s,%s,'barrel',20) req(%s,%s,'fluoroketone-hot-barrel',20) rcon.print('chests set')")

STATUS = ("local s=game.surfaces.nauvis local f=game.forces.player local m={} for k,v in pairs(defines.entity_status) do m[v]=k end local o={} "
          "for _,e in pairs(s.find_entities_filtered{area={{%d,%d},{%d,%d}},type='assembling-machine'}) do local r=e.get_recipe() local fl='' for i=1,e.fluids_count do local x=e.get_fluid(i) if x then fl=fl..' '..x.name..' '..math.floor(x.amount) end end "
          "o[#o+1]=e.name..' '..(r and r.name or 'no recipe')..' '..tostring(m[e.status])..' made '..e.products_finished..fl end local t={} for _,it in pairs{'fluoroketone-hot-barrel','fluoroketone-cold-barrel','barrel','tungsten-plate','carbon-fiber','lithium-plate','stone','foundation'} do local c=0 "
          "for _,nw in pairs(f.logistic_networks.nauvis or {}) do c=c+nw.get_item_count(it) end t[#t+1]=it..' '..c end o[#o+1]='nauvis stock: '..table.concat(t,', ') rcon.print(table.concat(o,string.char(10)))")


def main():
    a = sys.argv[1:]
    step = a[0] if a else "plan"
    apply = "--apply" in a
    if step in ("plan", "build"):
        r = tools["place_entities"](json.dumps(ents()), surface="nauvis", dry_run=not (apply and step == "build"))
        print(str(r)[:400])
        if apply and step == "build":
            f, e = at(1, 2), at(1, 10)
            print("   " + L(CONFIG % (f[0], f[1], e[0], e[1])).strip())
            # place_entities left both assemblers facing north: turn them (fluid ports must face the plant)
            print("   " + L("local s=game.surfaces.nauvis local n=0 for _,e in pairs(s.find_entities_filtered{area={{%d,%d},{%d,%d}},name='assembling-machine-3'}) do e.direction=defines.direction.south n=n+1 end rcon.print('turned south '..n)" % (BX, BY, BX + 13, BY + 13)).strip())
    elif step == "status":
        print(L(STATUS % (BX, BY, BX + 13, BY + 13)))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
