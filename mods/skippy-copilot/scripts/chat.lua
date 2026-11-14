-- The conversation between player and model, held in the game's own chat, and the working light that shows what
-- the model is doing. The model reads what players typed with 'chat_read' and answers with 'say'.
local R = require("scripts.registry")

local KEEP = 200            -- chat lines remembered
local STATES = {
  idle = { text = "idle", color = { 0.6, 0.6, 0.6 } },
  thinking = { text = "thinking", color = { 0, 0.8, 1 } },
  working = { text = "working", color = { 0, 1, 0.53 } },
  blocked = { text = "needs you", color = { 1, 0.67, 0 } },
  failed = { text = "failed", color = { 1, 0.27, 0.27 } },
}
local C = {}

function C.init()
  storage.chat = storage.chat or {}
  storage.chat_next = storage.chat_next or 1
  storage.state = storage.state or { state = "idle", note = "" }
end

local function draw(player)
  local top = player.gui.top
  local frame = top.skippy_light
  if not frame then
    frame = top.add { type = "frame", name = "skippy_light", direction = "horizontal" }
    frame.add { type = "label", name = "state", caption = "" }
  end
  if not frame.skippy_mode then
    frame.add { type = "button", name = "skippy_mode", caption = "" }
  end
  local mode = storage.mode or "free-hand"
  frame.skippy_mode.caption = (mode == "my-character") and "moves your character" or "builds on its own"
  frame.skippy_mode.tooltip = "Click to switch: the assistant either builds on its own while you play, or moves your character and builds with its hands."
  if not frame.skippy_prompts then
    frame.add { type = "label", name = "skippy_prompts", caption = "" }
  end
  local prompts = storage.run and storage.run.prompts or 0
  frame.skippy_prompts.caption = prompts .. ((prompts == 1) and " prompt" or " prompts")
  frame.skippy_prompts.tooltip = "How many things you have asked the assistant in this game."
  local s = STATES[storage.state.state] or STATES.idle
  local note = storage.state.note or ""
  if C.connected() then
    frame.state.caption = "Skippy: " .. s.text .. ((note ~= "") and (" - " .. note) or "")
    frame.state.style.font_color = s.color
    frame.state.tooltip = ""
  else                                                    -- a newcomer's first question: is it even on?
    frame.state.caption = "Skippy: not connected"
    frame.state.style.font_color = { 0.6, 0.6, 0.6 }
    frame.state.tooltip = "The assistant is not connected. Outside the game, run:  python -m copilot --check  and it will say what is missing."
  end
end

-- Has anything outside the game called a tool lately? The bridge asks for chat every couple of seconds, so half a
-- minute of silence means nobody is there.
local QUIET_TICKS = 60 * 30

function C.heard()
  local was = C.connected()
  storage.last_call_tick = game.tick
  if not was then                                       -- the assistant has just connected: say so on the light at once
    storage.was_connected = true
    C.draw_all()
  end
end

function C.connected()
  return storage.last_call_tick ~= nil and game.tick - storage.last_call_tick <= QUIET_TICKS
end

-- Redraw when the connection comes or goes, checked a few times a second at most.
function C.on_tick(event)
  if event.tick % 120 ~= 0 then return end
  local now = C.connected()
  if now ~= storage.was_connected then
    storage.was_connected = now
    C.draw_all()
  end
end

R.register {
  name = "goal_state",
  description = "For the bridge: the standing goal, kept in the game so that everything talking to the game sees the same one. With 'set' it stores a goal ({kind, value}) or clears it ({kind = 'none'}); without, it returns the goal.",
  params = {
    set = { type = "table", description = "a goal {kind, value}, or {kind = 'none'} to clear" },
  },
  run = function(a)
    if a.set then
      if a.set.kind == "none" or a.set.kind == nil then storage.goal = nil else storage.goal = { kind = a.set.kind, value = a.set.value } end
    end
    return { goal = storage.goal or { kind = "none" } }
  end,
}

function C.draw_all()
  for _, p in pairs(game.players) do draw(p) end
end

function C.on_player(event)
  local p = game.get_player(event.player_index)
  if p then draw(p) end
end

function C.on_chat(event)
  if not event.message or event.message == "" then return end
  local p = event.player_index and game.get_player(event.player_index)
  local line = { id = storage.chat_next, tick = event.tick, player = p and p.name or "server", text = event.message }
  storage.chat_next = storage.chat_next + 1
  storage.chat[#storage.chat + 1] = line
  while #storage.chat > KEEP do table.remove(storage.chat, 1) end
end

R.register {
  name = "chat_read",
  description = "What players have typed in the game chat since a given line. Each line has an id; pass the last id you have seen as 'after' to get only newer lines.",
  params = {
    after = { type = "number", default = 0, description = "id of the last line already read; 0 for everything remembered" },
  },
  run = function(a)
    local out = {}
    for _, line in ipairs(storage.chat) do
      if line.id > a.after then out[#out + 1] = line end
    end
    return { lines = out, last_id = storage.chat_next - 1 }
  end,
}

R.register {
  name = "say",
  description = "Say something to the players in the game chat. Keep it short and plain: what you are about to do, what you did, or a question.",
  params = {
    text = { type = "string", required = true, description = "what to say" },
  },
  run = function(a)
    game.print("[color=0,1,0.53][Skippy][/color] " .. a.text)
    return { said = a.text }
  end,
}

R.register {
  name = "set_state",
  description = "Set the working light every player sees at the top of the screen. Set 'thinking' when you start on a request, 'working' while you change the game, 'blocked' when you need the player's answer, 'failed' when you could not do it, 'idle' when done.",
  params = {
    state = { type = "string", required = true, description = "idle, thinking, working, blocked or failed" },
    note = { type = "string", default = "", description = "a few words shown beside the light, such as what you are working on" },
  },
  run = function(a)
    if not STATES[a.state] then return { error = "state must be one of: idle, thinking, working, blocked, failed" } end
    storage.state = { state = a.state, note = a.note or "" }
    C.draw_all()
    return { state = a.state, note = a.note }
  end,
}

return C
