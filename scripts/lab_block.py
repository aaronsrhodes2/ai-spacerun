"""
Nauvis science centre: one compact, beaconed lab block in place of the two sparse 50-lab fields (the Captain, 2026-11-10).

Layout, west to east x -73..-6, north to south y 32..52: beacon row, lab row, beacon row, lab row, beacon row, lab row, beacon row.
Each lab row is 16 labs with a blue requester chest and bulk inserter at both ends; inserters between the labs pass packs toward the middle.
Substations take a beacon slot every 15 tiles in the two inner beacon rows. The four belts that used to end in a lab now end in red chests.
Packs and modules found in the old labs and chests are counted and put back into the new chests (nothing factory-made is lost).
Modules (2 productivity per lab, 2 speed-2 per beacon) are taken from the logistic network's stock, never spawned.

Steps: teardown, place [--apply], fill.   After fill run upgrade_quality.py --surface nauvis --items --apply.
"""
import json
import sys
from pathlib import Path

from _game import tools

STATE = Path(__file__).resolve().parent.parent / "docs" / "lab_block_carryover.json"
LAB_Y = [36.5, 42.5, 48.5]
BEACON_Y = [33.5, 39.5, 45.5, 51.5]
SUB_SLOTS = {2, 7, 12, 17, 21}
CHESTS = [(x, y) for y in LAB_Y for x in (-72.5, -6.5)]
RED = [(4.5, 33.5), (5.5, 33.5), (6.5, 33.5), (6.5, 34.5)]

TEARDOWN = (
    "local s=game.surfaces.nauvis local f=game.forces.player local got={} local n=0 "
    "local function add(name,q,c) local k=name..'|'..q got[k]=(got[k] or 0)+c end "
    "local function take(inv) if inv then for _,it in pairs(inv.get_contents()) do add(it.name,it.quality,it.count) end end end "
    "for _,a in pairs({{{-73,32},{-6,53}},{{-6,32},{9,52}},{{-32,52},{-5,54.9}}}) do for _,e in pairs(s.find_entities_filtered{area=a,force=f,type={'lab','inserter','electric-pole','entity-ghost','logistic-container'}}) do if e.valid then "
    "local skip=false if e.type=='inserter' and e.pickup_target and e.pickup_target.type=='transport-belt' then skip=true end "
    "if e.type=='electric-pole' and (e.position.y>=51.9 or (e.position.x>=3 and e.position.y<36)) then skip=true end "
    "if e.type=='logistic-container' and e.name~='requester-chest' then skip=true end "
    "if not skip then if e.type=='lab' then take(e.get_inventory(defines.inventory.lab_input)) take(e.get_module_inventory()) "
    "elseif e.type=='logistic-container' then take(e.get_inventory(defines.inventory.chest)) "
    "elseif e.type=='inserter' and e.held_stack.valid_for_read then add(e.held_stack.name,e.held_stack.quality.name,e.held_stack.count) end "
    "e.destroy() n=n+1 end end end end rcon.print(helpers.table_to_json({removed=n,got=got}))"
)

PAVE = (
    "local s=game.surfaces.nauvis local t={} for x=-73,-7 do for y=32,52 do local n=s.get_tile(x,y).name if not n:find('concrete') and not s.get_tile(x,y).collides_with('water_tile') then t[#t+1]={name='refined-concrete',position={x,y}} end end end "
    "if game.forces.player.recipes['refined-concrete'].enabled then s.set_tiles(t) rcon.print('paved '..#t) else rcon.print('refined concrete not researched') end"
)


def lua(code):
    out = tools["run_lua"](code).strip()
    try:
        d = json.loads(out)
        return d["result"] if isinstance(d, dict) and "result" in d else d
    except Exception:
        return out


def entities():
    e = []
    for y in BEACON_Y:
        for j in range(22):
            x = -71.5 + 3 * j
            if y in (39.5, 45.5) and j in SUB_SLOTS:
                e.append({"name": "substation", "x": x - 0.5, "y": y - 0.5})
            else:
                e.append({"name": "beacon", "x": x, "y": y})
    for y in LAB_Y:
        for k in range(16):
            e.append({"name": "lab", "x": -69.5 + 4 * k, "y": y})
        for k in range(15):
            if k != 7:
                e.append({"name": "bulk-inserter", "x": -67.5 + 4 * k, "y": y, "direction": 12 if k < 7 else 4})
        e.append({"name": "bulk-inserter", "x": -71.5, "y": y, "direction": 12})
        e.append({"name": "bulk-inserter", "x": -7.5, "y": y, "direction": 4})
    for x, y in CHESTS:
        e.append({"name": "requester-chest", "x": x, "y": y})
    for x, y in RED:
        e.append({"name": "passive-provider-chest", "x": x, "y": y})
    return e


def place(apply):
    ents = entities()
    res = json.loads(tools["place_entities"](json.dumps(ents), surface="nauvis", dry_run=True))
    res = json.loads(res["result"]) if "result" in res else res
    failed = res.get("failed") or {}
    print("dry run:", res.get("placed"), "ok;", "failed:", json.dumps(failed)[:1500])
    if apply:
        bad = set()
        for k, v in (failed.items() if isinstance(failed, dict) else enumerate(failed)):
            bad.add(json.dumps(v) if not isinstance(v, str) else v)
        # place everything that passed: re-run without dry_run; the tool skips what cannot be placed and reports it
        res = tools["place_entities"](json.dumps(ents), surface="nauvis", dry_run=False)
        print("placed:", res[:1500])


FILL = (
    "local s=game.surfaces.nauvis local f=game.forces.player local carry=%s local o={} "
    "local chests={} for _,p in pairs(%s) do local c=s.find_entities_filtered{name='requester-chest',position=p,radius=0.6}[1] if c then chests[#chests+1]=c "
    "local secs=c.get_logistic_sections() do local sec=secs.sections[1] or secs.add_section() local i=0 for _,n in pairs(prototypes.entity['lab'].lab_inputs) do i=i+1 sec.set_slot(i,{value={name=n,quality='normal'},min=100}) end end end end "
    "local put,lost=0,0 local i=0 for k,c in pairs(carry) do local name,q=k:match('^(.-)|(.+)$') local left=c local tries=0 while left>0 and tries<#chests do i=i%%#chests+1 tries=tries+1 "
    "local share=math.min(left,math.max(1,math.ceil(c/#chests))) local did=chests[i].get_inventory(defines.inventory.chest).insert{name=name,count=share,quality=q} left=left-did put=put+did end lost=lost+left end "
    "o[#o+1]='carried over '..put..' not placed '..lost "
    "local net=s.find_logistic_network_by_position(chests[1].position,f) local function pull(name,n) return net and net.remove_item({name=name,count=n,quality='normal'}) or 0 end "
    "local lm,bm=0,0 for _,l in pairs(s.find_entities_filtered{type='lab',force=f}) do local inv=l.get_module_inventory() local need=#inv-inv.get_item_count() if need>0 then local g=pull('productivity-module',need) if g>0 then lm=lm+inv.insert{name='productivity-module',count=g} end end end "
    "for _,b in pairs(s.find_entities_filtered{name='beacon',force=f,area={{-74,31},{-5,54}}}) do local inv=b.get_module_inventory() local need=#inv-inv.get_item_count() if need>0 then local g=pull('speed-module-2',need) if g>0 then bm=bm+inv.insert{name='speed-module-2',count=g} end end end "
    "o[#o+1]='lab modules '..lm..' beacon modules '..bm..' net '..(net and net.network_id or 'none') rcon.print(table.concat(o,' | '))"
)


def main():
    step = sys.argv[1]
    if step == "teardown":
        d = lua(TEARDOWN)
        d = json.loads(d) if isinstance(d, str) else d
        STATE.write_text(json.dumps(d["got"] or {}))
        print("removed", d["removed"], "carry-over", d["got"])
        print(lua(PAVE))
    elif step == "place":
        place("--apply" in sys.argv)
    elif step == "fill":
        carry = json.loads(STATE.read_text()) if STATE.exists() else {}
        lt = "{" + ",".join(f"['{k}']={v}" for k, v in carry.items()) + "}"
        pts = "{" + ",".join(f"{{{x},{y}}}" for x, y in CHESTS) + "}"
        print(lua(FILL % (lt, pts)))
        if STATE.exists():
            STATE.unlink()


if __name__ == "__main__":
    main()
