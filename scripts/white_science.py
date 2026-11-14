#!/usr/bin/env python3
"""The Captain's `White Science` platform (platform-1, Nauvis orbit): the chunk governor (2026-11-14).
Found: every belt of the chunk loop was full (2,469 carbonic, 303 metallic, 40 oxide chunks). A crusher hands its returned chunk
back to the loop; with no gap on the loop it stands at full_output holding that chunk, takes no new chunk, and the loop never gets a
gap: a deadlock. 12 metallic crushers stood like that, so no iron ore, no plates, and the 12 science assemblers were short of iron
plate. It began when the hub was full (58,700 iron plate): the products stopped, the 23 collectors kept loading.
  governor   every loop belt is read (hold) on one green wire -> arithmetic (each * -1) -> red; a constant combinator on the same
             red wire holds TARGETS. Red therefore carries "target minus what lies on the loop" per chunk kind. The 23 collector
             inserters and the collectors themselves set their filters from it (and work only on anything > 0): a kind is caught and
             loaded only while the loop holds fewer than its target, so the loop can never fill and the plentiful kind cannot
             crowd out the scarce one.
  release    an inserter on the hub's south edge (tile RX,4) puts parked chunks from the hub back on the loop under the same rule.
  hub caps   the three inserters that load carbon, ice and iron plate into the hub are wired (green) to the hub and stop at CAPS,
             so the hub can never again fill with one product and stop the others.
  unjam      moves PARK carbonic chunks from the loop into the hub (factory-made items, nothing spawned, nothing destroyed);
             the release inserter brings them back when the loop is short of carbonic.
Steps: check | build [--apply] | config | unjam | status. Never apply twice.
Usage: white_science.py check | build [--apply] | config | unjam | status"""
import json
import sys

from _game import tools

SURF = "platform-1"
TARGETS = {"metallic-asteroid-chunk": 500, "carbonic-asteroid-chunk": 300, "oxide-asteroid-chunk": 500}
CAPS = {"carbon": 6000, "ice": 4000, "iron-plate": 8000}
PARK = 500
RX = -3                      # release inserter tile x (row 4, between the hub's south edge and the loop's bottom row y=5)
CX, AX = -7, -6              # constant combinator tile x; arithmetic combinator tiles AX..AX+1 (row 4)
ents = [{"name": "fast-inserter", "x": RX + 0.5, "y": 4.5, "direction": 0, "params": {}},          # picks up from the north (the hub)
        {"name": "constant-combinator", "x": CX + 0.5, "y": 4.5, "direction": 0, "params": {}},
        {"name": "arithmetic-combinator", "x": AX + 1.0, "y": 4.5, "direction": 4, "params": {}}]

CHECK = ("local s=game.surfaces['SURF'] local o={} for x=-9,-2 do local n=s.count_entities_filtered{area={{x+0.1,4.1},{x+0.9,4.9}}} local b=s.find_entities_filtered{type='transport-belt',position={x+0.5,5.5},radius=0.3}[1] "
         "o[#o+1]=x..':'..(n==0 and 'free' or 'USED')..'/'..(b and b.direction or 'nobelt') end "
         "local ci=0 for _,i in pairs(s.find_entities_filtered{type='inserter'}) do local pt=i.pickup_target if pt and pt.type=='asteroid-collector' then ci=ci+1 end end "
         "local c=s.find_entities_filtered{type='asteroid-collector'}[1] local cb=c.get_or_create_control_behavior() local ok1=pcall(function() return cb.set_filter end) local ok2=pcall(function() return cb.circuit_set_filters end) "
         "rcon.print('row 4 tiles (x:state/belt below dir): '..table.concat(o,' ')..' | collector inserters '..ci..' | collector behaviour has set_filter '..tostring(ok1)..', circuit_set_filters '..tostring(ok2)..' | chunk stack size '..prototypes.item['carbonic-asteroid-chunk'].stack_size)")
CONFIG = ("local s=game.surfaces['SURF'] local W=defines.wire_connector_id local hub=s.platform.hub local function at(t,x,y) return s.find_entities_filtered{type=t,position={x,y},radius=0.3}[1] end "
          "local cc=at('constant-combinator',CXP,4.5) local ar=at('arithmetic-combinator',AXP,4.5) local rel=at('inserter',RXP,4.5) "
          "local ccb=cc.get_or_create_control_behavior() while ccb.sections_count>0 do ccb.remove_section(1) end local sec=ccb.add_section() local k=0 for name,c in pairs(TARGETS) do k=k+1 sec.set_slot(k,{value={type='item',name=name,quality='normal'},min=c}) end "
          "ar.get_or_create_control_behavior().parameters={first_signal={type='virtual',name='signal-each'},second_constant=-1,operation='*',output_signal={type='virtual',name='signal-each'}} "
          "local red=ar.get_wire_connector(W.combinator_output_red,true) red.connect_to(cc.get_wire_connector(W.circuit_red,true),false) "
          "local prev=ar.get_wire_connector(W.combinator_input_green,true) local nb=0 for _,b in pairs(s.find_entities_filtered{type='transport-belt'}) do local has=false for l=1,2 do for _,it in pairs(b.get_transport_line(l).get_contents()) do if it.name:find('chunk',1,true) then has=true end end end "
          "local bc=b.get_control_behavior() if has or (bc and bc.read_contents and b.get_wire_connector(W.circuit_green,true).connection_count>0) then bc=b.get_or_create_control_behavior() bc.read_contents=true bc.read_contents_mode=defines.control_behavior.transport_belt.content_read_mode.hold "
          "local g=b.get_wire_connector(W.circuit_green,true) g.connect_to(prev,false) prev=g nb=nb+1 end end "
          "local function gov(i) i.get_wire_connector(W.circuit_red,true).connect_to(red,false) i.use_filters=true i.inserter_filter_mode='whitelist' local ib=i.get_or_create_control_behavior() ib.circuit_set_filters=true ib.circuit_enable_disable=true ib.circuit_condition={first_signal={type='virtual',name='signal-anything'},comparator='>',constant=0} end "
          "local ni,nc=0,0 for _,i in pairs(s.find_entities_filtered{type='inserter'}) do local pt=i.pickup_target if pt and pt.type=='asteroid-collector' then gov(i) ni=ni+1 end end gov(rel) "
          "for _,c in pairs(s.find_entities_filtered{type='asteroid-collector'}) do c.get_wire_connector(W.circuit_red,true).connect_to(red,false) local cb=c.get_or_create_control_behavior() cb.set_filter=true nc=nc+1 end "
          "local nh=0 for name,cap in pairs(CAPS) do for _,i in pairs(s.find_entities_filtered{type='inserter'}) do local dt=i.drop_target if dt and dt==hub and i.use_filters and i.get_filter(1) and i.get_filter(1).name==name then "
          "i.get_wire_connector(W.circuit_green,true).connect_to(hub.get_wire_connector(W.circuit_green,true),false) local ib=i.get_or_create_control_behavior() ib.circuit_enable_disable=true ib.circuit_condition={first_signal={type='item',name=name},comparator='<',constant=cap} nh=nh+1 end end end "
          "pcall(function() hub.get_or_create_control_behavior().read_contents=true end) "
          "rcon.print('loop belts read '..nb..', collector inserters governed '..ni..', collectors '..nc..', hub caps '..nh)")
UNJAM = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local inv=hub.get_inventory(defines.inventory.hub_main) local left=PARK local moved=0 "
         "for _,b in pairs(s.find_entities_filtered{type='transport-belt'}) do if left<=0 then break end for l=1,2 do local tl=b.get_transport_line(l) local c=tl.get_item_count('carbonic-asteroid-chunk') if c>0 and left>0 then local n=math.min(c,left) "
         "local put=inv.insert{name='carbonic-asteroid-chunk',count=n} if put>0 then tl.remove_item{name='carbonic-asteroid-chunk',count=put} moved=moved+put left=left-put end end end end "
         "rcon.print('carbonic chunks parked in the hub '..moved..', hub free slots '..inv.count_empty_stacks())")
STATUS = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local inv=hub.get_inventory(defines.inventory.hub_main) local o={} local st={} "
          "for _,e in pairs(s.find_entities_filtered{type={'assembling-machine','furnace'}}) do local k='?' for n,v in pairs(defines.entity_status) do if v==e.status then k=n end end local rc=e.get_recipe() k=(rc and rc.name or e.name)..' '..k st[k]=(st[k] or 0)+1 end "
          "for k,v in pairs(st) do o[#o+1]=k..' '..v end table.sort(o) local bt={} for _,e in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt','splitter'}}) do for li=1,e.get_max_transport_line_index() do for _,it in pairs(e.get_transport_line(li).get_contents()) do bt[it.name]=(bt[it.name] or 0)+it.count end end end "
          "local b={} for k,v in pairs(bt) do b[#b+1]=k..' '..v end table.sort(b) local h={} for _,n in pairs({'space-science-pack','iron-plate','carbon','ice','carbonic-asteroid-chunk','metallic-asteroid-chunk','oxide-asteroid-chunk'}) do h[#h+1]=n..' '..inv.get_item_count(n) end "
          "local f=game.forces.player.get_item_production_statistics(s) local function fl(n,p) return string.format('%.1f',f.get_flow_count{name=n,category='input',precision_index=p}) end "
          "rcon.print(table.concat(o,' ; ')..' ; ON BELTS '..table.concat(b,', ')..' ; HUB free '..inv.count_empty_stacks()..': '..table.concat(h,', ')..' ; space science a minute: last minute '..fl('space-science-pack',defines.flow_precision_index.one_minute)..', ten minutes '..fl('space-science-pack',defines.flow_precision_index.ten_minutes)..' ; paused '..tostring(s.platform.paused))")


def lua(code):
    t = "{" + ",".join("['%s']=%d" % kv for kv in TARGETS.items()) + "}"
    c = "{" + ",".join("['%s']=%d" % kv for kv in CAPS.items()) + "}"
    return tools["run_lua"](code.replace("SURF", SURF).replace("TARGETS", t).replace("CAPS", c).replace("PARK", str(PARK))
                            .replace("RXP", str(RX + 0.5)).replace("CXP", str(CX + 0.5)).replace("AXP", str(AX + 1.0)))


def main():
    step = sys.argv[1]
    if step == "check":
        print(lua(CHECK))
    elif step == "build":
        apply = "--apply" in sys.argv
        print(tools["place_entities"](json.dumps(ents), surface=SURF, dry_run=not apply))
        if apply:
            print(lua(CONFIG))
    elif step == "config":
        print(lua(CONFIG))
    elif step == "unjam":
        print(lua(UNJAM))
    elif step == "status":
        print(lua(STATUS).replace(" ; ", "\n"))


if __name__ == "__main__":
    main()
