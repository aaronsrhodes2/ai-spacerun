"""Read only: one line of White Science every INTERVAL seconds for N samples: game minute, assemblers working, crushers by trouble,
loop chunks, collector stock, hub ice/carbon/plates/packs/parked chunks/free slots, packs a minute. Usage: _white_watch.py [samples] [interval]"""
import sys
import time

from _game import tools

N = int(sys.argv[1]) if len(sys.argv) > 1 else 4
IV = int(sys.argv[2]) if len(sys.argv) > 2 else 25
LUA = ("local s=game.surfaces['platform-1'] local inv=s.platform.hub.get_inventory(defines.inventory.hub_main) local W=defines.entity_status.working local aw,an=0,0 local cr={} "
       "for _,e in pairs(s.find_entities_filtered{type='assembling-machine'}) do local r=e.get_recipe() if r and r.name=='space-science-pack' then an=an+1 if e.status==W then aw=aw+1 end elseif e.name=='crusher' then "
       "local out=e.get_inventory(defines.inventory.crafter_output) local stuck=false if e.status==defines.entity_status.full_output and out then for _,it in pairs(out.get_contents()) do if it.name:find('chunk',1,true) then stuck=true end end end if stuck then cr[#cr+1]=e.position.x..','..e.position.y end end end "
       "local bt={met=0,car=0,oxi=0} for _,e in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt','splitter'}}) do for li=1,e.get_max_transport_line_index() do for _,it in pairs(e.get_transport_line(li).get_contents()) do local k=it.name:sub(1,3) if bt[k] and it.name:find('chunk',1,true) then bt[k]=bt[k]+it.count end end end end "
       "local ct={met=0,car=0,oxi=0} for _,c in pairs(s.find_entities_filtered{type='asteroid-collector'}) do for _,it in pairs(c.get_output_inventory().get_contents()) do local k=it.name:sub(1,3) ct[k]=ct[k]+it.count end end "
       "local f=game.forces.player.get_item_production_statistics(s) "
       "rcon.print(string.format('min %.1f | science %d/%d working | crushers holding a chunk they cannot return: %d %s | loop m/c/o %d/%d/%d | collectors m/c/o %d/%d/%d | hub ice %d carbon %d plate %d packs %d parked %d free %d | packs/min 1m %.0f 10m %.0f | ice +%.0f -%.0f',"
       "game.tick/3600,aw,an,#cr,table.concat(cr,' '),bt.met,bt.car,bt.oxi,ct.met,ct.car,ct.oxi,inv.get_item_count('ice'),inv.get_item_count('carbon'),inv.get_item_count('iron-plate'),inv.get_item_count('space-science-pack'),inv.get_item_count('carbonic-asteroid-chunk'),inv.count_empty_stacks(),"
       "f.get_flow_count{name='space-science-pack',category='input',precision_index=defines.flow_precision_index.one_minute},f.get_flow_count{name='space-science-pack',category='input',precision_index=defines.flow_precision_index.ten_minutes},"
       "f.get_flow_count{name='ice',category='input',precision_index=defines.flow_precision_index.ten_minutes},f.get_flow_count{name='ice',category='output',precision_index=defines.flow_precision_index.ten_minutes}))")
for i in range(N):
    print(tools["run_lua"](LUA).strip(), flush=True)
    if i + 1 < N:
        time.sleep(IV)
