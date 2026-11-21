-- The mode of the mod, changeable at any time in the game (Settings > Mod settings > Map), by the button on the
-- working light, or by asking the assistant.
data:extend {
  {
    type = "string-setting",
    name = "skippy-copilot-mode",
    setting_type = "runtime-global",
    default_value = "free-hand",
    allowed_values = { "advise", "free-hand", "my-character" },
    order = "a",
  },
  -- The spider commander (the Captain, 2026-11-21): the player lives in remote view and places ghosts; the body rides a
  -- spidertron that the assistant drives, whose robots build. Off by default; can be switched on in a running game.
  {
    type = "bool-setting",
    name = "skippy-commander",
    setting_type = "runtime-global",
    default_value = false,
    order = "a2",
  },
  -- The AI the bridge talks to (the Captain, 2026-11-21: "a configurable ollama url:port, and connect automatically").
  -- The game cannot open connections itself; the bridge on the player's computer reads these and connects, and follows
  -- a change within a minute. Empty: the bridge's own setting (copilot/copilot.env).
  {
    type = "string-setting",
    name = "skippy-ai-url",
    setting_type = "runtime-global",
    default_value = "",
    allow_blank = true,
    order = "a3",
  },
  {
    type = "string-setting",
    name = "skippy-ai-model",
    setting_type = "runtime-global",
    default_value = "qwen3:8b",
    allow_blank = true,
    order = "a4",
  },
}

-- One switch for every allowance (skippy_allowances.lua), all on by default: the rules the mod deliberately relaxes.
for i, row in ipairs(require("skippy_allowances")) do
  data:extend {
    {
      type = "bool-setting",
      name = "skippy-allow-" .. row.id,
      setting_type = "runtime-global",
      default_value = true,
      order = string.format("b%02d", i),
    },
  }
end
