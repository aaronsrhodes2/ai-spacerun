import sys, time
sys.path.insert(0,"scripts")
from _game import tools
lua=("local s=game.surfaces['platform-1'] local hub=s.platform.hub.get_inventory(defines.inventory.hub_main) local n=game.surfaces.nauvis "
 "local pad=n.find_entities_filtered{name='cargo-landing-pad',force='player'}[1] local labs=0 for _,l in pairs(n.find_entities_filtered{type='lab'}) do labs=labs+l.get_inventory(defines.inventory.lab_input).get_item_count('space-science-pack') end "
 "local ps=game.forces.player.get_item_production_statistics(s) local pods=#n.find_entities_filtered{type='cargo-pod'} "
 "local f=game.forces.player rcon.print(string.format('hub %d pad %d labs %d pods-on-nauvis %d made %.2f/s research %s %.2f',hub.get_item_count('space-science-pack'),pad.get_inventory(defines.inventory.chest).get_item_count('space-science-pack'),labs,pods,ps.get_flow_count{name='space-science-pack',category='input',precision_index=defines.flow_precision_index.one_minute}/60,f.current_research and f.current_research.name or 'none',f.research_progress))")
for i in range(9):
    print(time.strftime("%H:%M:%S"), tools["run_lua"](lua), flush=True)
    time.sleep(20)
