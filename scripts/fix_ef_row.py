"""Move the electric-furnace west row from y0=-85 to y0=-84 (its tap splitter at (72,-80) sat on the AC give target)."""
import json
import sys

sys.path.insert(0, ".")
from _game import tools

from bridge.factorio import bus, westbus
from bridge.factorio.blocks import assembler_row
from bridge.factorio.planner import batches

X = 98


def ef_entities(y0):
    ents = assembler_row(X, y0, "electric-furnace", 1, o_west=True).entities
    taps = [(7, y0 + 6), (2, y0 + 7)]
    ents += [e for k, y in taps for e in bus.tap(k, y, X)]
    ents += bus.give(2, y0, X - 1)
    split = [e for e in bus.trunk_entities(taps) if e["name"] == "splitter"]
    return westbus.mirror(ents), westbus.mirror(split), taps


def main():
    old, old_split, old_taps = ef_entities(-85)
    pts = [(e["x"], e["y"], e["name"]) for e in old + old_split]
    lua = "local s=game.surfaces.nauvis local n=0 local pts={" + ",".join(f"{{{x},{y}}}" for x, y, _ in pts) + "} " \
          "for _,p in pairs(pts) do for _,e in pairs(s.find_entities_filtered{position=p,radius=0.6,type={'assembling-machine','inserter','transport-belt','underground-belt','splitter','electric-pole'}}) do " \
          "if not (e.type=='electric-pole' and false) then e.destroy() n=n+1 end end end rcon.print(n)"
    print(tools["save_game"]("before-ef-fix"))
    print("destroyed", tools["run_lua"](lua))
    # restore trunk belts where splitters were
    restore = []
    for kv, y in old_taps:
        x, ty = westbus.real_splitter_tile(kv, y)
        restore.append({"name": "transport-belt", "x": x + 0.5, "y": ty + 0.5, "direction": 8})
    print("restore", tools["place_entities"](json.dumps(restore)))
    new, new_split, new_taps = ef_entities(-84)
    for kv, y in new_taps:
        x, ty = westbus.real_splitter_tile(kv, y)
        tools["remove_entities"](x + 0.2, ty + 0.2, x + 0.8, ty + 0.8, names="transport-belt")
    for part in batches(new + new_split):
        r = json.loads(tools["place_entities"](json.dumps(part)))
        print("placed", r.get("placed"), r.get("failed"))


if __name__ == "__main__":
    main()
