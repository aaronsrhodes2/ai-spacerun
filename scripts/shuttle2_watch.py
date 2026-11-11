"""
Watches scheduled build_shuttle2 ships: every --every seconds rebuilds what asteroids broke (free in friendly build mode) and prints where each ship is,
its speed, and the half-totals the schedule reads (fuel, oxidizer, water of one tank each) plus hub magazines,
accumulator charge and how many machines are short of power.

Usage: scripts/shuttle2_watch.py [--platforms 5,6,7] [--every 15] [--minutes 5]
"""
import sys
import time

from _game import tools

LUA = ("local o={} for _,i in pairs({%s}) do local p=game.forces.player.platforms[i] local s=p.surface local r=0 local hit={} for pass=1,12 do local did=0 "
       "for _,g in pairs(s.find_entities_filtered{type={'tile-ghost','entity-ghost'}}) do if g.valid then local w=(g.type=='tile-ghost' and 't' or g.ghost_name)..'@'..math.floor(g.position.x)..','..math.floor(g.position.y) if g.revive() then r=r+1 did=did+1 hit[#hit+1]=w end end end if did==0 then break end end "
       "local n=p.hub.get_circuit_network(defines.wire_connector_id.circuit_green) local function g(t,k) return n and n.get_signal({type=t,name=k}) or -1 end "
       "o[#o+1]=i..' '..(p.space_location and p.space_location.name or 'flying')..' '..string.format('%%.0f',p.speed*60)..'km/s next='..p.schedule.records[p.schedule.current].station"
       "..' fuel '..g('fluid','thruster-fuel')..' ox '..g('fluid','thruster-oxidizer')..' water '..g('fluid','water')..' mags '..g('item','firearm-magazine')..' rebuilt '..r..(r>0 and ' ['..table.concat(hit,' ')..']' or '') "
       "local e,c,low=0,0,0 for _,a in pairs(s.find_entities_filtered{name='accumulator'}) do e=e+a.energy c=c+a.electric_buffer_size end "
       "for _,x in pairs(s.find_entities_filtered{type={'assembling-machine','furnace','asteroid-collector','inserter'}}) do if x.status==defines.entity_status.low_power or x.status==defines.entity_status.no_power then low=low+1 end end "
       "if c>0 then o[#o]=o[#o]..' accu '..math.floor(e/1e6)..'/'..math.floor(c/1e6)..'MJ lowpower '..low end end "
       "rcon.print(table.concat(o,' | '))")


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def main():
    platforms, every, minutes = arg("--platforms", "5,6,7"), arg("--every", 15), arg("--minutes", 5)
    end = time.time() + minutes * 60
    while time.time() < end:
        print(tools["run_lua"](LUA % platforms).strip(), flush=True)
        time.sleep(every)


if __name__ == "__main__":
    main()
