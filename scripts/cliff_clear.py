#!/usr/bin/env python3
"""Clear cliffs with construction robots. The robots need cliff explosives in the logistic network (one per cliff piece, the game's rule);
the drone-fed cells made by `build_cells.py --kind cliffx / barrel` make them (Nauvis: x -278..-271, y -185..-176).

Usage:
  cliff_clear.py mark X0 Y0 X1 Y1 [--surface nauvis] [--max N] [--apply]   mark every cliff piece in the box for deconstruction
                                                                           (dry run until --apply; only pieces inside a roboport's construction
                                                                           range are marked, the rest are counted and left alone)
  cliff_clear.py unmark X0 Y0 X1 Y1 [--surface nauvis]                      cancel the marks in a box
  cliff_clear.py status [--surface nauvis]                                  cliffs on the surface, marked now, cleared since we marked them,
                                                                           explosives held in the network and what the cells are doing
Cliffs change the map for good: mark only boxes the Captain has named.  The pieces this script marks are written to
snapshots/cliff_clear_state.json so `status` can count how many were cleared."""
import argparse
import json
import os
import sys

from _game import tools

STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "snapshots", "cliff_clear_state.json")
MAX_DEFAULT = 2000


def lua(code):
    return tools["run_lua"](code)


def load():
    try:
        with open(STATE, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def save(st):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as fh:
        json.dump(st, fh)


MARK = ("local s=game.surfaces['SURF'] local f=game.forces.player local nets=f.logistic_networks[s.name] or {} local seen,mk,un,out=0,0,0,{} local MAXN=MAXV "
        "for _,c in pairs(s.find_entities_filtered{area={{X0,Y0},{X1,Y1},},type='cliff'}) do seen=seen+1 "
        "if not c.to_be_deconstructed() then local inr=false for _,n in pairs(nets) do local cell=n.find_cell_closest_to(c.position) "
        "if cell and cell.is_in_construction_range(c.position) then inr=true break end end "
        "if inr then if APPLY and mk<MAXN then c.order_deconstruction(f) out[#out+1]=c.position.x..','..c.position.y end mk=mk+1 else un=un+1 end end end "
        "rcon.print(seen..';'..mk..';'..un..';'..table.concat(out,' '))")

UNMARK = ("local s=game.surfaces['SURF'] local f=game.forces.player local n=0 "
          "for _,c in pairs(s.find_entities_filtered{area={{X0,Y0},{X1,Y1}},type='cliff'}) do if c.to_be_deconstructed() then c.cancel_deconstruction(f) n=n+1 end end "
          "rcon.print(n)")

STATUS = ("local s=game.surfaces['SURF'] local f=game.forces.player local o={} local all=s.count_entities_filtered{type='cliff'} "
          "local mk=s.count_entities_filtered{type='cliff',to_be_deconstructed=true} o[#o+1]=all..';'..mk "
          "local best,bc=nil,0 for _,n in pairs(f.logistic_networks[s.name] or {}) do if #n.cells>bc then best=n bc=#n.cells end end "
          "if best then o[#o+1]=best.get_item_count('cliff-explosives')..';'..best.get_item_count('explosives')..';'..best.get_item_count('calcite')..';'..best.get_item_count('barrel')..';'..best.get_item_count('grenade')..';'..best.get_item_count('steel-plate') "
          "else o[#o+1]='none' end "
          "local E=defines.entity_status local SN={} for k,v in pairs(E) do SN[v]=k end local cs={} "
          "for _,m in pairs(s.find_entities_filtered{type='assembling-machine',force=f}) do local r=m.get_recipe() if r and (r.name=='cliff-explosives') then cs[#cs+1]=m.position.x..','..m.position.y..' '..SN[m.status]..' made '..m.products_finished end end "
          "o[#o+1]=table.concat(cs,' | ') rcon.print(table.concat(o,'\\n'))")

CHECK = ("local s=game.surfaces['SURF'] local o={} for _,p in ipairs(PTS) do if #s.find_entities_filtered{type='cliff',position=p,radius=0.5}==0 then o[#o+1]='1' else o[#o+1]='0' end end "
         "rcon.print(table.concat(o))")


def box(a):
    x0, y0, x1, y1 = [float(v) for v in a.box]
    return min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)


def cmd_mark(a):
    x0, y0, x1, y1 = box(a)
    code = (MARK.replace("SURF", a.surface).replace("X0", str(x0)).replace("Y0", str(y0)).replace("X1", str(x1)).replace("Y1", str(y1))
            .replace("MAXV", str(a.max)).replace("APPLY", "true" if a.apply else "false"))
    seen, mk, un, pts = lua(code).strip().split(";", 3)
    seen, mk, un = int(seen), int(mk), int(un)
    print(f"{a.surface} box ({x0},{y0})-({x1},{y1}): {seen} cliff pieces, {mk} could be marked, {un} outside every roboport's reach (left alone)")
    if not a.apply:
        print(f"dry run. Marking needs {min(mk, a.max)} cliff explosives (1 per piece); add --apply to mark" + (f" (capped at --max {a.max})" if mk > a.max else ""))
        return
    done = [tuple(float(v) for v in p.split(",")) for p in pts.split()]
    st = load()
    st.setdefault(a.surface, [])
    have = {tuple(p) for p in st[a.surface]}
    st[a.surface] += [list(p) for p in done if p not in have]
    save(st)
    print(f"marked {len(done)} pieces" + (f" ({mk - len(done)} more not marked, over --max {a.max})" if mk > len(done) else "") + "; run `status` to follow the drones")


def cmd_unmark(a):
    x0, y0, x1, y1 = box(a)
    n = lua(UNMARK.replace("SURF", a.surface).replace("X0", str(x0)).replace("Y0", str(y0)).replace("X1", str(x1)).replace("Y1", str(y1)))
    print(f"unmarked {n.strip()} cliff pieces in the box")


def cmd_status(a):
    lines = lua(STATUS.replace("SURF", a.surface)).strip().split("\n")
    allc, mk = lines[0].split(";")
    print(f"{a.surface}: {allc} cliff pieces left, {mk} marked for deconstruction now")
    st = load().get(a.surface, [])
    if st:
        cleared = 0
        for i in range(0, len(st), 500):
            pts = "{" + ",".join("{%s,%s}" % (p[0], p[1]) for p in st[i:i + 500]) + "}"
            cleared += lua(CHECK.replace("SURF", a.surface).replace("PTS", pts)).count("1")
        print(f"marked by this script: {len(st)}, cleared: {cleared}, still standing: {len(st) - cleared}")
    else:
        print("no marks by this script on this surface yet")
    if lines[1] == "none":
        print("no logistic network on this surface")
    else:
        ce, ex, ca, ba, gr, stl = lines[1].split(";")
        print(f"network holds: cliff explosives {ce}, explosives {ex}, calcite {ca}, barrels {ba}, grenades {gr}, steel plate {stl}")
        print(f"  cliff explosives still needed for the marks: {mk}; short by {max(0, int(mk) - int(ce))}")
    if len(lines) > 2 and lines[2]:
        print("cliff explosive machines:", lines[2])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["mark", "unmark", "status"])
    ap.add_argument("box", nargs="*", help="X0 Y0 X1 Y1 (tiles) for mark / unmark")
    ap.add_argument("--surface", default="nauvis")
    ap.add_argument("--max", type=int, default=MAX_DEFAULT, help="most pieces one mark call may mark (default %d)" % MAX_DEFAULT)
    ap.add_argument("--apply", action="store_true", help="mark for real (mark is a dry run without it)")
    a = ap.parse_args()
    if a.cmd in ("mark", "unmark") and len(a.box) != 4:
        sys.exit("mark / unmark need X0 Y0 X1 Y1")
    {"mark": cmd_mark, "unmark": cmd_unmark, "status": cmd_status}[a.cmd](a)


if __name__ == "__main__":
    main()
