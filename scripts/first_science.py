"""
The first red packs. Assemblers aren't unlocked until 10 packs have been researched,
so the first packs are hand-crafted by the player's character, from plates taken off
the factory's own belts. Crafting a lab is also what unlocks red science.
"""
import json
import sys
import time

from _game import tools

PLAYER = "aaronsrhodes"
PACKS = 20  # automation (10) + gun-turret (10)


def lua(code):
    return tools["run_lua"](" ".join(code.splitlines()))


def give_plates(iron, copper):
    """Move real plates from the belts to the player. Nothing is created."""
    print(lua(f"""
        local s = game.surfaces.nauvis
        local p = game.players['{PLAYER}']
        local function take(name, want, y)
          local got = 0
          for x = -36, -65, -1 do
            local b = s.find_entity('transport-belt', {{x+0.5, y+0.5}})
            if b and got < want then
              for i = 1, 2 do
                local n = b.get_transport_line(i).remove_item{{name=name, count=want-got}}
                got = got + n
              end
            end
          end
          if got > 0 then p.get_main_inventory().insert{{name=name, count=got}} end
          return got
        end
        rcon.print(helpers.table_to_json({{iron=take('iron-plate', {iron}, -56), copper=take('copper-plate', {copper}, -57)}}))
    """))


def craft(recipe, count):
    print(recipe, lua(f"""
        local p = game.players['{PLAYER}']
        rcon.print(p.begin_crafting{{recipe='{recipe}', count={count}}})
    """))


def state():
    return json.loads(lua(f"""
        local f = game.forces.player
        local p = game.players['{PLAYER}']
        rcon.print(helpers.table_to_json({{
          unlocked=f.technologies['automation-science-pack'].researched,
          queue=p.crafting_queue_size,
          packs=p.get_main_inventory().get_item_count('automation-science-pack'),
          labs=p.get_main_inventory().get_item_count('lab'),
          iron=p.get_main_inventory().get_item_count('iron-plate'),
          copper=p.get_main_inventory().get_item_count('copper-plate')}}))
    """))


def main():
    print(tools["tell_player"]("Borrowing your crafting queue: one lab, then 20 red packs, using plates off the belts. Crafting anything of your own just queues after it."))
    give_plates(36 + PACKS * 2 + 4, 15 + PACKS + 2)
    print(state())
    craft("lab", 1)
    for _ in range(40):
        time.sleep(3)
        s = state()
        if s["unlocked"]:
            break
    print("after lab:", s)
    if not s["unlocked"]:
        sys.exit("lab trigger did not fire")
    craft("automation-science-pack", PACKS)
    print(state())


if __name__ == "__main__":
    main()
