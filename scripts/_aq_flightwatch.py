"""Watch ship 4 on a kit flight: _aq_flightwatch.py MINUTES [SECS]. Prints location, state, ammo, kit aboard and the Aquilo ghost/pad counts."""
import sys
import time

from _game import tools

L = tools["run_lua"]
Q = ("local p for _,q in pairs(game.forces.player.platforms) do if q.name:find('Fulgora-Aquilo 4',1,true) then p=q end end local hi=p.hub.get_inventory(defines.inventory.hub_main) "
     "local ap=game.surfaces.aquilo.find_entities_filtered{type='cargo-landing-pad'}[1].get_inventory(defines.inventory.cargo_landing_pad_main) "
     "local dm=0 local ds=0 for _,e in pairs(p.surface.find_entities_filtered{force='player'}) do if e.health and e.max_health and e.health<e.max_health then dm=dm+1 end end for _,e in pairs(p.surface.find_entities_filtered{type='entity-ghost'}) do ds=ds+1 end "
     "rcon.print(game.tick..' '..(p.space_location and p.space_location.name or 'flight')..' st '..p.state..' paused '..tostring(p.paused)..' rockets '..hi.get_item_count('explosive-rocket')..' mags '..hi.get_item_count('uranium-rounds-magazine')"
     "..' | hub pipe '..hi.get_item_count('pipe')..' brick '..hi.get_item_count('stone-brick')..' holmium '..hi.get_item_count('holmium-plate')..' trash '..p.hub.get_inventory(defines.inventory.hub_trash).get_item_count()"
     "..' | aquilo pad pipe '..ap.get_item_count('pipe')..' brick '..ap.get_item_count('stone-brick')..' holmium '..ap.get_item_count('holmium-plate')..' | damaged '..dm..' ship ghosts '..ds)")
mins = float(sys.argv[1]) if len(sys.argv) > 1 else 10
secs = float(sys.argv[2]) if len(sys.argv) > 2 else 30
end = time.time() + mins * 60
while time.time() < end:
    try:
        print(L(Q).strip(), flush=True)
    except Exception as exc:  # noqa: BLE001
        print("err", repr(exc), flush=True)
    time.sleep(secs)
