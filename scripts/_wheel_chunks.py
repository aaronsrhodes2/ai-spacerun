"""Read only: chunks lying on each wheel's belts by region (four spokes, centre, rim, spiral), collector fill, crusher statuses in the centre."""
from _game import tools
from _wheels import wheels

LUA = (
    "local s=game.surfaces['SURF'] local reg={} local function add(r,n,c) reg[r]=reg[r] or {} reg[r][n]=(reg[r][n] or 0)+c end "
    "for _,e in pairs(s.find_entities_filtered{type={'transport-belt','underground-belt','splitter'}}) do local x,y=e.position.x,e.position.y local d=math.sqrt(x*x+y*y) local r "
    "if d>580 then r='rim' elseif x<-52 and x>-128 and y<-3 and y>-80 then r='spiral' elseif d<=52 then r='centre' elseif math.abs(y)<=4 and x<0 then r='W spoke' elseif math.abs(y)<=4 then r='E spoke' elseif math.abs(x)<=4 and y<0 then r='N spoke' elseif math.abs(x)<=4 then r='S spoke' else r='other' end "
    "for l=1,e.get_max_transport_line_index() do for _,it in pairs(e.get_transport_line(l).get_contents()) do if it.name:find('chunk') then add(r,it.name:sub(1,3),it.count) end end end end "
    "local o={} for r,t in pairs(reg) do local c={} for n,v in pairs(t) do c[#c+1]=n..' '..v end table.sort(c) o[#o+1]=r..': '..table.concat(c,', ') end table.sort(o) "
    "local cf,ct,cn=0,0,0 for _,c in pairs(s.find_entities_filtered{type='asteroid-collector'}) do cn=cn+1 local inv=c.get_output_inventory() if inv then ct=ct+inv.get_item_count() if inv.is_full() then cf=cf+1 end end end "
    "o[#o+1]='collectors '..cn..' holding '..ct..' chunks, full '..cf "
    "local st={} for _,c in pairs(s.find_entities_filtered{name='crusher'}) do local x,y=c.position.x,c.position.y if x*x+y*y<56*56 then local k='?' for n,v in pairs(defines.entity_status) do if v==c.status then k=n end end local rc=c.get_recipe() k=(rc and rc.name or 'none')..' '..k st[k]=(st[k] or 0)+1 end end "
    "local l={} for k,v in pairs(st) do l[#l+1]=k..' '..v end table.sort(l) o[#o+1]='centre crushers: '..table.concat(l,'; ') "
    "rcon.print(table.concat(o,'\\n'))")
for name, planet, surface, turrets in wheels():
    print("==", name, surface)
    print(tools["run_lua"](LUA.replace("SURF", surface)))
