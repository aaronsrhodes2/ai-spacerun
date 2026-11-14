#!/usr/bin/env python3
"""The Captain's `White Science` platform (platform-1, Nauvis orbit): chunk governor, reprocessing balance, productivity (2026-11-14).
The Captain: it does nothing but space science and should be a model of it.

Layout as it stands (the Captain's build): one chunk loop round the hull fed by 23 collectors; three sorting inserters put each kind
on its own stretch: 12 oxide crushers (y=-9.5, x -46..-24) -> ice, 12 metallic crushers (y=1.5, x -46..-24) -> ore straight into 8
furnaces -> plates, 10 carbonic crushers (x=-15.5, y -19..-1) -> carbon. Products go through the hub to 12 assemblers (y=-8.5).
A crusher hands its returned chunks back to the stretch it feeds from.

Found: every loop belt was full (2,469 carbonic chunks). A crusher with a returned chunk and no gap to put it on stands at
full_output, takes no new chunk, and the loop never gets a gap: a deadlock. It began when the hub was full of iron plate (58,700).
Nauvis orbit gives metallic : carbonic : oxide about 3 : 2 : 1, the packs need 1 : 1 : 2, so oxide (ice) is always the scarce kind.

  governor   every loop belt is read (hold) on one green wire -> arithmetic (each * -1) -> red; a constant combinator on the same
             red wire holds TARGETS. Red therefore carries "target minus what lies on the loop" per chunk kind. The 23 collector
             inserters and the collectors themselves set their filters from it (and work only on anything > 0): a kind is caught and
             loaded only while the loop holds fewer than its target, so the loop stays loose and returns always find a gap.
  release    an inserter on the hub's south edge (tile RX,4) puts parked chunks from the hub back on the loop under the same rule.
  hub caps   the three inserters that load carbon, ice and iron plate into the hub are wired (green) to the hub and stop at CAPS,
             so the hub can never again fill with one product and stop the others.
  balance    reprocessing turns the plentiful kinds into oxide (a craft takes 1 chunk and gives 0.4 of the same kind and 0.2 of
             each other kind). Metallic: the crushers at x in KEEP (the middle one of each three, which between them feed all
             eight furnaces) stay on crushing, the other eight reprocess. Carbonic: the six at y -19..-9 reprocess, the four at
             y -7..-1 crush. Two deciders (row 4, tiles -2..-1 and 0..1) read the governor (red) and the hub (green):
               metallic reprocessors run while oxide is wanted (loop below its target) AND the hub holds more than FLOOR iron plate
               carbonic reprocessors run while oxide is wanted AND the hub holds more than FLOOR carbon
             (signal R on the decider's green output to the reprocessors' intake inserters). So plates and carbon keep first call,
             everything else becomes oxide, and when ice and oxide are plentiful the reprocessors rest and the collectors' filters
             stop the intake: nothing is ever thrown away.
  modules    the 12 science assemblers carry two legendary productivity module 2 each (+30%: ice is the scarce input, so packs per
             ice is what counts; machine capacity falls from 602 to about 356 packs a minute, still above what the chunks give).
             Taken from the Nauvis network (factory-made), the epic speed modules go back there. Crushers and furnaces already hold
             epic productivity module 2; reprocessing takes no productivity (speed modules there). Every slot is full, so
             module_mall.py install (the autopilot), which only fills EMPTY slots, changes nothing here.
  unjam      moves PARK carbonic chunks from the loop into the hub (factory-made items, nothing spawned, nothing destroyed);
             the release inserter brings them back when the loop is short of carbonic.
Steps: check | build [--apply] | balance [--apply] | config | unjam | modules | status. Never apply a build twice.
Usage: white_science.py check | build [--apply] | balance [--apply] | config | unjam | modules | status"""
import json
import sys

from _game import tools

SURF = "platform-1"
TARGETS = {"metallic-asteroid-chunk": 300, "carbonic-asteroid-chunk": 200, "oxide-asteroid-chunk": 500}
CAPS = {"carbon": 6000, "ice": 4000, "iron-plate": 8000}
FLOOR = {"iron-plate": 2000, "carbon": 300}       # carbon has first call anyway: the four carbon crushers stand first on the carbonic stretch
KEEP = (-44, -38, -32, -26)  # metallic crushers (centre x) that stay on crushing
PARK = 300
RX = -3                      # release inserter tile x (row 4, between the hub's south edge and the loop's bottom row y=5)
CX, AX = -7, -6              # constant combinator tile x; arithmetic combinator tiles AX..AX+1 (row 4)
DM, DC = -1.0, 1.0           # decider centres x (row 4): metallic, carbonic
ents = [{"name": "fast-inserter", "x": RX + 0.5, "y": 4.5, "direction": 0, "params": {}},          # picks up from the north (the hub)
        {"name": "constant-combinator", "x": CX + 0.5, "y": 4.5, "direction": 0, "params": {}},
        {"name": "arithmetic-combinator", "x": AX + 1.0, "y": 4.5, "direction": 4, "params": {}}]
ents2 = [{"name": "decider-combinator", "x": DM, "y": 4.5, "direction": 4, "params": {}},
         {"name": "decider-combinator", "x": DC, "y": 4.5, "direction": 4, "params": {}}]

CHECK = ("local s=game.surfaces['SURF'] local o={} for x=-9,3 do local n=s.count_entities_filtered{area={{x+0.1,4.1},{x+0.9,4.9}}} local b=s.find_entities_filtered{type='transport-belt',position={x+0.5,5.5},radius=0.3}[1] "
         "o[#o+1]=x..':'..(n==0 and 'free' or 'USED')..'/'..(b and b.direction or 'nobelt') end "
         "local ci=0 for _,i in pairs(s.find_entities_filtered{type='inserter'}) do local pt=i.pickup_target if pt and pt.type=='asteroid-collector' then ci=ci+1 end end "
         "rcon.print('row 4 tiles (x:state/belt below dir): '..table.concat(o,' ')..' | collector inserters '..ci..' | chunk stack size '..prototypes.item['carbonic-asteroid-chunk'].stack_size)")
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
BALANCE = ("local s=game.surfaces['SURF'] local W=defines.wire_connector_id local hub=s.platform.hub local function at(t,x,y) return s.find_entities_filtered{type=t,position={x,y},radius=0.3}[1] end "
           "local ar=at('arithmetic-combinator',AXP,4.5) local red=ar.get_wire_connector(W.combinator_output_red,true) local dm,dc=at('decider-combinator',DMX,4.5),at('decider-combinator',DCX,4.5) if not dm or not dc then rcon.print('deciders missing: run balance --apply') return end "
           "local function setd(d,item,floor) for _,id in pairs{W.combinator_input_red,W.combinator_input_green,W.combinator_output_red,W.combinator_output_green} do d.get_wire_connector(id,true).disconnect_all() end "
           "d.get_wire_connector(W.combinator_input_red,true).connect_to(red,false) d.get_wire_connector(W.combinator_input_green,true).connect_to(hub.get_wire_connector(W.circuit_green,true),false) "
           "d.get_or_create_control_behavior().parameters={conditions={{first_signal={type='item',name='oxide-asteroid-chunk'},first_signal_networks={red=true,green=false},comparator='>',constant=0},"
           "{first_signal={type='item',name=item},first_signal_networks={red=false,green=true},comparator='>',constant=floor,compare_type='and'}},outputs={{signal={type='virtual',name='signal-R'},copy_count_from_input=false,constant=1}}} end "
           "setd(dm,'iron-plate',FLOORP) setd(dc,'carbon',FLOORC) local keep={} for _,x in pairs({KEEP}) do keep[x]=true end local back,nr,nk=0,0,0 "
           "for _,c in pairs(s.find_entities_filtered{name='crusher'}) do local r=c.get_recipe() local rn=r and r.name or '' local want=rn "
           "if rn:find('metallic',1,true) then want=keep[c.position.x] and 'metallic-asteroid-crushing' or 'metallic-asteroid-reprocessing' end "
           "if want~=rn then for _,it in pairs(c.set_recipe(want)) do back=back+hub.insert{name=it.name,count=it.count,quality=it.quality} end end "
           "local rep=want:find('reprocessing',1,true)~=nil local d=want:find('metallic',1,true) and dm or dc "
           "if want:find('oxide',1,true)==nil then for _,i in pairs(s.find_entities_filtered{type='inserter',area={{c.position.x-3,c.position.y-3},{c.position.x+3,c.position.y+3}}}) do if i.drop_target==c then local g=i.get_wire_connector(W.circuit_green,true) g.disconnect_all() local cb=i.get_or_create_control_behavior() "
           "if rep then g.connect_to(d.get_wire_connector(W.combinator_output_green,true),false) cb.circuit_enable_disable=true cb.circuit_condition={first_signal={type='virtual',name='signal-R'},comparator='>',constant=0} nr=nr+1 else cb.circuit_enable_disable=false nk=nk+1 end end end end end "
           "rcon.print('reprocessor intakes gated '..nr..', crusher intakes free '..nk..', items handed to the hub on recipe change '..back)")
UNJAM = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local inv=hub.get_inventory(defines.inventory.hub_main) local left=PARK local moved=0 "
         "for _,b in pairs(s.find_entities_filtered{type='transport-belt'}) do if left<=0 then break end for l=1,2 do local tl=b.get_transport_line(l) local c=tl.get_item_count('carbonic-asteroid-chunk') if c>0 and left>0 then local n=math.min(c,left) "
         "local put=inv.insert{name='carbonic-asteroid-chunk',count=n} if put>0 then tl.remove_item{name='carbonic-asteroid-chunk',count=put} moved=moved+put left=left-put end end end end "
         "rcon.print('carbonic chunks parked in the hub '..moved..', hub free slots '..inv.count_empty_stacks())")
MODULES = ("local s=game.surfaces['SURF'] local net=game.surfaces.nauvis.find_logistic_network_by_position({-27.5,-393.5},'player') local put,back,short=0,0,0 "
           "for _,m in pairs(s.find_entities_filtered{type='assembling-machine'}) do local r=m.get_recipe() if r and r.name=='space-science-pack' then local mi=m.get_module_inventory() for i=1,#mi do local st=mi[i] "
           "if not (st.valid_for_read and st.name=='productivity-module-2' and st.quality.name=='legendary') then if net.get_item_count({name='productivity-module-2',quality='legendary'})>0 and net.remove_item{name='productivity-module-2',quality='legendary',count=1}==1 then "
           "if st.valid_for_read then back=back+net.insert{name=st.name,count=st.count,quality=st.quality.name} end st.set_stack{name='productivity-module-2',count=1,quality='legendary'} put=put+1 else short=short+1 end end end end end "
           "rcon.print('legendary productivity module 2 installed '..put..', old modules returned to the Nauvis network '..back..', slots left for want of modules '..short..', left in the network '..net.get_item_count({name='productivity-module-2',quality='legendary'}))")
STATUS = ("local s=game.surfaces['SURF'] local hub=s.platform.hub local inv=hub.get_inventory(defines.inventory.hub_main) local o={} local st={} "
          "for _,e in pairs(s.find_entities_filtered{type={'assembling-machine','furnace'}}) do local k='?' for n,v in pairs(defines.entity_status) do if v==e.status then k=n end end local rc=e.get_recipe() k=(rc and rc.name or e.name)..' '..k st[k]=(st[k] or 0)+1 end "
          "for k,v in pairs(st) do o[#o+1]=k..' '..v end table.sort(o) local bt={} for _,e in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt','splitter'}}) do for li=1,e.get_max_transport_line_index() do for _,it in pairs(e.get_transport_line(li).get_contents()) do bt[it.name]=(bt[it.name] or 0)+it.count end end end "
          "local b={} for k,v in pairs(bt) do b[#b+1]=k..' '..v end table.sort(b) local h={} for _,n in pairs({'space-science-pack','iron-plate','carbon','ice','carbonic-asteroid-chunk','metallic-asteroid-chunk','oxide-asteroid-chunk'}) do h[#h+1]=n..' '..inv.get_item_count(n) end "
          "local ct={} for _,c in pairs(s.find_entities_filtered{type='asteroid-collector'}) do for _,it in pairs(c.get_output_inventory().get_contents()) do ct[it.name:sub(1,3)]=(ct[it.name:sub(1,3)] or 0)+it.count end end "
          "local f=game.forces.player.get_item_production_statistics(s) local P=defines.flow_precision_index local function fl(n,c,p) return string.format('%.1f',f.get_flow_count{name=n,category=c,precision_index=p}) end "
          "local ch={} for _,n in pairs({'metallic-asteroid-chunk','carbonic-asteroid-chunk','oxide-asteroid-chunk','ice'}) do ch[#ch+1]=n:sub(1,3)..' +'..fl(n,'input',P.ten_minutes)..' -'..fl(n,'output',P.ten_minutes) end "
          "rcon.print(table.concat(o,' ; ')..' ; ON BELTS '..table.concat(b,', ')..' ; IN COLLECTORS met '..(ct.met or 0)..', car '..(ct.car or 0)..', oxi '..(ct.oxi or 0)..' ; HUB free '..inv.count_empty_stacks()..': '..table.concat(h,', ')"
          "..' ; made/used a minute (10 min): '..table.concat(ch,', ')..' ; space science a minute: last minute '..fl('space-science-pack','input',P.one_minute)..', ten minutes '..fl('space-science-pack','input',P.ten_minutes)..', hour '..fl('space-science-pack','input',P.one_hour)..' ; tick '..game.tick)")


def lua(code):
    t = "{" + ",".join("['%s']=%d" % kv for kv in TARGETS.items()) + "}"
    c = "{" + ",".join("['%s']=%d" % kv for kv in CAPS.items()) + "}"
    return tools["run_lua"](code.replace("SURF", SURF).replace("TARGETS", t).replace("CAPS", c).replace("PARK", str(PARK))
                            .replace("RXP", str(RX + 0.5)).replace("CXP", str(CX + 0.5)).replace("AXP", str(AX + 1.0))
                            .replace("DMX", str(DM)).replace("DCX", str(DC)).replace("FLOORP", str(FLOOR["iron-plate"])).replace("FLOORC", str(FLOOR["carbon"]))
                            .replace("KEEP", ",".join(str(k) for k in KEEP)))


def main():
    step = sys.argv[1]
    apply = "--apply" in sys.argv
    if step == "check":
        print(lua(CHECK))
    elif step == "build":
        print(tools["place_entities"](json.dumps(ents), surface=SURF, dry_run=not apply))
        if apply:
            print(lua(CONFIG))
    elif step == "balance":
        print(tools["place_entities"](json.dumps(ents2), surface=SURF, dry_run=not apply))
        if apply:
            print(lua(CONFIG))
            print(lua(BALANCE))
    elif step == "config":
        print(lua(CONFIG))
        print(lua(BALANCE))
    elif step == "unjam":
        print(lua(UNJAM))
    elif step == "modules":
        print(lua(MODULES))
    elif step == "status":
        print(lua(STATUS).replace(" ; ", "\n"))


if __name__ == "__main__":
    main()
