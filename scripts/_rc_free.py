from _game import tools
lua = ("local s=game.surfaces.nauvis local o={} for y=-252,-236,2 do local row='' for x=-370,-282 do "
       "local e=s.count_entities_filtered{area={{x,y},{x+1,y+2}}} local c=s.get_tile(x,y).collides_with('player') "
       "row=row..(c and 'W' or (e>0 and '#' or '.')) end o[#o+1]=y..' '..row end rcon.print(table.concat(o,'|'))")
print(tools["run_lua"](lua).replace("|", "\n"))
