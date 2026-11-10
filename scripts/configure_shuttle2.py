"""
Wires and sets up a ship built by build_shuttle2.py (2026-11-10). Safe to run again.

    hub reads its contents onto a red wire
    chunk inserter takes only the chunk types the hub holds fewer than CHUNKS of (three deciders, green wire, set-filters)
    metallic crusher input runs while iron ore < ORE; furnace inputs while iron plates < PLATES; magazines leave the assembler while < MAGS
    the two chunk-back inserters and the two ammunition belt inserters get fixed filters
    the reactor's fuel inserter runs while the reactor is cooler than TEMP
    the furnace inputs take iron ore only (otherwise they smelt the hub's plates into steel)
    the fuel and oxidizer plants are fed only while the water tanks hold more than RESERVE, so the reactor never runs dry

Run it BEFORE anything is put in the hub: until the filters are set the two ammunition belt inserters carry whatever the hub holds.

Usage: scripts/configure_shuttle2.py --surface platform-3 --platform 5
"""
import sys

from _game import tools

# the hub has 59 slots and a chunk takes a whole slot, so the limits are small: about 12 slots of chunks, 4 ore, 2 plates, 20 magazines, 5 fuel cells
CHUNKS, ORE, PLATES, MAGS, TEMP, RESERVE = 3, 200, 200, 2000, 600, 5000

LUA = """
local s=game.surfaces['%(surface)s'] local p=game.forces.player.platforms[%(platform)d] local hub=p.hub local o={}
local W=defines.wire_connector_id
local function at(x,y,t) return s.find_entities_filtered{position={x+0.5,y+0.5},type=t}[1] end
local function wire(a,ia,b,ib) a.get_wire_connector(ia,true).connect_to(b.get_wire_connector(ib,true),false) end
local function try(n,f) local ok,err=pcall(f) o[#o+1]=n..'='..(ok and 'ok' or tostring(err)) end
try('hub',function() hub.get_or_create_control_behavior().read_contents=true end)
local function gate(x,y,sig,n,prev) local e=at(x,y,'inserter') local cb=e.get_or_create_control_behavior() cb.circuit_enable_disable=true
 cb.circuit_condition={first_signal={type='item',name=sig},comparator='<',constant=n} wire(prev,W.circuit_red,e,W.circuit_red) return e end
try('gates',function() local a=gate(-5,-3,'iron-ore',%(ore)d,hub) gate(-5,0,'iron-plate',%(plates)d,a)
 local b=gate(4,-3,'iron-plate',%(plates)d,hub) gate(4,2,'firearm-magazine',%(mags)d,b) end)
local function filt(x,y,item) local e=at(x,y,'inserter') e.use_filters=true e.inserter_filter_mode='whitelist' e.set_filter(1,item) end
try('filters',function() filt(-2,4,'oxide-asteroid-chunk') filt(2,4,'carbonic-asteroid-chunk') filt(4,-4,'firearm-magazine') filt(-1,4,'firearm-magazine') end)
try('furnace ore only',function() filt(-5,0,'iron-ore') filt(4,-3,'iron-ore') end)
try('water reserve',function() local tank=at(6,9,'storage-tank') local prev=tank for _,q in pairs({{1,7},{-3,7},{-5,3}}) do local e=at(q[1],q[2],'inserter')
 wire(prev,W.circuit_green,e,W.circuit_green) prev=e end
 for _,q in pairs({{1,7},{-5,3}}) do local cb=at(q[1],q[2],'inserter').get_or_create_control_behavior() cb.circuit_enable_disable=true
  cb.circuit_condition={first_signal={type='fluid',name='water'},comparator='>',constant=%(reserve)d} end end)
try('chunks',function() local ci=at(-5,-4,'inserter') ci.use_filters=true ci.inserter_filter_mode='whitelist' ci.get_or_create_control_behavior().circuit_set_filters=true
 local prev_in,prev_out=hub,ci local kinds={'metallic-asteroid-chunk','oxide-asteroid-chunk','carbonic-asteroid-chunk'}
 for i,y in pairs({-5,-7,-9}) do local d=s.find_entities_filtered{position={-4.5,y},type='decider-combinator'}[1] local c=kinds[i]
  d.get_or_create_control_behavior().parameters={conditions={{first_signal={type='item',name=c},comparator='<',constant=%(chunks)d}},outputs={{signal={type='item',name=c},copy_count_from_input=false,constant=1}}}
  wire(prev_in,(prev_in==hub) and W.circuit_red or W.combinator_input_red,d,W.combinator_input_red)
  wire(prev_out,(prev_out==ci) and W.circuit_green or W.combinator_output_green,d,W.combinator_output_green) prev_in=d prev_out=d end end)
try('reactor',function() local r=s.find_entities_filtered{name='nuclear-reactor'}[1] local cb=r.get_or_create_control_behavior() cb.read_temperature=true cb.temperature_signal={type='virtual',name='signal-T'}
 local e=at(0,-5,'inserter') local ib=e.get_or_create_control_behavior() ib.circuit_enable_disable=true ib.circuit_condition={first_signal={type='virtual',name='signal-T'},comparator='<',constant=%(temp)d}
 wire(r,W.circuit_green,e,W.circuit_green) end)
rcon.print(table.concat(o,' | '))
"""


def main():
    surface = sys.argv[sys.argv.index("--surface") + 1]
    platform = int(sys.argv[sys.argv.index("--platform") + 1])
    code = LUA % dict(surface=surface, platform=platform, chunks=CHUNKS, ore=ORE, plates=PLATES, mags=MAGS, temp=TEMP, reserve=RESERVE)
    print(tools["run_lua"](" ".join(code.split())).strip())


if __name__ == "__main__":
    main()
