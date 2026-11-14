"""Dump a platform's schedule records in full. Usage: _sched.py "Nauvis-Gleba 2" """
import sys

from _game import tools

LUA = """
local f=game.forces.player local o={} for i,p in pairs(f.platforms) do if p.name:find('%s',1,true) then
o[#o+1]='#'..i..' state '..p.state..' paused '..tostring(p.paused)..' can_leave '..tostring(p.can_leave_current_location())..' tick '..game.tick
o[#o+1]=serpent.line(p.schedule) local sc=p.get_schedule and p.get_schedule() if sc then o[#o+1]='group '..tostring(sc.group)..' interrupts '..sc.interrupt_count end end end rcon.print(table.concat(o,'|'))
"""
print(tools["run_lua"](" ".join((LUA % sys.argv[1]).split())).replace("|", "\n"))
