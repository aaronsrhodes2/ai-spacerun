#!/usr/bin/env python3
"""Factory compaction routine (the Captain, 2026-11-14: "script an easy routine ... so we can use it in the future"): lossless squeeze of a block of
modules into a smaller, squarer footprint, with free ground left in one piece. Works on any block, not only the Replicator.

How it moves a module: surface.clone_entities (tested live: copies recipes, modules, chest requests, inventories and every wire BETWEEN the copied
entities), then it re-attaches every wire that went to something OUTSIDE the module (the hub roboport, silos, lattice poles) to the copy, checks the
copy, and only then removes the original. Nothing is rebuilt from scripts, so a module needs no script of its own to be movable.
What a clone cannot carry is a constant written in some other script (replicator_viz.py hard-codes positions; snapshots/replicator_cells.json holds cell
coordinates): a module's "post" list says what to update, `move` prints it and the `cellreg` hook edits the cell registry for you.

Modules live in snapshots/compact_modules.json: {name: {box:[x1,y1,x2,y2], skip:[[x1,y1,x2,y2],..], exclude:[entity names], post:[notes or "cellreg:NAME"]}}.
An entity belongs to a module when its centre is inside `box` and not inside a `skip` box and its name is not in `exclude` (default: walls and robots).

Steps (read-only unless --apply):
  survey X1 Y1 X2 Y2        ASCII map of a box plus how much of it is built on (find the empty ground)
  list                      the registered modules, their size and entity counts
  define NAME X1 Y1 X2 Y2 [--exclude a,b] [--skip x1,y1,x2,y2] [--part x1,y1,x2,y2 ...] [--post text]   register or edit a module (NAME's box is its bounding
                            box; repeat --part when it interleaves with others: the module is then exactly those rectangles; the first --part replaces)
  check NAME                what is inside the module (names and counts) and which wires leave it (review a new definition before moving it)
  plan --at X Y [--width W] [--gap G] [--order a,b,c]   pack the registered modules in shelves from (X,Y), widest-first, W wide (default: square-ish);
                            prints each module's move; writes snapshots/compact_plan.json
  move NAME DX DY [--apply]  one module (dry run checks the destination; --apply saves the game first)
  run [--apply]             every move of the plan in order; a move whose destination still overlaps another module's current box is deferred
                            until that module has moved (a cycle is reported, not forced)
  undo NAME                 move the module back by its last recorded offset
  wall X1 Y1 X2 Y2 [--apply] [--clear-old ox1 oy1 ox2 oy2]   stone-wall (epic) ring on the tile ring just outside the box; --clear-old removes the walls inside the given OLD scan box first
Usage: PYTHONPATH=scripts python scripts/compact.py <step> ...   (shell: bash, PLATINUM 20)"""
import json
import sys
from pathlib import Path

from _game import tools

HERE = Path(__file__).resolve().parent
REG = HERE.parent / "snapshots" / "compact_modules.json"
PLAN = HERE.parent / "snapshots" / "compact_plan.json"
MOVES = HERE.parent / "snapshots" / "compact_moves.json"
CELLREG = HERE.parent / "snapshots" / "replicator_cells.json"
DEFAULT_EXCLUDE = ["stone-wall", "logistic-robot", "construction-robot", "character", "cargo-pod", "item-entity", "entity-ghost"]


def load(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def save(path, data):
    path.write_text(json.dumps(data, indent=1, sort_keys=True), encoding="utf-8")


def lua(code):
    return tools["run_lua"](" ".join(code.split("\n"))).strip()


def opt(name, n=1, default=None):
    if name not in sys.argv:
        return default
    i = sys.argv.index(name)
    return sys.argv[i + 1:i + 1 + n] if n > 1 else sys.argv[i + 1]


def lua_list(v):
    return "{" + ",".join(json.dumps(x) if isinstance(x, str) else str(x) for x in v) + "}"


def lua_boxes(bs):
    return "{" + ",".join("{%s}" % ",".join(str(c) for c in b) for b in bs) + "}"


# --------------------------------------------------------------------------------------------------------------- gather (shared Lua prefix)
GATHER = r'''
local s = game.surfaces.nauvis
local f = game.forces.player
local PARTS, SKIP, EXC = BOXV, SKIPV, EXCV
local excl = {} for _, n in ipairs(EXC) do excl[n] = true end
local function inbox(p, b) return p.x >= b[1] and p.x < b[3] and p.y >= b[2] and p.y < b[4] end
local E, inset = {}, {}
local seen = {}
for _, BOX in ipairs(PARTS) do for _, e in ipairs(s.find_entities_filtered{area = {{BOX[1] - 3, BOX[2] - 3}, {BOX[3] + 3, BOX[4] + 3}}, force = f}) do
  local p = e.position
  if inbox(p, BOX) and not excl[e.name] and not seen[e] then
    seen[e] = true
    local skipped = false
    for _, sb in ipairs(SKIP) do if inbox(p, sb) then skipped = true end end
    if not skipped then E[#E + 1] = e inset[e.unit_number or -#E] = true end
  end
end end
local W = defines.wire_connector_id
local IDS = {W.circuit_red, W.circuit_green, W.combinator_input_red, W.combinator_input_green, W.combinator_output_red, W.combinator_output_green, W.pole_copper}
local function externals()
  local R = {}
  for i, e in ipairs(E) do
    for _, id in ipairs(IDS) do
      local c = e.get_wire_connector(id, false)
      if c then for _, conn in ipairs(c.connections) do
        local t = conn.target
        local o = t.owner
        if not inset[o.unit_number or 0] then R[#R + 1] = {i = i, id = id, o = o, tid = t.wire_connector_id} end
      end end
    end
  end
  return R
end
'''


def parts(mod):
    """The rectangles a module is made of (default: its one box). A module that interleaves with others is several rectangles moved rigidly together."""
    return mod.get("parts") or [mod["box"]]


def gather(mod):
    ex = mod.get("exclude", []) + DEFAULT_EXCLUDE
    return (GATHER.replace("BOXV", lua_boxes(parts(mod))).replace("SKIPV", lua_boxes(mod.get("skip", []))).replace("EXCV", lua_list(ex)))


# --------------------------------------------------------------------------------------------------------------- steps
def cmd_survey():
    x1, y1, x2, y2 = (int(v) for v in sys.argv[2:6])
    r = lua(
        "local s=game.surfaces.nauvis local g={} local cnt=0 "
        "local codes={['stone-wall']='#',['assembling-machine-3']='M',['chemical-plant']='C',['electric-furnace']='F',['decider-combinator']='d',['arithmetic-combinator']='a',"
        "['constant-combinator']='c',['selector-combinator']='s',['buffer-chest']='B',['requester-chest']='R',['passive-provider-chest']='P',['fast-inserter']='i',['stack-inserter']='i',"
        "['bulk-inserter']='i',['substation']='S',['roboport']='O',['display-panel']='L',['small-lamp']='l',['solar-panel']='$',['accumulator']='A',['pipe']='=',['pipe-to-ground']='u'} "
        "for _,e in ipairs(s.find_entities_filtered{area={{%d,%d},{%d,%d}},force=game.forces.player}) do local c=codes[e.name] if not c and e.type~='logistic-robot' and e.type~='construction-robot' and e.type~='character' then c='?' end "
        "if c then local bb=e.bounding_box for x=math.floor(bb.left_top.x+0.01),math.ceil(bb.right_bottom.x-0.01)-1 do for y=math.floor(bb.left_top.y+0.01),math.ceil(bb.right_bottom.y-0.01)-1 do "
        "g[#g+1]=x..','..y..','..c end end end end rcon.print(table.concat(g,';'))" % (x1, y1, x2, y2))
    m = {}
    for t in r.split(";"):
        p = t.split(",")
        if len(p) == 3:
            m[(int(p[0]), int(p[1]))] = p[2]
    for y in range(y1, y2):
        print("%5d " % y + "".join(m.get((x, y), ".") for x in range(x1, x2)))
    built = sum(1 for k, v in m.items() if v != "#" and x1 <= k[0] < x2 and y1 <= k[1] < y2)
    print(f"x from {x1}; built-on tiles {built} of {(x2 - x1) * (y2 - y1)} ({100 * built // max(1, (x2 - x1) * (y2 - y1))}%); # = wall, ? = other entity")


def cmd_list():
    reg = load(REG, {})
    for name, mod in sorted(reg.items()):
        b = mod["box"]
        n = lua(gather(mod) + "rcon.print(#E)")
        print(f"{name:14s} box {b}  {b[2] - b[0]} x {b[3] - b[1]}  entities {n}  {'(UNVERIFIED) ' if not mod.get('verified', True) else ''}{mod.get('note', '')}")


def cmd_define():
    name = sys.argv[2]
    box = [float(v) for v in sys.argv[3:7]]
    reg = load(REG, {})
    mod = reg.get(name, {})
    mod["box"] = [int(v) if v == int(v) else v for v in box]
    if "--exclude" in sys.argv:
        mod["exclude"] = [n for n in opt("--exclude").split(",") if n]
    ps = [[float(v) for v in sys.argv[i + 1].split(",")] for i, a in enumerate(sys.argv) if a == "--part"]
    if ps:
        mod["parts"] = ps
    if "--skip" in sys.argv:
        mod.setdefault("skip", []).append([float(v) for v in opt("--skip").split(",")])
    if "--post" in sys.argv:
        mod.setdefault("post", []).append(opt("--post"))
    mod["verified"] = False
    reg[name] = mod
    save(REG, reg)
    print("defined", name, mod)


def cmd_check():
    mod = load(REG, {})[sys.argv[2]]
    out = lua(gather(mod) + "local c,ex={}, 0 for _,e in ipairs(E) do c[e.name]=(c[e.name] or 0)+1 end local R=externals() local t={} for n,k in pairs(c) do t[#t+1]=n..' '..k end table.sort(t) "
              "local xo={} for _,r in ipairs(R) do xo[#xo+1]=r.o.name..string.format('@%.1f,%.1f',r.o.position.x,r.o.position.y) end "
              "rcon.print(#E..' entities: '..table.concat(t,', ')..'\\n'..#R..' wires leave the module, to: '..table.concat(xo,' | '):sub(1,900))")
    print(out)
    print("module box", mod["box"], "; if the list holds lattice (substations/roboports of the base) or leaves out a part, edit with: define NAME ... --exclude / --skip")


def box_free(mod, dx, dy):
    """Foreign (non-module, non-excluded) entities in the destination rectangles, plus overlap with the module's own source rectangles."""
    b = mod["box"]
    nb = [b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy]
    overlap, bad_n, bad_l = False, 0, []
    for pr in parts(mod):
        d = [pr[0] + dx, pr[1] + dy, pr[2] + dx, pr[3] + dy]
        for o in parts(mod):
            if not (d[2] <= o[0] or d[0] >= o[2] or d[3] <= o[1] or d[1] >= o[3]):
                overlap = True
        out = lua(gather(mod) + "local keep={} for _,e in ipairs(E) do keep[e.unit_number or 0]=true end local bad={} "
                  "for _,e in ipairs(s.find_entities_filtered{area={{%s,%s},{%s,%s}}}) do if not keep[e.unit_number or 0] and e.type~='logistic-robot' and e.type~='construction-robot' and e.type~='character' and e.type~='resource' and e.type~='corpse' and e.type~='item-entity' then "
                  "local k=e.name local p=e.position bad[#bad+1]=k..string.format('@%%.1f,%%.1f',p.x,p.y) end end rcon.print(#bad..'|'..table.concat(bad,' ; '):sub(1,500))" % tuple(d))
        n, _, lst = out.partition("|")
        bad_n += int(n)
        if int(n):
            bad_l.append(lst)
    return nb, overlap, bad_n, " || ".join(bad_l)


def do_move(name, dx, dy, apply):
    reg = load(REG, {})
    mod = reg[name]
    nb, overlap, nbad, lst = box_free(mod, dx, dy)
    print(f"{name}: offset ({dx},{dy}), destination {nb}")
    if overlap:
        print("  destination overlaps the module's own source box: move it in two steps (a scratch offset first) or pick another offset")
        return False
    if nbad:
        print(f"  destination holds {nbad} foreign entities: {lst}")
        return False
    if not apply:
        print("  destination is free (dry run: nothing moved)")
        return True
    print("  save:", lua("game.server_save('pre-compact-%s') rcon.print('saved')" % name.replace(" ", "_")))
    code = gather(mod) + (
        "local R=externals() local n0=#E local DX,DY=%s,%s local pos={} for i,e in ipairs(E) do pos[i]={e.name,e.position.x+DX,e.position.y+DY,e.direction} end "
        "s.clone_entities{entities=E,destination_offset={DX,DY},clone_connections=true} local C={} local miss=0 "
        "for i,p in ipairs(pos) do local c=s.find_entities_filtered{name=p[1],position={p[2],p[3]},radius=0.15}[1] if c then C[i]=c else miss=miss+1 end end "
        "if miss>0 then rcon.print('ABORT: '..miss..' of '..n0..' clones missing; originals untouched; remove the partial copies by hand') return end "
        "local w,wf=0,0 for _,r in ipairs(R) do local c=C[r.i] local ok=c and pcall(function() c.get_wire_connector(r.id,true).connect_to(r.o.get_wire_connector(r.tid,true),false,defines.wire_origin.script) end) if ok then w=w+1 else wf=wf+1 end end "
        "if wf>0 then rcon.print('ABORT: '..wf..' external wires could not be re-attached; originals untouched') return end "
        "for i,e in ipairs(E) do e.destroy() end rcon.print('moved '..n0..' entities, re-attached '..w..' external wires')" % (dx, dy))
    out = lua(code)
    print(" ", out)
    if not out.startswith("moved"):
        return False
    mod["box"] = nb
    if mod.get("parts"):
        mod["parts"] = [[p[0] + dx, p[1] + dy, p[2] + dx, p[3] + dy] for p in mod["parts"]]
    if mod.get("skip"):
        mod["skip"] = [[p[0] + dx, p[1] + dy, p[2] + dx, p[3] + dy] for p in mod["skip"]]
    mod["verified"] = True
    reg[name] = mod
    save(REG, reg)
    moves = load(MOVES, {})
    moves.setdefault(name, []).append([dx, dy])
    save(MOVES, moves)
    for note in mod.get("post", []):
        if note.startswith("cellreg:"):
            cell = note.split(":", 1)[1]
            cr = load(CELLREG, {})
            if cell in cr:
                cr[cell]["x"] += dx
                cr[cell]["y"] += dy
                if "rank" in cr[cell]:
                    cr[cell]["rank"] = [cr[cell]["rank"][0] + dx, cr[cell]["rank"][1] + dy]
                    cr[cell]["ring"] = [cr[cell]["ring"][0] + dx, cr[cell]["ring"][1] + dy]
                save(CELLREG, cr)
                print(f"  cell registry: {cell} moved to ({cr[cell]['x']},{cr[cell]['y']})")
        else:
            print("  TODO after this move:", note)
    return True


def cmd_plan():
    reg = load(REG, {})
    ax, ay = (int(v) for v in opt("--at", 2, ["0", "0"]))
    gap = int(opt("--gap", default="2"))
    order = (opt("--order", default="") or "").split(",")
    names = [n for n in order if n in reg] or sorted(reg, key=lambda n: -(reg[n]["box"][2] - reg[n]["box"][0]))
    size = {n: (reg[n]["box"][2] - reg[n]["box"][0], reg[n]["box"][3] - reg[n]["box"][1]) for n in names}
    total = sum((w + gap) * (h + gap) for w, h in size.values())
    width = int(opt("--width", default=0)) or max(max(w for w, h in size.values()), int(total ** 0.5) + 1)
    # shelf packing, tallest first inside a shelf order
    shelves, cur, used = [], [], 0
    for n in sorted(names, key=lambda n: -size[n][1]):
        w, h = size[n]
        if cur and used + w > width:
            shelves.append(cur)
            cur, used = [], 0
        cur.append(n)
        used += w + gap
    if cur:
        shelves.append(cur)
    moves, y, maxx = [], ay, -10**9
    for sh in shelves:
        x, hmax = ax, 0
        for n in sh:
            w, h = size[n]
            b = reg[n]["box"]
            moves.append({"name": n, "dx": x - b[0], "dy": y - b[1], "to": [x, y, x + w, y + h]})
            x += w + gap
            hmax = max(hmax, h)
        maxx = max(maxx, x - gap)
        y += hmax + gap
    out = {"at": [ax, ay], "width": width, "gap": gap, "box": [ax, ay, maxx, y - gap], "moves": moves}
    save(PLAN, out)
    area = (maxx - ax) * (y - gap - ay)
    print(f"plan: {len(moves)} moves into {maxx - ax} x {y - gap - ay} = {area} tiles ({sum(w * h for w, h in size.values())} tiles of modules, gap {gap}); saved to {PLAN.name}")
    for m in moves:
        print(f"  {m['name']:14s} -> {m['to']}  offset ({m['dx']},{m['dy']})")


def cmd_run():
    apply = "--apply" in sys.argv
    plan = load(PLAN, None)
    if not plan:
        sys.exit("no plan: run `plan` first")
    pending = [m for m in plan["moves"] if m["dx"] or m["dy"]]
    reg = load(REG, {})
    progress = True
    while pending and progress:
        progress = False
        for m in list(pending):
            mod = reg[m["name"]]
            nb, overlap, nbad, lst = box_free(mod, m["dx"], m["dy"])
            if overlap or nbad:
                print(f"defer {m['name']}: " + ("overlaps itself" if overlap else f"{nbad} foreign entities there"))
                continue
            if do_move(m["name"], m["dx"], m["dy"], apply):
                reg = load(REG, {})
                pending.remove(m)
                progress = True
    if pending:
        print("not moved (blocked, move something else first or define the blocker as a module):", [m["name"] for m in pending])


def cmd_undo():
    name = sys.argv[2]
    moves = load(MOVES, {})
    if not moves.get(name):
        sys.exit("no recorded move")
    dx, dy = moves[name].pop()
    save(MOVES, moves)
    do_move(name, -dx, -dy, True)
    moves = load(MOVES, {})
    if moves.get(name):
        moves[name].pop()          # the undo itself was recorded as a move; drop it
        save(MOVES, moves)


def cmd_wall():
    x1, y1, x2, y2 = (int(v) for v in sys.argv[2:6])
    if "--clear-old" in sys.argv and "--apply" in sys.argv:
        ox1, oy1, ox2, oy2 = (int(v) for v in opt("--clear-old", 4))        # the old wall's scan box: only walls inside it go
        print(lua("local n=0 for _,w in ipairs(game.surfaces.nauvis.find_entities_filtered{name='stone-wall',force=game.forces.player,area={{%d,%d},{%d,%d}}}) do w.destroy() n=n+1 end rcon.print('cleared '..n..' old walls')" % (ox1, oy1, ox2, oy2)))
    ents = []
    for x in range(x1 - 1, x2 + 1):
        ents += [{"name": "stone-wall", "x": x + 0.5, "y": y1 - 0.5, "params": {"quality": "epic"}}, {"name": "stone-wall", "x": x + 0.5, "y": y2 + 0.5, "params": {"quality": "epic"}}]
    for y in range(y1, y2):
        ents += [{"name": "stone-wall", "x": x1 - 0.5, "y": y + 0.5, "params": {"quality": "epic"}}, {"name": "stone-wall", "x": x2 + 0.5, "y": y + 0.5, "params": {"quality": "epic"}}]
    r = json.loads(tools["place_entities"](json.dumps(ents), surface="nauvis", dry_run="--apply" not in sys.argv))
    fails = r.get("failed") or []
    why = {}
    for f in fails:
        why[f.get("why")] = why.get(f.get("why"), 0) + 1
    print(len(ents), "walls; placed", r.get("placed"), "; not placed:", why or "none")


STEPS = {"survey": cmd_survey, "list": cmd_list, "define": cmd_define, "check": cmd_check, "plan": cmd_plan, "run": cmd_run, "undo": cmd_undo, "wall": cmd_wall}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in STEPS and sys.argv[1] != "move":
        print(__doc__)
    elif sys.argv[1] == "move":
        do_move(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), "--apply" in sys.argv)
    else:
        STEPS[sys.argv[1]]()
