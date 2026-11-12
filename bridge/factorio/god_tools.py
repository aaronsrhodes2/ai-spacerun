"""
God-mode tools: Claude acts directly on the live map over RCON, with no character.

The rule these enforce (see .claude/skills/factorio/SKILL.md):
  - Placing an entity is free, but only once its recipe is researched.
  - Anything a machine consumes has to be produced by the factory, so nothing
    here creates items or changes research state beyond queueing it.

Every tool returns JSON. Lua errors come back as {"error": ...}, never as an
empty string that could be mistaken for success.
"""

import json
import re
from typing import Callable

_MAX_COMMAND = 60000  # RCON's limit is 65535; leave room for the wrapper and Lua.

_STATUS_NAMES = """
local status_names = {}
for k, v in pairs(defines.entity_status) do status_names[v] = k end
"""

_UNLOCK = """
local cache = {}
local function unlocked(force, ename)
  if cache[ename] then return cache[ename][1], cache[ename][2] end
  local function done(ok, why) cache[ename] = {ok, why} return ok, why end
  local ep = prototypes.entity[ename]
  if not ep then return done(false, 'unknown entity') end
  local items = ep.items_to_place_this
  if not items or #items == 0 then return done(false, 'no item places this') end
  for _, it in pairs(items) do
    local rs = prototypes.get_recipe_filtered{{filter='has-product-item', elem_filters={{filter='name', name=it.name}}}}
    for rname, _ in pairs(rs) do
      local r = force.recipes[rname]
      if r and r.enabled and not string.find(rname, '-recycling', 1, true) then return done(true, rname) end
    end
  end
  return done(false, 'not researched: ' .. items[1].name)
end
"""


def _compact(lua: str) -> str:
    """One line: RCON commands stay single-line. Lua here never uses -- comments."""
    return " ".join(line.strip() for line in lua.splitlines() if line.strip())


def _lua_json(value) -> str:
    return "helpers.json_to_table([==[" + json.dumps(value, separators=(",", ":")) + "]==])"


def register(mcp, q: Callable[[str], str]) -> None:
    """Add the god-mode tools to the FastMCP server. `q` runs Lua and returns its output."""

    def run(body: str) -> str:
        lua = _compact(
            "local ok, err = pcall(function() " + body + " end) "
            "if not ok then rcon.print(helpers.table_to_json({error=tostring(err)})) end"
        )
        if len(lua) > _MAX_COMMAND:
            return json.dumps({"error": f"command too long ({len(lua)} chars): send fewer entities per call"})
        return q(lua)

    @mcp.tool()
    def game_overview(surface: str = "nauvis") -> str:
        """Start here. Tick, players, research progress, the base's entity counts and
        bounding box, and the total of each resource in generated chunks."""
        return run(f"""
            local out = {{}}
            local f = game.forces.player
            local s = game.surfaces[{json.dumps(surface)}]
            if not s then rcon.print(helpers.table_to_json({{error='no such surface'}})) return end
            out.tick = game.tick
            out.players = {{}}
            for _, p in pairs(game.players) do
              local sel = p.connected and p.selected
              out.players[#out.players+1] = {{
                name=p.name, online=p.connected, surface=p.surface.name,
                x=math.floor(p.position.x), y=math.floor(p.position.y),
                hovering = sel and {{name=sel.name, x=sel.position.x, y=sel.position.y}} or false,
              }}
            end
            local done, total = 0, 0
            for _, t in pairs(f.technologies) do
              total = total + 1
              if t.researched then done = done + 1 end
            end
            out.research = {{researched=done, total=total, current=f.current_research and f.current_research.name or false}}
            local counts, minx, miny, maxx, maxy = {{}}, nil, nil, nil, nil
            for _, e in pairs(s.find_entities_filtered{{force=f}}) do
              if e.type ~= 'character' then
                counts[e.name] = (counts[e.name] or 0) + 1
                local x, y = e.position.x, e.position.y
                minx = math.min(minx or x, x) maxx = math.max(maxx or x, x)
                miny = math.min(miny or y, y) maxy = math.max(maxy or y, y)
              end
            end
            out.entities = counts
            out.base_bbox = minx and {{minx, miny, maxx, maxy}} or false
            local res = {{}}
            for _, e in pairs(s.find_entities_filtered{{type='resource'}}) do
              res[e.name] = (res[e.name] or 0) + e.amount
            end
            out.resources_generated = res
            rcon.print(helpers.table_to_json(out))
        """)

    @mcp.tool()
    def find_resource_patches(resource: str, surface: str = "nauvis", limit: int = 8) -> str:
        """Patches of `resource` in generated chunks, nearest to the base first. Each has
        center, bbox, tiles, amount, distance from the base's bounding box, and whether
        it's already mined (a drill of ours inside its bbox). Use this to pick an
        unused patch next to the used area."""
        return run(f"""
            local name, limit = {json.dumps(resource)}, {int(limit)}
            local s = game.surfaces[{json.dumps(surface)}]
            local f = game.forces.player
            local cells = {{}}
            for _, e in pairs(s.find_entities_filtered{{name=name}}) do
              local cx, cy = math.floor(e.position.x/16), math.floor(e.position.y/16)
              local k = cx .. ',' .. cy
              local c = cells[k]
              if not c then c = {{cx=cx, cy=cy, tiles={{}}}} cells[k] = c end
              c.tiles[#c.tiles+1] = e
            end
            local minx, miny, maxx, maxy
            for _, e in pairs(s.find_entities_filtered{{force=f}}) do
              if e.type ~= 'character' and e.name ~= 'crash-site-spaceship' then
                local x, y = e.position.x, e.position.y
                minx = math.min(minx or x, x) maxx = math.max(maxx or x, x)
                miny = math.min(miny or y, y) maxy = math.max(maxy or y, y)
              end
            end
            if not minx then minx, miny, maxx, maxy = 0, 0, 0, 0 end
            local patches, seen = {{}}, {{}}
            for k, c in pairs(cells) do
              if not seen[k] then
                seen[k] = true
                local stack, p = {{c}}, {{tiles=0, amount=0}}
                while #stack > 0 do
                  local cur = table.remove(stack)
                  for _, e in pairs(cur.tiles) do
                    local x, y = e.position.x, e.position.y
                    p.tiles = p.tiles + 1 p.amount = p.amount + e.amount
                    p.x1 = math.min(p.x1 or x, x) p.x2 = math.max(p.x2 or x, x)
                    p.y1 = math.min(p.y1 or y, y) p.y2 = math.max(p.y2 or y, y)
                  end
                  for dx = -1, 1 do for dy = -1, 1 do
                    local nk = (cur.cx+dx) .. ',' .. (cur.cy+dy)
                    if cells[nk] and not seen[nk] then seen[nk] = true stack[#stack+1] = cells[nk] end
                  end end
                end
                local gx = math.max(minx - p.x2, p.x1 - maxx, 0)
                local gy = math.max(miny - p.y2, p.y1 - maxy, 0)
                p.distance_from_base = math.floor(math.sqrt(gx*gx + gy*gy))
                p.center = {{x=math.floor((p.x1+p.x2)/2), y=math.floor((p.y1+p.y2)/2)}}
                p.in_use = s.count_entities_filtered{{force=f, type='mining-drill', area={{{{p.x1, p.y1}}, {{p.x2, p.y2}}}}}} > 0
                patches[#patches+1] = p
              end
            end
            table.sort(patches, function(a, b) return a.distance_from_base < b.distance_from_base end)
            local out = {{}}
            for i = 1, math.min(limit, #patches) do out[i] = patches[i] end
            rcon.print(helpers.table_to_json({{resource=name, patches_found=#patches, patches=out}}))
        """)

    @mcp.tool()
    def map_grid(x1: int, y1: int, x2: int, y2: int, surface: str = "nauvis") -> str:
        """One character per tile for a box, top row first, so layouts can be planned from
        real terrain. '.' free, '~' water, 'K' cliff, 'T' tree, 'R' rock, 'E' building,
        '?' not generated, and resources: i iron, c copper, k coal, s stone, u uranium,
        o oil. Trees and rocks can be cleared; ore can be built on. Max 400x400."""
        if x2 - x1 > 400 or y2 - y1 > 400 or x2 <= x1 or y2 <= y1:
            return json.dumps({"error": "box must be non-empty and at most 400x400"})
        return run(f"""
            local s = game.surfaces[{json.dumps(surface)}]
            local x1, y1, x2, y2 = {int(x1)}, {int(y1)}, {int(x2)}, {int(y2)}
            local area = {{{{x1, y1}}, {{x2, y2}}}}
            local rows = {{}}
            for y = y1, y2 - 1 do
              local r = {{}}
              for x = x1, x2 - 1 do
                r[x] = s.is_chunk_generated({{math.floor(x/32), math.floor(y/32)}}) and '.' or '?'
              end
              rows[y] = r
            end
            local function put(x, y, ch)
              if rows[y] and rows[y][x] then rows[y][x] = ch end
            end
            local ores = {{['iron-ore']='i', ['copper-ore']='c', ['coal']='k', ['stone']='s', ['uranium-ore']='u', ['crude-oil']='o'}}
            for _, e in pairs(s.find_entities_filtered{{area=area, type='resource'}}) do
              put(math.floor(e.position.x), math.floor(e.position.y), ores[e.name] or 'E')
            end
            for _, t in pairs(s.find_tiles_filtered{{area=area, collision_mask='water_tile'}}) do
              put(t.position.x, t.position.y, '~')
            end
            local skip = {{character=true, ['item-entity']=true, corpse=true, resource=true, fish=true, ['character-corpse']=true}}
            for _, e in pairs(s.find_entities_filtered{{area=area}}) do
              if not skip[e.type] then
                local ch = 'E'
                if e.type == 'tree' then ch = 'T'
                elseif e.type == 'simple-entity' then ch = 'R'
                elseif e.type == 'cliff' then ch = 'K' end
                local b = e.bounding_box
                for y = math.floor(b.left_top.y), math.ceil(b.right_bottom.y) - 1 do
                  for x = math.floor(b.left_top.x), math.ceil(b.right_bottom.x) - 1 do
                    put(x, y, ch)
                  end
                end
              end
            end
            local out = {{}}
            for y = y1, y2 - 1 do out[#out+1] = table.concat(rows[y], '', x1, x2 - 1) end
            rcon.print(helpers.table_to_json({{x1=x1, y1=y1, rows=out}}))
        """)

    @mcp.tool()
    def factory_problems(surface: str = "nauvis", samples: int = 5) -> str:
        """Where the factory is blocked. Machine counts by type and status, with sample
        positions of every machine that isn't working, plus items made and used per
        minute. A machine short of inputs points upstream; one with full output points
        downstream. Sort out low_power and no_power first. Also returns the game's own
        alert list for the surface (what the player sees in the alert overview), the number
        of damaged entities and of ghosts: read these first, every time."""
        return run(_STATUS_NAMES + f"""
            local s = game.surfaces[{json.dumps(surface)}]
            local f = game.forces.player
            local n = {int(samples)}
            local by, problems = {{}}, {{}}
            local kinds = {{'assembling-machine', 'furnace', 'mining-drill', 'lab', 'boiler', 'generator',
                           'rocket-silo', 'agricultural-tower', 'beacon', 'pump', 'offshore-pump', 'reactor'}}
            for _, e in pairs(s.find_entities_filtered{{force=f, type=kinds}}) do
              local st = status_names[e.status] or 'unknown'
              by[e.name] = by[e.name] or {{}}
              by[e.name][st] = (by[e.name][st] or 0) + 1
              if st ~= 'working' and st ~= 'normal' then
                local key = e.name .. ':' .. st
                problems[key] = problems[key] or {{count=0, at={{}}}}
                local pr = problems[key]
                pr.count = pr.count + 1
                if #pr.at < n then
                  local recipe = e.type == 'assembling-machine' or e.type == 'furnace'
                  pr.at[#pr.at+1] = {{x=e.position.x, y=e.position.y, recipe = recipe and e.get_recipe() and e.get_recipe().name or nil}}
                end
              end
            end
            local stats = f.get_item_production_statistics(s)
            local function rates(counts, category)
              local list = {{}}
              for item, _ in pairs(counts) do
                local rate = stats.get_flow_count{{name=item, category=category,
                  precision_index=defines.flow_precision_index.one_minute}}
                if rate > 0.01 then list[#list+1] = {{item=item, per_minute=math.floor(rate*10)/10}} end
              end
              table.sort(list, function(a, b) return a.per_minute > b.per_minute end)
              return list
            end
            local alert_names = {{}}
            for k, v in pairs(defines.alert_type) do alert_names[v] = k end
            local alerts = {{}}
            local pl = game.connected_players[1] or game.players[1]
            if pl then
              for _, by_type in pairs(pl.get_alerts{{surface=s}}) do
                for at, list in pairs(by_type) do
                  local a = {{type=alert_names[at] or tostring(at), count=#list, at={{}}, what={{}}}}
                  for i, al in pairs(list) do
                    local nm = (al.target and al.target.valid and al.target.name) or (al.prototype and al.prototype.name) or '?'
                    a.what[nm] = (a.what[nm] or 0) + 1
                    if i <= n and al.position then a.at[#a.at+1] = {{x=al.position.x, y=al.position.y}} end
                  end
                  alerts[#alerts+1] = a
                end
              end
            end
            local damaged = 0
            for _, e in pairs(s.find_entities_filtered{{force=f}}) do
              if e.health and e.max_health and e.health < e.max_health then damaged = damaged + 1 end
            end
            rcon.print(helpers.table_to_json({{
              alerts=alerts, damaged_entities=damaged, ghosts=s.count_entities_filtered{{type='entity-ghost', force=f}},
              machines=by, problems=problems,
              made_per_minute=rates(stats.input_counts, 'input'),
              used_per_minute=rates(stats.output_counts, 'output'),
            }}))
        """)

    @mcp.tool()
    def place_entities(entities: str, surface: str = "nauvis", dry_run: bool = False, clear_trees: bool = True) -> str:
        """Place entities for free, refusing anything whose recipe isn't researched.
        `entities` is a JSON list of {"name","x","y"} with optional "direction" (0=N, 4=E,
        8=S, 12=W), "recipe", and "params" (extra create_entity arguments such as
        {"type":"input"} for an underground belt). Reports placed and failed with a reason
        for each. Trees and rocks in the way are removed unless clear_trees is false.
        dry_run checks everything and changes nothing. Keep calls to ~500 entities."""
        try:
            parsed = json.loads(entities)
        except ValueError as e:
            return json.dumps({"error": f"entities is not valid JSON: {e}"})
        if not isinstance(parsed, list) or not parsed:
            return json.dumps({"error": "entities must be a non-empty JSON list"})
        # No `--` comments in the Lua below: it is sent as one line. Why `twin` exists: can_place_entity (manual)
        # says yes over anything it could fast-replace, and create_entity then stacks a second entity on the first.
        return run(_UNLOCK + f"""
            local list = {_lua_json(parsed)}
            local s = game.surfaces[{json.dumps(surface)}]
            if not s then rcon.print(helpers.table_to_json({{error='no such surface'}})) return end
            local f = game.forces.player
            local dry, clear = {str(dry_run).lower()}, {str(clear_trees).lower()}
            local placed, failed = 0, {{}}
            local function fail(i, spec, why) failed[#failed+1] = {{i=i, name=spec.name, x=spec.x, y=spec.y, why=why}} end
            for i, spec in ipairs(list) do
              local ok, why = unlocked(f, spec.name)
              local pos = {{x=spec.x, y=spec.y}}
              if not ok then fail(i, spec, why)
              elseif not s.is_chunk_generated({{math.floor(spec.x/32), math.floor(spec.y/32)}}) then fail(i, spec, 'chunk not generated')
              else
                local ep = prototypes.entity[spec.name]
                if clear and not dry then
                  local b = ep.collision_box
                  local r = math.max(math.abs(b.left_top.x), math.abs(b.left_top.y), b.right_bottom.x, b.right_bottom.y)
                  if string.find(ep.type, 'rail', 1, true) then r = math.max(r, 4) end
                  for _, t in pairs(s.find_entities_filtered{{area={{{{spec.x-r, spec.y-r}}, {{spec.x+r, spec.y+r}}}}, type={{'tree', 'simple-entity'}}}}) do t.destroy() end
                end
                local check = {{name=spec.name, position=pos, direction=spec.direction or 0, force=f,
                               build_check_type=defines.build_check_type.manual}}
                local can
                local b = ep.collision_box
                local hx, hy = b.right_bottom.x, b.right_bottom.y
                local dir = spec.direction or 0
                if dir == 4 or dir == 12 then hx, hy = hy, hx end
                local here = s.find_entities_filtered{{area={{{{spec.x-hx, spec.y-hy}}, {{spec.x+hx, spec.y+hy}}}}}}
                local twin
                local grp = ep.fast_replaceable_group
                for _, o in pairs(here) do
                  if o.type ~= 'entity-ghost' and (o.name == spec.name or (grp and o.prototype.fast_replaceable_group == grp)) then twin = o.name end
                end
                if dry and clear then
                  can = true
                  for _, o in pairs(here) do
                    if o.type ~= 'tree' and o.type ~= 'simple-entity' and o.type ~= 'resource'
                       and o.type ~= 'character' and o.type ~= 'item-entity'
                       and o.type ~= 'logistic-robot' and o.type ~= 'construction-robot' then can = false end
                  end
                else
                  can = s.can_place_entity(check)
                end
                if twin then fail(i, spec, 'already occupied by ' .. twin)
                elseif not can then fail(i, spec, 'blocked at this position')
                elseif dry then placed = placed + 1
                else
                  local args = {{name=spec.name, position=pos, direction=spec.direction or 0, force=f, raise_built=true, move_stuck_players=true}}
                  if spec.params then for k, v in pairs(spec.params) do args[k] = v end end
                  local e = s.create_entity(args)
                  if not e then fail(i, spec, 'create_entity returned nothing')
                  else
                    placed = placed + 1
                    if spec.recipe then
                      local rs, err = pcall(function() e.set_recipe(spec.recipe) end)
                      if not rs then fail(i, spec, 'placed, but recipe failed: ' .. tostring(err)) end
                    end
                  end
                end
              end
            end
            rcon.print(helpers.table_to_json({{dry_run=dry, placed=placed, failed=failed}}))
        """)

    @mcp.tool()
    def remove_entities(x1: float, y1: float, x2: float, y2: float, names: str = "",
                        surface: str = "nauvis", dry_run: bool = False) -> str:
        """Remove our force's entities in a box, except characters. `names` is an optional
        comma-separated filter. Contents are lost, so empty valuable chests first.
        Use dry_run to see what would go. Anything whose collision box overlaps the
        box counts, so for one tile use its centre +-0.2, not the tile's edges."""
        name_list = [n.strip() for n in names.split(",") if n.strip()]
        return run(f"""
            local s = game.surfaces[{json.dumps(surface)}]
            local f = game.forces.player
            local filter = {{force=f, area={{{{{float(x1)}, {float(y1)}}}, {{{float(x2)}, {float(y2)}}}}}}}
            local names = {_lua_json(name_list)}
            if #names > 0 then filter.name = names end
            local removed = {{}}
            for _, e in pairs(s.find_entities_filtered(filter)) do
              if e.type ~= 'character' then
                removed[e.name] = (removed[e.name] or 0) + 1
                if not {str(dry_run).lower()} then e.destroy{{raise_destroy=true}} end
              end
            end
            rcon.print(helpers.table_to_json({{dry_run={str(dry_run).lower()}, removed=removed}}))
        """)

    @mcp.tool()
    def seed_starter_fuel(x1: float, y1: float, x2: float, y2: float, drill_coal: int = 5,
                          surface: str = "nauvis") -> str:
        """Free starter coal, approved by the Captain so a self-fuelling loop can start.
        Only burner machines of ours in the box with an empty fuel slot get any: drills
        get `drill_coal` (max 10), everything else 1. Don't use it to keep something
        running; if a machine runs out later, fix its fuel supply."""
        return run(f"""
            local s = game.surfaces[{json.dumps(surface)}]
            local n = math.min({int(drill_coal)}, 10)
            local seeded, skipped = 0, 0
            for _, e in pairs(s.find_entities_filtered{{force=game.forces.player,
                area={{{{{float(x1)}, {float(y1)}}}, {{{float(x2)}, {float(y2)}}}}}}}) do
              local fuel = e.burner and e.get_fuel_inventory()
              if fuel then
                if fuel.is_empty() then
                  fuel.insert{{name='coal', count = e.type == 'mining-drill' and n or 1}}
                  seeded = seeded + 1
                else
                  skipped = skipped + 1
                end
              end
            end
            rcon.print(helpers.table_to_json({{seeded=seeded, already_fuelled=skipped}}))
        """)

    @mcp.tool()
    def restock_turrets(chest_x: float, chest_y: float, per_turret: int = 10, surface: str = "nauvis") -> str:
        """Move factory-made ammo from the chest at (chest_x, chest_y) into every gun
        turret of ours holding fewer than `per_turret` magazines. Nothing is created:
        turrets only get what the chest holds. Call it again when the chest refills."""
        return run(f"""
            local s = game.surfaces[{json.dumps(surface)}]
            local chest = s.find_entity('iron-chest', {{{float(chest_x)}, {float(chest_y)}}}) or s.find_entity('wooden-chest', {{{float(chest_x)}, {float(chest_y)}}})
            if not chest then rcon.print(helpers.table_to_json({{error='no chest there'}})) return end
            local inv = chest.get_inventory(defines.inventory.chest)
            local have = inv.get_item_count('firearm-magazine')
            local moved, short = 0, 0
            for _, t in pairs(s.find_entities_filtered{{force=game.forces.player, type='ammo-turret'}}) do
              local ammo = t.get_inventory(defines.inventory.turret_ammo)
              local need = {int(per_turret)} - ammo.get_item_count('firearm-magazine')
              if need > 0 then
                local give = math.min(need, have)
                if give > 0 then
                  local ok = ammo.insert{{name='firearm-magazine', count=give}}
                  if ok > 0 then inv.remove{{name='firearm-magazine', count=ok}} have = have - ok moved = moved + ok end
                end
                if give < need then short = short + 1 end
              end
            end
            rcon.print(helpers.table_to_json({{moved=moved, left_in_chest=have, turrets_still_short=short}}))
        """)

    @mcp.tool()
    def research_status() -> str:
        """Current research and queue, plus every tech researchable now with its science
        packs or, for techs unlocked by doing something, its trigger."""
        return run("""
            local f = game.forces.player
            local out = {current=f.current_research and f.current_research.name or false,
                         progress=f.research_progress, queue={}, available={}}
            for i, t in pairs(f.research_queue or {}) do out.queue[i] = t.name end
            for name, t in pairs(f.technologies) do
              if t.enabled and not t.researched then
                local ready = true
                for _, pre in pairs(t.prerequisites) do if not pre.researched then ready = false end end
                if ready then
                  local packs = {}
                  for _, ing in pairs(t.research_unit_ingredients) do packs[#packs+1] = ing.name end
                  out.available[#out.available+1] = {name=name, packs=packs, units=t.research_unit_count,
                    trigger=t.prototype.research_trigger or false}
                end
              end
            end
            rcon.print(helpers.table_to_json(out))
        """)

    @mcp.tool()
    def queue_research(techs: str) -> str:
        """Add comma-separated techs to the research queue. This only queues: labs still
        need real science packs. Techs unlocked by a trigger can't be queued."""
        names = [n.strip() for n in techs.split(",") if n.strip()]
        return run(f"""
            local f = game.forces.player
            local results = {{}}
            for _, name in ipairs({_lua_json(names)}) do
              local t = f.technologies[name]
              if not t then results[name] = 'no such tech'
              elseif t.researched then results[name] = 'already researched'
              elseif t.prototype.research_trigger then results[name] = 'unlocked by a trigger, not labs'
              else results[name] = f.add_research(t) and 'queued' or 'refused' end
            end
            rcon.print(helpers.table_to_json(results))
        """)

    @mcp.tool()
    def tell_player(message: str, x: float | None = None, y: float | None = None, surface: str = "nauvis") -> str:
        """Post in game chat. With x and y it also adds a map tag there, so the player
        can find the spot."""
        tag = ""
        if x is not None and y is not None:
            tag = (f"f.add_chart_tag(game.surfaces[{json.dumps(surface)}], "
                   f"{{position={{x={float(x)}, y={float(y)}}}, text={_lua_json([message])}[1]}})")
        return run(f"""
            local f = game.forces.player
            game.print('[Claude] ' .. {_lua_json([message])}[1])
            {tag}
            rcon.print(helpers.table_to_json({{sent=true}}))
        """)

    @mcp.tool()
    def screenshot(x: float, y: float, zoom: float = 0.5, width: int = 1600, height: int = 1000,
                   name: str = "view", player: str = "aaronsrhodes", surface: str = "nauvis") -> str:
        """Take a picture of any part of the map with the player's game client, which
        must be online. Then Read the returned local path to see it. Lower zoom shows
        more: 1 is close up, 0.25 a whole outpost, 0.1 a whole base. The player's own
        view isn't moved. Saved under the client's script-output folder."""
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,60}", name):
            return json.dumps({"error": "name must be letters, digits, - or _"})
        rel = f"claude/{name}.png"
        local = f"C:/Users/aaron/AppData/Roaming/Factorio/script-output/{rel}"
        return run(f"""
            local p = game.players[{json.dumps(player)}]
            if not p or not p.connected then
              rcon.print(helpers.table_to_json({{error='that player is not online, so no client can render'}}))
              return
            end
            game.take_screenshot{{by_player=p, surface={json.dumps(surface)}, position={{{float(x)}, {float(y)}}},
              resolution={{{min(int(width), 4000)}, {min(int(height), 4000)}}}, zoom={float(zoom)},
              path={json.dumps(rel)}, show_entity_info=true, daytime=0, anti_alias=true}}
            rcon.print(helpers.table_to_json({{requested={json.dumps(local)}, note='appears within a few seconds'}}))
        """)

    @mcp.tool()
    def save_game(name: str) -> str:
        """Save the live game under `name`, which also makes a restore point before risky
        work. Letters, digits, - and _ only. Don't use the running save's name unless you
        mean to overwrite it."""
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,60}", name):
            return json.dumps({"error": "name must be letters, digits, - or _"})
        return run(f"""
            game.server_save({json.dumps(name)})
            rcon.print(helpers.table_to_json({{saved={json.dumps(name)}}}))
        """)
