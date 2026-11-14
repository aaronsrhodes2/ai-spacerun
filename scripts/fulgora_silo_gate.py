#!/usr/bin/env python3
"""Fulgora: keep the rocket silo supplied while the electromagnetic pack gate is closed.

The 24 unload inserters at `Scrap Base Unload` (y -106.5) run only while the network holds fewer than 6,000 electromagnetic
packs. With the gate closed no scrap comes in, so the silo (150.5,-170.5) runs out of rocket fuel, low density structure and
processing units, no rocket can lift the packs, and the gate never reopens (found 2026-11-14).

Fix: four of the inserters (one per wagon: x 148.5, 155.5, 162.5, 169.5) follow a decider combinator at (162.5,-102) instead:
  run while  packs in the network < 6000                         (green wire: roboport (144,-96) reads the network)
         OR  a silo requester chest holds < 45 of its item       (red wire: the three chests at (149.5..151.5,-176.5))
Red runs chest -> substations (159,-179), (160,-160), (160,-140), (160,-120), (160,-100) -> combinator input.
Green runs roboport -> substations (140,-100), (160,-100) -> combinator input.
The output (signal-check = 1) goes by red wire from the combinator output straight to the four inserters.
A cut wire reads as 0, so it fails open (intake runs), never shut.

Usage: fulgora_silo_gate.py dry | apply | status | watch [seconds]"""
import json
import sys
import time

from _game import tools

SURFACE = "fulgora"
COMB = {"name": "decider-combinator", "x": 162.5, "y": -102.0, "direction": 0, "params": {"quality": "epic"}}
LEVEL = 45

WIRE = r'''
local s = game.surfaces['fulgora']
local W = defines.wire_connector_id
local function one(t, x, y) local l = s.find_entities_filtered{type = t, position = {x, y}, radius = 0.6} if #l ~= 1 then error(t .. ' at ' .. x .. ',' .. y .. ' found ' .. #l) end return l[1] end
local function link(a, ida, b, idb) local ca = a.get_wire_connector(ida, true) local cb = b.get_wire_connector(idb, true) if not ca.is_connected_to(cb) then if not ca.connect_to(cb) then error('wire failed ' .. a.name .. ' ' .. a.position.x .. ',' .. a.position.y .. ' -> ' .. b.name .. ' ' .. b.position.x .. ',' .. b.position.y) end end end
local comb = one('decider-combinator', 162.5, -102)
local chests = {one('logistic-container', 149.5, -176.5), one('logistic-container', 150.5, -176.5), one('logistic-container', 151.5, -176.5)}
local subs = {one('electric-pole', 159, -179), one('electric-pole', 160, -160), one('electric-pole', 160, -140), one('electric-pole', 160, -120), one('electric-pole', 160, -100)}
local port = one('roboport', 144, -96)
local sub_w = one('electric-pole', 140, -100)
local ins = {one('inserter', 162.5, -106.5), one('inserter', 155.5, -106.5), one('inserter', 148.5, -106.5), one('inserter', 169.5, -106.5)}
link(chests[1], W.circuit_red, chests[2], W.circuit_red)
link(chests[2], W.circuit_red, chests[3], W.circuit_red)
link(chests[3], W.circuit_red, subs[1], W.circuit_red)
for i = 1, 4 do link(subs[i], W.circuit_red, subs[i + 1], W.circuit_red) end
link(subs[5], W.circuit_red, comb, W.combinator_input_red)
port.get_or_create_control_behavior().read_items_mode = defines.control_behavior.roboport.read_items_mode.logistics
link(port, W.circuit_green, sub_w, W.circuit_green)
link(sub_w, W.circuit_green, subs[5], W.circuit_green)
link(subs[5], W.circuit_green, comb, W.combinator_input_green)
local R = {red = true, green = false}
local G = {red = false, green = true}
local function it(n) return {type = 'item', name = n} end
comb.get_or_create_control_behavior().parameters = {
  conditions = {
    {first_signal = it('electromagnetic-science-pack'), comparator = '<', constant = 6000, first_signal_networks = G},
    {first_signal = it('rocket-fuel'), comparator = '<', constant = LEVEL, first_signal_networks = R, compare_type = 'or'},
    {first_signal = it('low-density-structure'), comparator = '<', constant = LEVEL, first_signal_networks = R, compare_type = 'or'},
    {first_signal = it('processing-unit'), comparator = '<', constant = LEVEL, first_signal_networks = R, compare_type = 'or'}
  },
  outputs = {{signal = {type = 'virtual', name = 'signal-check'}, copy_count_from_input = false, constant = 1}}
}
link(comb, W.combinator_output_red, ins[1], W.circuit_red)
link(ins[1], W.circuit_red, ins[2], W.circuit_red)
link(ins[2], W.circuit_red, ins[3], W.circuit_red)
link(ins[1], W.circuit_red, ins[4], W.circuit_red)
for _, e in pairs(ins) do
  local cb = e.get_or_create_control_behavior()
  cb.connect_to_logistic_network = false
  cb.circuit_enable_disable = true
  cb.circuit_condition = {first_signal = {type = 'virtual', name = 'signal-check'}, comparator = '>', constant = 0}
end
game.forces.player.chart(s, {{130, -190}, {180, -90}})
rcon.print('wired')
'''.replace("LEVEL", str(LEVEL))

STATUS = r'''
local s = game.surfaces['fulgora']
local W = defines.wire_connector_id
local E = defines.entity_status
local SN = {}
for k, v in pairs(E) do SN[v] = k end
local o = {}
local comb = s.find_entities_filtered{type = 'decider-combinator', position = {162.5, -102}, radius = 0.6}[1]
if comb then
  local function sig(id, n) local net = comb.get_circuit_network(id) return net and net.get_signal({type = 'item', name = n}) or 'nowire' end
  o[#o + 1] = 'combinator ' .. (SN[comb.status] or comb.status) .. ' green packs=' .. sig(W.combinator_input_green, 'electromagnetic-science-pack') .. ' red rocket-fuel=' .. sig(W.combinator_input_red, 'rocket-fuel') .. ' lds=' .. sig(W.combinator_input_red, 'low-density-structure') .. ' pu=' .. sig(W.combinator_input_red, 'processing-unit')
  local on = comb.get_circuit_network(W.combinator_output_red)
  o[#o + 1] = 'output signal-check=' .. (on and on.get_signal({type = 'virtual', name = 'signal-check'}) or 'nowire')
else o[#o + 1] = 'no combinator' end
local t = {}
for _, e in pairs(s.find_entities_filtered{type = 'inserter', area = {{144, -107}, {172, -106}}}) do
  local wired = e.get_wire_connector(W.circuit_red, false)
  local k = ((wired and wired.connection_count > 0) and 'silo-gate ' or 'pack-gate ') .. (SN[e.status] or e.status)
  t[k] = (t[k] or 0) + 1
end
for k, v in pairs(t) do o[#o + 1] = 'unload inserters ' .. k .. ' x' .. v end
local silo = s.find_entities_filtered{type = 'rocket-silo'}[1]
local inv = silo.get_inventory(defines.inventory.crafter_input)
local have = {}
for _, i in pairs(inv.get_contents()) do have[#have + 1] = i.name .. '=' .. i.count end
o[#o + 1] = 'silo ' .. (SN[silo.status] or silo.status) .. ' parts=' .. silo.rocket_parts .. ' in[' .. table.concat(have, ' ') .. '] made=' .. silo.products_finished
for _, c in pairs(s.find_entities_filtered{type = 'logistic-container', area = {{149, -177}, {152, -176}}}) do
  local h = {}
  for _, i in pairs(c.get_inventory(defines.inventory.chest).get_contents()) do h[#h + 1] = i.name .. '=' .. i.count end
  o[#o + 1] = 'silo chest ' .. c.position.x .. ' [' .. table.concat(h, ' ') .. ']'
end
local rf = s.find_entities_filtered{type = 'assembling-machine', position = {111.5, -133.5}, radius = 0.6}[1]
if rf then o[#o + 1] = 'rocket fuel assembler ' .. (SN[rf.status] or rf.status) .. ' solid-fuel=' .. rf.get_inventory(defines.inventory.crafter_input).get_item_count('solid-fuel') .. ' made=' .. rf.products_finished end
local n = s.find_logistic_network_by_position({150, -146}, 'player')
local c = {}
for _, w in pairs({'electromagnetic-science-pack', 'scrap', 'solid-fuel', 'rocket-fuel', 'low-density-structure', 'processing-unit', 'stone', 'ice', 'steel-plate'}) do c[#c + 1] = w .. '=' .. n.get_item_count(w) end
o[#o + 1] = 'network ' .. table.concat(c, ' ')
local m = {}
for _, e in pairs(s.find_entities_filtered{type = {'assembling-machine', 'recycler', 'mining-drill'}}) do
  local rn = e.type
  if e.type == 'assembling-machine' then local r = e.get_recipe() rn = r and r.name or 'none' end
  if rn == 'electromagnetic-science-pack' or rn == 'electrolyte' or rn == 'recycler' or rn == 'mining-drill' then
    local k = rn .. ' ' .. (SN[e.status] or e.status)
    m[k] = (m[k] or 0) + 1
  end
end
for k, v in pairs(m) do o[#o + 1] = v .. 'x ' .. k end
local w = 0
for _, e in pairs(s.find_entities_filtered{type = 'cargo-wagon'}) do w = w + e.get_item_count('scrap') end
local acc, cap = 0, 0
local p = s.find_entities_filtered{type = 'electric-pole', position = {160, -100}, radius = 1}[1]
for _, a in pairs(s.find_entities_filtered{type = 'accumulator'}) do if a.electric_network_id == p.electric_network_id then acc = acc + a.energy cap = cap + a.electric_buffer_size end end
o[#o + 1] = 'scrap in wagons=' .. w .. ' accumulators MJ ' .. math.floor(acc / 1e6) .. ' of ' .. math.floor(cap / 1e6) .. ' tick=' .. game.tick
rcon.print(table.concat(o, '\n'))
'''


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "dry":
        print(tools["place_entities"](json.dumps([COMB]), surface=SURFACE, dry_run=True, clear_trees=False))
    elif cmd == "apply":
        has = tools["run_lua"]("rcon.print(#game.surfaces['fulgora'].find_entities_filtered{type='decider-combinator', position={162.5,-102}, radius=0.6})").strip()
        if has == "0":
            print(tools["save_game"]("skippy"))
            res = json.loads(tools["place_entities"](json.dumps([COMB]), surface=SURFACE))
            print("placed", res.get("placed"), "failed", res.get("failed"))
            if res.get("failed"):
                return
        print(tools["run_lua"](WIRE))
        print(tools["run_lua"](STATUS))
    elif cmd == "watch":
        secs = int(sys.argv[2]) if len(sys.argv) > 2 else 90
        end = time.time() + secs
        while True:
            print(tools["run_lua"](STATUS))
            if time.time() + 30 > end:
                break
            print("---")
            time.sleep(30)
    else:
        print(tools["run_lua"](STATUS))


if __name__ == "__main__":
    main()
