"""Capture one wild spawner with a real capture-robot-rocket so the game itself fires the
`capture-spawner` research trigger (biter-egg-handling). Never writes research state.

  python capture_spawner.py study     # trigger prototype, recipe, candidate spawner
  python capture_spawner.py status    # tech state, spawner state, captive spawners
  python capture_spawner.py capture [--apply]   # dry run unless --apply

Method: take ONE factory-made capture-robot-rocket from the player's inventory (moved, not
created), then create the game's own `capture-robot-rocket` projectile entity next to the
target spawner with target=spawner, force=player. The projectile prototype's own action
(capture logic) runs inside the game. The tech is only ever read.
"""
import sys
from _game import tools

TARGET = (151.5, -2303.5)   # isolated nest edge, ~2.3k tiles from any player structure
TECH = "biter-egg-handling"


def lua(code):
    return tools["run_lua"](code)


def study():
    print(lua("rcon.print(serpent.line(prototypes.technology['%s'].research_trigger)) rcon.print(serpent.line(prototypes.recipe['capture-robot-rocket'].ingredients))" % TECH))


def status():
    print(lua("local f=game.forces.player rcon.print('researched '..tostring(f.technologies['%s'].researched)) local s=game.surfaces.nauvis local c=s.find_entities_filtered{name='captive-biter-spawner'} rcon.print('captive spawners '..#c) for _,e in pairs(c) do rcon.print(e.name..' '..serpent.line(e.position)..' hp '..e.health) end local w=s.find_entities_filtered{type='unit-spawner',position={%s,%s},radius=6} for _,e in pairs(w) do rcon.print(e.name..' '..serpent.line(e.position)..' hp '..e.health) end" % (TECH, TARGET[0], TARGET[1])))


def capture(apply):
    if not apply:
        print("dry run: would remove 1 capture-robot-rocket (rare) from the player and fire projectile at", TARGET)
        return
    tools["save_game"]("skippy")
    code = (
        "local s=game.surfaces.nauvis local pl=game.connected_players[1] "
        "local tgt=s.find_entities_filtered{type='unit-spawner',position={%s,%s},radius=3}[1] "
        "if not tgt then rcon.print('no spawner') return end "
        "local q={name='capture-robot-rocket',quality='rare'} "
        "if pl.get_item_count(q)<1 then rcon.print('no rocket') return end "
        "pl.remove_item{name='capture-robot-rocket',quality='rare',count=1} "
        "local p=s.create_entity{name='capture-robot-rocket',position={tgt.position.x,tgt.position.y+12},target=tgt,force='player',speed=0.3} "
        "rcon.print('fired '..tostring(p and p.valid)..' at '..tgt.name..' '..serpent.line(tgt.position))"
    ) % TARGET
    print(lua(code))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    {"study": study, "status": status}.get(cmd, lambda: capture("--apply" in sys.argv))()
