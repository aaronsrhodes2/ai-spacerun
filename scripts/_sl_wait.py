import sys, time
sys.path.insert(0, "D:/Aaron/development/AI-factorio/scripts")
from _game import tools
L = tools["run_lua"]
Q = ("local p for _,q in pairs(game.forces.player.platforms) do if q.name:find('Fulgora-Aquilo 4',1,true) then p=q end end local hi=p.hub.get_inventory(defines.inventory.hub_main) "
     "local ap=game.surfaces.aquilo.find_entities_filtered{type='cargo-landing-pad'}[1].get_inventory(defines.inventory.cargo_landing_pad_main) "
     "rcon.print((p.space_location and p.space_location.name or 'flight')..' st'..p.state..' | rockets '..hi.get_item_count('explosive-rocket')..' | hub holm '..hi.get_item_count('holmium-plate')..' PU '..hi.get_item_count('processing-unit')..' SC '..hi.get_item_count('superconductor')..' rob '..hi.get_item_count('construction-robot')..' conc '..hi.get_item_count('refined-concrete')..' trash '..p.hub.get_inventory(defines.inventory.hub_trash).get_item_count()"
     "..' | AQUILO PAD holm '..ap.get_item_count('holmium-plate')..' PU '..ap.get_item_count('processing-unit')..' SC '..ap.get_item_count('superconductor')..' rob '..ap.get_item_count('construction-robot')..' conc '..ap.get_item_count('refined-concrete')..' free '..ap.count_empty_stacks())")
end = time.time() + float(sys.argv[1])
while time.time() < end:
    print(time.strftime("%H:%M:%S"), L(Q).strip(), flush=True)
    time.sleep(20)
