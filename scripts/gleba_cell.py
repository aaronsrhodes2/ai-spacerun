#!/usr/bin/env python3
"""Gleba stable science cell (docs/gleba-stable-cell.md), 2026-11-15.

  hub   near the labs at HUB origin: two rows of biochambers, everything robot-fed except mash and jelly (direct insertion, 3-4 min shelf)
  farms one yumako tower on the wild yumako patch, one jellynut tower beside the Captain's jellynut tower

Every gate is a logistic-network condition on an inserter, so the cell runs only up to its buffers (the Captain: "only outputting its
sustainable amount, not full tilt"). tune() re-sets the limits from the live buffers every autopilot cycle; status() reports them.

Seed vault (the Captain's order 2026-11-15): steel chests next to each fruit processor. Seeds go in only while the network already holds
SEED_VAULT_AFTER seeds (the farm is served first). Nothing takes seeds out: robots cannot reach a steel chest and no inserter leads out.
After a collapse and a redesign the Captain says when to empty them (vault_release(), by hand only).

Usage: gleba_cell.py probe | dry | build | status | tune | vault_release
"""
import json
import sys
import time
from pathlib import Path

from _game import tools

L = tools["run_lua"]
SURF = "gleba"
OX, OY = 90, 26                     # hub top-left tile (site checked 2026-11-15: no water, nothing of ours, in the robot network)
PUMP = (107.5, 48.5, 8)             # offshore pump spot found by can_place
SUB = (88, 28)                      # substation joining the hub to the grid (substation at 80,20 is 11 tiles away)
YT = (-176.5, -140.5)               # yumako tower: the only tower spot on the wild patch with a good field (296 soil tiles)
Q = "epic"

# setpoints (tune() moves the fruit caps; the rest are fixed safety lines)
SEED_FLOOR = 0                      # towers plant whenever the network holds a seed. (First version was 20: a cold start makes only ~10 yumako seeds, so the farm
                                    # would never have replanted. The reserve is the locked vault, not a floor.)
SEED_VAULT_AFTER = 50               # the vault fills only once the network holds this many
VAULT_BAR = 21                      # 20 slots of 10 = 200 seeds per vault
BIOFLUX_CAP = 500                   # fruit processors stop at this much bioflux (bioflux is the store: 2 h shelf)
NUTRIENT_CAP = 200                  # nutrients spoil in 5 min: make little
NUTRIENT_LOW = 50                   # below this the mash-to-nutrients restart chamber runs
EGG_CAP = 10                        # eggs hatch after 15 min: never more than this on hand
PACK_CAP = 2000                     # packs on hand before the pack chambers pause
FRUIT_CAP = {"yumako": 150, "jellynut": 80}


def cx(i):
    return OX + 4 * i + 1.5


class Plan:
    def __init__(self):
        self.ents = []

    def add(self, name, x, y, d=0, recipe=None, q=None, **cfg):
        e = {"name": name, "x": x, "y": y, "direction": d}
        if recipe:
            e["recipe"] = recipe
        if q:
            e["params"] = {"quality": q}
        e["cfg"] = cfg
        self.ents.append(e)


def hub():
    P = Plan()
    r1 = OY            # row 1: requester y OY+.5, inserter OY+1.5, chamber centre OY+3.5, out inserter OY+5.5, chest OY+6.5
    # unit 0 mash->nutrients (restart), 1 yumako processing, 2 bioflux, 3 jellynut processing, 4 nutrients from bioflux, 5 nutrients from spoilage (plain assembler: the cold start)
    units = [("biochamber", "nutrients-from-yumako-mash"), ("biochamber", "yumako-processing"), ("biochamber", "bioflux"),
             ("biochamber", "jellynut-processing"), ("biochamber", "nutrients-from-bioflux"), ("assembling-machine-3", "nutrients-from-spoilage")]
    # buffers sized to the robot round trip, not to the machine: yumako processing eats 2 a second and the farm is 270 tiles away (first run: 20 starved it)
    req = [{"nutrients": 10}, {"yumako": 250, "nutrients": 10}, {"nutrients": 10}, {"jellynut": 120, "nutrients": 10}, {"bioflux": 60, "nutrients": 10}, {"spoilage": 100}]
    gate = [("nutrients", "<", NUTRIENT_LOW), ("bioflux", "<", BIOFLUX_CAP), None, ("bioflux", "<", BIOFLUX_CAP), ("nutrients", "<", NUTRIENT_CAP), None]
    for i, (m, rec) in enumerate(units):
        x = cx(i)
        P.add(m, x, r1 + 3.5, 0, rec, Q)
        P.add("requester-chest", x, r1 + 0.5, request=req[i])
        P.add("bulk-inserter", x, r1 + 1.5, 0, None, Q, cond=gate[i])
    # direct insertion: yumako processing -> restart chamber (west) and -> bioflux (east); jellynut processing -> bioflux (west)
    P.add("bulk-inserter", OX + 3.5, r1 + 3.5, 4, None, Q, cond=("nutrients", "<", NUTRIENT_LOW))
    P.add("bulk-inserter", OX + 7.5, r1 + 3.5, 12, None, Q)
    P.add("bulk-inserter", OX + 11.5, r1 + 3.5, 4, None, Q)
    # outputs
    out_simple = {0: 2, 2: 6, 4: 2, 5: 2}            # unit -> passive provider bar (slots)
    for i, bar in out_simple.items():
        P.add("bulk-inserter", cx(i), r1 + 5.5, 0, None, Q)
        P.add("passive-provider-chest", cx(i), r1 + 6.5, bar=bar)
    for i, seed in ((1, "yumako-seed"), (3, "jellynut-seed")):
        x = cx(i)
        P.add("bulk-inserter", x - 1, r1 + 5.5, 0, None, Q, filt=seed)                                        # seeds to the farm
        P.add("passive-provider-chest", x - 1, r1 + 6.5)
        P.add("bulk-inserter", x, r1 + 5.5, 0, None, Q, filt=seed, cond=(seed, ">", SEED_VAULT_AFTER))        # seeds to the vault, farm first
        P.add("steel-chest", x, r1 + 6.5, bar=VAULT_BAR, vault=seed)
        P.add("bulk-inserter", x + 1, r1 + 5.5, 0, None, Q, filt="spoilage")                                   # rot out
        P.add("passive-provider-chest", x + 1, r1 + 6.5)
    for gx, gy in ((OX + 3.5, r1 + 2.5), (OX + 7.5, r1 + 2.5), (OX + 11.5, r1 + 2.5), (OX + 15.5, r1 + 3.5), (OX + 19.5, r1 + 3.5), (OX + 9.5, r1 + 7.5)):
        P.add("medium-electric-pole", gx, gy)
    P.add("substation", SUB[0], SUB[1])
    # row 2: eggs and packs. header pipe y OY+8.5, requester OY+9.5, inserter OY+10.5, chamber centre OY+12.5, out inserter OY+14.5, chest OY+15.5
    r2 = OY + 9
    for i in range(5):
        x = cx(i)
        if i % 2 == 0:       # egg chamber, facing east: its water inputs sit in the gap column to its right
            P.add("biochamber", x, r2 + 3.5, 4, "pentapod-egg", Q)
            P.add("requester-chest", x, r2 + 0.5, request={"nutrients": 60, "pentapod-egg": 2})
            P.add("bulk-inserter", x, r2 + 1.5, 0, None, Q, cond=("pentapod-egg", "<", EGG_CAP))
            P.add("bulk-inserter", x, r2 + 5.5, 0, None, Q)
            P.add("passive-provider-chest", x, r2 + 6.5, bar=1)
            for y in range(0, 6):
                P.add("pipe", OX + 4 * i + 3.5, r2 - 0.5 + y)
        else:                # pack chamber
            P.add("biochamber", x, r2 + 3.5, 0, "agricultural-science-pack", Q)
            P.add("requester-chest", x, r2 + 0.5, request={"bioflux": 10, "pentapod-egg": 4, "nutrients": 10})
            P.add("bulk-inserter", x, r2 + 1.5, 0, None, Q, cond=("agricultural-science-pack", "<", PACK_CAP))
            P.add("bulk-inserter", x, r2 + 5.5, 0, None, Q)
            P.add("passive-provider-chest", x, r2 + 6.5)
    for gx, gy in ((OX - 0.5, r2 + 3.5), (OX + 7.5, r2 + 3.5), (OX + 15.5, r2 + 3.5)):
        P.add("medium-electric-pole", gx, gy)
    # water: header along y OY+8.5 from the first egg column to x OX+21.5, down to y OY+16.5, west to the pump's pipe
    hy = OY + 8.5
    for x in range(4, 22):
        if (OX + x + 0.5) not in (OX + 3.5, OX + 11.5, OX + 19.5):      # those tiles are the egg columns' tops (added above)
            P.add("pipe", OX + x + 0.5, hy)
    P.add("offshore-pump", PUMP[0], PUMP[1], PUMP[2])
    return P


FARM_LUA = """
local s=game.surfaces.gleba local f=game.forces.player
local function farm_spot(cx,cy,soil,avoid)
  local best=nil
  for x=cx-25,cx+25 do for y=cy-25,cy+25 do local p={x+0.5,y+0.5}
    local far=true for _,a in pairs(avoid) do if math.abs(p[1]-a[1])<22 and math.abs(p[2]-a[2])<22 then far=false end end
    if far and s.can_place_entity{name='agricultural-tower',position=p,force=f,build_check_type=defines.build_check_type.manual}
       and s.can_place_entity{name='requester-chest',position={p[1],p[2]-2},force=f,build_check_type=defines.build_check_type.manual}
       and s.can_place_entity{name='passive-provider-chest',position={p[1],p[2]+3},force=f,build_check_type=defines.build_check_type.manual} then
      local n=s.count_tiles_filtered{area={{p[1]-10.5,p[2]-10.5},{p[1]+10.5,p[2]+10.5}},name=soil}
      local own=s.count_entities_filtered{area={{p[1]-11,p[2]-11},{p[1]+11,p[2]+11}},force=f,limit=1}
      if own==0 and (not best or n>best[3]) then best={p[1],p[2],n} end end end end
  return best end
local function in_net(p) return s.find_logistic_network_by_position(p,f)~=nil end
local j=farm_spot(195,100,'natural-jellynut-soil',{{195.5,100.5}})
local out={jelly=j, jelly_in_net=j and in_net({j[1],j[2]-2}) and in_net({j[1],j[2]+3}) or false,
           yumako_in_net=in_net({%s,%s}) }
rcon.print(helpers.table_to_json(out))
"""


def probe():
    r = json.loads(L(" ".join(FARM_LUA.split("\n")) % (YT[0], YT[1] - 3)))
    print(r)
    return r


JT = (202.5, 70.5)                  # jellynut tower: best in-network spot (103 soil tiles) clear of the Captain's tower range
# power and robots, found by land search 2026-11-15 (the yumako patch is cut by water; the spot above that tower is water, so its seeds come in from the east side)
YUMAKO_INFRA = [("big-electric-pole", -144, -129), ("big-electric-pole", -165, -129), ("big-electric-pole", -172, -136),
                ("medium-electric-pole", -174.5, -137.5), ("roboport", -165, -132)]
JELLY_INFRA = [("big-electric-pole", 200, 83), ("big-electric-pole", 203, 77), ("medium-electric-pole", 200.5, 70.5)]


def farm(P, t, seed, fruit, side_in=False):
    """Tower with a seed requester (inserter gated: network seeds > SEED_FLOOR) and a fruit chest below (gated: fruit < cap)."""
    x, y = t
    P.add("agricultural-tower", x, y, 0, None, Q)
    if side_in:
        P.add("requester-chest", x + 3, y, request={seed: 10})
        P.add("bulk-inserter", x + 2, y, 4, None, Q, cond=(seed, ">", SEED_FLOOR))
    else:
        P.add("requester-chest", x, y - 3, request={seed: 10})
        P.add("bulk-inserter", x, y - 2, 0, None, Q, cond=(seed, ">", SEED_FLOOR))
    P.add("bulk-inserter", x, y + 2, 0, None, Q, cond=(fruit, "<", FRUIT_CAP[fruit]), fruitgate=fruit)
    P.add("passive-provider-chest", x, y + 3)


def cfg_lua(P):
    """One Lua call per batch: filters, logistic conditions, requests, bars."""
    parts = []
    for e in P.ents:
        c = e["cfg"]
        if not c:
            continue
        b = "do local e=s.find_entities_filtered{name='%s',position={%s,%s},radius=0.3}[1] if e then " % (e["name"], e["x"], e["y"])
        if c.get("filt"):
            b += "e.use_filters=true e.set_filter(1,'%s') " % c["filt"]
        if c.get("cond"):
            n, op, v = c["cond"]
            b += ("local cb=e.get_or_create_control_behavior() cb.connect_to_logistic_network=true "
                  "cb.logistic_condition={first_signal={type='item',name='%s'},comparator='%s',constant=%d} " % (n, op, v))
        if c.get("request"):
            b += "local rp=e.get_requester_point() rp.trash_not_requested=true local sec=rp.sections_count>0 and rp.get_section(1) or rp.add_section() "
            for k, (n, m) in enumerate(c["request"].items()):
                b += "sec.set_slot(%d,{value={type='item',name='%s',quality='normal',comparator='='},min=%d}) " % (k + 1, n, m)
        if c.get("bar"):
            b += "e.get_inventory(defines.inventory.chest).set_bar(%d) " % c["bar"]
        b += "n=n+1 else miss[#miss+1]='%s@%s,%s' end end " % (e["name"], e["x"], e["y"])
        parts.append(b)
    out = []
    for i in range(0, len(parts), 12):
        code = "local s=game.surfaces.gleba local n=0 local miss={} " + "".join(parts[i:i + 12]) + "rcon.print('configured '..n..(#miss>0 and (' missing '..table.concat(miss,' ')) or ''))"
        out.append(L(code))
    return out


def plan():
    P = hub()
    for n, x, y in YUMAKO_INFRA + JELLY_INFRA:
        P.add(n, x, y, 0, None, Q if n == "roboport" else None)
    farm(P, YT, "yumako-seed", "yumako", side_in=True)
    farm(P, JT, "jellynut-seed", "jellynut")
    return P, {"jelly": JT}


SIZE = {"agricultural-tower": 1.5, "roboport": 2, "big-electric-pole": 1, "biochamber": 1.5, "assembling-machine-3": 1.5, "substation": 1}


def clear_plants(P, apply):
    """Wild plants in a footprint block placement. They are harvested (mine: a tree gives its 50 fruit, as a tower would) into a
    script inventory and the fruit goes into that farm's fruit chest once it stands: the yumako from them is the first seed source."""
    boxes = []
    for e in P.ents:
        h = SIZE.get(e["name"], 0.5)
        boxes.append("{%s,%s,%s}" % (e["x"], e["y"], h))
    code = ("local s=game.surfaces.gleba local n=0 local inv=storage.gleba_cell_harvest or game.create_inventory(40) storage.gleba_cell_harvest=inv "
            "for _,b in pairs({%s}) do for _,p in pairs(s.find_entities_filtered{area={{b[1]-b[3]+0.01,b[2]-b[3]+0.01},{b[1]+b[3]-0.01,b[2]+b[3]-0.01}},type='plant'}) do "
            "n=n+1 if %s then p.mine{inventory=inv,force=true,raise_destroyed=true} end end end "
            "local c={} for _,it in pairs(inv.get_contents()) do c[#c+1]=it.name..'='..it.count end rcon.print('plants in footprints '..n..' | harvested so far: '..table.concat(c,', '))"
            % (",".join(boxes), "true" if apply else "false"))
    return L(code)


def deliver_harvest():
    """Fruit harvested while clearing goes into the farm fruit chests (yumako to the yumako farm, jellynut to the jellynut farm)."""
    code = ("local s=game.surfaces.gleba local inv=storage.gleba_cell_harvest if not inv then rcon.print('nothing harvested') return end local o={} "
            "for fruit,pos in pairs({yumako={%s,%s},jellynut={%s,%s}}) do local ch=s.find_entities_filtered{name='passive-provider-chest',position=pos,radius=0.3}[1] "
            "local c=inv.get_item_count(fruit) if ch and c>0 then local m=ch.insert{name=fruit,count=c} inv.remove{name=fruit,count=m} o[#o+1]=fruit..' '..m end end "
            "rcon.print('harvest delivered: '..table.concat(o,', '))") % (YT[0], YT[1] + 3, JT[0], JT[1] + 3)
    return L(code)


def place(P, dry):
    out = [{k: v for k, v in e.items() if k != "cfg"} for e in P.ents]
    placed, failed = 0, []
    for i in range(0, len(out), 150):
        r = json.loads(tools["place_entities"](json.dumps(out[i:i + 150]), surface=SURF, dry_run=dry, clear_trees=True))
        placed += r.get("placed") or 0
        failed += r.get("failed") or []
    return placed, failed


def build(apply):
    P, pr = plan()
    print("entities", len(P.ents), "jellynut farm", pr.get("jelly"))
    print(clear_plants(P, apply))
    if not apply:
        placed, failed = place(P, True)
        print("dry run ok", placed, "failed (plants are cleared on the real run)", json.dumps(failed)[:3000])
        return
    tools["save_game"]("skippy")
    placed, failed = place(P, False)
    print("placed", placed, "failed", json.dumps(failed)[:3000])
    for r in cfg_lua(P):
        print(r)
    print(deliver_harvest())


STATUS = ("local s=game.surfaces.gleba local f=game.forces.player local net=s.find_logistic_network_by_position({%s,%s},f) local o={} "
          "for _,n in pairs({'yumako-seed','jellynut-seed','yumako','jellynut','bioflux','nutrients','pentapod-egg','agricultural-science-pack','spoilage'}) do o[n]=net.get_item_count(n) end "
          "local v={} for _,ch in pairs(s.find_entities_filtered{name='steel-chest',area={{%s,%s},{%s,%s}}}) do for _,it in pairs(ch.get_inventory(defines.inventory.chest).get_contents()) do v[it.name]=(v[it.name] or 0)+it.count end end o.vault=v "
          "local tr={} for _,t in pairs(s.find_entities_filtered{name='agricultural-tower',area={{%s,%s},{%s,%s}}}) do end "
          "local m={} for k,vv in pairs(defines.entity_status) do m[vv]=k end local st={} for _,e in pairs(s.find_entities_filtered{area={{%s,%s},{%s,%s}},type={'assembling-machine'}}) do local k=(e.get_recipe() and e.get_recipe().name or '-')..':'..(m[e.status] or '?') st[k]=(st[k] or 0)+1 end o.machines=st "
          "local ps=f.get_item_production_statistics(s) o.packs_per_min=ps.get_flow_count{name='agricultural-science-pack',category='input',precision_index=defines.flow_precision_index.ten_minutes,count=true}/10 "
          "rcon.print(helpers.table_to_json(o))") % (OX + 10, OY + 8, OX - 1, OY, OX + 24, OY + 17, -300, -300, 300, 300, OX - 1, OY, OX + 24, OY + 17)


def status():
    return json.loads(L(STATUS))


def tune():
    """Slow balancing (once an autopilot cycle): the fruit caps follow the bioflux store. Low bioflux -> pick more; full -> pick less."""
    st = status()
    bf = st.get("bioflux", 0)
    caps = {"yumako": max(40, min(400, int(150 + (BIOFLUX_CAP - bf) * 0.5))), "jellynut": max(20, min(200, int(80 + (BIOFLUX_CAP - bf) * 0.25)))}
    code = "local s=game.surfaces.gleba local n=0 "
    for fruit, cap in caps.items():
        code += ("for _,t in pairs(s.find_entities_filtered{name='agricultural-tower'}) do local i=s.find_entities_filtered{name='bulk-inserter',position={t.position.x,t.position.y+2},radius=0.3}[1] "
                 "if i then local cb=i.get_control_behavior() if cb and cb.logistic_condition and cb.logistic_condition.first_signal and cb.logistic_condition.first_signal.name=='%s' then "
                 "cb.logistic_condition={first_signal={type='item',name='%s'},comparator='<',constant=%d} n=n+1 end end end " % (fruit, fruit, cap))
    code += "rcon.print('fruit gates set '..n)"
    return "bioflux %d -> caps %s (%s)" % (bf, caps, L(code).strip())


WATCH_FILE = Path(__file__).resolve().parent.parent / "snapshots" / "gleba_cell_watch.json"
# alarm: (what, lowest ok value, minutes it may stay below before the alarm)
ALARMS = (("yumako-seed", 1, 20), ("jellynut-seed", 50, 10), ("bioflux", 150, 5), ("pentapod-egg", 1, 20))   # eggs: none anywhere = the egg loop is dead and cannot restart itself


def watch():
    """Autopilot hook, once a cycle: balance the fruit caps, log one line, raise an in-game alarm (once an hour per cause) when a line stays low.
    The first 30 minutes after a build or restart are a grace period: the buffers are still filling."""
    try:
        st = status()
    except Exception as exc:  # noqa: BLE001
        return "gleba cell: no reading (%r)" % exc
    tune_msg = tune()
    now = time.time()
    state = json.loads(WATCH_FILE.read_text()) if WATCH_FILE.exists() else {}
    state.setdefault("since", {})
    state.setdefault("alarmed", {})
    state.setdefault("started", now)
    alarms = []
    for name, low, minutes in ALARMS:
        v = st.get(name, 0)
        if v >= low:
            state["since"].pop(name, None)
            continue
        t0 = state["since"].setdefault(name, now)
        if now - t0 > minutes * 60 and now - state["started"] > 1800 and now - state["alarmed"].get(name, 0) > 3600:
            alarms.append("%s %d (below %d for %d min)" % (name, v, low, (now - t0) // 60))
            state["alarmed"][name] = now
    if alarms:
        L("game.print('[Gleba cell] ALARM: " + "; ".join(alarms) + ". Seeds in the vault stay locked until the Captain says.')")
    WATCH_FILE.write_text(json.dumps(state))
    return "gleba cell: packs/min %.1f, bioflux %d, nutrients %d, eggs %d, seeds Y%d J%d, vault %s%s | %s" % (
        st.get("packs_per_min", 0), st.get("bioflux", 0), st.get("nutrients", 0), st.get("pentapod-egg", 0), st.get("yumako-seed", 0),
        st.get("jellynut-seed", 0), st.get("vault") or {}, (" | ALARM " + "; ".join(alarms)) if alarms else "", tune_msg)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "probe":
        probe()
    elif cmd == "dry":
        build(False)
    elif cmd == "build":
        build(True)
    elif cmd == "status":
        print(json.dumps(status(), indent=1))
    elif cmd == "tune":
        print(tune())
    elif cmd == "watch":
        print(watch())
    elif cmd == "vault_release":
        print("vault_release is the Captain's call only: not automatic. Edit and run by hand after a redesign.")
