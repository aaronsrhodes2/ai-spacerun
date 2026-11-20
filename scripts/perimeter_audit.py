#!/usr/bin/env python3
"""Every platform: is the whole hull inside the reach of a turret that can shoot what comes at rest? (read-only)
Why (the Captain, 2026-11-20): "when shuttles are at rest, asteroids come from all directions. So you need to have some protection,
though not as much, around the entire perimeter of all shuttles and ships and stations."
At rest only small and medium asteroids drift in (every orbit but the far ones), so the turrets that count are gun and laser turrets
with ammunition or power; a rocket turret set to big and huge only does not count. For each platform the script takes every entity of
ours and finds the nearest such turret; an entity farther away than the turret's range less MARGIN (an asteroid must be shot before
it touches) is uncovered. It prints uncovered entities by compass sector (N = the nose, low y), so the open side is named.
Also printed: what the platform has lost so far (kill statistics, our losses).
Usage: perimeter_audit.py [PLATFORM NAME PART ...]"""
import json
import sys

from _game import tools

L = tools["run_lua"]
MARGIN = 6

NAMES = "local o={} for i,p in pairs(game.forces.player.platforms) do if p.surface and p.hub and p.hub.valid then o[#o+1]={i=i,n=p.name:gsub('%[.-%]',''):gsub('^%s+','')} end end rcon.print(helpers.table_to_json(o))"

ONE = ("local p=game.forces.player.platforms[%d] local s=p.surface local T={} local guns,lasers,empty=0,0,0 "
       "for _,t in pairs(s.find_entities_filtered{type={'ammo-turret','electric-turret'}}) do local ok=false if t.name=='gun-turret' then guns=guns+1 if t.get_inventory(defines.inventory.turret_ammo).is_empty() then empty=empty+1 else ok=true end "
       "elseif t.type=='electric-turret' then lasers=lasers+1 ok=true end if ok then local r=t.prototype.attack_parameters.range*(1+0.1*t.quality.level)-%d T[#T+1]={t.position.x,t.position.y,r*r} end end "
       "local sec={} local unc,tot=0,0 local far=0 for _,e in pairs(s.find_entities_filtered{force='player'}) do if e.type~='entity-ghost' and e.type~='tile-ghost' and e.type~='cargo-pod' then tot=tot+1 local x,y=e.position.x,e.position.y local ok=false "
       "for i=1,#T do local t=T[i] local dx,dy=x-t[1],y-t[2] if dx*dx+dy*dy<=t[3] then ok=true break end end "
       "if not ok then unc=unc+1 local k=(math.abs(y)>=math.abs(x)) and (y<0 and 'N' or 'S') or (x<0 and 'W' or 'E') sec[k]=(sec[k] or 0)+1 end end end "
       "local lost=0 for n,c in pairs(game.forces.player.get_kill_count_statistics(s).output_counts) do lost=lost+c end "
       "rcon.print(helpers.table_to_json({tot=tot,unc=unc,sec=sec,guns=guns,lasers=lasers,empty=empty,lost=lost,at=p.space_location and p.space_location.name or 'in flight'}))")


def main():
    want = [w.lower() for w in sys.argv[1:]]
    rows = []
    for p in json.loads(L(NAMES)):
        if want and not any(w in p["n"].lower() for w in want):
            continue
        r = json.loads(L(ONE % (p["i"], MARGIN)))
        sec = r["sec"] if isinstance(r["sec"], dict) else {}
        rows.append((r["unc"] / max(1, r["tot"]), p["n"], r, sec))
    rows.sort(key=lambda x: -x[0])
    print("%-34s %-9s %6s %5s %6s %9s %6s  open sides" % ("platform", "at", "ents", "guns", "lasers", "uncovered", "lost"))
    for frac, n, r, sec in rows:
        print("%-34s %-9s %6d %5d %6d %5d %3d%% %6d  %s%s" % (n[:34], r["at"][:9], r["tot"], r["guns"], r["lasers"], r["unc"], round(100 * frac), r["lost"],
              " ".join("%s %d" % (k, sec[k]) for k in "NESW" if k in sec), ("  (%d guns EMPTY)" % r["empty"]) if r["empty"] else ""))


if __name__ == "__main__":
    main()
