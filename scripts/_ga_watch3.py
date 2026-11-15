"""One-off: watch Gleba-Aquilo 1 Shuttle through the whole trip: location, packs aboard, rockets, silo, pods; until it is back at Gleba with the packs (or 70 minutes)."""
import time

from _game import tools

LUA = ("for _,q in pairs(game.forces.player.platforms) do if q.name:find('Gleba-Aquilo',1,true) then local h=q.hub.get_inventory(defines.inventory.hub_main) "
       "rcon.print(tostring(q.space_location and q.space_location.name)..' st'..q.state..' packs '..h.get_item_count('cryogenic-science-pack')..' rockets '..h.get_item_count('explosive-rocket')"
       "..' trash '..q.hub.get_inventory(defines.inventory.hub_trash).get_item_count()) end end "
       "local s=game.surfaces.aquilo local si=s.find_entities_filtered{name='rocket-silo'}[1] local n=s.find_entities_filtered{name='roboport'}[1].logistic_network rcon.print(' silo '..tostring(si.status)..' cryo in network '..n.get_item_count('cryogenic-science-pack'))")
end = time.time() + 4200
seen_aquilo = False
while time.time() < end:
    out = tools["run_lua"](LUA).replace("\n", " ").strip()
    print(time.strftime("%H:%M:%S"), out, flush=True)
    if out.startswith("aquilo"):
        seen_aquilo = True
    if seen_aquilo and out.startswith("gleba") and " packs 0" not in out:
        print("back at gleba with packs", flush=True)
        break
    time.sleep(20)
