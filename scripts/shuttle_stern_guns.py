#!/usr/bin/env python3
"""Old-hull shuttles: two stern guns, fed from the ship's own ammunition belt (the Captain, 2026-11-20: "protection, though not as much,
around the entire perimeter of all shuttles"; then "Shuttle sterns").

The old hull (13 ships) has 14 guns on the nose and the two sides down to row -2; the stern (tanks, thrusters, panels) lies out of
their reach (`perimeter_audit.py`: 111 of 544 entities, 98 of them at the stern). The ammunition belt runs north up tile column 12,
west along row -20 and south down column -13 to its dead end at (-13,-1).
  WEST  the dead end (-13,-1) is turned west; belt on row -1 to x -25, then south down the free edge column -26 to row 15;
        inserter (-25,15) feeds a gun on tiles x -24..-23, y 15..16. The belt's reserve now collects at the stern.
  EAST  the east column is the START of the belt, so a branch is taken off it by an inserter at (13,-1) (magazines only: the column
        also carries a few chunks), onto a belt on row -1 to x 24, south down the edge column 25 to row 15; inserter (24,15) feeds a
        gun on tiles x 22..23, y 15..16.
Everything is a placed entity (free, `place_entities`); quality follows the ship's guns. The filter is set by Lua right after placing
(place_entities sets no filters). A ship that does not match the hull (anchor belts missing, or a gun already at the stern) is skipped.
Steps: plan | build [--apply] [NAME PART ...] | status
Usage: shuttle_stern_guns.py plan ; shuttle_stern_guns.py build --apply "Nauvis-Fulgora 1" ; shuttle_stern_guns.py build --apply"""
import json
import sys

from _game import tools

L = tools["run_lua"]
MAGS = ("firearm-magazine", "piercing-rounds-magazine", "uranium-rounds-magazine")

SHIPS = ("local o={} for i,p in pairs(game.forces.player.platforms) do if p.surface and p.hub and p.hub.valid then local s=p.surface "
         "local function b(x,y,d) local e=s.find_entities_filtered{type='transport-belt',position={x,y},radius=0.3}[1] return e and e.direction==d end "
         "local g=s.find_entities_filtered{name='gun-turret'} local stern=0 for _,t in pairs(g) do if t.position.y>10 then stern=stern+1 end end "
         "local hull=(b(-12.5,-1.5,8) and b(12.5,-0.5,0) and (b(-12.5,-0.5,8) or b(-12.5,-0.5,12))) and true or false "
         "o[#o+1]={i=i,s=s.name,n=p.name:gsub('%[.-%]',''):gsub('^%s+',''),hull=hull,stern=stern,guns=#g,q=g[1] and g[1].quality.name or 'normal',at=p.space_location and p.space_location.name or 'in flight'} end end rcon.print(helpers.table_to_json(o))")

# after placing: turn the west dead end, set the branch inserter's filter
FINISH = ("local s=game.surfaces['%s'] local e=s.find_entities_filtered{type='transport-belt',position={-12.5,-0.5},radius=0.3}[1] if e then e.direction=defines.direction.west end "
          "local n=0 local i=s.find_entities_filtered{type='inserter',position={13.5,-0.5},radius=0.3}[1] if i then i.use_filters=true i.inserter_filter_mode='whitelist' "
          + "".join("i.set_filter(%d,'%s') " % (k + 1, m) for k, m in enumerate(MAGS)) +
          "n=1 end rcon.print('west end turned '..tostring(e~=nil)..', branch filter set '..n)")

STATUS = ("local s=game.surfaces['%s'] local o={} for _,t in pairs(s.find_entities_filtered{name='gun-turret'}) do if t.position.y>10 then o[#o+1]=t.position.x..','..t.position.y..'='..t.get_inventory(defines.inventory.turret_ammo).get_item_count() end end "
          "local b=0 for _,e in pairs(s.find_entities_filtered{type='transport-belt'}) do if e.position.y>-1 and math.abs(e.position.x)>24 then for l=1,2 do b=b+e.get_transport_line(l).get_item_count() end end end "
          "local em=0 for _,t in pairs(s.find_entities_filtered{name='gun-turret'}) do if t.get_inventory(defines.inventory.turret_ammo).is_empty() then em=em+1 end end rcon.print('stern guns '..(#o>0 and table.concat(o,' ') or 'none')..' | on the stern belts '..b..' | empty guns '..em)")


def ents(q):
    P = {"quality": q}
    out = []

    def add(name, tx, ty, d, w=1):
        out.append({"name": name, "x": tx + w / 2, "y": ty + w / 2, "direction": d, "params": dict(P)})

    # west: row -1 from x -14 to -25 (west), corner and edge column -26 down to row 15 (south)
    for x in range(-14, -26, -1):
        add("express-transport-belt", x, -1, 12)
    for y in range(-1, 16):
        add("express-transport-belt", -26, y, 8)
    add("fast-inserter", -25, 15, 12)          # direction = pick-up side: takes from the belt west of it
    add("gun-turret", -24, 15, 8, 2)
    # east: branch belt from x 14 to 24 (east), corner and edge column 25 down to row 15
    for x in range(14, 25):
        add("express-transport-belt", x, -1, 4)
    for y in range(-1, 16):
        add("express-transport-belt", 25, y, 8)
    add("fast-inserter", 24, 15, 4)
    add("gun-turret", 22, 15, 8, 2)
    add("fast-inserter", 13, -1, 12)           # the branch: placed LAST, its filter follows in the next call
    return out


def main():
    a = sys.argv[1:]
    step = a[0] if a else "plan"
    apply = "--apply" in a
    want = [w.lower() for w in a[1:] if not w.startswith("--")]
    ships = json.loads(L(SHIPS))
    for sh in ships:
        if want and not any(w in sh["n"].lower() for w in want):
            continue
        if not sh["hull"]:
            if not want and step == "plan":
                print("%-30s not this hull: skipped" % sh["n"][:30])
            continue
        if step == "status":
            print("%-30s %-9s %s" % (sh["n"][:30], sh["at"], L(STATUS % sh["s"]).strip()))
            continue
        if sh["stern"]:
            print("%-30s has %d stern guns already" % (sh["n"][:30], sh["stern"]))
            continue
        e = ents(sh["q"])
        if step == "plan":
            r = tools["place_entities"](json.dumps(e), surface=sh["s"], dry_run=True)
            print("%-30s %-9s %d guns (%s): %s" % (sh["n"][:30], sh["at"], sh["guns"], sh["q"], str(r)[:160]))
        elif step == "build":
            chk = tools["place_entities"](json.dumps(e), surface=sh["s"], dry_run=True)
            if '"failed":{}' not in str(chk).replace(" ", ""):
                print("%-30s does not fit as a whole: skipped (%s)" % (sh["n"][:30], str(chk)[:120]))
                continue
            r = tools["place_entities"](json.dumps(e), surface=sh["s"], dry_run=not apply)
            print("%-30s %s" % (sh["n"][:30], str(r)[:200]))
            if apply:
                print("   " + L(FINISH % sh["s"]).strip())


if __name__ == "__main__":
    main()
