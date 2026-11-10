"""
One-line readout of a build_shuttle2 ship: hub stock, tanks, turret magazines, reactor, machine states.
Usage: scripts/shuttle2_status.py --surface platform-3 --platform 5
"""
import sys

from _game import tools

LUA = """
local s=game.surfaces['%(surface)s'] local p=game.forces.player.platforms[%(platform)d] local o={}
local function at(x,y,n) return s.find_entities_filtered{position={x+0.5,y+0.5},name=n}[1] end
local function fl(e) local t=0 for _,v in pairs(e.get_fluid_contents()) do t=t+v end return math.floor(t) end
local h={} for _,it in pairs(p.hub.get_inventory(defines.inventory.hub_main).get_contents()) do h[#h+1]=it.name:gsub('asteroid%%-chunk','ch'):gsub('uranium%%-',''):gsub('firearm%%-','')..':'..it.count end
o[#o+1]='hub '..table.concat(h,' ')
o[#o+1]='water '..(fl(at(6,9,'storage-tank'))+fl(at(10,9,'storage-tank')))..' fuel '..(fl(at(6,14,'storage-tank'))+fl(at(10,14,'storage-tank')))..' ox '..(fl(at(-7,14,'storage-tank'))+fl(at(-11,14,'storage-tank')))
local t={} for _,e in pairs(s.find_entities_filtered{name='gun-turret'}) do t[#t+1]=e.get_inventory(defines.inventory.turret_ammo).get_item_count() end o[#o+1]='turrets '..table.concat(t,',')
local r=s.find_entities_filtered{name='nuclear-reactor'}[1] o[#o+1]='reactor '..math.floor(r.temperature)..'C fuel '..r.get_fuel_inventory().get_item_count()
local st={} for k,v in pairs(defines.entity_status) do st[v]=k end
local m={} for _,e in pairs(s.find_entities_filtered{type={'assembling-machine','furnace','generator','boiler','asteroid-collector'}}) do
 m[#m+1]=(e.type=='assembling-machine' and e.get_recipe() and e.get_recipe().name or e.name):sub(1,14)..'='..(st[e.status] or '?') end o[#o+1]=table.concat(m,' ')
local en=s.find_entities_filtered{name='steam-turbine'}[1] o[#o+1]='speed '..math.floor(p.speed*60)..' state '..p.state..' weight '..math.floor(p.weight/1000)..'t'
rcon.print(table.concat(o,' | '))
"""


def main():
    surface = sys.argv[sys.argv.index("--surface") + 1]
    platform = int(sys.argv[sys.argv.index("--platform") + 1])
    print(tools["run_lua"](" ".join((LUA % dict(surface=surface, platform=platform)).split())).strip())


if __name__ == "__main__":
    main()
