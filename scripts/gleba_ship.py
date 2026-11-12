#!/usr/bin/env python3
"""Gleba shipping: science belt -> buffer chest -> rocket silo -> Gleba Shuttle (platform 6) -> Nauvis landing pad. Same pattern as Vulcanus.
  build    substation (138,9), roboport (144,16), silo (143.5,3.5) with three blue chests on its north side, a red chest (128.5,20.5) the
           science belt's end is emptied into, a spoilage-only inserter from that chest into a heating tower (125.5,20.5)
  config   silo answers platform requests; blue chests ask for the rocket part ingredients; the five science chambers' egg inserters work
           only while the red chest holds under 1,000 packs (one rocket; packs rot in an hour, so they are made close to pickup) (green wire along the science belt), so science stops clean instead of piling up
  stock    moves rocket part ingredients from Nauvis stock into the blue chests (2,500 processing units, 2,400 low density structure,
           950 rocket fuel: 19 rockets; the limit is what one chest holds). Factory-made on Nauvis, moved not spawned, as on Vulcanus.
  space    shuttle 6 asks for 2,000 packs from Gleba; its Gleba stop leaves with 2,000 aboard (the hub signal counts double, so the constant is 4000), or after 10 minutes with whatever it has
           (packs spoil in an hour); the Nauvis landing pad asks for 8,000
Usage: gleba_ship.py build|config|stock|space [--apply]"""
import json
import sys

from _game import tools

R = {"quality": "rare"}


def build():
    e = [{"name": "substation", "x": 138, "y": 9}, {"name": "roboport", "x": 144, "y": 16}, {"name": "rocket-silo", "x": 143.5, "y": 3.5}]
    for x in (142.5, 143.5, 144.5):
        e += [{"name": "bulk-inserter", "x": x, "y": -1.5, "direction": 0}, {"name": "requester-chest", "x": x, "y": -2.5}]
    e += [{"name": "bulk-inserter", "x": 128.5, "y": 19.5, "direction": 0}, {"name": "passive-provider-chest", "x": 128.5, "y": 20.5},
          {"name": "bulk-inserter", "x": 127.5, "y": 20.5, "direction": 4}, {"name": "heating-tower", "x": 125.5, "y": 20.5}]
    for x in e:
        x["params"] = dict(R)
    return e


CONFIG = ("local s=game.surfaces.gleba local o={} local function at(t,x,y) return s.find_entities_filtered{type=t,position={x,y},radius=0.3}[1] end "
          "local sil=s.find_entities_filtered{name='rocket-silo'}[1] sil.use_transitional_requests=true "
          "for i,item in pairs{'processing-unit','low-density-structure','rocket-fuel'} do local c=at('logistic-container',141.5+i,-2.5) local ss=c.get_logistic_sections() local se=ss.sections[1] or ss.add_section() se.set_slot(1,{value={name=item,quality='normal'},min=100}) end "
          "local function filt(x,y,item) local i=at('inserter',x,y) i.use_filters=true i.inserter_filter_mode='whitelist' i.set_filter(1,item) return i end "
          "filt(128.5,19.5,'agricultural-science-pack') filt(127.5,20.5,'spoilage') "
          "local G=defines.wire_connector_id.circuit_green local chain={at('logistic-container',128.5,20.5)} "
          "for _,x in pairs{126.5,119.5,112.5,105.5,98.5,91.5} do local b=at('transport-belt',x,18.5) local cb=b.get_or_create_control_behavior() cb.read_contents=false cb.circuit_enable_disable=false chain[#chain+1]=b end "
          "local n=0 for _,x in pairs{84.5,80.5,76.5,72.5,68.5} do local i=at('inserter',x,16.5) local cb=i.get_or_create_control_behavior() cb.circuit_enable_disable=true "
          "cb.circuit_condition={first_signal={type='item',name='agricultural-science-pack'},comparator='<',constant=1000} chain[#chain+1]=i n=n+1 end "
          "local ok=0 for k=2,#chain do local a,b=chain[k-1].get_wire_connector(G,true),chain[k].get_wire_connector(G,true) if a.is_connected_to(b) or a.connect_to(b,false) then ok=ok+1 end end "
          "rcon.print('silo answers requests '..tostring(sil.use_transitional_requests)..', gated science egg inserters '..n..', wires '..ok..' of '..(#chain-1))")

STOCK = ("local f=game.forces.player local s=game.surfaces.gleba local best,bn=nil,0 for _,net in pairs(f.logistic_networks.nauvis or {}) do if net.all_logistic_robots>bn then best=net bn=net.all_logistic_robots end end "
         "local o={} for i,q in pairs{{'processing-unit',2500},{'low-density-structure',2400},{'rocket-fuel',950}} do local c=s.find_entities_filtered{type='logistic-container',position={141.5+i,-2.5},radius=0.3}[1] "
         "local inv=c.get_inventory(defines.inventory.chest) local want=q[2]-inv.get_item_count(q[1]) if want>0 then local got=best.remove_item{name=q[1],count=want} local put=got>0 and inv.insert{name=q[1],count=got} or 0 "
         "if put<got then best.insert{name=q[1],count=got-put} end o[#o+1]=q[1]..' moved '..put end o[#o+1]=q[1]..' now '..inv.get_item_count(q[1]) end rcon.print(table.concat(o,' | '))")

SPACE = ("local f=game.forces.player local o={} local p=f.platforms[6] if p.name~='Gleba Shuttle' then rcon.print('platform 6 is '..p.name) return end "
         "local secs=p.hub.get_logistic_sections() local have=false for _,sec in pairs(secs.sections) do for _,fl in pairs(sec.filters) do if fl.value and fl.value.name=='agricultural-science-pack' then have=true end end end "
         "if not have then local sec=secs.add_section() sec.set_slot(1,{value={name='agricultural-science-pack',quality='normal'},min=2000,import_from='gleba'}) end "
         "local sch=p.schedule local w=sch.records[2].wait_conditions local has=false for _,c in pairs(w) do if c.condition and c.condition.first_signal and c.condition.first_signal.name=='agricultural-science-pack' then has=true end end "
         "if not has then local base={} for _,c in pairs(w) do if c.type=='circuit' then base[#base+1]=c end end "
         "w[#w+1]={type='circuit',compare_type='and',condition={first_signal={type='item',name='agricultural-science-pack'},comparator='>=',constant=4000}} "
         "for k,c in pairs(base) do w[#w+1]={type='circuit',compare_type=(k==1 and 'or' or 'and'),condition=c.condition} end w[#w+1]={type='time',compare_type='and',ticks=36000} "
         "sch.records[2].wait_conditions=w p.schedule=sch end "
         "local pad=game.surfaces.nauvis.find_entities_filtered{name='cargo-landing-pad'}[1] local ps=pad.get_logistic_sections() local got=false local free "
         "for _,sec in pairs(ps.sections) do for k,fl in pairs(sec.filters) do if fl.value and fl.value.name=='agricultural-science-pack' then got=true end end end "
         "if not got then local sec=ps.sections[1] local k=1 while sec.filters[k] and sec.filters[k].value do k=k+1 end sec.set_slot(k,{value={name='agricultural-science-pack',quality='normal'},min=8000}) end "
         "local t={} for _,c in pairs(p.schedule.records[2].wait_conditions) do t[#t+1]=(c.compare_type or '')..' '..c.type..(c.ticks and (' '..c.ticks) or '')..(c.condition and (' '..(c.condition.first_signal.name)..c.condition.comparator..c.condition.constant) or '') end "
         "rcon.print('shuttle 6 asks Gleba for 4000 packs; Gleba stop: '..table.concat(t,', ')..'; Nauvis pad asks for 8000')")


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    if step == "build":
        print(tools["place_entities"](json.dumps(build()), surface="gleba", dry_run=not apply)[:700])
    elif step in ("config", "stock", "space"):
        lua = {"config": CONFIG, "stock": STOCK, "space": SPACE}[step]
        print(tools["run_lua"](lua) if apply else "(dry run) " + step)


if __name__ == "__main__":
    main()
