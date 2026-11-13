#!/usr/bin/env python3
"""Gleba egg redundancy (the Captain, 2026-11-13: keeping the eggs alive is the biggest challenge).
Layers after this script:
  1 keeper pair A (117.5/121.5): self-feeding, first on the nutrient tail, fast
  2 keeper pair B (93.5/97.5): self-feeding too (pair inserters at x 95.5), fed nutrients one at a time by slow inserters (about 80 a
    minute each) so it costs little, and still takes eggs off the belt when it has none (its belt inserters are gated like the others)
  3 the four production chambers reseed from the belt whenever eggs pass
  4 rot reserve: three blue chests in a row (130.5, 132.5, 134.5 at y 10.5), 9,600 spoilage each, about two hours of life support
Usage: gleba_eggs.py [--apply]"""
import json
import sys

from _game import tools

R = {"quality": "epic"}
E = [{"name": "bulk-inserter", "x": 95.5, "y": 14.5, "direction": 12}, {"name": "bulk-inserter", "x": 95.5, "y": 15.5, "direction": 4},
     {"name": "inserter", "x": 93.5, "y": 12.5, "direction": 0}, {"name": "inserter", "x": 97.5, "y": 12.5, "direction": 0},
     {"name": "bulk-inserter", "x": 131.5, "y": 10.5, "direction": 4}, {"name": "requester-chest", "x": 132.5, "y": 10.5},
     {"name": "bulk-inserter", "x": 133.5, "y": 10.5, "direction": 4}, {"name": "requester-chest", "x": 134.5, "y": 10.5}]
PRE = ("local s=game.surfaces.gleba local n=0 for _,x in pairs{93.5,97.5} do local i=s.find_entities_filtered{type='inserter',position={x,12.5},radius=0.3}[1] if i and i.name=='bulk-inserter' then i.destroy() n=n+1 end end rcon.print('fast nutrient inserters removed '..n)")
CFG = ("local s=game.surfaces.gleba local function at(t,x,y) return s.find_entities_filtered{type=t,position={x,y},radius=0.3}[1] end local n=0 "
       "local function f(x,y,item,stack) local i=at('inserter',x,y) i.use_filters=true i.inserter_filter_mode='whitelist' i.set_filter(1,item) if stack then i.inserter_stack_size_override=stack end n=n+1 end "
       "f(95.5,14.5,'pentapod-egg',1) f(95.5,15.5,'pentapod-egg',1) f(93.5,12.5,'nutrients',1) f(97.5,12.5,'nutrients',1) f(131.5,10.5,'spoilage') f(133.5,10.5,'spoilage') "
       "for _,x in pairs{132.5,134.5} do local c=at('logistic-container',x,10.5) local ss=c.get_logistic_sections() local se=ss.sections[1] or ss.add_section() se.set_slot(1,{value={name='spoilage',quality='normal'},min=9600}) end "
       "rcon.print('inserters set '..n..', reserve chests 3')")
for e in E:
    e["params"] = dict(R)
apply = "--apply" in sys.argv
if apply:
    print(tools["run_lua"](PRE))
print(tools["place_entities"](json.dumps(E), surface="gleba", dry_run=not apply)[:500])
if apply:
    print(tools["run_lua"](CFG))
