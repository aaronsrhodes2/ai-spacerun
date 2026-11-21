-- The conversation panel: the window on the talk between the player and the assistant, up all the time (the Captain,
-- 2026-11-21: a hands-free game, keyboard now and voice later, the mouse never needed). It sits on the right, where
-- the remote view leaves room: under the minimap and the shortcut buttons, above the bottom bar; the map on the left
-- and the planners at the bottom stay clear. A typed line goes into the same list as console chat, so the bridge reads
-- it the same way; every reply, voice line and purple line is shown as it happens.
local R = require("scripts.registry")

local P = {}
local KEEP, SHOWN = 120, 40          -- lines remembered, lines drawn
local WIDTH = 420                    -- the panel's width at scale 1, in GUI units
local TOP, BOTTOM = 330, 130         -- room left for the minimap and shortcut buttons above, the quickbar below
local COLOURS = {
  player = { 1, 1, 1 }, panel = { 1, 1, 1 }, voice = { 0.85, 0.85, 1 }, skippy = { 0, 1, 0.53 },
  purple = { 0.51, 0.55, 0.97 }, game = { 1, 0.67, 0 },
}
local STATE_TEXT = { idle = "idle", thinking = "thinking", working = "working", blocked = "needs you", failed = "failed" }
local STATE_COLOUR = { idle = { 0.6, 0.6, 0.6 }, thinking = { 0, 0.8, 1 }, working = { 0, 1, 0.53 }, blocked = { 1, 0.67, 0 }, failed = { 1, 0.27, 0.27 } }

function P.init()
  storage.talk = storage.talk or {}
  storage.talk_next = storage.talk_next or 1
end

-- One line of the conversation, as the panel shows it. kind: player, panel, voice, skippy, purple, game.
function P.add(kind, who, text)
  P.init()
  local line = { id = storage.talk_next, tick = game.tick, kind = kind, who = who, text = text }
  storage.talk_next = storage.talk_next + 1
  storage.talk[#storage.talk + 1] = line
  while #storage.talk > KEEP do table.remove(storage.talk, 1) end
  P.draw_all()
  return line
end

local function place(player, frame)
  local scale = player.display_scale or 1
  local res = player.display_resolution or { width = 1920, height = 1080 }
  local height = math.max(200, math.floor(res.height / scale) - TOP - BOTTOM)
  frame.style.width = WIDTH
  frame.style.height = height
  frame.location = { x = math.max(0, res.width - math.floor((WIDTH + 12) * scale)), y = math.floor(TOP * scale) }
end

local function status(frame)
  local st = storage.state or { state = "idle", note = "" }
  local connected = storage.last_call_tick ~= nil and game.tick - storage.last_call_tick <= 60 * 30
  local label = frame.skippy_status
  if connected then
    label.caption = "Skippy is " .. (STATE_TEXT[st.state] or st.state) .. (((st.note or "") ~= "") and (": " .. st.note) or "")
    label.style.font_color = STATE_COLOUR[st.state] or STATE_COLOUR.idle
  else
    label.caption = "Skippy is connecting: the bridge on your computer joins by itself"
    label.tooltip = "The Skippy bridge starts with your computer and joins the game within a minute. If it does not, run  python -m copilot --check  outside the game: it says what is missing. Its AI is set in Mod settings > Map > AI address."
    label.style.font_color = STATE_COLOUR.idle
  end
end

local function draw(player)
  local screen = player.gui.screen
  local frame = screen.skippy_panel
  if not frame then
    frame = screen.add { type = "frame", name = "skippy_panel", direction = "vertical", caption = "Skippy" }
    frame.add { type = "scroll-pane", name = "skippy_log", direction = "vertical" }
    frame.add { type = "label", name = "skippy_status", caption = "" }
    local box = frame.add { type = "textfield", name = "skippy_input", text = "" }
    box.tooltip = "Talk to Skippy: build, find, fix, explain. Enter sends. The Talk to Skippy key puts the cursor here."
    place(player, frame)
  end
  frame.skippy_log.style.vertically_stretchable = true
  frame.skippy_log.style.horizontally_stretchable = true
  frame.skippy_input.style.horizontally_stretchable = true
  local log = frame.skippy_log
  log.clear()
  local list = storage.talk or {}
  if #list == 0 then
    local hint = log.add { type = "label", caption = "Talk to Skippy here. Ask it to build, find, fix or explain; it places ghosts, moves the spider and tells you what it did." }
    hint.style.single_line = false
    hint.style.font_color = { 0.6, 0.6, 0.6 }
  end
  for i = math.max(1, #list - SHOWN + 1), #list do
    local line = list[i]
    local tag = (line.kind == "voice") and (line.who .. " (said)") or line.who
    local l = log.add { type = "label", caption = "[" .. tag .. "] " .. line.text }
    l.style.single_line = false
    l.style.maximal_width = WIDTH - 40
    l.style.font_color = COLOURS[line.kind] or COLOURS.player
  end
  log.scroll_to_bottom()
  status(frame)
end

function P.draw_all()
  for _, p in pairs(game.players) do
    if p.connected ~= false then draw(p) end
  end
end

function P.on_player(event)
  local p = game.get_player(event.player_index)
  if p then draw(p) end
end

function P.on_display(event)                     -- the screen changed size or scale: put the panel back on the right
  local p = game.get_player(event.player_index)
  if p and p.gui.screen.skippy_panel then place(p, p.gui.screen.skippy_panel) end
end

-- The player's line, typed in the panel: into the chat list the bridge reads, counted as a prompt, shown at once.
local CHAT_KEEP = 200                            -- as chat.lua keeps

local function take(player, text)
  text = string.match(text or "", "^%s*(.-)%s*$")
  if text == "" then return nil end
  local line = { id = storage.chat_next, tick = game.tick, player = player and player.name or "player", text = text, by = "panel" }
  storage.chat_next = storage.chat_next + 1
  storage.chat[#storage.chat + 1] = line
  while #storage.chat > CHAT_KEEP do table.remove(storage.chat, 1) end
  if storage.run then storage.run.prompts = (storage.run.prompts or 0) + 1 end
  P.add("panel", line.player, text)
  return line
end

function P.on_confirmed(event)                   -- Enter in the panel's text box
  local el = event.element
  if not (el and el.valid and el.name == "skippy_input") then return end
  local p = game.get_player(event.player_index)
  local text = el.text
  el.text = ""
  take(p, text)
  el.focus()                                     -- the cursor stays for the next line
end

function P.on_key(event)                         -- the Talk to Skippy key: the cursor into the box
  local p = game.get_player(event.player_index)
  if not p then return end
  draw(p)
  p.gui.screen.skippy_panel.skippy_input.focus()
end

R.register {
  name = "panel_type",
  description = "For the bridge and tests: type a line into a player's Skippy panel and press Enter, exactly as the player would.",
  params = {
    text = { type = "string", required = true, description = "what the player types" },
    player = { type = "string", default = "", description = "whose panel; leave out for the first player in the game" },
  },
  run = function(a)
    local p = (a.player ~= "" and game.get_player(a.player)) or game.connected_players[1] or game.players[1]
    if not p then return { error = "nobody is in the game to type" } end
    draw(p)
    local box = p.gui.screen.skippy_panel.skippy_input
    box.text = a.text
    P.on_confirmed { element = box, player_index = p.index }
    local last = storage.chat[#storage.chat]
    if not last or last.by ~= "panel" or last.text ~= string.match(a.text, "^%s*(.-)%s*$") then return { error = "there was nothing typed" } end
    return { id = last.id, player = p.name }
  end,
}

R.register {
  name = "bridge_settings",
  description = "For the bridge: the AI address and model the player set in the game (Mod settings > Map). Empty address: the bridge's own.",
  params = {},
  run = function()
    local function get(name)
      local s = settings.global[name]
      return s and s.value or ""
    end
    return { ai_url = get("skippy-ai-url"), ai_model = get("skippy-ai-model") }
  end,
}

R.register {
  name = "panel_read",
  description = "For the bridge and tests: the conversation as the Skippy panel shows it, newer than a given line id.",
  params = {
    after = { type = "number", default = 0, description = "id of the last line already read" },
  },
  run = function(a)
    local out = {}
    for _, line in ipairs(storage.talk or {}) do
      if line.id > a.after then out[#out + 1] = line end
    end
    return { lines = out, last_id = (storage.talk_next or 1) - 1 }
  end,
}

return P
