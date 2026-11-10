"""Survey every storage chest: position, contents, and which inserters feed or empty it."""
import json
import fx

LUA = ("local s=game.surfaces.nauvis local f=game.forces.player local out={} "
"for _,c in pairs(s.find_entities_filtered{name='storage-chest',force=f}) do local x,y=c.position.x,c.position.y local ins,outs={},{} "
"for _,i in pairs(s.find_entities_filtered{type='inserter',area={{x-1.6,y-1.6},{x+1.6,y+1.6}}}) do local pp,dp=i.pickup_position,i.drop_position "
"if math.abs(pp.x-x)<0.5 and math.abs(pp.y-y)<0.5 then outs[#outs+1]=i.name end if math.abs(dp.x-x)<0.5 and math.abs(dp.y-y)<0.5 then ins[#ins+1]=i.name end end "
"local inv=c.get_inventory(defines.inventory.chest) local its={} local tot=0 for _,it in pairs(inv.get_contents()) do its[#its+1]={it.name,it.count} tot=tot+it.count end table.sort(its,function(a,b) return a[2]>b[2] end) local top={} for i=1,4 do if its[i] then top[#top+1]=its[i] end end "
"out[#out+1]={x=x,y=y,i=#ins,o=#outs,tot=tot,n=#its,top=top,free=inv.count_empty_stacks()} end rcon.print(helpers.table_to_json(out))")

if __name__ == "__main__":
    data = fx.jlua(LUA)
    json.dump(data, open("_chests.json", "w"))
    data.sort(key=lambda c: (c["x"], c["y"]))
    for c in data:
        print(f"({c['x']:.1f},{c['y']:.1f}) in={c['i']} out={c['o']} items={c['tot']} kinds={c['n']} free={c['free']} {c['top']}")
