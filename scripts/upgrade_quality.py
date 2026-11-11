"""
Standing order (the Captain, 2026-11-10): when a quality level is researched, everything built goes up to it at once; no grinding for quality.

Raises every entity of ours on every surface to the best researched quality, in place, with the game's own upgrade (order_upgrade + apply_upgrade):
recipe, contents, modules, wires, heat and schedules stay. Stored electric energy is carried over by hand (an upgraded accumulator starts empty otherwise).
Modules in machines and robots resting in roboports are swapped for the same item at the new quality (--items; flying robots cannot be upgraded,
they change as they come home and the next run catches them).

Without --apply it only counts. Safe to run again: what is already at the target quality is skipped.

Usage: scripts/upgrade_quality.py [--surface NAME] [--items] [--apply]
"""
import json
import sys

from _game import tools

SKIP = "['logistic-robot']=1,['construction-robot']=1,['cargo-pod']=1,['character']=1,['rocket-silo-rocket']=1,['rocket-silo-rocket-shadow']=1,['entity-ghost']=1,['tile-ghost']=1,['spider-leg']=1,['item-request-proxy']=1"

BEST = ("local f=game.forces.player local best=nil for n,q in pairs(prototypes.quality) do if n~='quality-unknown' and f.is_quality_unlocked(n) and (best==nil or q.level>best.level) then best=q end end ")

TYPES = BEST + ("local s=game.surfaces['%s'] local skip={" + SKIP + "} local by={} for _,e in pairs(s.find_entities_filtered{force=f}) do if e.quality.level<best.level and not skip[e.type] then by[e.type]=(by[e.type] or 0)+1 end end "
                "rcon.print(helpers.table_to_json({best=best.name,types=by}))")

UP = BEST + ("local s=game.surfaces['%s'] local ok,fail,left=0,0,0 local why={} for _,e in pairs(s.find_entities_filtered{force=f,type='%s'}) do if e.valid and e.quality.level<best.level then "
             "if ok+fail>=%d then left=left+1 else local nm,en=e.name,nil if e.prototype.electric_energy_source_prototype then en=e.energy end "
             "local good,res=pcall(function() e.order_upgrade{force=f,target={name=nm,quality=best.name}} return e.apply_upgrade() end) "
             "if good and res and res.valid and res.quality.level==best.level then ok=ok+1 if en and en>0 then res.energy=en end else fail=fail+1 if e.valid then pcall(function() e.cancel_upgrade(f) end) end "
             "why[nm]=(why[nm] or 0)+1 end end end end rcon.print(helpers.table_to_json({ok=ok,fail=fail,left=left,why=why}))")

ITEMS = BEST + ("local s=game.surfaces['%s'] local apply=%s local mods,bots=0,0 local function swap(inv) local n=0 if inv then for i=1,#inv do local st=inv[i] "
                "if st.valid_for_read and st.quality.level<best.level then n=n+st.count if apply then st.set_stack{name=st.name,count=st.count,quality=best.name} end end end end return n end "
                "for _,e in pairs(s.find_entities_filtered{force=f,type={'assembling-machine','furnace','mining-drill','lab','beacon','rocket-silo','asteroid-collector'}}) do mods=mods+swap(e.get_module_inventory()) end "
                "for _,e in pairs(s.find_entities_filtered{force=f,type='roboport'}) do bots=bots+swap(e.get_inventory(defines.inventory.roboport_robot)) end "
                "rcon.print(helpers.table_to_json({modules=mods,robots_in_roboports=bots}))")


def jl(code):
    out = tools["run_lua"](code).strip()
    if not out.startswith("{"):
        raise SystemExit("unexpected reply: " + out[:500])
    d = json.loads(out)
    return json.loads(d["result"]) if "result" in d and isinstance(d["result"], str) else d


def main():
    apply = "--apply" in sys.argv
    if "--surface" in sys.argv:
        surfaces = [sys.argv[sys.argv.index("--surface") + 1]]
    else:
        surfaces = tools["run_lua"]("local o={} for _,s in pairs(game.surfaces) do o[#o+1]=s.name end rcon.print(table.concat(o,','))").strip().split(",")
    for name in surfaces:
        d = jl(TYPES % name)
        types = d["types"] or {}
        total = sum(types.values()) if types else 0
        print(f"{name}: {total} entities below {d['best']}", flush=True)
        if apply:
            for t, n in sorted(types.items(), key=lambda kv: kv[1]):
                ok = fail = 0
                why = {}
                while True:
                    r = jl(UP % (name, t, 2000))
                    ok += r["ok"]; fail += r["fail"]
                    why.update(r["why"] or {})
                    if not r["left"] or not r["ok"]:
                        break
                print(f"  {t}: {ok} upgraded" + (f", {fail} refused {why}" if fail else ""), flush=True)
        if "--items" in sys.argv:
            print(f"  items: {jl(ITEMS % (name, 'true' if apply else 'false'))}", flush=True)


if __name__ == "__main__":
    main()
