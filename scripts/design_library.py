#!/usr/bin/env python3
"""The design library (working rules approved by the Captain, 2026-11-20): every standard unit is kept as a BLUEPRINT, in two places:
  in game   a blueprint item, labelled "<name> v<N>", in the steel chest tagged "Design library" on Nauvis at (-367,-187)
  in repo   designs/<name>-v<N>.txt (the blueprint string) and a row in designs/README.md
Improve the blueprint, not the map: change a unit, export it again (the version goes up, the chest keeps the newest, the repo keeps all).
A blueprint item is a free tool, not a product: it is made by script (create_blueprint), as a player would with an empty blueprint.
Each export also puts a map tag with the design's name on the place it was taken from (map tags are our place names).
Steps: chest | export NAME SURFACE X0 Y0 X1 Y1 [--note TEXT] | list
Usage: design_library.py chest ; design_library.py export egg-cell nauvis -365 -187 -347 -174 --note "captive spawner + module assembler\""""
import datetime
import glob
import json
import os
import sys

from _game import tools

L = tools["run_lua"]
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "designs")
CX, CY = -366.5, -186.5

CHEST = ("local s=game.surfaces.nauvis local f=game.forces.player local c=s.find_entities_filtered{name='steel-chest',position={%s,%s},radius=0.3}[1] local tags=f.find_chart_tags(s,{{%s-1,%s-1},{%s+1,%s+1}}) "
         "if #tags==0 then f.add_chart_tag(s,{position={%s,%s},text='Design library',icon={type='item',name='blueprint'}}) end rcon.print((c and 'chest stands' or 'NO chest')..', tag '..(#tags==0 and 'added' or 'there'))"
         % (CX, CY, CX, CY, CX, CY, CX, CY))

EXPORT = ("local s=game.surfaces['%s'] local f=game.forces.player local inv=game.create_inventory(1) inv.insert{name='blueprint'} local st=inv[1] st.create_blueprint{surface=s,force=f,area={{%s,%s},{%s,%s}},always_include_tiles=false} "
          "if not st.is_blueprint_setup() then inv.destroy() rcon.print('EMPTY') return end st.label='%s' local n=#st.get_blueprint_entities() local str=st.export_stack() "
          "local c=game.surfaces.nauvis.find_entities_filtered{name='steel-chest',position={%s,%s},radius=0.3}[1] local put='no chest' if c then local ci=c.get_inventory(defines.inventory.chest) "
          "for i=1,#ci do local x=ci[i] if x.valid_for_read and x.is_blueprint and x.label and x.label:sub(1,%d)=='%s' then x.clear() end end local e=ci.find_empty_stack() if e then e.set_stack(st) put='in the chest' else put='chest full' end end "
          "local tags=f.find_chart_tags(s,{{%s,%s},{%s,%s}}) local has=false for _,t in pairs(tags) do if t.text=='%s' then has=true end end if not has then f.add_chart_tag(s,{position={%s,%s},text='%s'}) end "
          "inv.destroy() rcon.print(n..'|'..put..'|'..str)")


def main():
    a = sys.argv[1:]
    step = a[0] if a else "list"
    os.makedirs(DIR, exist_ok=True)
    if step == "chest":
        r = tools["place_entities"](json.dumps([{"name": "steel-chest", "x": CX, "y": CY, "params": {"quality": "legendary"}}]), surface="nauvis")
        print(str(r)[:200])
        print(L(CHEST).strip())
    elif step == "export":
        name, surf = a[1], a[2]
        x0, y0, x1, y1 = (float(v) for v in a[3:7])
        note = a[a.index("--note") + 1] if "--note" in a else ""
        ver = len(glob.glob(os.path.join(DIR, name + "-v*.txt"))) + 1
        label = "%s v%d" % (name, ver)
        r = L(EXPORT % (surf, x0, y0, x1, y1, label, CX, CY, len(name) + 2, name + " v", x0, y0, x1, y1, name, (x0 + x1) / 2, (y0 + y1) / 2, name)).strip()
        if r == "EMPTY" or "|" not in r:
            print("nothing exported: " + r[:200])
            return
        n, put, s = r.split("|", 2)
        open(os.path.join(DIR, "%s-v%d.txt" % (name, ver)), "w", encoding="utf-8", newline="\n").write(s + "\n")
        idx = os.path.join(DIR, "README.md")
        if not os.path.exists(idx):
            open(idx, "w", encoding="utf-8", newline="\n").write("# Designs\n\nBlueprint strings, one file a version (`scripts/design_library.py`). The newest of each is also a blueprint in the\n\"Design library\" chest on Nauvis at (-367,-187).\n\n| Design | Version | Taken from | Entities | Date | Note |\n|---|---|---|---|---|---|\n")
        open(idx, "a", encoding="utf-8", newline="\n").write("| %s | %d | %s (%g,%g)..(%g,%g) | %s | %s | %s |\n" % (name, ver, surf, x0, y0, x1, y1, n, datetime.date.today().isoformat(), note))
        print("%s: %s entities, %d characters, %s, designs/%s-v%d.txt" % (label, n, len(s), put, name, ver))
    else:
        print(L("local c=game.surfaces.nauvis.find_entities_filtered{name='steel-chest',position={%s,%s},radius=0.3}[1] local o={} if c then local ci=c.get_inventory(defines.inventory.chest) for i=1,#ci do local x=ci[i] if x.valid_for_read and x.is_blueprint then o[#o+1]=x.label or '(no label)' end end end rcon.print(#o>0 and table.concat(o,string.char(10)) or 'the chest holds no blueprint')" % (CX, CY)))


if __name__ == "__main__":
    main()
