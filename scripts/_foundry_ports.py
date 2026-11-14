"""Read only: the foundry's fluid boxes (production type, pipe connection positions for the north-facing prototype), its speed by quality,
and for one standing foundry on a wheel the fluidbox neighbours."""
from _game import tools

print(tools["run_lua"](
    "local p=prototypes.entity['foundry'] local o={} for i,fb in pairs(p.fluidbox_prototypes) do local c={} for _,pc in pairs(fb.pipe_connections) do c[#c+1]=serpent.line(pc.positions)..' dir '..tostring(pc.direction)..' '..tostring(pc.flow_direction) end "
    "o[#o+1]=i..' '..fb.production_type..' '..table.concat(c,' / ') end "
    "o[#o+1]='speed normal '..p.get_crafting_speed()..' epic '..p.get_crafting_speed('epic')..' size '..serpent.line(p.collision_box) "
    "for _,r in pairs({'iron-ore-melting','casting-iron','casting-steel'}) do local rp=prototypes.recipe[r] local a={} for _,g in pairs(rp.ingredients) do a[#a+1]=g.amount..' '..g.name end local b={} for _,g in pairs(rp.products) do b[#b+1]=g.amount..' '..g.name end o[#o+1]=r..': '..table.concat(a,' + ')..' -> '..table.concat(b,' + ')..' in '..rp.energy..' s, enabled '..tostring(game.forces.player.recipes[r].enabled) end "
    "rcon.print(table.concat(o,' ; '))").replace(" ; ", "\n"))
