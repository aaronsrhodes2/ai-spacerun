import time
from _game import tools
PACKS = ['automation-science-pack','logistic-science-pack','military-science-pack','chemical-science-pack','production-science-pack','utility-science-pack','space-science-pack','metallurgic-science-pack','electromagnetic-science-pack','agricultural-science-pack']
LIST = "{" + ",".join("'" + p + "'" for p in PACKS) + "}"
LUA = ("local f=game.forces.player local out={} for _,pk in pairs(" + LIST + ") do local tot=0 "
       "for _,s in pairs(game.surfaces) do local st=f.get_item_production_statistics(s) tot=tot+st.get_input_count(pk) end "
       "out[#out+1]=pk..'='..tot end rcon.print(table.concat(out,' '))")
def sample():
    raw = tools["run_lua"](LUA)
    d = {}
    for tok in raw.split():
        if '=' in tok:
            k, v = tok.split('=', 1)
            try: d[k] = int(v)
            except ValueError: pass
    return d
a = sample()
time.sleep(60)
b = sample()
for p in PACKS:
    print(f"{p:32s} made in 60s: {b.get(p,0)-a.get(p,0)}   (total so far {b.get(p,0)})")
