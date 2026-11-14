#!/usr/bin/env python3
"""Run a Lua file (newlines joined to one line) over RCON: _aq_lua.py file.lua. Scratch helper for the Aquilo cryogenic work."""
import sys

from _game import tools

src = open(sys.argv[1], encoding="utf-8").read()
lua = " ".join(l.strip() for l in src.splitlines() if l.strip())
for i, a in enumerate(sys.argv[2:], 1):
    lua = lua.replace("$%d" % i, a)
print(tools["run_lua"](lua))
