#!/usr/bin/env python3
"""Colour-coded area tags on the map (the Captain, 2026-11-14: "make tags like that for all of the areas in different colors so it's easier to
suss out the factory at sky scale"). One chart tag per area, an icon plus a coloured label, the colour = what the area is for:
  yellow  launch and logistics   silos, landing pads
  blue    science                labs, science lines, pack stops
  green   raw materials, metal   mines, smelters, foundries, oil
  red     ammunition, defence    rocket and ammo lines, explosives
  cyan    automation             the Replicator, the status wall
  white   construction           foundations, concrete, modules, cliffs
  pink    biology                egg farm, spawners, Gleba eggs
  orange  power and heat         reactor, towers, fuel works
Colours are rich-text colours in the label (`[color=#rrggbb]`), icons are the matching colour signals where one exists.
Re-running replaces the tags this script made (a registry in snapshots/map_tags.json) and the four older tags of the status-wall build.
Steps: apply | remove | list.   Usage: map_tags.py apply"""
import json
import os
import sys

from _game import tools

REG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "snapshots", "map_tags.json")

COLORS = {"yellow": ("#ffd54a", "signal-yellow"), "blue": ("#4fa3ff", "signal-blue"), "green": ("#58d66b", "signal-green"),
          "red": ("#ff5a4f", "signal-red"), "cyan": ("#35e0e0", "signal-cyan"), "white": ("#ffffff", "signal-white"),
          "pink": ("#ff6bd5", "signal-pink"), "orange": ("#ff9a3c", "signal-yellow")}

# (surface, x, y, colour, label)
AREAS = [
    # Nauvis
    ("nauvis", -327, -212, "cyan", "REPLICATOR"),
    ("nauvis", -225, -167, "cyan", "STATUS WALL"),
    ("nauvis", -250, -212, "yellow", "ROCKET SILOS"),
    ("nauvis", -216, -228, "yellow", "LANDING PAD"),
    ("nauvis", -275, -180, "white", "CLIFF EXPLOSIVES"),
    ("nauvis", -410, -185, "white", "HAZARD CONCRETE"),
    ("nauvis", -178, -225, "white", "FOUNDATION CELLS"),
    ("nauvis", -121, -466, "white", "MODULE MALL"),
    ("nauvis", -300, -85, "red", "EXPLOSIVE ROCKETS + AMMO"),
    ("nauvis", -423, 283, "green", "STEEL FOUNDRY"),
    ("nauvis", -697, -404, "green", "OIL FIELD WEST"),
    ("nauvis", -330, -255, "green", "REFINERY + PLASTIC"),
    ("nauvis", 151, -2303, "pink", "EGG FARM SITE (captive spawner)"),
    # Gleba
    ("gleba", 124, 32, "blue", "RESEARCH LABS"),
    ("gleba", 95, 12, "pink", "EGG + NUTRIENT CHAMBERS"),
    ("gleba", 143, 3, "yellow", "SILO"),
    ("gleba", 142, 24, "yellow", "LANDING PAD"),
    # Fulgora
    ("fulgora", 155, -106, "green", "SCRAP BASE UNLOAD"),
    ("fulgora", 134, -148, "blue", "ELECTROMAGNETIC SCIENCE"),
    ("fulgora", 150, -171, "yellow", "SILO"),
    ("fulgora", 150, -154, "yellow", "LANDING PAD"),
    ("fulgora", 200, -128, "white", "FOUNDATION CELLS"),
    # Vulcanus
    ("vulcanus", -20, -52, "green", "TUNGSTEN FOUNDRIES"),
    ("vulcanus", -117, -70, "green", "TUNGSTEN ORE UNLOAD"),
    ("vulcanus", -31, -51, "yellow", "SILO"),
    ("vulcanus", -30, -62, "yellow", "LANDING PAD"),
    ("vulcanus", -38, -62, "red", "ARTILLERY SHELL CELL"),
    # Aquilo
    ("aquilo", 22, -14, "orange", "POWER + HEAT"),
    ("aquilo", 32, -3, "orange", "FUEL WORKS"),
    ("aquilo", 1, -26, "white", "ICE PLATFORM WORKS"),
    ("aquilo", -28, -38, "blue", "CRYOGENIC SCIENCE"),
    ("aquilo", -22, -19, "green", "LITHIUM"),
    ("aquilo", -34, -70, "green", "FLUORINE VENT"),
    ("aquilo", -52, 58, "green", "LITHIUM BRINE WELL"),
    ("aquilo", -5, 4, "yellow", "SILO"),
    ("aquilo", 10, -18, "yellow", "LANDING PAD"),
]
OLD = ["Factory Status Wall", "Replicator site", "Rocket silos", "Landing pad"]


def lua_str(s):
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


def load():
    try:
        return json.load(open(REG))
    except Exception:
        return []


def remove():
    reg = load()
    n = 0
    for surf, x, y, txt in [(a[0], a[1], a[2], None) for a in reg] if reg and isinstance(reg[0], list) else []:
        pass
    items = reg + [[None, None, None, o] for o in OLD]
    for it in items:
        surf, x, y, txt = it[0], it[1], it[2], it[3]
        if surf:
            lua = ("local f=game.forces.player local k=0 for _,t in pairs(f.find_chart_tags(game.surfaces[%s],{{%f,%f},{%f,%f}})) do if t.text==%s then t.destroy() k=k+1 end end rcon.print(k)"
                   % (lua_str(surf), x - 1.5, y - 1.5, x + 1.5, y + 1.5, lua_str(txt)))
        else:
            lua = ("local f=game.forces.player local k=0 for _,sn in pairs{'nauvis','gleba','fulgora','vulcanus','aquilo'} do for _,t in pairs(f.find_chart_tags(game.surfaces[sn])) do if t.text==%s then t.destroy() k=k+1 end end end rcon.print(k)" % lua_str(txt))
        n += int(tools["run_lua"](lua).strip() or 0)
    json.dump([], open(REG, "w"))
    return n


def apply():
    removed = remove()
    reg = []
    for surf, x, y, col, label in AREAS:
        hexc, icon = COLORS[col]
        txt = "[color=%s]%s[/color]" % (hexc, label)
        lua = ("local f=game.forces.player local s=game.surfaces[%s] local t=f.add_chart_tag(s,{position={%d,%d},text=%s,icon={type='virtual',name='%s'}}) "
               "f.chart(s,{{%d,%d},{%d,%d}}) rcon.print(t and 'ok' or 'fail')" % (lua_str(surf), x, y, lua_str(txt), icon, x - 16, y - 16, x + 16, y + 16))
        r = tools["run_lua"](lua).strip()
        reg.append([surf, x, y, txt])
        print("%-9s %-7s %-34s %s" % (surf, col, label, r))
    os.makedirs(os.path.dirname(REG), exist_ok=True)
    json.dump(reg, open(REG, "w"))
    print("removed old", removed, "added", len(reg))


def listing():
    for a in AREAS:
        print(a)


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "list"
    if step == "apply":
        apply()
    elif step == "remove":
        print("removed", remove())
    else:
        listing()
