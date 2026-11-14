#!/usr/bin/env python3
"""Starting the Aquilo base once the relayed cargo has landed on its pad (see aquilo_base.py for the layout and the heat rules).
Steps, in this order:
  reactor   puts the nuclear reactor back (it soaks 10 MJ a degree, so only with fuel), the first fuel cell straight into it (its inserter is
            frozen until it is hot) and the rest of a first batch in the chest beside it; takes the cells out of the pad
  robots    moves the construction and logistic robots from the pad into the roboport
  icebergs  orders the nearest lithium icebergs deconstructed (robots mine them: ice platform, ice, lithium); counts as mining for the
            lithium-processing trigger; spoils go to the storage chest
  status    heat, power, water, robots, lithium and the three triggers
Usage: aquilo_start.py reactor|robots|icebergs [N]|status"""
import json
import sys

from _game import tools

Q = {"quality": "epic"}
PAD = "local s=game.surfaces.aquilo local pad=s.find_entities_filtered{type='cargo-landing-pad'}[1] local pi=pad.get_inventory(defines.inventory.cargo_landing_pad_main) "


def reactor():
    ents = [{"name": "nuclear-reactor", "x": 17.5, "y": -16.5, "direction": 0, "params": Q}, {"name": "fast-inserter", "x": 17.5, "y": -19.5, "direction": 0, "params": Q},
            {"name": "steel-chest", "x": 17.5, "y": -20.5, "direction": 0, "params": Q}]
    r = json.loads(tools["place_entities"](json.dumps(ents), surface="aquilo", dry_run=False))
    print("placed", r.get("placed"), r.get("failed") or "")
    print(tools["run_lua"](PAD + "local have=pi.get_item_count('uranium-fuel-cell') if have<2 then rcon.print('no fuel cells on the pad yet ('..have..')') return end local n=pi.remove{name='uranium-fuel-cell',count=math.min(have,12)} "
                           "local rx=s.find_entities_filtered{name='nuclear-reactor'}[1] local a=rx.get_fuel_inventory().insert{name='uranium-fuel-cell',count=1} local c=s.find_entities_filtered{name='steel-chest',position={17.5,-20.5},radius=0.4}[1] local b=c.get_inventory(defines.inventory.chest).insert{name='uranium-fuel-cell',count=n-a} "
                           "rcon.print('reactor fuelled: '..a..' in the reactor, '..b..' in its chest; pad cells left '..pi.get_item_count('uranium-fuel-cell'))"))


def robots():
    print(tools["run_lua"](PAD + "local rp=s.find_entities_filtered{name='roboport'}[1] local inv=rp.get_inventory(defines.inventory.roboport_robot) local x,y=0,0 "
                           "for _,it in pairs(pi.get_contents()) do if it.name=='construction-robot' or it.name=='logistic-robot' then local n=pi.remove{name=it.name,count=it.count,quality=it.quality} local k=inv.insert{name=it.name,count=n,quality=it.quality} if it.name=='construction-robot' then x=x+k else y=y+k end end end "
                           "rcon.print('robots into the roboport (any quality): construction '..x..', logistic '..y)"))


def icebergs(n):
    print(tools["run_lua"]("local s=game.surfaces.aquilo local f=game.forces.player local rp=s.find_entities_filtered{name='roboport'}[1] local list={} for _,e in pairs(s.find_entities_filtered{name={'lithium-iceberg-big','lithium-iceberg-huge'},position=rp.position,radius=30}) do "
                           "list[#list+1]={math.abs(e.position.x-rp.position.x)+math.abs(e.position.y-rp.position.y),e} end table.sort(list,function(a,b) return a[1]<b[1] end) local k=0 for i=1,math.min(%d,#list) do if list[i][2].order_deconstruction(f) then k=k+1 end end "
                           "rcon.print('icebergs ordered for the robots: '..k..' of '..#list..' within 30 tiles')" % n))


def status():
    print(tools["run_lua"]("local s=game.surfaces.aquilo local f=game.forces.player local o={} local function st(e) for a,v in pairs(defines.entity_status) do if v==e.status then return a end end return '?' end "
                           "local rx=s.find_entities_filtered{name='nuclear-reactor'}[1] local tw=s.find_entities_filtered{name='heating-tower'}[1] local ex=s.find_entities_filtered{name='heat-exchanger'}[1] local tb=s.find_entities_filtered{name='steam-turbine'}[1] local ml=s.find_entities_filtered{name='chemical-plant'}[1] "
                           "o[#o+1]='reactor '..(rx and (st(rx)..' '..string.format('%.0f',rx.temperature)..'C fuel '..rx.get_fuel_inventory().get_item_count()) or 'none')..' | tower '..st(tw)..' '..string.format('%.0f',tw.temperature)..'C | exchanger '..st(ex)..' | turbine '..st(tb)..' | melter '..st(ml) "
                           "local fr,tot=0,0 for _,e in pairs(s.find_entities_filtered{area={{0,-24},{36,0}},force='player'}) do tot=tot+1 if e.status==defines.entity_status.frozen then fr=fr+1 end end o[#o+1]='frozen '..fr..' of '..tot "
                           "local rp=s.find_entities_filtered{name='roboport'}[1] o[#o+1]='roboport '..st(rp)..' robots '..rp.get_inventory(defines.inventory.roboport_robot).get_item_count() "
                           "local pad=s.find_entities_filtered{type='cargo-landing-pad'}[1] local pi=pad.get_inventory(defines.inventory.cargo_landing_pad_main) o[#o+1]='pad: cells '..pi.get_item_count('uranium-fuel-cell')..' lithium '..pi.get_item_count('lithium')..' ice '..pi.get_item_count('ice')..' rocket fuel '..pi.get_item_count('rocket-fuel') "
                           "local t={} for _,n in pairs{'lithium-processing','cryogenic-plant','cryogenic-science-pack'} do t[#t+1]=n..'='..tostring(f.technologies[n].researched) end o[#o+1]='techs '..table.concat(t,', ') rcon.print(table.concat(o,' ;; '))").replace(" ;; ", "\n"))


if __name__ == "__main__":
    step = sys.argv[1]
    if step == "reactor":
        reactor()
    elif step == "robots":
        robots()
    elif step == "icebergs":
        icebergs(int(sys.argv[2]) if len(sys.argv) > 2 else 12)
    else:
        status()
