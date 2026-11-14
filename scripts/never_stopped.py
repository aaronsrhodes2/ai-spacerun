#!/usr/bin/env python3
"""Finds machines that never stopped: samples every crafting machine's status on every surface and reports those that were
working (or low_power, still running) in EVERY sample. Always-working machines are the saturated ones: the source bottlenecks
worth replicating. Read-only on the factory; it keeps a temporary table in `storage` and deletes it at the end.

Factorio keeps no status history, so "never stopped" means "in every sample of this window"; a longer window is more certain.

Usage: scripts/never_stopped.py [seconds] [interval]   (defaults 300 s, every 5 s)
Report is printed and written to scripts/_never_stopped.log"""
import sys
import time

from _game import tools

SECONDS = int(sys.argv[1]) if len(sys.argv) > 1 else 300
INTERVAL = int(sys.argv[2]) if len(sys.argv) > 2 else 5

SAMPLE = r'''
local ns = storage.nostop_r12
if not ns then ns = {n = 0, m = {}}; storage.nostop_r12 = ns end
ns.n = ns.n + 1
local W, L = defines.entity_status.working, defines.entity_status.low_power
local function rn(x)
  for _ = 1, 3 do
    if type(x) == 'string' then return x end
    if x == nil then return '' end
    local ok, v = pcall(function() return x.name end)
    if not ok then return '' end
    x = v
  end
  return type(x) == 'string' and x or ''
end
for _, s in pairs(game.surfaces) do
  for _, e in pairs(s.find_entities_filtered{type = {'assembling-machine', 'furnace', 'chemical-plant', 'oil-refinery', 'lab', 'rocket-silo'}}) do
    local u = e.unit_number
    if u then
      local r = ns.m[u]
      if not r then
        r = {s = s.name, t = e.type, nm = e.name, x = e.position.x, y = e.position.y, rc = '', w = 0, c = 0}
        ns.m[u] = r
      end
      if r.rc == '' then
        local ok, rec = pcall(function() return e.get_recipe() end)
        if ok and rec then r.rc = rn(rec) end
        if r.rc == '' and e.type == 'furnace' then
          local ok2, prev = pcall(function() return e.previous_recipe end)
          if ok2 and prev then r.rc = rn(prev) end
        end
        if r.rc == '' and e.type == 'lab' then r.rc = 'lab' end
      end
      r.c = r.c + 1
      local st = e.status
      if st == W or st == L then r.w = r.w + 1 end
    end
  end
end
rcon.print(ns.n)
'''

REPORT = r'''
local ns = storage.nostop_r12
if not ns then rcon.print('NO DATA'); return end
local g = {}
local total_always, total = 0, 0
for u, r in pairs(ns.m) do
  if r.c >= ns.n * 0.9 then
    total = total + 1
    local key = r.s .. '|' .. (r.rc ~= '' and r.rc or (r.t .. ':' .. r.nm))
    local gr = g[key]
    if not gr then gr = {all = 0, always = 0, ex = nil}; g[key] = gr end
    gr.all = gr.all + 1
    if r.w == r.c then
      gr.always = gr.always + 1
      total_always = total_always + 1
      gr.ex = gr.ex or (string.format('%.0f,%.0f', r.x, r.y))
    end
  end
end
local rows = {}
for k, v in pairs(g) do if v.always > 0 then rows[#rows + 1] = {k = k, a = v.always, n = v.all, ex = v.ex} end end
table.sort(rows, function(a, b) if a.a ~= b.a then return a.a > b.a end return a.k < b.k end)
local o = {'samples ' .. ns.n .. ', machines tracked ' .. total .. ', never stopped ' .. total_always}
for i = 1, math.min(70, #rows) do
  local r = rows[i]
  o[#o + 1] = string.format('%4d of %4d  %s  e.g. %s', r.a, r.n, r.k, r.ex)
end
rcon.print(table.concat(o, '\n'))
'''

CLEAN = "storage.nostop_r12 = nil rcon.print('cleaned')"


def main():
    n = max(2, SECONDS // INTERVAL)
    tools["run_lua"](CLEAN)
    try:
        for i in range(n):
            tools["run_lua"](SAMPLE)
            if i < n - 1:
                time.sleep(INTERVAL)
        report = tools["run_lua"](REPORT)
    finally:
        tools["run_lua"](CLEAN)
    print(report)
    with open("_never_stopped.log", "w") as f:
        f.write(report + "\n")


if __name__ == "__main__":
    main()
