#!/usr/bin/env python3
"""Fusion power on Aquilo (the Captain, 2026-11-15: "accomplish stable fusion power on Aquilo"). Read-only so far: the bill of materials
for N reactors + G generators against what every planet holds, and the weakest link on the route. Plan: docs/fusion-and-galaxy-edge-plan.md.
Usage: scripts/fusion_aquilo.py bom [reactors] [generators] [cells]   (default 1 reactor, 2 generators, 20 start cells)"""
import sys

from _game import tools

L = tools["run_lua"]
RAW = ["tungsten-plate", "superconductor", "quantum-processor", "processing-unit", "tungsten-carbide", "carbon-fiber",
       "lithium-plate", "holmium-plate", "fusion-power-cell"]
SURFACES = ["nauvis", "vulcanus", "fulgora", "gleba", "aquilo"]


def stock():
    names = ",".join("'%s'" % n for n in RAW)
    sf = ",".join("'%s'" % s for s in SURFACES)
    code = ("local items={%s} local o={} for _,sn in ipairs({%s}) do local s=game.surfaces[sn] local tot={} "
            "for _,e in pairs(s.find_entities_filtered{force='player',type={'container','logistic-container','cargo-landing-pad'}}) do "
            "for _,inv in ipairs({defines.inventory.chest,defines.inventory.cargo_landing_pad_main}) do local ok,iv=pcall(function() return e.get_inventory(inv) end) "
            "if ok and iv then for _,c in ipairs(iv.get_contents()) do for _,i in ipairs(items) do if c.name==i then tot[i]=(tot[i] or 0)+c.count end end end end end end "
            "local t={} for k,v in pairs(tot) do t[#t+1]=k..'='..v end o[#o+1]=sn..'|'..table.concat(t,',') end rcon.print(table.concat(o,';'))") % (names, sf)
    out = {}
    for part in L(code).split(";"):
        sn, rest = part.split("|")
        out[sn] = {kv.split("=")[0]: int(kv.split("=")[1]) for kv in rest.split(",") if kv}
    return out


def bom(reactors, gens, cells):
    qp = 250 * reactors + 50 * gens
    need = {"tungsten-plate": 200 * reactors + 100 * gens, "superconductor": 200 * reactors + 100 * gens + qp,
            "quantum-processor": qp, "processing-unit": qp, "tungsten-carbide": qp, "carbon-fiber": qp,
            "lithium-plate": 2 * qp + 5 * cells, "holmium-plate": cells}
    return need


def main():
    a = sys.argv[1:]
    cmd = a[0] if a else "bom"
    r, g, c = (int(x) for x in (a[1:4] + ["1", "2", "20"][len(a[1:4]):]))
    need, st = bom(r, g, c), stock()
    print("fusion plant: %d reactor(s), %d generator(s), %d start cells (quantum processors %d)" % (r, g, c, need["quantum-processor"]))
    for item, n in need.items():
        have = {s: st[s].get(item, 0) for s in SURFACES}
        total = sum(have.values())
        flag = "OK " if have["aquilo"] >= n else ("far" if total >= n else "SHORT")
        print("  %-18s need %6d  aquilo %6d  elsewhere %s  %s" % (item, n, have["aquilo"], {k: v for k, v in have.items() if k != "aquilo" and v}, flag))
    print("quantum-processor / carbon-fiber have no producer yet; carbon fiber = 10 yumako mash + 1 carbon (Gleba)")


if __name__ == "__main__":
    main()
