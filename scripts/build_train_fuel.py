"""
Automatic locomotive refuelling at the iron and copper loading stops: on the south side of the rail, a burner inserter takes coal from a
steel chest and drops it into the locomotive. Burner inserters fuel themselves from the coal they move, so no power is needed. Both
locomotives of each train are covered (front and rear positions at the load stop; the train swaps ends at the unload stop).
The chests are stocked from coal already in the factory's storage chests (about 800 each).
Usage: scripts/build_train_fuel.py [--build]
"""
import json
import sys

from _game import tools

from bridge.factorio.planner import batches

S_ = 8
SPOTS = [  # (x tile, rail row south edge y tile of the inserter)
    (-168, -408), (-147, -408),      # iron load: rail rows -410,-409
    (168, -292), (185, -292),        # copper load: rail rows -294,-293
]
COAL_EACH = 800


def main():
    build = "--build" in sys.argv
    ents = []
    for x, y in SPOTS:
        ents.append({"name": "burner-inserter", "x": x + 0.5, "y": y + 0.5, "direction": S_})     # picks the chest (south), drops north
        ents.append({"name": "steel-chest", "x": x + 0.5, "y": y + 1.5, "direction": 0})
    for part in batches(ents):
        r = json.loads(tools["place_entities"](json.dumps(part), dry_run=True))
        if r.get("error") or r["failed"]:
            raise SystemExit(f"dry run failed: {json.dumps(r)[:1200]}")
    print("dry run clean", len(ents))
    if not build:
        return
    print(tools["save_game"]("before-train-fuel"))
    print(tools["place_entities"](json.dumps(ents)))
    print(tools["run_lua"](" ".join(f"""
local s=game.surfaces.nauvis
local need={COAL_EACH * len(SPOTS)}
local got=0
for _,c in pairs(s.find_entities_filtered{{type='container'}}) do
  if got<need and not (c.name=='steel-chest' and c.position.y>-300 and false) then
    local inv=c.get_inventory(defines.inventory.chest)
    local n=inv.get_item_count('coal')
    if n>500 and c.position.x>-400 and c.position.y>-120 then
      local take=math.min(n-100,need-got)
      got=got+inv.remove{{name='coal',count=take}}
    end
  end
end
local spots={{{",".join(f"{{{x},{y}}}" for x, y in SPOTS)}}}
local per=math.floor(got/#spots)
for _,p in pairs(spots) do
  local chest=s.find_entity('steel-chest',{{p[1]+0.5,p[2]+1.5}})
  chest.get_inventory(defines.inventory.chest).insert{{name='coal',count=per}}
  local bi=s.find_entity('burner-inserter',{{p[1]+0.5,p[2]+0.5}})
  bi.get_fuel_inventory().insert{{name='coal',count=5}}
end
rcon.print('coal moved '..got..', per chest '..per)""".splitlines())))


if __name__ == "__main__":
    main()
