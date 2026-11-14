#!/usr/bin/env python3
"""Calls one Skippy Copilot tool on the local test server (never the live game) and prints the answer.
The server is a second, headless copy of the Steam install with its own data folder under .testserver/ (see docs/solver-plan.md).
Usage: modtest.py tools | modtest.py <tool> ['<json arguments>'] | modtest.py --lua '<lua>'"""
import json
import pathlib
import sys

import factorio_rcon

ROOT = pathlib.Path(__file__).resolve().parent.parent
PORT = 27116


def client():
    return factorio_rcon.RCONClient("127.0.0.1", PORT, (ROOT / ".testserver" / "rcon.pw").read_text().strip())


def call(tool, args=None, c=None):
    c = c or client()
    out = c.send_command("/skippy %s %s" % (tool, json.dumps(args) if args else "")) or ""
    return json.loads(out) if out.strip() else {"ok": False, "error": "empty reply"}


if __name__ == "__main__":
    if sys.argv[1] == "--lua":
        print(client().send_command("/sc " + sys.argv[2]))
    else:
        r = call(sys.argv[1], json.loads(sys.argv[2]) if len(sys.argv) > 2 else None)
        if isinstance(r.get("result"), dict) and "picture" in r["result"]:
            print(r["result"].pop("picture"))
        print(json.dumps(r, indent=1)[:6000])
