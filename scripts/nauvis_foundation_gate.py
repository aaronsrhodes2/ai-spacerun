#!/usr/bin/env python3
"""Steel reserve gate for the space-platform-foundation cells on Nauvis: science and everything else has first call on steel.

Every inserter that feeds a foundation assembler from its requester chest gets a logistic-network condition (no wires): it only works
while the network holds more than RESERVE steel plate. The cells stay; their chests still hold their small request (100 steel each).

Usage: nauvis_foundation_gate.py [status | apply [RESERVE] | off]     (default status; RESERVE default 20000)"""
import sys

from _game import tools

HEAD = ("local s=game.surfaces.nauvis local n,g=0,0 local o={} "
        "for _,m in pairs(s.find_entities_filtered{type='assembling-machine'}) do local r=m.get_recipe() if r and r.name=='space-platform-foundation' then n=n+1 "
        "for _,i in pairs(s.find_entities_filtered{type='inserter',area={{m.position.x-3,m.position.y-3},{m.position.x+3,m.position.y+3}}}) do "
        "if i.drop_target==m then local cb=i.get_or_create_control_behavior() ")
TAIL = " end end end end "
APPLY = HEAD + ("cb.connect_to_logistic_network=true cb.logistic_condition={first_signal={type='item',name='steel-plate'},comparator='>',constant=RESERVE} g=g+1"
                ) + TAIL + "rcon.print('foundation machines '..n..', feeding inserters gated on steel > RESERVE: '..g)"
OFF = HEAD + "cb.connect_to_logistic_network=false g=g+1" + TAIL + "rcon.print('foundation machines '..n..', gates removed: '..g)"
STATUS = HEAD + ("if cb.connect_to_logistic_network then g=g+1 o[cb.logistic_condition.constant]=true end"
                 ) + TAIL + ("local c={} for k in pairs(o) do c[#c+1]=k end local E=defines.entity_status local w=0 "
                             "for _,m in pairs(s.find_entities_filtered{type='assembling-machine'}) do local r=m.get_recipe() if r and r.name=='space-platform-foundation' and m.status==E.working then w=w+1 end end "
                             "local ln=s.find_logistic_network_by_position({-178,-200},game.forces.player) "
                             "rcon.print('foundation machines '..n..' (working '..w..'), gated inserters '..g..', reserve '..table.concat(c,',')..', network steel '..ln.get_item_count('steel-plate')..', foundations '..ln.get_item_count('space-platform-foundation'))")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "apply":
        reserve = sys.argv[2] if len(sys.argv) > 2 else "20000"
        print(tools["run_lua"](APPLY.replace("RESERVE", reserve)))
    elif cmd == "off":
        print(tools["run_lua"](OFF))
    print(tools["run_lua"](STATUS))


if __name__ == "__main__":
    main()
