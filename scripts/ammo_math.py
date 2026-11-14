#!/usr/bin/env python3
"""Which ammunition kills which asteroid, from the game's own prototypes and the force's research (the Captain, 2026-11-14: "do the math
and find the best ammunition"). For every ammunition a turret can fire: damage per shot after the force's bonuses and the asteroid's
resistances (flat decrease first, then percent, the game's order), shots to kill, seconds to kill for one turret, and the raw cost.
Area damage (explosive rockets) is counted once, on the target only. Usage: ammo_math.py"""
import json

from _game import tools

LUA = r"""
local f=game.forces.player local out={ammo={},ast={},tur={}}
local function effects(list,acc) for _,e in pairs(list or {}) do if e.type=='damage' and e.damage then acc[#acc+1]={e.damage.type,e.damage.amount} elseif e.type=='nested-result' and e.action then for _,a in pairs(e.action) do for _,d in pairs(a.action_delivery or {}) do effects(d.target_effects,acc) end end elseif e.type=='create-entity' and e.entity_name then local p=prototypes.entity[e.entity_name] if p and p.attack_result then for _,a in pairs(p.attack_result) do for _,d in pairs(a.action_delivery or {}) do effects(d.target_effects,acc) end end end end end end
for n,it in pairs(prototypes.item) do if it.type=='ammo' then local cat=it.ammo_category.name if cat=='bullet' or cat=='rocket' or cat=='railgun' then local at=it.get_ammo_type('turret') or it.get_ammo_type() local acc={} for _,a in pairs(at.action or {}) do for _,d in pairs(a.action_delivery or {}) do effects(d.target_effects,acc) if d.projectile then local p=prototypes.entity[d.projectile] if p then for _,pa in pairs(p.attack_result or {}) do for _,pd in pairs(pa.action_delivery or {}) do effects(pd.target_effects,acc) end end end end end end
local r=prototypes.recipe[n] local ing={} if r then for _,i in pairs(r.ingredients) do ing[#ing+1]={i.name,i.amount} end end
out.ammo[#out.ammo+1]={name=n,cat=cat,mag=it.magazine_size,dmg=acc,ing=ing,enabled=(f.recipes[n] and f.recipes[n].enabled) or false,bonus=f.get_ammo_damage_modifier(cat),speed=f.get_gun_speed_modifier(cat),weight=it.weight,stack=it.stack_size} end end end
for _,sz in pairs{'small','medium','big','huge'} do local p=prototypes.entity[sz..'-metallic-asteroid'] local res={} for k,r in pairs(p.resistances or {}) do res[k]={r.percent or 0,r.decrease or 0} end out.ast[sz]={hp=p.get_max_health(),res=res} end
for _,n in pairs{'gun-turret','rocket-turret','railgun-turret'} do local p=prototypes.entity[n] local ap=p.attack_parameters out.tur[n]={cooldown=ap.cooldown,range=ap.range,mod=ap.damage_modifier,tbonus=f.get_turret_attack_modifier(n)} end
rcon.print(helpers.table_to_json(out))
"""


def main():
    d = json.loads(tools["run_lua"](" ".join(LUA.split())))
    tur = {"bullet": "gun-turret", "rocket": "rocket-turret", "railgun": "railgun-turret"}
    print("turrets:", json.dumps(d["tur"]))
    print("asteroids:", json.dumps(d["ast"]))
    rows = []
    for a in sorted(d["ammo"], key=lambda a: (a["cat"], a["name"])):
        t = d["tur"][tur[a["cat"]]]
        mult = (1 + a["bonus"]) * (t.get("mod") or 1) * (1 + (t.get("tbonus") or 0))
        rate = 60.0 / t["cooldown"] * (1 + a["speed"])                       # shots a second for one turret
        line = {"ammo": a["name"], "researched": a["enabled"], "mult": round(mult, 2), "shots_per_s": round(rate, 2),
                "base": a["dmg"], "cost": a["ing"], "rounds_per_item": a["mag"], "kg_per_item": a["weight"] / 1000}
        for sz in ("small", "medium", "big", "huge"):
            ast = d["ast"][sz]
            per = 0.0
            for typ, amt in a["dmg"]:
                pct, dec = ast["res"].get(typ, [0, 0])
                per += max(0.0, amt * mult - dec) * (1 - pct)
            if per <= 0.5:
                line[sz] = "no effect"
            else:
                shots = -(-ast["hp"] // per)
                line[sz] = "%d dmg, %d shots, %.1f s, %.2f items" % (per, shots, shots / rate, shots / a["mag"])
        rows.append(line)
    for r in rows:
        print(json.dumps(r))


if __name__ == "__main__":
    main()
