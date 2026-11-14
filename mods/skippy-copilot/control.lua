-- Skippy Copilot: the tools an AI model uses to play Factorio, and the chat between player and model.
-- One console command carries every call:   /skippy <tool> <arguments as JSON>
--   /skippy tools                 the list of tools with their parameters (what the model is shown)
--   /skippy lookup {"name":"electronic-circuit"}
-- The answer is one line of JSON: {"ok":true,"result":...} or {"ok":false,"error":"...","hint":"..."}.
-- A bridge outside the game sends these over RCON; a player can type them too and reads the answer in the console.
local R = require("scripts.registry")
require("scripts.lookup")
require("scripts.grid")
require("scripts.diagnose")
require("scripts.alerts")
require("scripts.bottlenecks")
local avatar = require("scripts.avatar")
require("scripts.build")
require("scripts.travel")
require("scripts.progress")
local stats = require("scripts.science")
local research = require("scripts.research")
require("scripts.world")
require("scripts.view")
local chat = require("scripts.chat")
local events = require("scripts.events")

local function answer(event, tbl)
  local text = helpers.table_to_json(tbl)
  rcon.print(text)                                   -- reaches the caller only when the command came over RCON
  if event.player_index then
    local p = game.get_player(event.player_index)
    if p then p.print(text) end
  end
end

commands.add_command("skippy", "Skippy Copilot tool call: /skippy <tool> <arguments as JSON>. /skippy tools lists the tools.", function(event)
  if event.player_index then
    local p = game.get_player(event.player_index)
    if p and not p.admin then
      p.print("Only admins can call Skippy tools directly.")
      return
    end
  end
  if not event.player_index then chat.heard() end       -- a call from outside the game: the assistant is connected
  local text = event.parameter or ""
  local name, rest = string.match(text, "^%s*(%S+)%s*(.*)$")
  if not name or name == "tools" then
    answer(event, { ok = true, result = R.describe_all() })
    return
  end
  local args = {}
  if rest and rest ~= "" then
    args = helpers.json_to_table(rest)
    if type(args) ~= "table" then
      answer(event, { ok = false, error = "the arguments are not valid JSON", hint = 'write them like {"name":"iron-plate"}' })
      return
    end
  end
  answer(event, R.call(name, args))
end)

script.on_init(function()
  stats.init()
  chat.init()
  events.init()
  avatar.init()
  chat.draw_all()
end)

script.on_configuration_changed(function()
  stats.init()
  chat.init()
  events.init()
  avatar.init()
  chat.draw_all()
end)

script.on_event(defines.events.on_player_created, chat.on_player)
script.on_event(defines.events.on_player_joined_game, chat.on_player)
script.on_event(defines.events.on_console_chat, function(event)
  chat.on_chat(event)
  stats.on_chat(event)
  chat.draw_all()                                     -- the prompt count on the working light
end)
script.on_event(defines.events.on_research_finished, function(event)
  events.on_research(event)
  events.check_idle(research.idle())
end)
script.on_event(defines.events.on_research_started, function() storage.research_idle_told = nil end)
avatar.redraw = chat.draw_all                         -- the working light shows the mode
script.on_event(defines.events.on_runtime_mod_setting_changed, avatar.on_setting)
script.on_event(defines.events.on_gui_click, function(event)
  if event.element and event.element.valid and event.element.name == "skippy_mode" then
    local r = avatar.set_mode(avatar.other_mode())
    local p = game.get_player(event.player_index)
    if r.error and p then p.print(r.error) end
    chat.draw_all()
  end
end)
script.on_event(defines.events.on_tick, function(event)
  avatar.on_tick(event)
  stats.on_tick(event)
  chat.on_tick(event)
  if event.tick % 600 == 0 then events.check_idle(research.idle()) end        -- research with nothing chosen, noticed within ten seconds
end)
script.on_event(defines.events.on_script_path_request_finished, avatar.on_path)
