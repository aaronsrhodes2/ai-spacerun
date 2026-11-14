#!/usr/bin/env python3
"""Factory status wall on Nauvis (the Captain, 2026-11-14: "Add some visualization so we can easily see what is going on in the factory").
A board of display panels (icon + short text, always shown) and small lamps (green / amber / red) standing on the clear ground south of the
silos, x -231..-219, y -186..-148, three cells across. A cell is a lamp on the left and a panel beside it, the text floats above the panel.
No wiring: `update` computes every figure with a few one-line Lua queries and writes panel texts, icons and lamp colours directly.

Usage:  factory_wall.py build [--apply]     lay the board (poles, lamps, panels) and the map tags; idempotent, dry run unless --apply
        factory_wall.py update              refresh every panel and lamp (about 1 s of RCON, 5 calls); the autopilot runs it every WALL_EVERY cycles
        factory_wall.py clear-test          remove the two test panels and the test lamp built while designing it

Colours:  GREEN good, AMBER watch, RED act, WHITE heading, GREY no data. Thresholds (change them here, nowhere else):
  power:    accumulators < 20 % or any machine on low_power -> RED; < 50 % -> AMBER; else GREEN.  Aquilo: reactor below 300 C or accumulators < 20 % -> RED, < 50 % AMBER.
  plates:   used > 1.2 x made -> RED (the stock is draining), used > made -> AMBER, else GREEN.   steel likewise.
  furnaces: more than half in full_output -> AMBER (plates backed up: a consumer is short), else GREEN.
  packs:    0 per minute -> RED; below half of the best pack's rate -> AMBER (the target is equal packs); else GREEN.
  labs:     none working -> RED; below 80 % working -> AMBER.      research: no research -> RED.
  shuttle (Aquilo):  hub magazines < 150 or no power data -> RED; < 400, paused or ghosts to rebuild -> AMBER.
  ships:    any damaged (ghosts left) -> AMBER, 3 or more -> RED; paused ships count as AMBER only for the Aquilo one.
  triangle: ghosts left -> AMBER; stalled (no tiles built since last update and ghosts left) -> RED.
  wheel stock: 0 -> RED, < 100 -> AMBER.   Aquilo: heating tower < 15 C or solid fuel 0 -> RED; fuel < 500 -> AMBER.
  silos:    any silo no_power -> RED; none working -> AMBER; some working -> GREEN.
  network stock (silo parts): 0 -> RED, < 500 -> AMBER (cliff explosives and refined concrete: < 100).
  alerts:   any damage anywhere -> AMBER (>= 20 RED); a hub with 2 or fewer free slots -> AMBER; any machine with no_power -> RED.
"""
import json
import re
import sys
import time
from pathlib import Path

from _game import tools

STATE = Path(__file__).resolve().parent.parent / "snapshots" / "fwall_state.json"
X0, Y0 = -229.5, -185.5          # lamp of the first cell; its panel is one tile east
COLS, PITCH_X, PITCH_Y = 3, 4, 2
COL = {"green": (.1, 1, .2), "amber": (1, .65, 0), "red": (1, .05, .05), "white": (1, 1, 1), "grey": (.35, .35, .35)}
CI = {c: i + 1 for i, c in enumerate(COL)}
SURF = "nauvis"

PACKS = ["automation", "logistic", "chemical", "production", "utility", "space", "metallurgic", "electromagnetic", "agricultural", "cryogenic"]
I = lambda n: ("item", n)
SIG = lambda n: ("virtual", n)
SL = lambda n: ("space-location", n)

# the layout: sections in order; every section starts with its heading cell and fills three cells a row, the rest of the last row stays empty
SECTIONS = [
    ("POWER", I("solar-panel"), [("p_nau", SL("nauvis")), ("p_ful", SL("fulgora")), ("p_aqu", SL("aquilo")), ("p_oth", SL("gleba"))]),
    ("METAL", I("iron-gear-wheel"), [("m_cu", I("copper-plate")), ("m_fe", I("iron-plate")), ("m_st", I("steel-plate")), ("m_fu", I("electric-furnace"))]),
    ("SCIENCE", I("lab"), [("k_" + p, I(p + "-science-pack")) for p in PACKS] + [("k_labs", I("lab")), ("k_res", SIG("signal-info")), ("k_units", SIG("signal-heart"))]),
    ("SPACE", I("space-platform-foundation"), [("s_aq", SIG("signal-rightwards-leftwards-arrow")), ("s_aqacc", I("accumulator")), ("s_cnt", SIG("signal-rightwards-leftwards-arrow")),
                                                ("s_tri", SIG("signal-shuffle")), ("s_trim", I("space-platform-foundation")),
                                                ("w_foundation", SIG("signal-snowflake")), ("w_pu", I("processing-unit")), ("w_rf", I("rocket-fuel")), ("w_lds", I("low-density-structure")),
                                                ("a_ht", I("heating-tower")), ("a_sf", I("solid-fuel")), ("a_ice", I("ice-platform")), ("a_cryo", I("cryogenic-science-pack"))]),
    ("SILOS", I("rocket-silo"), [("r_" + n, SL(n)) for n in ("nauvis", "fulgora", "vulcanus", "gleba", "aquilo")] +
     [("n_lds", I("low-density-structure")), ("n_pu", I("processing-unit")), ("n_rf", I("rocket-fuel")), ("n_ce", I("cliff-explosives")), ("n_rc", I("refined-concrete"))]),
    ("ALERTS", SIG("signal-skull"), [("x_dmg", SIG("signal-fire")), ("x_hub", I("space-platform-hub")), ("x_np", SIG("signal-no-entry"))]),
]


def cells():
    """-> list of dict(key, icon, x, y, heading, title). Rows run top to bottom, three cells across."""
    out, row = [], 0
    for title, icon, items in SECTIONS:
        seq = [("h_" + title, icon, True)] + [(k, ic, False) for k, ic in items]
        for i, (k, ic, h) in enumerate(seq):
            r, c = row + i // COLS, i % COLS
            out.append({"key": k, "icon": ic, "heading": h, "title": title, "lx": X0 + PITCH_X * c, "y": Y0 + PITCH_Y * r})
        row += (len(seq) + COLS - 1) // COLS
    return out


def poles(cs):
    top = max(c["y"] for c in cs)
    out, y = [], Y0 + 1
    while y < top + 3:
        for x in (X0 + 2, X0 + 6):                         # -227.5 and -223.5: free tiles between the cells
            out.append((x, y))
        y += 6
    return out


def lua(code):
    return tools["run_lua"](" ".join(code.split("\n"))).strip()


# ------------------------------------------------------------------------------------------------ build
def build(apply):
    cs = cells()
    ents = []
    for c in cs:
        ents.append({"name": "small-lamp", "x": c["lx"], "y": c["y"], "direction": 0})
        ents.append({"name": "display-panel", "x": c["lx"] + 1, "y": c["y"], "direction": 0})
    for x, y in poles(cs):
        ents.append({"name": "medium-electric-pole", "x": x, "y": y, "direction": 0})
    have = lua("local s=game.surfaces.nauvis local o={} for _,e in pairs(s.find_entities_filtered{area={{-232,-188},{-218,-145}},name={'small-lamp','display-panel','medium-electric-pole'}}) do o[#o+1]=e.name..'@'..e.position.x..','..e.position.y end rcon.print(table.concat(o,';'))")
    have = set(have.split(";")) if have else set()
    todo = [e for e in ents if "%s@%s,%s" % (e["name"], e["x"], e["y"]) not in have]
    r = json.loads(tools["place_entities"](json.dumps(todo), surface=SURF, dry_run=not apply))
    print("entities wanted", len(ents), "to place", len(todo), "failed", r.get("failed"))
    if apply:
        tags()
    return r


def tags():
    for x, y, text, icon in [(-225, -167, "Factory Status Wall", "signal-info"), (-327, -212, "Replicator site", "signal-star"), (-250, -212, "Rocket silos", "rocket-silo"), (-216, -228, "Landing pad", "cargo-landing-pad")]:
        t = text.replace("'", "")
        lua("local s=game.surfaces.nauvis local f=game.forces.player local have=false for _,t in pairs(f.find_chart_tags(s,{{%s-3,%s-3},{%s+3,%s+3}})) do if t.text:find('%s',1,true) then have=true end end "
            "if not have then f.add_chart_tag(s,{position={%s,%s},text='%s',icon={type='%s',name='%s'}}) end rcon.print('ok')" % (x, y, x, y, t, x, y, t, "item" if icon in ("rocket-silo", "cargo-landing-pad") else "virtual", icon))


def clear_test():
    print(lua("local s=game.surfaces.nauvis local n=0 for _,e in pairs(s.find_entities_filtered{area={{-226.5,-179.5},{-222.5,-178.0}},name={'display-panel','small-lamp'}}) do e.destroy() n=n+1 end rcon.print(n)"))


# ------------------------------------------------------------------------------------------------ data
Q_POWER = """
local f=game.forces.player local o={}
local function acc(s) local a,c=0,0 for _,e in pairs(s.find_entities_filtered{type='accumulator'}) do a=a+e.energy c=c+e.electric_buffer_size end if c>0 then return a/c*100 end return -1 end
for _,n in pairs({'nauvis','fulgora','vulcanus','gleba','aquilo'}) do local s=game.surfaces[n] if s then o[#o+1]='acc_'..n..'='..string.format('%.1f',acc(s))
local np,lp=0,0 for _,e in pairs(s.find_entities_filtered{force=f,type={'assembling-machine','furnace','lab','mining-drill','chemical-plant','oil-refinery','rocket-silo','roboport','reactor'}}) do local st=e.status if st==defines.entity_status.no_power then np=np+1 elseif st==defines.entity_status.low_power then lp=lp+1 end end
o[#o+1]='np_'..n..'='..np o[#o+1]='lp_'..n..'='..lp end end
local aq=game.surfaces.aquilo if aq then local rx=aq.find_entities_filtered{name='nuclear-reactor'}[1] o[#o+1]='rx='..(rx and string.format('%.0f',rx.temperature) or -1)
local ht=aq.find_entities_filtered{name='heating-tower'}[1] local ok,t=pcall(function() return ht.temperature end) o[#o+1]='ht='..((ok and t) and string.format('%.0f',t) or -1)
local pad=aq.find_entities_filtered{type='cargo-landing-pad'}[1] if pad then local pi=pad.get_inventory(defines.inventory.cargo_landing_pad_main) o[#o+1]='sf='..pi.get_item_count('solid-fuel') o[#o+1]='cryo='..pi.get_item_count('cryogenic-science-pack') end
o[#o+1]='ice='..aq.count_tiles_filtered{name='ice-platform'} end
rcon.print(table.concat(o,';'))
"""

Q_SCI = """
local f=game.forces.player local o={} local P=defines.flow_precision_index.one_minute
local function rate(item,cat,surf) return f.get_item_production_statistics(surf).get_flow_count{name=item,category=cat,precision_index=P} end
for _,it in pairs({'copper-plate','iron-plate','steel-plate'}) do o[#o+1]=it..'='..string.format('%.1f',rate(it,'input','nauvis')/60)..','..string.format('%.1f',rate(it,'output','nauvis')/60) end
local fu,ft=0,0 for _,e in pairs(game.surfaces.nauvis.find_entities_filtered{type='furnace',force=f}) do ft=ft+1 if e.status==defines.entity_status.full_output then fu=fu+1 end end o[#o+1]='furn='..fu..','..ft
local packs={'automation','logistic','chemical','production','utility','space','metallurgic','electromagnetic','agricultural','cryogenic'}
for _,p in pairs(packs) do local t=0 for _,s in pairs(game.surfaces) do t=t+rate(p..'-science-pack','input',s) end o[#o+1]='pack_'..p..'='..string.format('%.1f',t) end
local u=0 for _,s in pairs(game.surfaces) do u=u+rate('automation-science-pack','output',s) end o[#o+1]='units='..string.format('%.1f',u)
local lw,lt=0,0 for _,s in pairs(game.surfaces) do for _,e in pairs(s.find_entities_filtered{type='lab',force=f}) do lt=lt+1 if e.status==defines.entity_status.working then lw=lw+1 end end end o[#o+1]='labs='..lw..','..lt
local r=f.current_research o[#o+1]='res='..(r and (r.name..','..string.format('%.0f',f.research_progress*100)) or 'none,0')
rcon.print(table.concat(o,';'))
"""

Q_SPACE = """
local f=game.forces.player local o={}
for _,p in pairs(f.platforms) do if p.valid and p.surface and p.surface.valid and p.hub and p.hub.valid then
local nm=p.name:gsub('%b[]',''):gsub('^%s+',''):gsub('%s+$','') local s=p.surface
local g=s.count_entities_filtered{type={'entity-ghost','tile-ghost'}} local inv=p.hub.get_inventory(defines.inventory.hub_main)
local rec={nm,p.state,(p.space_location and p.space_location.name or '-'),p.paused and 1 or 0,g,inv.get_item_count('firearm-magazine'),inv.count_empty_stacks(),
inv.get_item_count('space-platform-foundation'),inv.get_item_count('processing-unit'),inv.get_item_count('rocket-fuel'),inv.get_item_count('low-density-structure')}
if nm:find('Triangle',1,true) then rec[#rec+1]=s.count_tiles_filtered{name='space-platform-foundation'} elseif nm:find('Aquilo',1,true) then local a,c=0,0 for _,e in pairs(s.find_entities_filtered{type='accumulator'}) do a=a+e.energy c=c+e.electric_buffer_size end rec[#rec+1]=c>0 and string.format('%.0f',a/c*100) or -1 else rec[#rec+1]=0 end
o[#o+1]=table.concat(rec,',') end end
rcon.print(table.concat(o,';'))
"""

Q_SILO = """
local o={}
for _,n in pairs({'nauvis','fulgora','vulcanus','gleba','aquilo'}) do local s=game.surfaces[n] if s then local t,w,np=0,0,0 for _,e in pairs(s.find_entities_filtered{name='rocket-silo'}) do t=t+1 local st=e.status if st==defines.entity_status.working then w=w+1 elseif st==defines.entity_status.no_power then np=np+1 end end o[#o+1]='silo_'..n..'='..t..','..w..','..np end end
local pad=game.surfaces.nauvis.find_entities_filtered{type='cargo-landing-pad'}[1] local net=pad and game.surfaces.nauvis.find_logistic_network_by_position(pad.position,'player')
for _,it in pairs({'low-density-structure','processing-unit','rocket-fuel','cliff-explosives','refined-concrete'}) do o[#o+1]='net_'..it..'='..(net and net.get_item_count(it) or -1) end
rcon.print(table.concat(o,';'))
"""


def parse(s):
    d = {}
    for part in s.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            d[k] = v
    return d


def num(d, k, default=-1.0):
    try:
        return float(d[k])
    except (KeyError, ValueError):
        return default


def short(n):
    n = float(n)
    return "%.1fk" % (n / 1000) if abs(n) >= 10000 else "%d" % round(n)


def collect():
    t0 = time.time()
    d = {}
    for q in (Q_POWER, Q_SCI, Q_SILO):
        d.update(parse(lua(q)))
    plats = [p.split(",") for p in lua(Q_SPACE).split(";") if p]
    return d, plats, time.time() - t0


def lvl(value, red, amber, low_is_bad=True):
    if value < 0:
        return "grey"
    if low_is_bad:
        return "red" if value < red else ("amber" if value < amber else "green")
    return "red" if value > red else ("amber" if value > amber else "green")


def compute():
    d, plats, secs = collect()
    t = {}                                         # key -> (text, colour)
    for title, icon, items in SECTIONS:
        t["h_" + title] = (title, "white")

    # power
    def pw(n, label):
        a, lp = num(d, "acc_" + n), num(d, "lp_" + n, 0)
        c = "grey" if a < 0 else ("red" if a < 20 or lp > 0 else ("amber" if a < 50 else "green"))
        return "%s %d%%" % (label, a) if a >= 0 else label + " n/a", c
    t["p_nau"] = pw("nauvis", "Nau")
    t["p_ful"] = pw("fulgora", "Ful")
    rx, a_aq = num(d, "rx"), num(d, "acc_aquilo")
    c = "grey" if rx < 0 and a_aq < 0 else ("red" if (0 <= rx < 300) or (0 <= a_aq < 20) else ("amber" if 0 <= a_aq < 50 else "green"))
    t["p_aqu"] = ("%dC %d%%" % (rx, a_aq), c)
    v, g = num(d, "acc_vulcanus"), num(d, "acc_gleba")
    t["p_oth"] = ("V%d G%d" % (v, g), "grey" if min(v, g) < 0 else ("red" if min(v, g) < 20 else ("amber" if min(v, g) < 50 else "green")))

    # metal
    for key, it, label in (("m_cu", "copper-plate", "Cu"), ("m_fe", "iron-plate", "Fe"), ("m_st", "steel-plate", "Steel")):
        made, used = (float(x) for x in d.get(it, "0,0").split(","))
        c = "red" if used > 1.2 * made and used > 1 else ("amber" if used > made and used > 1 else "green")
        t[key] = ("%s/%s" % (short(made), short(used)), c)
    fu, ft = (float(x) for x in d.get("furn", "0,1").split(","))
    t["m_fu"] = ("%d/%d" % (fu, ft), "amber" if fu > ft / 2 else "green")

    # science
    rates = {p: num(d, "pack_" + p, 0) * 1.0 for p in PACKS}
    best = max(rates.values()) if rates else 0
    for p in PACKS:
        r = rates[p]
        t["k_" + p] = ("%s/min" % short(r), "red" if r <= 0.05 else ("amber" if r < best / 2 else "green"))
    lw, lt = (float(x) for x in d.get("labs", "0,0").split(","))
    t["k_labs"] = ("labs %d/%d" % (lw, lt), "red" if lw == 0 else ("amber" if lw < .8 * lt else "green"))
    rn, rp = d.get("res", "none,0").split(",")
    t["k_res"] = (("%s%% %s" % (rp, rn.replace("-", " ")[:5])) if rn != "none" else "no res", "green" if rn != "none" else "red")
    t["k_units"] = ("%s/min" % short(num(d, "units", 0)), "green" if num(d, "units", 0) > 0.05 else "red")

    # space
    ships = [p for p in plats if p[0].endswith("Shuttle")]
    byname = {p[0]: p for p in plats}
    aq = byname.get("Fulgora-Aquilo 4 Shuttle")
    stl = {"6": "W", "2": "T", "7": "P", "4": "S"}
    if aq:
        mags, ghosts, paused = int(aq[5]), int(aq[4]), aq[3] == "1"
        t["s_aq"] = ("%s %s m%s" % (aq[2][:1].upper(), stl.get(aq[1], "?") if not paused else "P", short(mags)), "red" if mags < 150 else ("amber" if mags < 400 or paused or ghosts > 0 else "green"))
        a = float(aq[11])
        t["s_aqacc"] = ("acc %d%%" % a if a >= 0 else "acc n/a", lvl(a, 20, 50))
    nt = sum(1 for p in ships if p[1] == "2")
    nw = sum(1 for p in ships if p[1] == "6" and p[3] == "0")
    npz = sum(1 for p in ships if p[3] == "1")
    nd = sum(1 for p in ships if int(p[4]) > 0)
    t["s_cnt"] = ("T%d W%d P%d" % (nt, nw, npz), "red" if nd >= 3 else ("amber" if nd > 0 else "green"))
    tri = next((p for p in plats if "Triangle" in p[0]), None)
    prev = {}
    try:
        prev = json.loads(STATE.read_text())
    except (OSError, ValueError):
        pass
    now = time.time()
    if tri:
        tiles, gh = int(tri[11]), int(tri[4])
        rate = None
        if "tiles" in prev and now - prev["time"] > 20:
            rate = (tiles - prev["tiles"]) * 60.0 / (now - prev["time"])
        STATE.parent.mkdir(exist_ok=True)
        if rate is not None or "tiles" not in prev or now - prev["time"] > 600:
            STATE.write_text(json.dumps({"tiles": tiles, "time": now, "rate": rate if rate is not None else prev.get("rate", 0)}))
            prev_rate = rate if rate is not None else prev.get("rate", 0)
        else:
            prev_rate = prev.get("rate", 0)
        t["s_tri"] = ("t%s g%d" % (short(tiles), gh), "green" if gh == 0 else ("red" if prev_rate <= 0 else "amber"))
        t["s_trim"] = ("%+.0f/min" % prev_rate, "green" if prev_rate > 0 else ("grey" if gh == 0 else "red"))
    wheels = [p for p in plats if "Wheel" in p[0]]
    for key, idx, label in (("w_foundation", 7, "fnd"), ("w_pu", 8, "PU"), ("w_rf", 9, "RF"), ("w_lds", 10, "LDS")):
        n = sum(int(p[idx]) for p in wheels)
        t[key] = ("%s %s" % (label, short(n)), "red" if n == 0 else ("amber" if n < 100 else "green"))
    ht, sf = num(d, "ht"), num(d, "sf")
    t["a_ht"] = ("%dC" % ht if ht >= 0 else "n/a", "grey" if ht < 0 else ("red" if ht < 15 else "green"))
    t["a_sf"] = ("fuel %s" % short(max(sf, 0)), "red" if sf <= 0 else ("amber" if sf < 500 else "green"))
    t["a_ice"] = ("ice %s" % short(max(num(d, "ice", 0), 0)), "grey")
    t["a_cryo"] = ("cryo %s" % short(max(num(d, "cryo", 0), 0)), "grey")

    # silos
    for n in ("nauvis", "fulgora", "vulcanus", "gleba", "aquilo"):
        tt, w, np_ = (int(x) for x in d.get("silo_" + n, "0,0,0").split(","))
        t["r_" + n] = ("%s %d/%d" % (n[:3].title(), w, tt), "grey" if tt == 0 else ("red" if np_ > 0 else ("green" if w > 0 else "amber")))
    for key, it, label, amber in (("n_lds", "low-density-structure", "LDS", 500), ("n_pu", "processing-unit", "PU", 500), ("n_rf", "rocket-fuel", "RF", 500),
                                  ("n_ce", "cliff-explosives", "CE", 100), ("n_rc", "refined-concrete", "RC", 100)):
        n = num(d, "net_" + it)
        t[key] = ("%s %s" % (label, short(n)) if n >= 0 else label + " n/a", "grey" if n < 0 else ("red" if n == 0 else ("amber" if n < amber else "green")))

    # alerts
    ghs = sum(int(p[4]) for p in plats)
    t["x_dmg"] = ("damage %d" % ghs, "red" if ghs >= 20 else ("amber" if ghs > 0 else "green"))
    full = [p[0] for p in plats if int(p[6]) <= 2]
    t["x_hub"] = ("full %d" % len(full), "amber" if full else "green")
    nps = {n: int(num(d, "np_" + n, 0)) for n in ("nauvis", "fulgora", "vulcanus", "gleba", "aquilo")}
    bad = "".join(n[0].upper() for n in ("nauvis", "fulgora", "vulcanus", "gleba", "aquilo") if nps[n] > 0)
    t["x_np"] = (("np " + bad) if bad else "power ok", "red" if bad else "green")
    return t, secs, {"full_hubs": full}


def esc(s):
    return s.replace("\\", "").replace("'", "").replace("\n", " ")


def update(set_icons=False):
    t0 = time.time()
    t, qsecs, extra = compute()
    cs = cells()
    rows = []
    for c in cs:
        text, colour = t.get(c["key"], ("?", "grey"))
        ic = c["icon"]
        rows.append("{%s,%s,'%s',%d,'%s','%s'}" % (c["lx"], c["y"], esc(text), CI[colour], ic[0], ic[1]))
    pal = "{" + ",".join("{r=%s,g=%s,b=%s}" % COL[k] for k in COL) + "}"
    code = ("local s=game.surfaces.nauvis local pal=%s local n=0 for _,q in pairs({%s}) do local p=s.find_entities_filtered{name='display-panel',position={q[1]+1,q[2]},radius=0.3}[1] "
            "if p then p.display_panel_text=q[3] p.display_panel_always_show=true p.display_panel_show_in_chart=false if %s then p.display_panel_icon={type=q[5],name=q[6]} end n=n+1 end "
            "local l=s.find_entities_filtered{name='small-lamp',position={q[1],q[2]},radius=0.3}[1] if l then l.always_on=true l.color=pal[q[4]] end end rcon.print(n)") % (pal, ",".join(rows), "true" if set_icons else "false")
    assert len(code) < 60000, len(code)
    n = lua(code)
    return {"panels": n, "query_s": round(qsecs, 2), "total_s": round(time.time() - t0, 2), "full_hubs": extra["full_hubs"], "readings": {k: v[0] + " [" + v[1] + "]" for k, v in t.items()}}


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "update"
    if cmd == "build":
        build("--apply" in sys.argv)
        if "--apply" in sys.argv:
            print(update(True))
    elif cmd == "update":
        r = update(True if "--icons" in sys.argv else False)
        print(json.dumps(r, indent=1))
    elif cmd == "clear-test":
        clear_test()
