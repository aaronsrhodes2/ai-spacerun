local s=game.surfaces.aquilo local o={}
for _,p in pairs({{16.5,4.5},{16.5,5.5},{18.5,2.5},{18.5,3.5},{-27.5,2.5},{-23.5,2.5}}) do for _,d in pairs({4,12}) do
o[#o+1]=p[1]..','..p[2]..' d'..d..' '..tostring(s.can_place_entity{name='offshore-pump',position=p,direction=d,force='player',build_check_type=defines.build_check_type.manual}) end end
for y=1,6 do local r={} for x=15,21 do r[#r+1]=s.get_tile(x,y).name end o[#o+1]=y..': '..table.concat(r,' ') end
rcon.print(table.concat(o,'\n'))
