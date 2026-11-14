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
require("scripts.build")
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
  chat.init()
  events.init()
  chat.draw_all()
end)

script.on_configuration_changed(function()
  chat.init()
  events.init()
  chat.draw_all()
end)

script.on_event(defines.events.on_player_created, chat.on_player)
script.on_event(defines.events.on_player_joined_game, chat.on_player)
script.on_event(defines.events.on_console_chat, chat.on_chat)
script.on_event(defines.events.on_research_finished, events.on_research)
