#!/usr/bin/env python3
"""Move the Replicator (the make-anything block of scripts/omni_maker.py and scripts/omni_fluid.py; the Captain's name, after the
Star Trek replicator) on Nauvis from beside the old base (-60..40, -430..-360) to the area next to the rocket silos and launch pad
the Captain marked with striped-floor tile ghosts (x -366..-288, y -234..-190, 78 x 44 tiles: "so we can do compression experiments").

The new Replicator = omni_maker site `replicator` (3 recipe machines + furnace unit + stock stage, machines at x -354..-323,
y -231..-218) + omni_fluid --site replicator (chemical plant at -300,-224 with barrel machines at x -306..-294, y -230..-218) + their
recipe tables, which fill the free bands of the area. Tile ghosts are left alone (the floor can be laid under the entities).
Existing lattice (substations, roboports, solar, accumulators, pipe-to-ground) in the area is not touched. Everything is placed with
place_entities, wired with script wires (over-reach), then `config` is re-run.

Steps:
  check                   dry-run of every placement + what already stands (no change)
  build [--apply]         save, place machines, tables, furnace unit, fluid unit; wire it all (never apply twice: refuses if it stands)
  verify                  power, logistic network and recipe state of the new block; wiring counts
  status                  omni_maker + omni_fluid status of both copies
  retire-old [--apply]    orders deconstruction (robots; contents return to the network) of ONLY what the scripts built at the old
                          site (entity name + position match the script layouts); lists the rest of the old box and checks that
                          the network stays connected and covered. After it: re-run `config` for the new site so the silos'
                          orbital-request wires move over (done here when --apply).
Usage: replicator_move.py check | build [--apply] | verify | status | retire-old [--apply]
Shell: bash (PLATINUM 20). PYTHONPATH=scripts."""
import json
import subprocess
import sys
from pathlib import Path

import omni_fluid
import omni_maker
from _game import tools

HERE = Path(__file__).resolve().parent
BOX = (-366, -234, -288, -190)            # the marked area: x1, y1, x2, y2 (tiles)
OLD_BOX = (-62, -432, 42, -358)


def sh(*args):
    """Run one of the sibling scripts and return its filtered output."""
    r = subprocess.run([sys.executable, "-u", str(HERE / args[0])] + list(args[1:]), capture_output=True, text=True, encoding="utf-8",
                       env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8", "PYTHONPATH": str(HERE)})
    return "\n".join(l for l in (r.stdout + r.stderr).splitlines() if not any(k in l for k in ("INFO", "tunnel", "aaron_s", "27015")))


def lua(code):
    return tools["run_lua"](code)


def check():
    for a in (["omni_maker.py", "build", "replicator"], ["omni_maker.py", "rom", "replicator"], ["omni_maker.py", "furnace", "replicator"],
              ["omni_fluid.py", "build", "--site", "replicator"]):
        print(" ".join(a[:3]), "->", sh(*a))
    print(lua("local s=game.surfaces.nauvis local c={} for _,e in pairs(s.find_entities_filtered{area={{%d,%d},{%d,%d}},force='player'}) do if e.type~='logistic-robot' and e.type~='construction-robot' then c[e.name]=(c[e.name] or 0)+1 end end local t={} for k,v in pairs(c) do t[#t+1]=k..' '..v end rcon.print('standing in the area: '..table.concat(t,', '))" % BOX))


def build(apply):
    if not apply:
        return check()
    if omni_maker.standing("replicator"):
        sys.exit("the Replicator already stands at site replicator: never apply twice")
    print("save:", tools["save_game"]("skippy"))
    print(sh("omni_maker.py", "build", "replicator", "--apply"))
    print(sh("omni_maker.py", "rom", "replicator", "--apply"))
    print(sh("omni_maker.py", "furnace", "replicator", "--apply"))
    print(sh("omni_fluid.py", "build", "--site", "replicator", "--apply"))
    print(sh("omni_maker.py", "config", "replicator"))
    print(sh("omni_fluid.py", "config", "--site", "replicator"))


VERIFY = ("local s=game.surfaces.nauvis local f=game.forces.player local names={['assembling-machine-3']=1,['chemical-plant']=1,['electric-furnace']=1,['roboport']=1,['requester-chest']=1,['passive-provider-chest']=1,"
          "['fast-inserter']=1,['decider-combinator']=1,['arithmetic-combinator']=1,['selector-combinator']=1,['constant-combinator']=1,['substation']=1,pipe=1} local inv={} local nonet=0 local st={} local mine=0 "
          "local ids=s.find_entities_filtered{area={{BOXA},{BOXB}},force=f} local nets={} for _,e in pairs(ids) do if names[e.name] and e.position.y>=-231 and e.position.y<=-190 and not (e.name=='substation' and (e.position.y==-232 or e.position.y==-216 or e.position.y==-200 or e.position.y==-213)) and not (e.name=='roboport' and e.position.y==-216) then mine=mine+1 "
          "local k='?' for a,v in pairs(defines.entity_status) do if v==e.status then k=a end end local key=e.name..':'..k st[key]=(st[key] or 0)+1 "
          "if e.type=='logistic-container' then if not e.logistic_network then nonet=nonet+1 else nets[e.logistic_network.network_id]=(nets[e.logistic_network.network_id] or 0)+1 end end end end "
          "local t={} for k,v in pairs(st) do t[#t+1]=k..' '..v end table.sort(t) local n={} for k,v in pairs(nets) do n[#n+1]='net '..k..': '..v..' chests' end rcon.print('replicator entities '..mine..' ; chests outside any logistic network '..nonet..' ; '..table.concat(n,', ')..' ;; '..table.concat(t,', '))")


def verify():
    print(lua(VERIFY.replace("BOXA", "%d,%d" % BOX[:2]).replace("BOXB", "%d,%d" % BOX[2:])).replace(" ;; ", "\n"))
    print(sh("omni_maker.py", "status", "replicator"))
    print(sh("omni_fluid.py", "status", "--site", "replicator"))


def status():
    print("--- old copy ---")
    print(sh("omni_maker.py", "status", "nauvis"))
    print(sh("omni_fluid.py", "status", "--site", "old"))
    print("--- Replicator ---")
    verify()


def old_entities():
    """(name, x, y) of everything the scripts built at the old site, from the script layouts themselves."""
    out = []
    n_all = int(lua(omni_maker.COUNT).strip())
    n_f = int(lua("local f=game.forces.player " + omni_maker.SMELT + "rcon.print(#mk)").strip())
    for e in omni_maker.layout("nauvis") + omni_maker.stock_stage("nauvis") + omni_maker.furnace_layout("nauvis", n_f):
        out.append((e["name"], e["x"], e["y"]))
    for tx, ty in omni_maker.rom_slots("nauvis", n_all):
        out.append(("decider-combinator", tx + 0.5, ty + 1))
    omni_fluid.use("old")
    n_fl = int(lua(omni_fluid.LIST + "rcon.print(#rs)").strip())
    for e in omni_fluid.layout(n_fl):
        out.append((e["name"], e["x"], e["y"]))
    return out


RETIRE = ("local s=game.surfaces.nauvis local f=game.forces.player local L=LIST local APPLY=DOIT local found,missing,marked={}, 0, 0 local seen={} "
          "for _,p in ipairs(L) do local e=s.find_entities_filtered{name=p[1],position={p[2],p[3]},radius=0.45,force=f}[1] if e and not seen[e.unit_number] then seen[e.unit_number]=true found[#found+1]=e else if not e then missing=missing+1 end end end "
          "local rest={} for _,e in pairs(s.find_entities_filtered{area={{BX1,BY1},{BX2,BY2}},force=f}) do if e.type~='logistic-robot' and e.type~='construction-robot' and e.type~='entity-ghost' and e.type~='tile-ghost' and not (e.unit_number and seen[e.unit_number]) then rest[e.name]=(rest[e.name] or 0)+1 end end "
          "local all,keep,old={}, {}, {} for _,e in pairs(s.find_entities_filtered{name='roboport',force=f}) do all[#all+1]=e if seen[e.unit_number] then old[#old+1]=e else keep[#keep+1]=e end end "
          "local function rad(r) return r.logistic_cell and r.logistic_cell.logistic_radius or 25 end "
          "local function comps(list) local par={} for i=1,#list do par[i]=i end local function fd(i) while par[i]~=i do par[i]=par[par[i]] i=par[i] end return i end "
          "for i=1,#list do for j=i+1,#list do local a,b=list[i],list[j] local r=rad(a)+rad(b) if math.abs(a.position.x-b.position.x)<=r and math.abs(a.position.y-b.position.y)<=r then par[fd(i)]=fd(j) end end end local c=0 for i=1,#list do if fd(i)==i then c=c+1 end end return c end "
          "local orph={} for _,c in pairs(s.find_entities_filtered{area={{BX1,BY1},{BX2,BY2}},force=f}) do if (c.type=='logistic-container' or c.type=='roboport') and not seen[c.unit_number] then local covered=false for _,r in ipairs(keep) do local q=rad(r) if math.abs(r.position.x-c.position.x)<=q and math.abs(r.position.y-c.position.y)<=q then covered=true break end end if not covered then orph[#orph+1]=c.name..'@'..c.position.x..','..c.position.y end end end "
          "local ca,cb=comps(all),comps(keep) "
          "if APPLY then for _,e in ipairs(found) do if e.order_deconstruction(f) then marked=marked+1 end end end "
          "local t={} for k,v in pairs(rest) do t[#t+1]=k..' '..v end table.sort(t) rcon.print('script-built entities found '..#found..', missing '..missing..', marked '..marked..' ;; roboports on nauvis '..#all..' (script-built at the old site: '..#old..'), connected groups before '..ca..', after removal '..cb..' ;; left standing in the old box (not built by the scripts): '..table.concat(t,', ')..' ;; logistic chests/roboports in the old box left without cover: '..#orph..' '..table.concat(orph,' ',1,math.min(#orph,12)))")


def retire(apply):
    ents = old_entities()
    lst = "{" + ",".join("{'%s',%s,%s}" % e for e in ents) + "}"
    code = (RETIRE.replace("LIST", lst).replace("DOIT", "true" if apply else "false").replace("BX1", str(OLD_BOX[0])).replace("BY1", str(OLD_BOX[1]))
            .replace("BX2", str(OLD_BOX[2])).replace("BY2", str(OLD_BOX[3])))
    if len(code) > 65000:
        sys.exit("lua too long: %d" % len(code))
    print(lua(code).replace(" ;; ", "\n"))
    if apply:
        print("robots are deconstructing; when done, run: omni_maker.py config replicator (moves the silos' orbital wires) -- done now:")
        print(sh("omni_maker.py", "config", "replicator"))


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "check"
    apply = "--apply" in sys.argv
    if step == "check":
        check()
    elif step == "build":
        build(apply)
    elif step == "verify":
        verify()
    elif step == "status":
        status()
    elif step == "retire-old":
        if apply:
            print("save:", tools["save_game"]("skippy"))
        retire(apply)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
