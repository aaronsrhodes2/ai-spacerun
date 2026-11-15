import sys
import time

from _game import tools
ITEM, SLOT = sys.argv[1], int(sys.argv[2])
FIND = "local s=game.surfaces.nauvis local c=s.find_entities_filtered{name='requester-chest',position={-337.5,-239.5},radius=0.4}[1] "
print("stock:", tools["run_lua"]("local s=game.surfaces.nauvis local rp=s.find_entities_filtered{name='roboport',position={-352,-229},radius=1}[1] rcon.print(rp.logistic_network.get_item_count('%s'))" % ITEM))
t0 = int(tools["run_lua"](FIND + "local lp=c.get_logistic_point(defines.logistic_member_index.logistic_container) local se=lp.get_section(1) se.set_slot(%d,{value={type='item',name='%s',quality='normal'},min=1}) rcon.print(game.tick)" % (SLOT, ITEM)))
PROBE = ("local s=game.surfaces.nauvis local W=defines.wire_connector_id local o={} for u=0,2 do local sel=s.find_entities_filtered{name='selector-combinator',position={-354+7*u+6.5,-223},radius=0.4}[1] "
         "local n=sel.get_circuit_network(W.combinator_output_green) o[#o+1]=(n and n.signals and n.signals[1]) and n.signals[1].signal.name or '-' end rcon.print(game.tick..' '..table.concat(o,' '))")
end = time.time() + 100
while time.time() < end:
    r = tools["run_lua"](PROBE).split()
    if ITEM in r[1:]:
        print("picked after %d ticks (%.1f game s) by machine %d; choices %s" % (int(r[0]) - t0, (int(r[0]) - t0) / 60, r[1:].index(ITEM) + 1, r[1:]))
        break
else:
    print("not picked within 100 s real; last", r)
