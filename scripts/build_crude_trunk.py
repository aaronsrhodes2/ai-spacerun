"""
Crude trunk: underground pipe from the Oil A unload tank at the bus head to the refinery tank farm.

    start   the existing crude pipe at (227.5,-165.5) in the Oil A unload pipe row (a tank at (cx,cy) facing north has its ports at
            (cx-1,cy-2), (cx-2,cy-1), (cx+1,cy+2), (cx+2,cy+1), so the tile west of the tank is NOT a port)
    north   pipe-to-ground pairs up column x=227 from the tile above that pipe to the trunk row
    west    pipe-to-ground pairs along the trunk row to the refinery's crude column (x=-268.5),
            with pumps where the row is powered so no pipeline is longer than 320 tiles

Only free tiles are used (can_place_entity, manual check); nothing is removed. A pipe-to-ground of
someone else on the same line and axis is never straddled.

Usage: scripts/build_crude_trunk.py [--row Y] [--apply]
"""
import json
import sys

from _game import tools

START = (227, -166)          # tile of the existing crude pipe the trunk starts from (nothing is placed on it)
WEST_X = -268                # last tile of the west run; the crude column is the tile west of it
ROWS = range(-304, -285)     # tile rows that touch the crude column
PUMPS_NEAR = (60, -110)      # wanted pump x tiles (two pumps -> three pipelines)
SPAN = 10



def scan(x1, y1, x2, y2):
    """Tiles of the line (inclusive): free for a pipe end, powered, and foreign pipe-to-ground on the same axis."""
    horiz = y1 == y2
    code = f"""
      local s=game.surfaces.nauvis local f=game.forces.player local free,pow,ptg={{}},{{}},{{}}
      local x1,y1,x2,y2={x1},{y1},{x2},{y2}
      local n=math.max(math.abs(x2-x1),math.abs(y2-y1)) local dx=(x2>x1 and 1) or (x2<x1 and -1) or 0 local dy=(y2>y1 and 1) or (y2<y1 and -1) or 0
      local poles=s.find_entities_filtered{{force=f,type='electric-pole',area={{{{math.min(x1,x2)-10,math.min(y1,y2)-10}},{{math.max(x1,x2)+10,math.max(y1,y2)+10}}}}}}
      for i=0,n do local x,y=x1+dx*i+0.5,y1+dy*i+0.5
        free[#free+1]=s.can_place_entity{{name='pipe-to-ground',position={{x,y}},direction={12 if horiz else 0},force=f,build_check_type=defines.build_check_type.manual}} and 'F' or 'x'
        local p='-' for _,e in pairs(poles) do local d=e.prototype.get_supply_area_distance(e.quality) if math.abs(e.position.x-x)<=d-0.5 and math.abs(e.position.y-y)<=d-0.5 then p='P' break end end pow[#pow+1]=p
        local g=s.find_entities_filtered{{name='pipe-to-ground',position={{x,y}}}}[1]
        if g and ((g.direction%8==4)=={'true' if horiz else 'false'}) then ptg[#ptg+1]=i end
      end
      rcon.print(helpers.table_to_json({{free=table.concat(free),pow=table.concat(pow),ptg=ptg}}))
    """
    out = tools["run_lua"](" ".join(code.split()))
    d = json.loads(out)
    if "result" in d:
        d = json.loads(d["result"])
    if "free" not in d:
        raise SystemExit(f"scan failed: {out[:600]}")
    return d


def pairs_for(free, ptg, a, b):
    """Fewest (entrance, exit) index pairs covering a..b, entrance at a, exit at b."""
    INF = 10 ** 9
    best = {a - 1: (0, None)}          # exit index -> (pairs, previous)
    blocked = set(ptg if isinstance(ptg, list) else [])
    for j in range(a + 1, b + 1):
        if free[j] != "F":
            continue
        cand = (INF, None)
        for i in range(max(a, j - SPAN), j):
            if free[i] != "F" or (i - 1) not in best:
                continue
            if any(i < k < j for k in blocked):
                continue
            c = best[i - 1][0] + 1
            if c < cand[0]:
                cand = (c, i)
        if cand[1] is not None:
            best[j] = cand
    if b not in best:
        reach = max(best)
        raise ValueError(f"no run from {a} to {b}: furthest exit index {reach}")
    out, j = [], b
    while j >= a:
        i = best[j][1]
        out.append((i, j))
        j = i - 1
    return out[::-1]


def plan(row):
    ents = []
    # north leg: column START x, from the tile above the start pipe to the tile below the corner
    col = scan(START[0], START[1] - 1, START[0], row + 1)
    for i, j in pairs_for(col["free"], col["ptg"], 0, len(col["free"]) - 1):
        ents.append({"name": "pipe-to-ground", "x": START[0] + 0.5, "y": START[1] - 1 - i + 0.5, "direction": 8})
        ents.append({"name": "pipe-to-ground", "x": START[0] + 0.5, "y": START[1] - 1 - j + 0.5, "direction": 0})
    ents.append({"name": "pipe", "x": START[0] + 0.5, "y": row + 0.5})
    # west leg
    x0 = START[0] - 1
    line = scan(x0, row, WEST_X, row)
    free, pow_ = line["free"], line["pow"]
    n = len(free) - 1
    pumps = []
    for want in PUMPS_NEAR:
        k0 = x0 - want
        for off in sorted(range(-40, 41), key=abs):
            k = k0 + off      # pump on indices k, k+1; exit at k-1, entrance at k+2
            if 2 <= k and k + 3 <= n and all(free[t] == "F" for t in (k - 1, k, k + 1, k + 2)) and pow_[k] == "P" and pow_[k + 1] == "P":
                pumps.append(k)
                break
        else:
            raise ValueError(f"row {row}: no powered free spot for a pump near x={want}")
    a = 0
    for k in pumps + [None]:
        b = n if k is None else k - 1
        for i, j in pairs_for(free, line["ptg"], a, b):
            ents.append({"name": "pipe-to-ground", "x": x0 - i + 0.5, "y": row + 0.5, "direction": 4})
            ents.append({"name": "pipe-to-ground", "x": x0 - j + 0.5, "y": row + 0.5, "direction": 12})
        if k is not None:
            ents.append({"name": "pump", "x": x0 - k, "y": row + 0.5, "direction": 12})
            a = k + 2
    return ents, pumps


def main():
    rows = [int(sys.argv[sys.argv.index("--row") + 1])] if "--row" in sys.argv else list(ROWS)
    best = None
    for row in rows:
        try:
            ents, pumps = plan(row)
        except ValueError as e:
            print("row", row, "no:", e)
            continue
        print("row", row, "ok:", len(ents), "entities, pumps at index", pumps)
        if best is None or len(ents) < len(best[1]):
            best = (row, ents)
    if best is None:
        raise SystemExit("no row works")
    row, ents = best
    print("chosen row", row, "entities", len(ents))
    r = json.loads(tools["place_entities"](json.dumps(ents), dry_run=True))
    if r.get("error") or r["failed"]:
        raise SystemExit(f"dry run failed, nothing built: {json.dumps(r)[:1500]}")
    print("dry run clean")
    if "--apply" not in sys.argv:
        print(json.dumps([e for e in ents if e["name"] != "pipe-to-ground"]))
        return
    print(tools["save_game"]("pre-crude-trunk"))
    r = json.loads(tools["place_entities"](json.dumps(ents)))
    print("placed", r.get("placed"), "failed", r.get("failed"))


if __name__ == "__main__":
    main()
