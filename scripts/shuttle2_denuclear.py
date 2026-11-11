"""
Takes the nuclear plant off a ship built by build_shuttle2.py before 2026-11-10 (the Captain's order: solar and accumulators instead).
Removes the reactor, heat exchanger, turbine, the two fuel cell inserters and the water riser to the heat exchanger; whatever the reactor
holds goes back to the hub. Run it with the ship parked and paused, then build_shuttle2.py --apply and configure_shuttle2.py.

Usage: scripts/shuttle2_denuclear.py --surface platform-3 --platform 5
"""
import sys

from _game import tools

LUA = """
local s=game.surfaces['%(surface)s'] local p=game.forces.player.platforms[%(platform)d] local hub=p.hub.get_inventory(defines.inventory.hub_main) local n,moved=0,0
if p.space_location==nil or not p.paused then rcon.print('refused: ship must be parked and paused') return end
for _,r in pairs(s.find_entities_filtered{name='nuclear-reactor'}) do for _,id in pairs({defines.inventory.fuel,defines.inventory.burnt_result}) do local inv=r.get_inventory(id)
 if inv then for i=1,#inv do local st=inv[i] if st.valid_for_read then moved=moved+hub.insert(st) end end end end end
for _,e in pairs(s.find_entities_filtered{name={'nuclear-reactor','heat-exchanger','steam-turbine'}}) do e.destroy() n=n+1 end
local function kill(x,y,t) for _,e in pairs(s.find_entities_filtered{position={x+0.5,y+0.5},type=t}) do e.destroy() n=n+1 end end
kill(0,-5,'inserter') kill(-1,-5,'inserter') for y=-11,7 do kill(8,y,'pipe') end kill(7,-11,'pipe') kill(3,-11,'pipe') kill(2,-11,'pipe') kill(6,-11,'pipe-to-ground') kill(4,-11,'pipe-to-ground')
rcon.print('removed '..n..' entities, moved '..moved..' items to the hub')
"""


def main():
    surface = sys.argv[sys.argv.index("--surface") + 1]
    platform = int(sys.argv[sys.argv.index("--platform") + 1])
    print(tools["run_lua"](" ".join((LUA % dict(surface=surface, platform=platform)).split())).strip())


if __name__ == "__main__":
    main()
