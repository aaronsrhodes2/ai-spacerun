"""Read only: per wheel, items made (+) and used (-) a minute over a window (default ten minutes; `1m` or `1h` as argument)."""
import sys

from _game import tools
from _wheels import wheels

PREC = {"1m": "one_minute", "10m": "ten_minutes", "1h": "one_hour"}[sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in ("1m", "10m", "1h") else "10m"]
ITEMS = ["metallic-asteroid-chunk", "carbonic-asteroid-chunk", "oxide-asteroid-chunk", "iron-ore", "copper-ore", "carbon", "sulfur", "ice", "calcite", "coal", "stone",
         "iron-plate", "copper-plate", "steel-plate", "iron-gear-wheel", "copper-cable", "electronic-circuit", "advanced-circuit", "plastic-bar", "stone-brick", "rail",
         "space-science-pack", "automation-science-pack", "logistic-science-pack", "chemical-science-pack", "military-science-pack", "production-science-pack", "utility-science-pack"]
LUA = ("local s=game.surfaces['SURF'] local f=game.forces.player local st=f.get_item_production_statistics(s) local fl=f.get_fluid_production_statistics(s) local pr=defines.flow_precision_index.PREC local o={} "
       "for _,n in pairs({ITEMS}) do local a=st.get_flow_count{name=n,category='input',precision_index=pr} local b=st.get_flow_count{name=n,category='output',precision_index=pr} if a>0.05 or b>0.05 then o[#o+1]=n..' +'..string.format('%.1f',a)..' -'..string.format('%.1f',b) end end "
       "for _,n in pairs({'molten-iron','molten-copper','petroleum-gas','water'}) do local a=fl.get_flow_count{name=n,category='input',precision_index=pr} local b=fl.get_flow_count{name=n,category='output',precision_index=pr} if a>0.05 or b>0.05 then o[#o+1]=n..' +'..string.format('%.0f',a)..' -'..string.format('%.0f',b) end end "
       "rcon.print(table.concat(o,'; '))")
if __name__ == "__main__":
    for name, planet, surface, turrets in wheels():
        print("==", name, surface, PREC)
        print(tools["run_lua"](LUA.replace("SURF", surface).replace("PREC", PREC).replace("ITEMS", ",".join("'%s'" % i for i in ITEMS))))
