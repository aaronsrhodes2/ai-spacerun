#!/usr/bin/env python3
"""Aquilo supply line (the Captain, 2026-11-14: "fix logistics out to Aquilo so it can get ground items fulfilled").
Aquilo cannot make holmium plate, processing units, low density structure, robots, modules, fuel cells, superconductors, concrete.
They come up from the planets by the proven ship `Fulgora-Aquilo 4 Shuttle` (platform 36, explosive-rocket fit, hold control).

CHAIN (read SKILL.md 'Aquilo supply line'):
  1. SOURCE   Fulgora makes holmium plate (5 solution plants + 2 EM plants, provider chests at (146.5/151.5,-132.5)) and holds PU, superconductors,
              robots. Nauvis items (LDS, modules, cells, rocket fuel) reach Fulgora by the Nauvis-Fulgora shuttles (not changed here).
  2. LIFT     ship 4 in Fulgora orbit has a section 'aq-supply-36' (import_from fulgora, planet): the Fulgora silo (transitional requests, robots
              load it from the network) lifts each item; pods land on the ship, also while it is leaving.
  3. FLY      schedule: Fulgora stop waits (circuit on fuel/oxidizer, item_count on cargo and ammunition; NO time wait: it cannot be trusted).
  4. DROP     at Aquilo a section 'aq-drop-36' (min = max = 0, import_from aquilo) makes the cargo hub TRASH; trash goes down to the Aquilo pad
              (an UNREQUESTED item never leaves a hub: lds_pickup.py). The Aquilo stop leaves when every kit item_count is < 1, or
              the ammunition reserve is reached (explosive-rocket <= RESERVE), whichever first.
  5. AMMO     every round trip burns about 1,800 explosive rockets: LOAD EVERYTHING IN ONE TRIP (`ammo N` moves finished rockets from the Nauvis
              cells into the hub by Lua, like aquilo_gleba_route.py load).
Steps:  status | plan | apply [--route fulgora] [--go] | ammo N | stage | verify | off
  apply   writes the two sections (read back) and the schedule (paused unless --go); `fit explosive` is done once by aquilo_ship3.py fit explosive
  stage   moves factory-made items by Lua from Fulgora provider chests onto the ship hub for whatever the silo has not delivered (--lua); never spawns
  off     removes the two sections and puts the old Fulgora/Aquilo schedule shape back (no kit gates)
Usage: aquilo_supply_line.py status | plan | apply [--route fulgora] [--go] | ammo N | stage [--lua] | verify | off"""
import sys
import time

from _game import tools

L = tools["run_lua"]
SHIP = "Fulgora-Aquilo 4"
IDX = 36
SUPPLY, DROP = "aq-supply-%d" % IDX, "aq-drop-%d" % IDX
# item -> amount per trip (the proven load, from what exists at Fulgora; a standing kit would use the list in aquilo_delivery_list.txt)
KIT = {"holmium-plate": 800, "processing-unit": 100, "superconductor": 100, "construction-robot": 30, "refined-concrete": 40}
AMMO_GATE = 2300       # explosive rockets aboard to leave Fulgora (a trip burns ~1,800; outbound ~1,000, return ~800)
RESERVE = 1000         # leave Aquilo at once when rockets fall to this (the return needs ~800)
MAGS_GATE = 1500
FIND = "local p for _,q in pairs(game.forces.player.platforms) do if q.name:find('%s',1,true) then p=q end end " % SHIP
PT = "local pt for _,q in pairs(p.hub.get_logistic_point()) do if q.mode==defines.logistic_mode.requester then pt=q end end "
NL = "string.char(10)"


def kit_lua():
    return "{" + ",".join("{'%s',%d}" % kv for kv in KIT.items()) + "}"


def read_list(path="D:/Aaron/development/AI-factorio/scripts/aquilo_delivery_list.txt"):
    rows = {}
    for line in open(path, encoding="utf-8"):
        t = line.split()
        if len(t) == 3 and not line.lstrip().startswith("#") and t[1].isdigit() and t[2].isdigit():
            rows[t[0]] = (int(t[1]), int(t[2]))      # a later line (the science agent's block) replaces an earlier one
    return rows


APPLY = (FIND + PT + "local function drop(g) for i=pt.sections_count,1,-1 do if pt.sections[i].group==g then pt.remove_section(i) end end end drop('" + SUPPLY + "') drop('" + DROP + "') "
         "local s=pt.add_section('" + SUPPLY + "') local d=pt.add_section('" + DROP + "') local i=0 for _,k in ipairs(KITLUA) do i=i+1 "
         "s.set_slot(i,{value={type='item',name=k[1],quality='normal'},min=k[2],max=100000,import_from='fulgora',request_from='planet'}) "
         "pcall(function() local f=s.filters[i] f.minimum_delivery_count=math.min(k[2],math.floor(1000000/prototypes.item[k[1]].weight)) s.set_slot(i,f) end) "
         "d.set_slot(i,{value={type='item',name=k[1],quality='normal'},min=0,max=0,import_from='aquilo',request_from='planet'}) end "
         "local function c(t,n,k,op,cmp) return {type='circuit',compare_type=cmp or 'and',condition={first_signal={type=t,name=n},comparator=op or '>=',constant=k}} end "
         "local function ic(n,k,op,cmp) return {type='item_count',compare_type=cmp or 'and',condition={first_signal={type='item',name=n},comparator=op or '>=',constant=k}} end "
         "local f={c('fluid','thruster-fuel',40000),c('fluid','thruster-oxidizer',40000),ic('carbon',1900),ic('iron-ore',1900),ic('explosive-rocket',AGATE),ic('uranium-rounds-magazine',MGATE),ic('repair-pack',250)} "
         "for _,k in ipairs(KITLUA) do f[#f+1]=ic(k[1],k[2]) end "
         "local a={c('fluid','thruster-fuel',15000),c('fluid','thruster-oxidizer',15000)} for _,k in ipairs(KITLUA) do a[#a+1]=ic(k[1],1,'<') end a[#a+1]=ic('explosive-rocket',RES,'<=','or') "
         "local cur=1 if p.space_location and p.space_location.name=='aquilo' then cur=2 end "
         "p.schedule={current=cur,records={{station='fulgora',wait_conditions=f},{station='aquilo',wait_conditions=a}}} p.paused=PAUSED if p.space_location then p.space_location=p.space_location.name end "
         "rcon.print('schedule set, paused='..tostring(p.paused)..' state '..p.state..' current '..cur)")
READBACK = (FIND + "local o={} for _,q in pairs(p.hub.get_logistic_point()) do if q.mode==defines.logistic_mode.requester then for _,x in pairs(q.sections) do if x.group=='" + SUPPLY + "' or x.group=='" + DROP + "' then "
            "local t={} for _,fl in pairs(x.filters) do if fl.value then t[#t+1]=fl.value.name..' '..fl.min..'..'..tostring(fl.max)..' from '..tostring(fl.import_from and fl.import_from.name or fl.import_from)..'/'..tostring(fl.request_from)..' mdc='..tostring(fl.minimum_delivery_count) end end "
            "o[#o+1]='section '..x.group..' active='..tostring(x.active)..': '..table.concat(t,'; ') end end end end "
            "for i,r in pairs(p.schedule.records) do local w={} for _,x in pairs(r.wait_conditions or {}) do w[#w+1]=x.compare_type..' '..x.type..(x.condition and (' '..tostring(x.condition.first_signal and x.condition.first_signal.name)..x.condition.comparator..tostring(x.condition.constant)) or '') end o[#o+1]='stop '..i..' '..r.station..': '..table.concat(w,' | ') end "
            "rcon.print(table.concat(o," + NL + "))")
STATUS = (FIND + "local hi=p.hub.get_inventory(defines.inventory.hub_main) local kit=KITLUA local o={} "
          "o[#o+1]=p.name:sub(-24)..' at '..(p.space_location and p.space_location.name or 'flight')..' state '..p.state..' paused '..tostring(p.paused)..' hub free '..hi.count_empty_stacks()..'/'..#hi..' trash '..p.hub.get_inventory(defines.inventory.hub_trash).get_item_count() "
          "local t={} for _,k in ipairs(kit) do t[#t+1]=k[1]..' '..hi.get_item_count(k[1])..'/'..k[2] end o[#o+1]='kit aboard: '..table.concat(t,', ') "
          "o[#o+1]='ammo aboard: explosive-rocket '..hi.get_item_count('explosive-rocket')..' plain '..hi.get_item_count('rocket')..' mags '..hi.get_item_count('uranium-rounds-magazine')..' carbon '..hi.get_item_count('carbon')..' ore '..hi.get_item_count('iron-ore')..' repair '..hi.get_item_count('repair-pack') "
          "local fl={} for _,tk in pairs(p.surface.find_entities_filtered{name='storage-tank'}) do for k,v in pairs(tk.get_fluid_contents()) do fl[k]=(fl[k] or 0)+v end end o[#o+1]='fuel '..math.floor(fl['thruster-fuel'] or 0)..' oxidizer '..math.floor(fl['thruster-oxidizer'] or 0) "
          "local fp=game.surfaces.fulgora.find_entities_filtered{type='cargo-landing-pad'}[1].get_inventory(defines.inventory.cargo_landing_pad_main) local ap=game.surfaces.aquilo.find_entities_filtered{type='cargo-landing-pad'}[1].get_inventory(defines.inventory.cargo_landing_pad_main) "
          "local a={} local b={} for _,k in ipairs(kit) do a[#a+1]=k[1]..' '..fp.get_item_count(k[1]) b[#b+1]=k[1]..' '..ap.get_item_count(k[1]) end o[#o+1]='fulgora pad (free '..fp.count_empty_stacks()..'): '..table.concat(a,', ') o[#o+1]='AQUILO pad (free '..ap.count_empty_stacks()..'/'..#ap..'): '..table.concat(b,', ') "
          "local net={} for _,k in ipairs(kit) do local n=0 for _,e in pairs(game.surfaces.fulgora.find_entities_filtered{type={'container','logistic-container'}}) do n=n+e.get_inventory(defines.inventory.chest).get_item_count(k[1]) end net[#net+1]=k[1]..' '..n end o[#o+1]='fulgora chests: '..table.concat(net,', ') "
          "local si=game.surfaces.fulgora.find_entities_filtered{name='rocket-silo'}[1] o[#o+1]='fulgora silo status '..si.status..' rocket '..tostring(si.rocket~=nil)..' parts '..si.rocket_parts "
          "rcon.print(table.concat(o," + NL + "))")
AMMO = ("local s=game.surfaces.nauvis " + FIND + "local hi=p.hub.get_inventory(defines.inventory.hub_main) local want=RN local got=0 "
        "local cells={{-322,-99},{-315,-99},{-308,-99},{-322,-90},{-322,-86}} for _,c in pairs(cells) do local ch=s.find_entities_filtered{name='steel-chest',position={c[1]+6.5,c[2]+1.5},radius=0.4}[1] local inv=ch.get_inventory(defines.inventory.chest) "
        "local n=math.min(want-got,inv.get_item_count('explosive-rocket')) if n>0 then local put=hi.insert{name='explosive-rocket',count=n} if put>0 then inv.remove{name='explosive-rocket',count=put} got=got+put end end end "
        "rcon.print('moved '..got..' explosive rockets from the Nauvis cells into '..p.name:sub(-24)..' (hub now '..hi.get_item_count('explosive-rocket')..')')")
STAGE = ("local fs=game.surfaces.fulgora " + FIND + "local hi=p.hub.get_inventory(defines.inventory.hub_main) local o={} for _,k in ipairs(KITLUA) do local need=k[2]-hi.get_item_count(k[1]) local moved=0 "
         "if need>0 then for _,e in pairs(fs.find_entities_filtered{type={'logistic-container','container'}}) do if moved<need and (e.name=='passive-provider-chest' or e.name=='storage-chest') then local inv=e.get_inventory(defines.inventory.chest) "
         "local n=math.min(need-moved,inv.get_item_count(k[1])) if n>0 then local put=hi.insert{name=k[1],count=n} if put>0 then inv.remove{name=k[1],count=put} moved=moved+put end end end end end o[#o+1]=k[1]..' +'..moved..' (hub '..hi.get_item_count(k[1])..')' end "
         "rcon.print('moved from Fulgora provider/storage chests: '..table.concat(o,', '))")
OFF = (FIND + PT + "for i=pt.sections_count,1,-1 do local g=pt.sections[i].group if g=='" + SUPPLY + "' or g=='" + DROP + "' then pt.remove_section(i) end end "
       "local function c(t,n,k) return {type='circuit',compare_type='and',condition={first_signal={type=t,name=n},comparator='>=',constant=k}} end "
       "p.schedule={current=1,records={{station='fulgora',wait_conditions={c('fluid','thruster-fuel',40000),c('fluid','thruster-oxidizer',40000),c('item','carbon',3000),c('item','iron-ore',3000),c('item','explosive-rocket',4600),c('item','uranium-rounds-magazine',3000),{type='time',compare_type='and',ticks=1800}}},"
       "{station='aquilo',wait_conditions={{type='time',compare_type='and',ticks=5400},c('fluid','thruster-fuel',15000),c('fluid','thruster-oxidizer',15000)}}}} p.paused=true "
       "rcon.print('sections removed, old shape schedule set, ship PAUSED')")
CELLRATE = ("local s=game.surfaces.nauvis local tot=0 local n=0 for _,c in pairs({{-322,-99},{-315,-99},{-308,-99},{-322,-90},{-322,-86}}) do local m=s.find_entities_filtered{name='assembling-machine-3',position={c[1]+3.5,c[2]+1.5},radius=0.5}[1] "
            "if m then tot=tot+m.crafting_speed*(1+m.productivity_bonus)/8*60 n=n+1 end end rcon.print(n..' explosive cells, '..string.format('%.0f',tot)..' rockets/min at full input')")


def run(code):
    return L(code.replace("KITLUA", kit_lua()).replace("AGATE", str(AMMO_GATE)).replace("MGATE", str(MAGS_GATE)).replace("RES", str(RESERVE))).strip()


def plan():
    rows = read_list()
    w = {}
    out = tools["run_lua"]("local o={} for n,_ in pairs{%s} do local p=prototypes.item[n] if p then o[#o+1]=n..'='..p.weight..'='..p.stack_size end end rcon.print(table.concat(o,','))" % ",".join("['%s']=1" % k for k in rows))
    for t in out.strip().split(","):
        n, wt, st = t.split("=")
        w[n] = (float(wt), int(st))
    print("%-24s %9s %9s %8s %9s %9s" % ("item", "per hour", "one-off", "kg each", "rockets/h", "slots/h"))
    tr = ts = 0
    for k, (ph, oo) in rows.items():
        wt, st = w.get(k, (0, 1))
        r = ph * wt / 1e6
        tr += r
        ts += ph / st
        print("%-24s %9d %9d %8.2f %9.2f %9.1f" % (k, ph, oo, wt / 1000, r, ph / st))
    print("steady state: %.1f rocket-loads/h and %.0f hub slots/h; one-off: %.1f rocket-loads" % (tr, ts, sum(oo * w.get(k, (0, 1))[0] / 1e6 for k, (ph, oo) in rows.items())))
    print("kit of this script (per trip): " + ", ".join("%s %d" % kv for kv in KIT.items()))
    print(run(CELLRATE))


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    if step == "status":
        print(run(STATUS))
    elif step == "plan":
        plan()
    elif step == "apply":
        print(run(APPLY.replace("PAUSED", "false" if "--go" in sys.argv else "true")))
        print(run(READBACK))
    elif step == "ammo":
        print(run(AMMO.replace("RN", sys.argv[2])))
    elif step == "stage":
        print(run(STAGE) if "--lua" in sys.argv else "dry: use --lua to move chest stock onto the hub")
    elif step == "verify":
        print(run(STATUS))
        print(run(READBACK))
    elif step == "off":
        print(run(OFF))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
