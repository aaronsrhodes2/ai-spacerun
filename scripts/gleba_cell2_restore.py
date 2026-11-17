#!/usr/bin/env python3
"""Gleba cell 2 (origin 56,82): put back the three missing row-2 biochambers and the pack chests' requests.

Found 2026-11-17: cell 2's pack chamber (61.5,94.5) and egg chambers (65.5,94.5), (73.5,94.5) were normal-quality ghosts with no recipe, and
the two pack requester chests (61.5,91.5), (69.5,91.5) asked for nutrients only (their recipe combinators were gone). Only cell 1's two pack
chambers ran, flat out: 190 packs a minute against the 306 the ten labs use. Remnants lay under the ghosts and Gleba's loss statistics show
3 biochambers, 2 arithmetic combinators, 13 pipes, 2 poles and 1 laser turret lost, with 1,048 premature big wrigglers killed: eggs hatched
there. Two laser turrets now stand south of the row at (63,99) and (71,99) (placed by hand on 2026-11-17, not by this script).

This places the chambers (legendary, like the rest; entities are free once researched), sets recipe and facing, and gives the pack chests the
design's requests (gleba_cell.py row 2). Items are never created.

Usage: gleba_cell2_restore.py [--apply]"""
import json
import sys

from _game import tools

Q = {"quality": "legendary"}
CH = [(61.5, 94.5, "agricultural-science-pack", 0), (65.5, 94.5, "pentapod-egg", 4), (73.5, 94.5, "pentapod-egg", 4)]
PACK_CHESTS = [(61.5, 91.5), (69.5, 91.5)]
PACK_REQ = (("bioflux", 10), ("pentapod-egg", 4), ("nutrients", 10))

GHOSTS = ("local s=game.surfaces.gleba local n=0 for _,p in pairs{%s} do for _,g in pairs(s.find_entities_filtered{type='entity-ghost',position=p,radius=0.5}) do "
          "if g.ghost_name=='biochamber' then g.destroy() n=n+1 end end end rcon.print('ghosts removed '..n)") % ",".join("{%s,%s}" % (x, y) for x, y, _, _ in CH)
CFG = ("local s=game.surfaces.gleba local o={} "
       + "".join("do local e=s.find_entities_filtered{name='biochamber',position={%s,%s},radius=0.5}[1] if e then e.set_recipe('%s') e.direction=%d o[#o+1]='%s '..e.direction..' '..e.quality.name end end "
                 % (x, y, r, d, r) for x, y, r, d in CH)
       + "".join("do local c=s.find_entities_filtered{name='requester-chest',position={%s,%s},radius=0.3}[1] local sec=c.get_requester_point().get_section(1) %s o[#o+1]='requests set' end "
                 % (x, y, " ".join("sec.set_slot(%d,{value={type='item',name='%s',quality='normal'},min=%d})" % (i + 1, n, m) for i, (n, m) in enumerate(PACK_REQ)))
                 for x, y in PACK_CHESTS)
       # the two rebuilt egg chambers' chests: their recipe combinators read nothing (wires lost with the old chambers), so the design's
       # request goes into the chest's manual section
       + "".join("do local c=s.find_entities_filtered{name='requester-chest',position={%s,91.5},radius=0.3}[1] local rp=c.get_requester_point() local sec "
                 "for _,q in pairs(rp.sections) do if q.is_manual then sec=q end end if not sec then sec=rp.add_section() end "
                 "sec.set_slot(1,{value={type='item',name='nutrients',quality='normal'},min=60}) sec.set_slot(2,{value={type='item',name='pentapod-egg',quality='normal'},min=2}) "
                 "o[#o+1]='egg requests set' end " % x for x in (65.5, 73.5))
       + "rcon.print(table.concat(o,' | '))")

apply = "--apply" in sys.argv
ents = [{"name": "biochamber", "x": x, "y": y, "direction": d, "recipe": r, "params": dict(Q)} for x, y, r, d in CH]
if apply:
    print(tools["run_lua"](GHOSTS))
print(tools["place_entities"](json.dumps(ents), surface="gleba", dry_run=not apply)[:600])
if apply:
    print(tools["run_lua"](CFG))
