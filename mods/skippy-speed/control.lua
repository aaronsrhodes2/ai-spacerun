-- Skippy Speed: change game.speed from a button bar or hotkeys. Only admins (and single player) may change it.
local STEPS = { 0.25, 0.5, 1, 2, 3, 5, 10, 20 }

local function step_index(speed)
  local best, bestd = 3, math.huge
  for i, v in ipairs(STEPS) do
    local d = math.abs(v - speed)
    if d < bestd then best, bestd = i, d end
  end
  return best
end

local function label(speed)
  if speed == math.floor(speed) then return string.format("%dx", speed) end
  return string.format("%sx", tostring(speed))
end

local function refresh_all()
  for _, player in pairs(game.connected_players) do
    local frame = player.gui.top["skippy-speed-frame"]
    if frame and frame["skippy-speed-label"] then
      frame["skippy-speed-label"].caption = label(game.speed)
    end
  end
end

local function build_gui(player)
  if player.gui.top["skippy-speed-frame"] then player.gui.top["skippy-speed-frame"].destroy() end
  local frame = player.gui.top.add { type = "frame", name = "skippy-speed-frame", direction = "horizontal" }
  frame.style.padding = 2
  frame.add { type = "button", name = "skippy-speed-down", caption = "-", style = "mini_button", tooltip = "Slower (Shift+PageDown)" }
  frame.add { type = "label", name = "skippy-speed-label", caption = label(game.speed) }.style.minimal_width = 36
  frame.add { type = "button", name = "skippy-speed-up", caption = "+", style = "mini_button", tooltip = "Faster (Shift+PageUp)" }
  frame.add { type = "button", name = "skippy-speed-reset", caption = "1x", style = "mini_button", tooltip = "Normal speed (Shift+Home)" }
end

local function set_speed(player, speed)
  if not (player.admin or not game.is_multiplayer()) then
    player.print("Only admins can change the game speed.")
    return
  end
  game.speed = speed
  game.print(player.name .. " set game speed to " .. label(speed))
  refresh_all()
end

local function change(player, delta)
  local i = step_index(game.speed) + delta
  i = math.max(1, math.min(#STEPS, i))
  set_speed(player, STEPS[i])
end

local function handle(player, action)
  if action == "down" then change(player, -1)
  elseif action == "up" then change(player, 1)
  elseif action == "reset" then set_speed(player, 1) end
end

script.on_init(function() for _, p in pairs(game.players) do build_gui(p) end end)
script.on_configuration_changed(function() for _, p in pairs(game.players) do build_gui(p) end end)
script.on_event(defines.events.on_player_created, function(e) build_gui(game.get_player(e.player_index)) end)
script.on_event(defines.events.on_player_joined_game, function(e)
  local p = game.get_player(e.player_index)
  if not p.gui.top["skippy-speed-frame"] then build_gui(p) end
  refresh_all()
end)

script.on_event(defines.events.on_gui_click, function(e)
  local name = e.element and e.element.valid and e.element.name
  local action = name == "skippy-speed-down" and "down" or name == "skippy-speed-up" and "up" or name == "skippy-speed-reset" and "reset"
  if action then handle(game.get_player(e.player_index), action) end
end)

script.on_event("skippy-speed-down", function(e) handle(game.get_player(e.player_index), "down") end)
script.on_event("skippy-speed-up", function(e) handle(game.get_player(e.player_index), "up") end)
script.on_event("skippy-speed-reset", function(e) handle(game.get_player(e.player_index), "reset") end)
