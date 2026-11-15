#!/usr/bin/env python3
"""Ghost-to-request bridge (2026-11-15, the Captain: ghosts on Gleba never turn into requests to the interplanetary network).
A ghost is only a build job: the robots look in the local logistic network and wait if the item is not there. Nothing asks orbit for it. The only link from a
planet to orbit is the cargo landing pad's request list. This script writes that list from the ghosts.

Per planet that has a cargo landing pad:
  needs     entity ghosts (`ghost_prototype.items_to_place_this`) and tile ghosts (`items_to_place_this` of the tile) that sit inside the pad's own logistic network,
            by (item, quality) EXACTLY (a ghost asks for its own quality), minus what that network already holds (pad included)
  request   section group `ghost-auto-<planet>` (ours alone, rewritten each run; nothing else is touched) on the pad's requester point:
            min = pad count + shortfall, max = same, import_from unset (any platform in orbit). A shortfall of 0 means no slot.
  report    ghosts outside roboport coverage (robots cannot build them: not requested) and items with a shortfall
Quality parity (2026-11-15, the Captain): we never build epic machines, we build normal ones and upgrade them afterwards (upgrade_quality.py). So an entity ghost of a
  higher quality would ask for an item nobody makes and never be built. `normalize` (below) re-lays each such ghost as a NORMAL ghost in the same place, direction and
  mirroring, with its module/item plan, before the request is computed; the request then asks for the normal item. Dry run only counts them; --apply rewrites them.
Rules kept: no item is created, no ghost is touched; the section only asks, the platforms still have to carry the goods.
Caps: --max-stacks N (default 40) limits the total pad stacks one run asks for, biggest shortfall in stacks first, so a huge blueprint cannot flood the pad.

Usage: ghost_requests.py [--planet NAME ...] [--apply] [--max-stacks N]     (default: all planets, dry run)"""
import sys

from _game import tools

L = tools["run_lua"]
GROUP = "ghost-auto"   # used as ghost-auto-<planet>: a group name is SHARED by every section that has it (found live), so one name copied one planet's list onto all pads
PLANETS = ["nauvis", "vulcanus", "gleba", "fulgora", "aquilo"]
NL = "string.char(10)"

args = sys.argv[1:]
APPLY = "--apply" in args
MAXST = int(args[args.index("--max-stacks") + 1]) if "--max-stacks" in args else 40
ONLY = [args[i + 1] for i, a in enumerate(args) if a == "--planet"]


NORMALIZE = """
local s=game.surfaces['PLANET'] local f=game.forces.player local APPLY=APPLYFLAG local n,bad=0,0
local pad=s.find_entities_filtered{type='cargo-landing-pad',force=f}[1]
local net=pad and (pad.logistic_network or s.find_logistic_network_by_position(pad.position,f))
for _,g in pairs(s.find_entities_filtered{type='entity-ghost',force=f}) do
  if g.quality.name~='normal' and (not net or s.find_logistic_network_by_position(g.position,f)==net) then
    n=n+1
    if APPLY then
      local d={name='entity-ghost',inner_name=g.ghost_name,position=g.position,direction=g.direction,force=f,quality='normal',fast_replace=false,raise_built=false}
      pcall(function() d.mirroring=g.mirroring end)
      pcall(function() d.tags=g.tags end)
      pcall(function() if g.ghost_type=='underground-belt' then d.type=g.belt_to_ground_type elseif g.ghost_type=='loader' or g.ghost_type=='loader-1x1' then d.type=g.loader_type end end)
      local plan pcall(function() plan=g.insert_plan end)
      local oq=g.quality.name g.destroy()
      local ng=s.create_entity(d)
      if ng then pcall(function() if plan and #plan>0 then ng.insert_plan=plan end end)
      else bad=bad+1 d.quality=oq s.create_entity(d) end
    end
  end
end
rcon.print('non-normal entity ghosts '..n..(APPLY and (', re-laid as normal, failed '..bad) or ' (dry run)'))
"""


def lua(code):
    return L(" ".join(code.split())).strip()


READ = """
local s=game.surfaces['PLANET'] local f=game.forces.player local o={}
if not s then rcon.print('NOSURFACE') return end
local pad=s.find_entities_filtered{type='cargo-landing-pad',force=f}[1]
if not pad then rcon.print('NOPAD') return end
local net=pad.logistic_network or s.find_logistic_network_by_position(pad.position,f)
if not net then for _,r in pairs(s.find_entities_filtered{type='roboport',force=f}) do local n=r.logistic_network if n and (not net or #n.cells>#net.cells) then net=n end end end
if not net then rcon.print('NONET') return end
local need={} local outside=0 local inside=0
local function add(g,items) local n=s.find_logistic_network_by_position(g.position,f)
  if not n or n.network_id ~= net.network_id then outside=outside+1 return end inside=inside+1
  for _,it in pairs(items) do local k=it.name..' '..g.quality.name need[k]=(need[k] or 0)+it.count end end
for _,g in pairs(s.find_entities_filtered{type='entity-ghost',force=f}) do add(g,g.ghost_prototype.items_to_place_this or {}) end
for _,g in pairs(s.find_entities_filtered{type='tile-ghost',force=f}) do local tp=g.ghost_prototype add(g,tp.items_to_place_this or {}) end
local pinv=pad.get_inventory(defines.inventory.cargo_landing_pad_main)
for k,n in pairs(need) do local nm,q=k:match('(%S+) (%S+)')
  local have=net.get_item_count{name=nm,quality=q} local onpad=pinv.get_item_count{name=nm,quality=q}
  local pr=prototypes.item[nm]
  o[#o+1]=table.concat({'N',nm,q,n,have,onpad,pr and pr.stack_size or 1},' ') end
o[#o+1]='S '..inside..' '..outside..' '..pinv.count_empty_stacks()
rcon.print(table.concat(o,string.char(10)))
"""

WRITE = """
local s=game.surfaces['%s'] local f=game.forces.player
local pad=s.find_entities_filtered{type='cargo-landing-pad',force=f}[1]
local pt for _,q in pairs(pad.get_logistic_point()) do if q.mode==defines.logistic_mode.requester then pt=q end end
if not pt then rcon.print('NOPOINT') return end
for i=pt.sections_count,1,-1 do local g=pt.sections[i].group if g=='GRP' or g=='ghost-auto' then pt.remove_section(i) end end
local K=%s
if #K>0 then local sec=pt.add_section('GRP')
  for i,k in ipairs(K) do sec.set_slot(i,{value={type='item',name=k[1],quality=k[2]},min=k[3],max=k[3]}) end end
rcon.print('wrote '..#K..' slots')
"""


def game_has(planet):
    return lua("rcon.print(game.surfaces['%s'] and 'y' or 'n')" % planet) == "y"


def read(planet):
    out = lua(READ.replace('PLANET', planet))
    if out in ("NOSURFACE", "NOPAD", "NONET"):
        return out, [], None
    rows, stat = [], None
    for ln in out.split("\n"):
        t = ln.split()
        if not t:
            continue
        if t[0] == "N":
            nm, q, need, have, onpad, stack = t[1], t[2], int(t[3]), int(t[4]), int(t[5]), int(t[6])
            rows.append(dict(item=nm, q=q, need=need, have=have, onpad=onpad, stack=stack, short=max(0, need - have)))
        elif t[0] == "S":
            stat = dict(inside=int(t[1]), outside=int(t[2]), free=int(t[3]))
    return "ok", rows, stat


def main():
    for planet in (ONLY or PLANETS):
        print("== %s" % planet)
        if game_has(planet):
            print("  quality parity: " + lua(NORMALIZE.replace("PLANET", planet).replace("APPLYFLAG", "true" if APPLY else "false")))
        status, rows, stat = read(planet)
        if status != "ok":
            print("  skipped: %s" % {"NOSURFACE": "no such surface", "NOPAD": "no cargo landing pad", "NONET": "pad has no logistic network"}[status])
            continue
        print("  ghosts inside the pad network: %d, outside coverage (not requested): %d, pad free stacks: %d" % (stat["inside"], stat["outside"], stat["free"]))
        short = sorted([r for r in rows if r["short"] > 0], key=lambda r: -(r["short"] / r["stack"]))
        pick, used = [], 0
        for r in short:
            st = -(-r["short"] // r["stack"])
            if used + st > MAXST:
                continue
            used += st
            pick.append(r)
        for r in sorted(rows, key=lambda r: -r["need"])[:12]:
            print("  %-26s %-9s need %6d  network has %6d  short %6d%s" % (r["item"], r["q"], r["need"], r["have"], r["short"], "" if r in pick or not r["short"] else "  (over the stack cap)"))
        if not short:
            print("  nothing missing")
        slots = "{" + ",".join("{'%s','%s',%d}" % (r["item"], r["q"], r["onpad"] + r["short"]) for r in pick) + "}"
        if APPLY:
            print("  " + lua((WRITE % (planet, slots)).replace("GRP", GROUP + "-" + planet)))
        else:
            print("  dry run: would write %d slots (%d stacks); --apply to write" % (len(pick), used))


def cycle():
    """For the autopilot: apply on every planet, quiet; returns one log line ('gleba 3 slots, aquilo 1 slots', or 'nothing missing')."""
    done = []
    for planet in PLANETS:
        status, rows, _ = read(planet)
        if status != "ok":
            continue
        short = sorted([r for r in rows if r["short"] > 0], key=lambda r: -(r["short"] / r["stack"]))
        pick, used = [], 0
        for r in short:
            st = -(-r["short"] // r["stack"])
            if used + st <= MAXST:
                used += st
                pick.append(r)
        slots = "{" + ",".join("{'%s','%s',%d}" % (r["item"], r["q"], r["onpad"] + r["short"]) for r in pick) + "}"
        lua((WRITE % (planet, slots)).replace("GRP", GROUP + "-" + planet))
        if pick:
            done.append("%s %d slots" % (planet, len(pick)))
    return ", ".join(done) or "nothing missing"


if __name__ == "__main__":
    main()
