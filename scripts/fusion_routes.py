#!/usr/bin/env python3
"""Shipping routes for the Aquilo fusion plant (the Captain, 2026-11-15: "shipping routes first"). Pattern used everywhere in this factory:
a ship's hub asks for the item at the origin stop (`import_from` origin), the destination pad asks for it (the ship unloads what the pad requests).
Hops:  tungsten plate  Vulcanus -> Nauvis -> Fulgora -> Aquilo     tungsten carbide  Nauvis -> Fulgora -> Aquilo
       holmium plate   Fulgora -> Aquilo                         carbon fiber      Gleba -> Aquilo
Sections are named `fusion-<kind>-<place>` (group names are global, so each needs its own); re-running replaces them. Amounts are the first-plant bill (scripts/fusion_aquilo.py bom) with a margin.
Usage: fusion_routes.py show | apply"""
import sys

from _game import tools

L = tools["run_lua"]
W_PLATE, W_CARB, HOLM, FIBER = 600, 500, 60, 500

# (kind, match, group, [(item, qty, import_from)])   kind: pad = a planet's landing pad (match = planet), hub = platforms whose name contains match
ROUTES = [
    ("hub", "Nauvis-Vulcanus", "G", [("tungsten-plate", W_PLATE, "vulcanus")]),
    ("pad", "nauvis", "G", [("tungsten-plate", W_PLATE, "vulcanus")]),
    ("hub", "Nauvis-Fulgora", "G", [("tungsten-plate", W_PLATE, "nauvis"), ("tungsten-carbide", W_CARB, "nauvis")]),
    ("pad", "fulgora", "G", [("tungsten-plate", W_PLATE, "nauvis"), ("tungsten-carbide", W_CARB, "nauvis")]),
    ("hub", "Fulgora-Aquilo", "G", [("tungsten-plate", W_PLATE, "fulgora"), ("tungsten-carbide", W_CARB, "fulgora"), ("holmium-plate", HOLM, "fulgora")]),
    ("pad", "gleba", "G", [("carbon-fiber", FIBER, None)]),      # bots bring the fiber from the works' provider chests to the pad, where the ship loads it
    ("hub", "Gleba-Aquilo", "G", [("carbon-fiber", FIBER, "gleba")]),
    ("pad", "aquilo", "G", [("tungsten-plate", W_PLATE, None), ("tungsten-carbide", W_CARB, None), ("carbon-fiber", FIBER, None)]),
]

LUA = r'''
local f=game.forces.player local o={}
local function setsec(tag, container_pt, group, items, hub)
  local secs = hub and container_pt or container_pt
  for i=#secs.sections,1,-1 do if (secs.sections[i].group or ''):find('fusion-',1,true)==1 then secs.remove_section(i) end end
  local sec=secs.add_section(group)
  for k,it in ipairs(items) do local sl={value={type='item',name=it[1],quality='normal'},min=it[2]} if it[3] then sl.import_from=it[3] end if tag=='pad' and it[3] then sl.max=it[2] end sec.set_slot(k,sl) end
  return #items
end
ROUTES_HERE
rcon.print(table.concat(o,' | '))
'''


def lua_items(items):
    return "{" + ",".join("{'%s',%d,%s}" % (n, q, ("'%s'" % s) if s else "nil") for n, q, s in items) + "}"


def build_lua():
    parts = []
    for kind, match, group, items in ROUTES:
        group = "fusion-%s-%s" % (kind, match.lower())     # group names are global: one name shared by two sections shares their filters
        it = lua_items(items)
        if kind == "pad":
            parts.append("do local pad=game.surfaces.%s.find_entities_filtered{type='cargo-landing-pad'}[1] local done=false for _,pt in pairs(pad.get_logistic_point()) do if pt.mode==defines.logistic_mode.requester then "
                         "o[#o+1]='pad %s '..setsec('pad',pt,'%s',%s,false) done=true end end if not done then o[#o+1]='pad %s no requester' end end" % (match, match, group, it, match))
        else:
            parts.append("do local n=0 for _,p in pairs(f.platforms) do if p.valid and p.hub and p.name:find('%s',1,true) and p.name:find('Shuttle$') then setsec('hub',p.hub.get_logistic_sections(),'%s',%s,true) n=n+1 end end o[#o+1]='hubs %s x'..n end"
                         % (match, group, it, match))
    return LUA.replace("ROUTES_HERE", " ".join(parts))


def show():
    code = ("local f=game.forces.player local o={} local function d(tag,secs) for _,s in pairs(secs) do if (s.group or ''):find('fusion') then local q={} for _,fl in pairs(s.filters) do if fl.value then q[#q+1]=fl.value.name..' '..(fl.min or 0)..(fl.import_from and ('@'..tostring(fl.import_from.name or fl.import_from)) or '') end end o[#o+1]=tag..': '..table.concat(q,', ') end end end "
            "for _,sn in ipairs({'nauvis','fulgora','gleba','aquilo'}) do for _,pt in pairs(game.surfaces[sn].find_entities_filtered{type='cargo-landing-pad'}[1].get_logistic_point()) do if pt.mode==defines.logistic_mode.requester then d('pad '..sn,pt.sections) end end end "
            "for _,p in pairs(f.platforms) do if p.valid and p.hub and p.name:find('Shuttle$') then d(p.name:sub(-26),p.hub.get_logistic_sections().sections) end end rcon.print(table.concat(o,string.char(10)))")
    print(L(code))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"
    if cmd == "apply":
        print(L(" ".join(build_lua().split("\n"))))
    show()


if __name__ == "__main__":
    main()
