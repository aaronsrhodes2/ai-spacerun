#!/usr/bin/env python3
"""Nauvis trains on nuclear fuel only.
Old refuelling inserters take coal or rocket fuel straight from a belt and drop it into locomotives. For each one listed:
  remove   the station already has a blue nuclear-fuel chest: just remove the old inserter
  convert  the station has none: put an inserter and a blue chest (nuclear fuel 10) on the opposite side of the track, then remove the old inserter
Usage: nauvis_train_fuel.py [--apply]"""
import json
import sys

from _game import tools

REMOVE = [(90.5, -147.5), (110.5, -147.5), (20.5, -155.5), (-240.5, -99.5), (-241.5, -72.5)]
CONVERT = [(24.5, 43.5), (24.5, -4.5), (-204.5, -282.5), (-204.5, -221.5)]

INFO = ("local s=game.surfaces.nauvis local i=s.find_entities_filtered{type='inserter',position={%s,%s},radius=0.3}[1] "
        "if not i then rcon.print('{}') else rcon.print(helpers.table_to_json({x=i.position.x,y=i.position.y,dx=i.drop_position.x-i.position.x,dy=i.drop_position.y-i.position.y})) end")
KILL = ("local f=game.forces.player local s=game.surfaces.nauvis local i=s.find_entities_filtered{type='inserter',position={%s,%s},radius=0.3}[1] "
        "if i then local h=i.held_stack if h.valid_for_read then local net=s.find_logistic_network_by_position({-40,42},f) net.insert({name=h.name,count=h.count,quality=h.quality}) h.clear() end i.destroy() rcon.print('old inserter removed') else rcon.print('no inserter there') end")
REQ = ("local s=game.surfaces.nauvis local c=s.find_entities_filtered{name='requester-chest',position={%s,%s},radius=0.3}[1] local ss=c.get_logistic_sections() "
       "local se=ss.sections[1] or ss.add_section() se.set_slot(1,{value={name='nuclear-fuel',quality='normal'},min=10}) rcon.print('chest in network '..tostring(c.logistic_network~=nil))")


def main():
    apply = "--apply" in sys.argv
    for x, y in REMOVE:
        print("remove", (x, y), tools["run_lua"](KILL % (x, y)) if apply else "(dry run)")
    for x, y in CONVERT:
        info = json.loads(tools["run_lua"](INFO % (x, y)))
        if not info:
            print("convert", (x, y), "no inserter")
            continue
        dx = 0 if abs(info["dx"]) < 0.5 else (1 if info["dx"] > 0 else -1)
        dy = 0 if abs(info["dy"]) < 0.5 else (1 if info["dy"] > 0 else -1)
        direction = {(0, -1): 0, (1, 0): 4, (0, 1): 8, (-1, 0): 12}[(dx, dy)]      # pickup side = away from the track
        ents = [{"name": "bulk-inserter", "x": x + 3 * dx, "y": y + 3 * dy, "direction": direction},
                {"name": "requester-chest", "x": x + 4 * dx, "y": y + 4 * dy}]
        r = json.loads(tools["place_entities"](json.dumps(ents), surface="nauvis", dry_run=not apply))
        print("convert", (x, y), "towards", (dx, dy), r)
        if apply and r["placed"] == 2:
            print("  ", tools["run_lua"](REQ % (x + 4 * dx, y + 4 * dy)), tools["run_lua"](KILL % (x, y)))


if __name__ == "__main__":
    main()
