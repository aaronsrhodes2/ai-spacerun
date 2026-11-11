"""
Fulgora stage 2: scrap mining and recycling block on the home patch (island around 22,-95). No inserters and no scrap belts:
each electric mining drill drops scrap straight into a recycler, and the recycler drops its products onto a belt.

One strip, west to east from x=12, 3 tiles per slice:
  belt A (y -97.5, flows west)   <- north recyclers (rows -97..-94) <- north drills (rows -93..-91)
  belt B (y -82.5, flows west)   <- south recyclers (rows -87..-84) <- south drills (rows -90..-88)
The two drill rows sit back to back in the densest scrap. A medium pole stands in the spare column beside each recycler.
A unit is placed only where its drill reaches scrap and both machines fit; belts dive under anything in their way.
Speed modules for the drills are taken from Nauvis' logistic stock (factory-made, moved), never spawned.

Usage: scripts/fulgora_scrap.py [--slices 11] [--modules 3] [--apply]
"""
import json
import sys

from _game import tools

X0 = 12
YA, YB = -97.5, -82.5


def lua(code):
    out = tools["run_lua"](code).strip()
    try:
        d = json.loads(out)
        return d["result"] if isinstance(d, dict) and "result" in d else d
    except Exception:
        return out


def _j(v):
    return json.loads(v) if isinstance(v, str) else v


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def units(n):
    u = []
    for k in range(n):
        x = X0 + 3 * k
        u.append({"side": "N", "drill": (x + 1.5, -91.5, 0), "rec": (x + 2, -95, 0), "pole": (x + 0.5, -95.5), "out": (x + 1.5, YA)})
        u.append({"side": "S", "drill": (x + 1.5, -88.5, 8), "rec": (x + 1, -85, 8), "pole": (x + 2.5, -85.5), "out": (x + 1.5, YB)})
    return u


def check(us):
    spec = "{" + ",".join(f"{{{u['drill'][0]},{u['drill'][1]},{u['drill'][2]},{u['rec'][0]},{u['rec'][1]},{u['rec'][2]}}}" for u in us) + "}"
    code = ("local s=game.surfaces.fulgora local f=game.forces.player local o={} for i,u in pairs(" + spec + ") do "
            "local ore=s.count_entities_filtered{name='scrap',area={{u[1]-2.49,u[2]-2.49},{u[1]+2.49,u[2]+2.49}}} "
            "local a=s.can_place_entity{name='electric-mining-drill',position={u[1],u[2]},direction=u[3],force=f,build_check_type=defines.build_check_type.manual} "
            "local b=s.can_place_entity{name='recycler',position={u[4],u[5]},direction=u[6],force=f,build_check_type=defines.build_check_type.manual} "
            "o[i]=(ore>0 and a and b) and ore or 0 end rcon.print(helpers.table_to_json(o))")
    return _j(lua(code))


def blocked(y, xs):
    code = ("local s=game.surfaces.fulgora local f=game.forces.player local o={} for _,x in pairs({" + ",".join(str(x) for x in xs) + "}) do "
            f"o[#o+1]=s.can_place_entity{{name='express-transport-belt',position={{x,{y}}},force=f,build_check_type=defines.build_check_type.manual}} and 0 or 1 end rcon.print(helpers.table_to_json(o))")
    return dict(zip(xs, _j(lua(code))))


def belt(y, x_east, taken):
    """Belt flowing west from x_east to X0+0.5; underground under blocked runs or under tiles the units need."""
    xs = [x_east - i for i in range(int(x_east - (X0 + 0.5)) + 1)]
    bl = blocked(y, xs)
    for x in xs:
        if x in taken:
            bl[x] = 1
    ents, hidden, i = [], set(), 0
    while i < len(xs):
        x = xs[i]
        if bl[x]:
            raise SystemExit(f"belt y={y}: start tile {x} blocked")
        j = i + 1
        if j < len(xs) and bl[xs[j]]:
            while j < len(xs) and bl[xs[j]]:
                hidden.add(xs[j]); j += 1
            if j >= len(xs) or j - i - 1 > 8:
                raise SystemExit(f"belt y={y}: cannot pass the block after x={x}")
            ents.append({"name": "express-underground-belt", "x": x, "y": y, "direction": 12, "params": {"type": "input"}})
            ents.append({"name": "express-underground-belt", "x": xs[j], "y": y, "direction": 12, "params": {"type": "output"}})
            i = j + 1
        else:
            ents.append({"name": "express-transport-belt", "x": x, "y": y, "direction": 12})
            i += 1
    return ents, hidden


def main():
    n, mods, apply = arg("--slices", 11), arg("--modules", 3), "--apply" in sys.argv
    us = units(n)
    ok = check(us)
    us = [u for u, o in zip(us, ok) if o]
    ents, keep = [], []
    for side, y in (("N", YA), ("S", YB)):
        mine = [u for u in us if u["side"] == side]
        if not mine:
            continue
        b, hidden = belt(y, max(u["out"][0] for u in mine), set())
        mine = [u for u in mine if u["out"][0] not in hidden]
        ents += b
        keep += mine
    for u in keep:
        ents.append({"name": "electric-mining-drill", "x": u["drill"][0], "y": u["drill"][1], "direction": u["drill"][2]})
        ents.append({"name": "recycler", "x": u["rec"][0], "y": u["rec"][1], "direction": u["rec"][2]})
        ents.append({"name": "medium-electric-pole", "x": u["pole"][0], "y": u["pole"][1]})
    print(f"units {len(keep)} of {2 * n} (north {sum(u['side'] == 'N' for u in keep)}, south {sum(u['side'] == 'S' for u in keep)}), entities {len(ents)}")
    res = tools["place_entities"](json.dumps(ents), surface="fulgora", dry_run=not apply)
    print(res[:1500])
    if apply and mods:
        need = len(keep) * mods
        code = ("local f=game.forces.player local got=0 for _,net in pairs(f.logistic_networks.nauvis) do if got<%d then got=got+net.remove_item({name='speed-module-2',count=%d-got,quality='normal'}) end end "
                "local put=0 for _,d in pairs(game.surfaces.fulgora.find_entities_filtered{name='electric-mining-drill',area={{%d,-94},{%d,-87}}}) do local inv=d.get_module_inventory() local room=math.min(%d,#inv)-inv.get_item_count() "
                "if room>0 and got-put>0 then put=put+inv.insert{name='speed-module-2',count=math.min(room,got-put)} end end "
                "if got>put then for _,net in pairs(f.logistic_networks.nauvis) do if got>put then put=put+net.insert({name='speed-module-2',count=got-put}) end end end rcon.print('modules taken '..got..' placed or returned '..put)")
        print(lua(code % (need, need, X0, X0 + 3 * n, mods)))


if __name__ == "__main__":
    main()
