#!/usr/bin/env python3
"""Aquilo build logistics (2026-11-14, the Captain: "fix Aquilo's logistics, it has things to be built, but no logistics line is delivering it").
Aquilo ghosts (entity ghosts, `concrete` and `ice-platform` tile ghosts) wait for items that nothing on Aquilo makes. This script is the AUTOMATIC chain:
  needs    ghost items by (item, quality) from the ghosts themselves (`ghost_prototype.items_to_place_this`), split inside / outside roboport
           coverage, against what the Aquilo network, the ship's hub, Fulgora and Nauvis hold; concrete by class (on water, next to heavy machines)
  kit      the kit one trip should carry, within a weight budget in rocket loads (1,000 kg each), sourced per item at its EXACT quality
  stage    moves the kit items from where they are (Fulgora chests, then the Nauvis network) onto the ship's hub; factory-made items only, never spawned
  apply    writes the ship's request section `aq-ghost-36` (import_from fulgora: the Fulgora silo lifts what Fulgora holds) and the drop section
           `aq-ghostdrop-36` (min = max = 0 at Aquilo: an UNREQUESTED item never leaves a hub), and adds the kit items to the Aquilo stop's leave rule
  reload   ONE ammunition step for both Aquilo ships: a ship parked at its home planet is topped up to a target (default 5,600 explosive rockets and
           4,000 uranium magazines) from the Nauvis ammo cells' steel output chests (x -330..-280, y -105..-80: not in the robot network) and then any Nauvis network chest, only when stock exists. `--plain` fits plain rockets (NOT proven: see SKILL.md)
  works    the concrete works on Aquilo: ice melter -> concrete assembler fed bricks + ore by a requester chest, output to a provider chest
           (concrete 10 kg a piece; 5 bricks + 1 ore make 10 concrete = 12 kg, 8x lighter)
  verify   the checks for a flight; status = everything in one screen
  cycle    what the autopilot runs every few cycles: needs -> kit -> apply -> reload; failures logged, never fatal
Rules kept: items only move between inventories; no item is created; ghosts are never touched; the Nauvis-Fulgora ferry sections are not touched
(`relay` writes only its own group `aq-ghost-relay`).
Quality: a ghost asks for EXACTLY its quality. Aquilo's entity ghosts are mostly EPIC; the Replicator makes normal. `needs` shows the gap.
Usage: aquilo_build_logistics.py status | needs | kit [--loads N] [--concrete N] | stage [--apply] | apply [--apply] | reload [--apply] [--plain] [--rockets N] [--mags N]
                                 | works [--apply] | relay [--apply] | verify | cycle
"""
import json
import math
import sys

from _game import tools

L = tools["run_lua"]
NL = "string.char(10)"
SHIPS = {"Gleba-Aquilo 1 Shuttle": "gleba"}   # Fulgora-Aquilo 5 was lost 2026-11-19 and removed here 2026-11-21 (its absence raised an error every 5th autopilot cycle)
SHIP = "Fulgora-Aquilo 5"           # the ship that carries kits (ship 4, platform 36, no longer exists: found 2026-11-16, the kit route was dead)
IDX = 39
GHOST_SEC, GHOST_DROP = "aq-ghost-%d" % IDX, "aq-ghostdrop-%d" % IDX
SHIP_OWN = {"iron-ore", "carbon", "explosive-rocket", "rocket", "uranium-rounds-magazine", "repair-pack"}   # the ship's own supplies: never dropped
ROCKET_KG = 1000
ROCKET_TARGET, MAG_TARGET = 5600, 4000      # the Captain: depart only with a 5,000-rocket buffer (a first leg burns ~3,800); ship 5 carries 3,500+ mags
CONCRETE_PER_CRAFT = 10        # 5 stone-brick + 1 iron-ore + 100 water -> 10 concrete
FIND = "local p for _,q in pairs(game.forces.player.platforms) do if q.name:find('%s',1,true) then p=q end end if not p then rcon.print('no kit ship named %s (lost or renamed): nothing to do') return end " % (SHIP, SHIP)


def lua(code):
    return L(" ".join(code.split())).strip()


def tolua(rows):
    """[(name, quality, qty)] -> Lua table literal."""
    return "{" + ",".join("{'%s','%s',%d}" % r for r in rows) + "}"


# ------------------------------------------------------------------ needs
NEEDS = ("local s=game.surfaces.aquilo local f=game.forces.player local R={} for _,r in pairs(s.find_entities_filtered{type='roboport',force=f}) do R[#R+1]=r.position end "
         "local function cov(p) for _,r in ipairs(R) do if math.abs(p.x-r.x)<=55 and math.abs(p.y-r.y)<=55 then return true end end return false end "
         "local net=(function() local b for _,r in pairs(game.surfaces.aquilo.find_entities_filtered{type='roboport'}) do local n=r.logistic_network if n and (not b or #n.cells>#b.cells) then b=n end end return b end)() local need={} "
         "for _,g in pairs(s.find_entities_filtered{type='entity-ghost',force=f}) do local inn=cov(g.position) for _,it in pairs(g.ghost_prototype.items_to_place_this) do "
         "local k=it.name..' '..g.quality.name local e=need[k] if not e then e={0,0} need[k]=e end if inn then e[1]=e[1]+it.count else e[2]=e[2]+it.count end end end "
         "local o={} for k,e in pairs(need) do local n,q=k:match('(%S+) (%S+)') o[#o+1]='E '..n..' '..q..' '..e[1]..' '..e[2]..' '..net.get_item_count{name=n,quality=q} end "
         "local occ={} for _,e in pairs(s.find_entities_filtered{force=f,type={'assembling-machine','rocket-silo','roboport','reactor','heating-tower','lab','generator','heat-exchanger','storage-tank','furnace','cargo-landing-pad','mining-drill','pumpjack'}}) do "
         "local b=e.bounding_box for x=math.floor(b.left_top.x)-2,math.floor(b.right_bottom.x)+2 do for y=math.floor(b.left_top.y)-2,math.floor(b.right_bottom.y)+2 do occ[x..','..y]=1 end end end "
         "local c={tot=0,inn=0,water=0,heavy=0,plat=0,platin=0} local box={} for _,g in pairs(s.find_entities_filtered{type='tile-ghost',force=f}) do local p=g.position "
         "if g.ghost_name=='concrete' then c.tot=c.tot+1 local inn=cov(p) if inn then c.inn=c.inn+1 end if s.get_tile(p).collides_with('water_tile') then c.water=c.water+1 "
         "elseif inn then local h=occ[math.floor(p.x)..','..math.floor(p.y)] if h then c.heavy=c.heavy+1 end local k=(math.floor(p.x/20)*20)..','..(math.floor(p.y/20)*20) box[k]=(box[k] or 0)+1 end "
         "elseif g.ghost_name=='ice-platform' then c.plat=c.plat+1 if cov(p) then c.platin=c.platin+1 end end end "
         "o[#o+1]='T '..c.tot..' '..c.inn..' '..c.water..' '..c.heavy..' '..c.plat..' '..c.platin..' '..net.get_item_count('concrete')..' '..net.get_item_count('stone-brick')..' '..net.get_item_count('iron-ore') "
         "local bl={} for k,v in pairs(box) do bl[#bl+1]={k,v} end table.sort(bl,function(a,b) return a[2]>b[2] end) for i=1,math.min(8,#bl) do o[#o+1]='B '..bl[i][1]..' '..bl[i][2] end "
         "rcon.print(table.concat(o," + NL + "))")


def weights(names):
    out = lua("local o={} for _,n in ipairs{%s} do local p=prototypes.item[n] if p then o[#o+1]=n..' '..p.weight..' '..p.stack_size end end rcon.print(table.concat(o,';'))" % ",".join("'%s'" % n for n in sorted(set(names))))
    w = {}
    for t in out.split(";"):
        if t.strip():
            n, wt, st = t.split()
            w[n] = (float(wt), int(st))
    return w


def read_needs():
    out = lua(NEEDS)
    ents, tiles, boxes = [], None, []
    for ln in out.split("\n"):
        t = ln.split()
        if not t:
            continue
        if t[0] == "E":
            ents.append({"item": t[1], "q": t[2], "in": int(t[3]), "out": int(t[4]), "stock": int(t[5])})
        elif t[0] == "T":
            v = [int(x) for x in t[1:]]
            tiles = dict(zip(("concrete", "concrete_in", "concrete_water", "concrete_heavy", "platform", "platform_in", "stock_concrete", "stock_brick", "stock_ore"), v))
        elif t[0] == "B":
            boxes.append((t[1], int(t[2])))
    return ents, tiles, boxes


# ------------------------------------------------------------------ where items are
def where(rows):
    """rows [(name, q)] -> {(name,q): dict(aquilo, hub, fulgora, nauvis, pad)}"""
    lst = "{" + ",".join("{'%s','%s'}" % r for r in rows) + "}"
    out = lua("local W=%s " % lst + FIND + "local hi=p.hub.get_inventory(defines.inventory.hub_main) local an=(function() local b for _,r in pairs(game.surfaces.aquilo.find_entities_filtered{type='roboport'}) do local n=r.logistic_network if n and (not b or #n.cells>#b.cells) then b=n end end return b end)() "
              "local nn=game.surfaces.nauvis.find_entities_filtered{type='roboport',force='player'}[1].logistic_network local fs=game.surfaces.fulgora local ch=fs.find_entities_filtered{type={'container','logistic-container'}} "
              "local fp=fs.find_entities_filtered{type='cargo-landing-pad'}[1].get_inventory(defines.inventory.cargo_landing_pad_main) local o={} "
              "for _,w in ipairs(W) do local n=0 for _,e in pairs(ch) do n=n+e.get_inventory(defines.inventory.chest).get_item_count{name=w[1],quality=w[2]} end "
              "o[#o+1]=w[1]..' '..w[2]..' '..an.get_item_count{name=w[1],quality=w[2]}..' '..hi.get_item_count{name=w[1],quality=w[2]}..' '..n..' '..nn.get_item_count{name=w[1],quality=w[2]}..' '..fp.get_item_count{name=w[1],quality=w[2]} end "
              "rcon.print(table.concat(o," + NL + "))")
    res = {}
    for ln in out.split("\n"):
        t = ln.split()
        if len(t) == 7:
            res[(t[0], t[1])] = dict(aquilo=int(t[2]), hub=int(t[3]), fulgora=int(t[4]), nauvis=int(t[5]), pad=int(t[6]))
    return res


def needs(show=True):
    ents, tiles, boxes = read_needs()
    w = weights([e["item"] for e in ents] + ["concrete", "stone-brick", "iron-ore"])
    src = where([(e["item"], e["q"]) for e in ents] + [("stone-brick", "normal"), ("iron-ore", "normal")])
    if show:
        print("ENTITY GHOSTS by item and quality (a ghost asks for exactly its quality):")
        print("%-24s %-7s %6s %6s %6s %6s %6s %6s %7s" % ("item", "quality", "inside", "outside", "aq net", "aboard", "fulg", "nauvis", "kg"))
        for e in sorted(ents, key=lambda e: -(e["in"] + e["out"])):
            s = src.get((e["item"], e["q"]), {})
            print("%-24s %-7s %6d %6d %6d %6d %6d %6d %7.0f" % (e["item"], e["q"], e["in"], e["out"], e["stock"], s.get("hub", 0), s.get("fulgora", 0), s.get("nauvis", 0), (e["in"] + e["out"]) * w[e["item"]][0] / 1000))
    if show and tiles:
        t = tiles
        buildable = t["concrete_in"] - t["concrete_water"]
        print("CONCRETE ghosts %d: inside coverage %d, on water %d (wait for a platform), next to a machine (heavy) %d; network stock concrete %d, bricks %d, ore %d" % (
            t["concrete"], t["concrete_in"], t["concrete_water"], t["concrete_heavy"], t["stock_concrete"], t["stock_brick"], t["stock_ore"]))
        print("  weight if shipped as concrete: %.0f kg = %.1f rocket loads; as ingredients (5 bricks + 1 ore per 10): %.0f kg = %.1f loads (%.1fx lighter)" % (
            t["concrete"] * w["concrete"][0] / 1000, t["concrete"] * w["concrete"][0] / 1e6,
            math.ceil(t["concrete"] / 10) * (5 * w["stone-brick"][0] + w["iron-ore"][0]) / 1000, math.ceil(t["concrete"] / 10) * (5 * w["stone-brick"][0] + w["iron-ore"][0]) / 1e6,
            10 * w["concrete"][0] / (5 * w["stone-brick"][0] + w["iron-ore"][0])))
        print("  busiest 20x20 boxes (inside coverage, on land): " + ", ".join("%s: %d" % b for b in boxes))
        print("ICE-PLATFORM ghosts %d (inside coverage %d; the works make them, only coverage limits the rest)" % (t["platform"], t["platform_in"]))
    return ents, tiles, w, src


# ------------------------------------------------------------------ kit
# consumables Aquilo burns that no ghost asks for (the Captain, 2026-11-14: "set up a fuel cell supply to Aquilo"); the reactor's feed chest
# holds 50 more on top (requester contents are not counted by the network)
# (2026-11-14, "I really want Aquilo science flowing"): the silo stopped at 8/50 rocket parts with 0 LDS on Aquilo while 3,738 cryo packs
# waited; and 40 logistic robots (all busy) load a 1000-pack rocket in ~2 minutes. LDS 300 = 6 rockets of parts; robots go to the network's
# intake through robot_network.py (demand-gated), no Nauvis shuttle reaches Aquilo's pad so the kit carries them.
AQUILO_STOCK_FIRST = {"low-density-structure": 300, "logistic-robot": 60, "processing-unit": 300}   # science: before the ghost items
AQUILO_STOCK = {"uranium-fuel-cell": 100}                                                           # after the ghost items


def kit(loads=8.0, concrete=None, show=True):
    """Kit = entity-ghost items (inside coverage first) at exact quality + ingredients for `concrete` concrete, within `loads` rocket loads."""
    ents, tiles, w, src = needs(show=False)
    budget = loads * ROCKET_KG * 1000.0
    rows, unsourced = [], []
    used = 0.0

    def take(item, q, want, why):
        nonlocal used
        s = src.get((item, q), {})
        have = s.get("fulgora", 0) + s.get("nauvis", 0) + s.get("hub", 0)
        got = min(want, have)
        got = int(min(got, max(0, (budget - used)) // w[item][0]))
        if got > 0:
            rows.append((item, q, got, why))
            used += got * w[item][0]
        if got < want:
            unsourced.append((item, q, want - got, "no stock at that quality" if have < want else "weight budget"))

    stock = where([(n, "normal") for n in list(AQUILO_STOCK_FIRST) + list(AQUILO_STOCK)])
    w.update(weights(list(AQUILO_STOCK_FIRST) + list(AQUILO_STOCK)))
    src.update(stock)

    def top_up(targets):
        for n, target in targets.items():
            s = stock.get((n, "normal"), {})
            want = target - s.get("aquilo", 0) - s.get("hub", 0)
            if want > 0:
                take(n, "normal", want, "Aquilo stock target %d" % target)

    top_up(AQUILO_STOCK_FIRST)
    for e in sorted(ents, key=lambda e: (-(e["in"] > 0), -(e["in"] + e["out"]))):
        short = e["in"] + e["out"] - e["stock"]
        if short > 0:
            take(e["item"], e["q"], short, "ghost" + ("" if e["in"] else " (outside coverage)"))
    if tiles:
        buildable = max(0, tiles["concrete_in"] - tiles["concrete_water"] - tiles["stock_concrete"])
        n = buildable if concrete is None else min(concrete, buildable)
        crafts = math.ceil(n / CONCRETE_PER_CRAFT)
        if crafts:
            bricks_have = tiles["stock_brick"]
            take("stone-brick", "normal", max(0, 5 * crafts - bricks_have), "concrete works: %d concrete" % n)
            take("iron-ore", "normal", max(0, crafts - tiles["stock_ore"]), "concrete works")
    # standing stock on Aquilo (consumables no ghost asks for): top up to the target, counting what is aboard the ship
    top_up(AQUILO_STOCK)
    if show:
        print("KIT within %.1f rocket loads (%.0f kg used = %.2f loads):" % (loads, used / 1000, used / 1e6))
        for r in rows:
            print("  %-24s %-7s %6d   %7.0f kg  %s" % (r[0], r[1], r[2], r[2] * w[r[0]][0] / 1000, r[3]))
        for u in unsourced:
            print("  NOT SENT %-24s %-7s %6d  (%s)" % u)
    return rows, unsourced, w


# ------------------------------------------------------------------ stage
STAGE = ("local fs=game.surfaces.fulgora local nn=game.surfaces.nauvis.find_entities_filtered{type='roboport',force='player'}[1].logistic_network " + FIND +
         "local hi=p.hub.get_inventory(defines.inventory.hub_main) local ch=fs.find_entities_filtered{type={'container','logistic-container'}} local o={} "
         "local function pull(inv,n,q,need) local k=inv.get_item_count{name=n,quality=q} k=math.min(k,need) if k<=0 then return 0 end local put=k if APPLY then put=hi.insert{name=n,quality=q,count=k} if put>0 then inv.remove{name=n,quality=q,count=put} end end return put end "
         "for _,r in ipairs(KIT) do local n,q,want=r[1],r[2],r[3] local need=want-hi.get_item_count{name=n,quality=q} local from=0 if need>0 then "
         "for _,e in pairs(ch) do if need<=0 then break end local g=0 if e.name=='passive-provider-chest' or e.name=='storage-chest' then g=pull(e.get_inventory(defines.inventory.chest),n,q,need) end need=need-g from=from+g end "
         "local nf=0 for _,pt in pairs(nn.storages) do if need<=0 then break end local ok,inv=pcall(function() return pt.get_inventory(defines.inventory.chest) end) if ok and inv then local g=pull(inv,n,q,need) need=need-g nf=nf+g end end "
         "for _,pt in pairs(nn.providers) do if need<=0 then break end local ok,inv=pcall(function() return pt.get_inventory(defines.inventory.chest) end) if ok and inv then local g=pull(inv,n,q,need) need=need-g nf=nf+g end end "
         "o[#o+1]=n..'/'..q..' want '..want..' +'..(from+nf)..' (fulgora '..from..', nauvis '..nf..') short '..math.max(0,need) end end "
         "rcon.print(table.concat(o," + NL + ")..string.char(10)..'hub free slots '..hi.count_empty_stacks())")


def stage(apply=False, loads=8.0, concrete=None):
    rows, _, _ = kit(loads, concrete, show=False)
    if not rows:
        print("empty kit: nothing to stage")
        return
    print(lua(STAGE.replace("KIT", tolua([(r[0], r[1], r[2]) for r in rows])).replace("APPLY", "true" if apply else "false")))
    if not apply:
        print("(dry run: nothing moved) use --apply")


# ------------------------------------------------------------------ apply: ship sections + schedule
def apply_sections(apply=False, loads=8.0, concrete=None):
    rows, _, w = kit(loads, concrete, show=False)
    rows = [r for r in rows if r[0] not in SHIP_OWN]
    if not rows:
        print("empty kit: sections not changed")
        return
    kitlua = tolua([(r[0], r[1], r[2]) for r in rows])
    code = (FIND + "local pt for _,q in pairs(p.hub.get_logistic_point()) do if q.mode==defines.logistic_mode.requester then pt=q end end local K=" + kitlua + " "
            "local function drop(g) for i=pt.sections_count,1,-1 do if pt.sections[i].group==g then pt.remove_section(i) end end end drop('" + GHOST_SEC + "') drop('" + GHOST_DROP + "') "
            "local s=pt.add_section('" + GHOST_SEC + "') local d=pt.add_section('" + GHOST_DROP + "') for i,k in ipairs(K) do "
            "s.set_slot(i,{value={type='item',name=k[1],quality=k[2]},min=k[3],max=100000,import_from='fulgora',request_from='planet'}) "
            "pcall(function() local fl=s.filters[i] fl.minimum_delivery_count=math.min(k[3],math.floor(1000000/prototypes.item[k[1]].weight)) s.set_slot(i,fl) end) "
            "d.set_slot(i,{value={type='item',name=k[1],quality=k[2]},min=0,max=0,import_from='aquilo',request_from='planet'}) end "
            "local sch=p.schedule local rec=sch.records[2] local mine={} for _,k in ipairs(K) do mine[k[1]]=k end local keep={} local nt=nil for _,x in pairs(rec.wait_conditions) do "
            "local nm=x.condition and x.condition.first_signal and x.condition.first_signal.name if not (nm and mine[nm] and x.type=='item_count' and x.condition.comparator=='<') then keep[#keep+1]=x end end "
            "local at=#keep+1 for i,x in ipairs(keep) do if x.compare_type=='or' then at=i break end end local added=0 "
            # no "hub holds < 1 of X" leave rule any more (2026-11-15): one item the pad could not take held Fulgora-Aquilo 4 at Aquilo for hours;
            # the drop section still unloads, and the ship leaves on time and fuel.
            "rec.wait_conditions=keep sch.records[2]=rec p.schedule=sch "            "rcon.print('sections '..'" + GHOST_SEC + "'..' '..#K..' items, leave rule +'..added..' conditions')")
    if not apply:
        print("dry run: would write %d items to %s / %s:" % (len(rows), GHOST_SEC, GHOST_DROP))
        for r in rows:
            print("   %s/%s %d" % (r[0], r[1], r[2]))
        return
    print(lua(code))


# ------------------------------------------------------------------ reload
RELOAD = ("local o={} local nn=game.surfaces.nauvis.find_entities_filtered{type='roboport',force='player'}[1].logistic_network local want={['ROCKET']=RN,['uranium-rounds-magazine']=MN} "
          "local H=HOMES for _,p in pairs(game.forces.player.platforms) do local home=nil for hn,hv in pairs(H) do if p.name:find(hn,1,true) then home=hv end end if home and p.hub then local loc=p.space_location and p.space_location.name or 'flight' "
          "local inv=p.hub.get_inventory(defines.inventory.hub_main) if loc~=home then o[#o+1]=p.name:sub(-24)..' not parked at '..home..' ('..loc..'): skipped' else "
          "local r={} for k,target in pairs(want) do local need=target-inv.get_item_count(k) local got=0 "
          "if need>0 then local cells=game.surfaces.nauvis.find_entities_filtered{name='steel-chest',area={{-330,-105},{-280,-80}}} for _,list in ipairs{cells,nn.providers,nn.storages} do for _,pt in pairs(list) do if got>=need then break end local ok,ci=pcall(function() return pt.get_inventory(defines.inventory.chest) end) "
          "if ok and ci then local n=math.min(need-got,ci.get_item_count(k)) if n>0 then local put=n if APPLY then put=inv.insert{name=k,count=n} if put>0 then ci.remove{name=k,count=put} end end got=got+put end end end end end "
          "r[#r+1]=k..' '..inv.get_item_count(k)..'/'..target..(got>0 and (' (+'..got..(APPLY and '' or ' dry')..')') or '') end "
          "if not APPLY then end o[#o+1]=p.name:sub(-24)..' at '..home..': '..table.concat(r,', ') end end end rcon.print(table.concat(o," + NL + "))")


def reload(apply=False, rockets=ROCKET_TARGET, mags=MAG_TARGET, plain=False):
    homes = "{" + ",".join("['%s']='%s'" % kv for kv in SHIPS.items()) + "}"
    code = RELOAD.replace("HOMES", homes).replace("ROCKET", "rocket" if plain else "explosive-rocket").replace("RN", str(rockets)).replace("MN", str(mags)).replace("APPLY", "true" if apply else "false")
    out = lua(code)
    return out


# ------------------------------------------------------------------ concrete works
# ice-melting chemical plant (ice from a requester chest) -> one pipe -> concrete assembler (bricks + ore from a requester chest) -> provider chest.
# Geometry follows aquilo_cryo.platform_plan: inserter direction = the side it picks from; an assembler facing N has its water port on the top middle,
# a chemical plant facing N its first fluid output on the bottom left, so one pipe tile joins them.
WORKS_BOX = (-14, -24, 62, 16)
ICE_ASK, BRICK_ASK, ORE_ASK = 400, 500, 100


def works_plan(ax, ay):
    import aquilo_cryo as C
    P = C.Plan()
    P.add("assembling-machine-3", ax, ay, 3, 3, C.N, recipe="concrete")
    P.add("chemical-plant", ax + 1, ay - 4, 3, 3, C.N, recipe="ice-melting")
    P.pipe(ax + 1, ay - 1)
    P.add("fast-inserter", ax + 4, ay - 3, d=C.E)
    P.add("requester-chest", ax + 5, ay - 3)
    P.add("fast-inserter", ax + 3, ay + 1, d=C.E)
    P.add("requester-chest", ax + 4, ay + 1)
    P.add("fast-inserter", ax - 1, ay + 1, d=C.E)
    P.add("passive-provider-chest", ax - 2, ay + 1)
    P.add("substation", ax - 3, ay - 3, 2, 2)
    return P


WORKS_ASK = ("local s=game.surfaces.aquilo local function ask(x,y,items) local c=s.find_entities_filtered{name='requester-chest',position={x,y},radius=0.4}[1] if not c then return 'no chest' end "
             "local pt=c.get_logistic_point(defines.logistic_member_index.logistic_container) local sec=pt.sections[1] or pt.add_section() sec.filters={} for i,it in ipairs(items) do sec.set_slot(i,{value={type='item',name=it[1],quality='normal'},min=it[2]}) end return 'ok' end "
             "rcon.print(ask(AX+5.5,AY-2.5,{{'ice',ICE}})..' '..ask(AX+4.5,AY+1.5,{{'stone-brick',BRICK},{'iron-ore',ORE}}))")


def works(apply=False):
    import aquilo_cryo as C
    if lua("local s=game.surfaces.aquilo local a=s.find_entities_filtered{name='assembling-machine-3'} local n=0 for _,e in pairs(a) do local r=e.get_recipe() if r and r.name=='concrete' then n=n+1 end end rcon.print(n)") != "0":
        print("a concrete assembler already stands: nothing to build")
        return
    grid = C.fetch(WORKS_BOX)
    net = C.heat_tiles(WORKS_BOX)
    rps = [tuple(float(v) for v in r.split(",")) for r in lua("local o={} for _,r in pairs(game.surfaces.aquilo.find_entities_filtered{type='roboport'}) do o[#o+1]=r.position.x..','..r.position.y end rcon.print(table.concat(o,' '))").split()]
    poles = [tuple(float(v) for v in r.split(",")) for r in lua("local o={} for _,r in pairs(game.surfaces.aquilo.find_entities_filtered{name='substation'}) do o[#o+1]=r.position.x..','..r.position.y end rcon.print(table.concat(o,' '))").split()]
    cands = []
    x0, y0, x1, y1 = WORKS_BOX
    for ax in range(x0 + 6, x1 - 8):
        for ay in range(y0 + 6, y1 - 6):
            P = works_plan(ax, ay)
            occ = P.occupied()
            if any(grid.get(t) not in C.USABLE or grid.get(t) in ("i", "P", "~") for t in occ):
                continue
            cx, cy = ax + 1.5, ay + 1.5
            if not any(abs(cx - r[0]) <= 22 and abs(cy - r[1]) <= 22 for r in rps):
                continue
            if not any(abs(cx - p[0]) <= 20 and abs(cy - p[1]) <= 20 for p in poles):
                continue
            d = min(abs(t[0] - cx) + abs(t[1] - cy) for t in net) if net else 99
            cands.append((d, ax, ay))
    cands.sort()
    print("candidate sites:", len(cands))
    best = None
    for d, ax, ay in cands[:25]:
        P = works_plan(ax, ay)
        H, cold = C.heat_plan(P, grid, net)
        if cold:
            continue
        if best is None or len(H) < best[0]:
            best = (len(H), ax, ay)
    if not best:
        print("no site with a heat route")
        return
    n, ax, ay = best
    print("site: assembler top-left (%d,%d), %d new heat pipes" % (ax, ay, n))
    P = works_plan(ax, ay)
    C.build(P, grid, net, apply)
    if apply:
        import time
        time.sleep(2)
        print(lua(WORKS_ASK.replace("AX", str(ax)).replace("AY", str(ay)).replace("ICE", str(ICE_ASK)).replace("BRICK", str(BRICK_ASK)).replace("ORE", str(ORE_ASK))))


# ------------------------------------------------------------------ status / verify / cycle
def ship_state():
    return lua(FIND + "local hi=p.hub.get_inventory(defines.inventory.hub_main) rcon.print(p.name:sub(-24)..' at '..(p.space_location and p.space_location.name or 'flight')..' state '..p.state..' paused '..tostring(p.paused)"
               "..' | explosive '..hi.get_item_count('explosive-rocket')..' plain '..hi.get_item_count('rocket')..' mags '..hi.get_item_count('uranium-rounds-magazine')..' | hub free '..hi.count_empty_stacks()..'/'..#hi..' trash '..p.hub.get_inventory(defines.inventory.hub_trash).get_item_count())")


def status():
    print(ship_state())
    needs()
    kit()


# ------------------------------------------------------------------ pad overflow
# The Aquilo pad has 80 slots; a hub's trash lands there only when slots are free. Bulk ore from the other ship filled 57 of them (2026-11-14) and held
# a kit's drop for minutes. Two epic storage chests (19.5,-11.5) (20.5,-11.5), inside the roboport network, take the ore: factory-made items moved, not made.
OVERFLOW = [(19.5, -11.5), (20.5, -11.5)]
PAD_MIN_FREE = 25


def overflow():
    return lua("local s=game.surfaces.aquilo local pad=s.find_entities_filtered{type='cargo-landing-pad'}[1].get_inventory(defines.inventory.cargo_landing_pad_main) local moved=0 "
               "if pad.count_empty_stacks()<%d then for _,x in ipairs{%s} do local c=s.find_entities_filtered{name='storage-chest',position={x,%s},radius=0.3}[1] if c then local ci=c.get_inventory(defines.inventory.chest) "
               "local n=math.min(pad.get_item_count('iron-ore')-400,ci.get_insertable_count('iron-ore')) if n>0 then local put=ci.insert{name='iron-ore',count=n} if put>0 then pad.remove{name='iron-ore',count=put} moved=moved+put end end end end end "
               "rcon.print('pad free '..pad.count_empty_stacks()..', ore moved to overflow chests '..moved)" % (PAD_MIN_FREE, ",".join(str(o[0]) for o in OVERFLOW), OVERFLOW[0][1]))


# ------------------------------------------------------------------ baseline / verify / relay / cycle
BASE = "D:/Aaron/development/AI-factorio/snapshots/aquilo_build_baseline.json"


def counts():
    ents, tiles, _ = read_needs()
    c = {"%s/%s" % (e["item"], e["q"]): e["in"] + e["out"] for e in ents}
    c["concrete-ghosts"] = tiles["concrete"]
    c["concrete-stock"] = tiles["stock_concrete"]
    c["ice-platform-ghosts"] = tiles["platform"]
    return c


def baseline():
    c = counts()
    json.dump(c, open(BASE, "w"), indent=1)
    print("baseline saved:", json.dumps(c))


def verify():
    print(ship_state())
    now = counts()
    try:
        before = json.load(open(BASE))
    except OSError:
        before = {}
    print("%-34s %8s %8s %8s" % ("ghosts / stock", "before", "now", "built"))
    for k in sorted(set(before) | set(now)):
        b, n = before.get(k), now.get(k, 0)
        print("%-34s %8s %8d %8s" % (k, "-" if b is None else b, n, "" if b is None or k.endswith("stock") else b - n))
    print(lua("local s=game.surfaces.aquilo local o={} for _,e in pairs(s.find_entities_filtered{name='assembling-machine-3'}) do local r=e.get_recipe() if r and r.name=='concrete' then o[#o+1]='works assembler status '..tostring(e.status)..' products '..e.products_finished..' output chest see provider' end end "
              "local pad=s.find_entities_filtered{type='cargo-landing-pad'}[1].get_inventory(defines.inventory.cargo_landing_pad_main) o[#o+1]='aquilo pad stone-brick '..pad.get_item_count('stone-brick')..' pipe '..pad.get_item_count('pipe') rcon.print(table.concat(o,string.char(10)))"))


RELAY_GROUP = "aq-ghost-relay"


def relay(apply=False, loads=8.0, concrete=None):
    """Nauvis -> Fulgora leg of the chain: the group `aq-ghost-relay` (ours alone) on `Nauvis-Fulgora 2 Shuttle` (import_from nauvis) and on the Fulgora pad.
    Off by default: the Fulgora pad has 0 free slots (a delivery would land in the trash), so the run uses `stage` instead."""
    rows, _, _ = kit(loads, concrete, show=False)
    rows = [r for r in rows if r[0] not in SHIP_OWN]
    print("relay would ask Nauvis for:", ", ".join("%s/%s %d" % (r[0], r[1], r[2]) for r in rows))
    if not apply:
        return
    k = tolua([(r[0], r[1], r[2]) for r in rows])
    # one group name per request point: a shared group copies one list onto every point (the pad's no-import list overwrote the shuttle's)
    print(lua("local K=" + k + " local function fill(pt,imp) local G='" + RELAY_GROUP + "'..(imp and ' ship' or ' pad') local function drop(g) for i=pt.sections_count,1,-1 do if pt.sections[i].group==g then pt.remove_section(i) end end end drop('" + RELAY_GROUP + "') drop(G) local s=pt.add_section(G) "
              "for i,r in ipairs(K) do local sl={value={type='item',name=r[1],quality=r[2]},min=r[3]} if imp then sl.max=r[3] sl.import_from=imp end s.set_slot(i,sl) end end "
              "local n=0 for _,p in pairs(game.forces.player.platforms) do if p.name:find('Nauvis-Fulgora 2 Shuttle',1,true) and p.hub then for _,pt in pairs(p.hub.get_logistic_point()) do if pt.mode==defines.logistic_mode.requester then fill(pt,'nauvis') n=n+1 end end end end "
              "for _,pt in pairs(game.surfaces.fulgora.find_entities_filtered{type='cargo-landing-pad'}[1].get_logistic_point()) do if pt.mode==defines.logistic_mode.requester then fill(pt,nil) n=n+1 end end rcon.print('relay group written on '..n..' request points')"))


KIT_CHEST = (-193.5, -221.5)   # Nauvis requester chest the Replicator fills with what Aquilo's ghosts need and no one stocks
RELEASE = ("local c=game.surfaces.nauvis.find_entities_filtered{name='requester-chest',position={%s,%s},radius=0.5}[1] if not c then rcon.print('no kit chest') return end "
           "local nn=c.logistic_network local inv=c.get_inventory(defines.inventory.chest) local moved=0 for _,it in pairs(inv.get_contents()) do local left=it.count "
           "for _,st in pairs(nn.storages) do if left<=0 then break end if st.name=='storage-chest' then local n=st.insert{name=it.name,quality=it.quality,count=left} if n>0 then inv.remove{name=it.name,quality=it.quality,count=n} left=left-n moved=moved+n end end end end "
           "rcon.print('kit chest released '..moved..' items to Nauvis storage')")
ASK = ("local c=game.surfaces.nauvis.find_entities_filtered{name='requester-chest',position={%s,%s},radius=0.5}[1] local nn=c.logistic_network local pt=c.get_logistic_point(defines.logistic_member_index.logistic_container) "
       "local sec=pt.sections[1] or pt.add_section() local keep={} for i,f in pairs(sec.filters) do if f.value and nn.get_item_count(f.value.name)==0 then keep[f.value.name]=f.min end end "
       "for _,it in ipairs({%s}) do keep[it[1]]=it[2] end sec.filters={} local i=0 local held=0 for nm,mn in pairs(keep) do if nn.get_item_count(nm)==0 then i=i+1 sec.set_slot(i,{value={type='item',name=nm,quality='normal'},min=mn}) else held=held+1 end end "
       "rcon.print('kit chest asks '..i..' (held back '..held..': stock waiting for a ship)')")


def release(unsourced=None):
    """Move what the Replicator made into the kit chest on to Nauvis storage (a requester chest's contents are invisible to
    network counts, so `kit` never shipped them - found 2026-11-14 with 81 heat pipes sitting there), then ask for the shortfall left.
    The chest only asks for items Nauvis storage holds NONE of: a requester pulls from storage, so asking while released stock waits
    for a ship pulled it straight back (seen 2026-11-14: 55 heat pipes back in the chest, 0 made). Always re-filters, so a released
    item stops being requested at once."""
    out = lua(RELEASE % KIT_CHEST)
    want = {}
    for item, q, missing, why in (unsourced or []):
        if q == "normal" and why.startswith("no stock"):
            want[item] = want.get(item, 0) + missing
    out += "; " + lua(ASK % (KIT_CHEST + (",".join("{'%s',%d}" % kv for kv in sorted(want.items())),)))
    return out


def cycle(loads=8.0):
    """The autopilot step. Never raises."""
    out = []
    try:
        out.append(release())
    except Exception as exc:  # noqa: BLE001
        out.append("release error " + repr(exc))
    try:
        rows, unsourced, _ = kit(loads, None, show=False)
        try:
            out.append(release(unsourced))
        except Exception as exc:  # noqa: BLE001
            out.append("kit ask error " + repr(exc))
        loc = lua(FIND + "rcon.print(p.space_location and p.space_location.name or 'flight')")
        out.append("kit %d items (%d unsourced), ship %s" % (len(rows), len(unsourced), loc))
        if rows and loc == "fulgora":                     # sections are only rewritten while the ship is parked at Fulgora, never mid-flight
            apply_sections(True, loads, None)
    except Exception as exc:  # noqa: BLE001
        out.append("kit error " + repr(exc))
    try:                                                  # Nauvis -> Fulgora leg (2026-11-14: was off, so nothing ever left Nauvis; the Fulgora pad
        if rows:                                          # had 1/80 free slots - 3 cargo bays added, 194 slots)
            pad_free = int(lua("local i=game.surfaces.fulgora.find_entities_filtered{type='cargo-landing-pad'}[1].get_inventory(defines.inventory.cargo_landing_pad_main) rcon.print(i.count_empty_stacks())"))
            if pad_free >= 30:
                import io
                import contextlib
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    relay(True, loads, None)
                out.append("relay on (pad free %d)" % pad_free)
            else:
                out.append("relay held: Fulgora pad free %d < 30" % pad_free)
    except Exception as exc:  # noqa: BLE001
        out.append("kit error " + repr(exc))
    try:
        out.append(overflow())
    except Exception as exc:  # noqa: BLE001
        out.append("overflow error " + repr(exc))
    try:
        out.append(reload(True))
    except Exception as exc:  # noqa: BLE001
        out.append("reload error " + repr(exc))
    return " | ".join(out).replace(chr(10), " ; ")


def main():
    a = sys.argv
    step = a[1] if len(a) > 1 else "status"
    apply = "--apply" in a

    def opt(name, default, cast=float):
        return cast(a[a.index(name) + 1]) if name in a else default
    loads = opt("--loads", 8.0)
    conc = opt("--concrete", None, int)
    if step == "status":
        status()
    elif step == "needs":
        needs()
    elif step == "kit":
        kit(loads, conc)
    elif step == "stage":
        stage(apply, loads, conc)
    elif step == "apply":
        apply_sections(apply, loads, conc)
    elif step == "reload":
        print(reload(apply, opt("--rockets", ROCKET_TARGET, int), opt("--mags", MAG_TARGET, int), "--plain" in a))
    elif step == "baseline":
        baseline()
    elif step == "verify":
        verify()
    elif step == "relay":
        relay(apply, loads, conc)
    elif step == "cycle":
        print(cycle(loads))
    elif step == "works":
        works(apply)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
