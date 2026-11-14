"""One-off: watch Gleba-Aquilo 1 Shuttle at Aquilo: packs aboard, rockets, damage, until it leaves (or 25 minutes)."""
import time

from _game import tools

LUA = ("for _,q in pairs(game.forces.player.platforms) do if q.name:find('Gleba-Aquilo',1,true) then local h=q.hub.get_inventory(defines.inventory.hub_main) "
       "rcon.print(tostring(q.space_location and q.space_location.name)..' st'..q.state..' packs '..h.get_item_count('cryogenic-science-pack')..' rockets '..h.get_item_count('explosive-rocket')"
       "..' trash '..q.hub.get_inventory(defines.inventory.hub_trash).get_item_count()..' ghosts '..q.surface.count_entities_filtered{type='entity-ghost'}) end end "
       "local s=game.surfaces.aquilo local si=s.find_entities_filtered{name='rocket-silo'}[1] rcon.print(' silo '..tostring(si.status)..' parts '..si.rocket_parts)")
end = time.time() + 1500
left = False
while time.time() < end:
    out = tools["run_lua"](LUA).replace("\n", " ").strip()
    print(time.strftime("%H:%M:%S"), out, flush=True)
    if not out.startswith("aquilo"):
        left = True
        break
    time.sleep(15)
print("left aquilo" if left else "still at aquilo after 25 min", flush=True)
