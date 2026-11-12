#!/usr/bin/env python3
"""Nauvis clean-up, stage 3 pilot: one foundry line in place of the 8 electric furnaces at the small iron site (-378,-357).
The ore belt (x -377.5, flowing north) now ends at y -351.5. An inserter feeds a melting foundry (-377.5,-355.5, iron-ore-melting, calcite from a
blue chest on its west side); one link pipe at (-378.5,-358.5) carries molten iron to a casting foundry (-377.5,-361.5, casting-iron); a long-handed
inserter puts the plates on the east plate belt (x -371.5), which still runs to the train station.
Usage: nauvis_foundry_pilot.py [--apply]"""
import json
import sys

from _game import tools

CLEAR = ("local f=game.forces.player local s=game.surfaces.nauvis local net=s.find_logistic_network_by_position({-40,42},f) local n,moved=0,0 "
         "local function stash(inv) if inv then for _,it in pairs(inv.get_contents()) do moved=moved+net.insert({name=it.name,count=it.count,quality=it.quality}) end inv.clear() end end "
         "for _,e in pairs(s.find_entities_filtered{force=f,area={{-383,-363},{-372,-351}},type={'furnace','inserter'}}) do "
         "if e.type=='furnace' then stash(e.get_inventory(defines.inventory.crafter_input)) stash(e.get_output_inventory()) stash(e.get_module_inventory()) "
         "else local h=e.held_stack if h.valid_for_read then moved=moved+net.insert({name=h.name,count=h.count,quality=h.quality}) h.clear() end end e.destroy() n=n+1 end "
         "for _,b in pairs(s.find_entities_filtered{force=f,type='transport-belt',area={{-378,-362},{-377,-352}}}) do for l=1,2 do local line=b.get_transport_line(l) "
         "for _,st in pairs(line.get_contents()) do moved=moved+net.insert({name=st.name,count=st.count,quality=st.quality}) end line.clear() end b.destroy() n=n+1 end "
         "rcon.print('removed furnaces, inserters and ore belt pieces: '..n..', items moved to storage '..moved)")


def build():
    return [{"name": "bulk-inserter", "x": -377.5, "y": -352.5, "direction": 8},
            {"name": "foundry", "x": -377.5, "y": -355.5, "direction": 0, "recipe": "iron-ore-melting"},
            {"name": "bulk-inserter", "x": -380.5, "y": -355.5, "direction": 12}, {"name": "requester-chest", "x": -381.5, "y": -355.5},
            {"name": "pipe", "x": -378.5, "y": -358.5},
            {"name": "foundry", "x": -377.5, "y": -361.5, "direction": 0, "recipe": "casting-iron"},
            {"name": "long-handed-inserter", "x": -373.5, "y": -361.5, "direction": 12}]


CFG = ("local f=game.forces.player local s=game.surfaces.nauvis local c=s.find_entities_filtered{name='requester-chest',position={-381.5,-355.5},radius=0.3}[1] "
       "local ss=c.get_logistic_sections() local se=ss.sections[1] or ss.add_section() se.set_slot(1,{value={name='calcite',quality='normal'},min=50}) "
       "for _,m in pairs(s.find_entities_filtered{name='foundry',area={{-381,-365},{-374,-352}}}) do m.direction=0 end rcon.print('calcite request set')")


def main():
    apply = "--apply" in sys.argv
    if apply:
        print(tools["run_lua"]("game.server_save('before-nauvis-foundry-pilot') rcon.print('saved')"))
        print(tools["run_lua"](CLEAR))
    print(tools["place_entities"](json.dumps(build()), surface="nauvis", dry_run=not apply)[:800])
    if apply:
        print(tools["run_lua"](CFG))


if __name__ == "__main__":
    main()
