-- The mode of the mod, changeable at any time in the game (Settings > Mod settings > Map), by the button on the
-- working light, or by asking the assistant.
data:extend {
  {
    type = "string-setting",
    name = "skippy-copilot-mode",
    setting_type = "runtime-global",
    default_value = "free-hand",
    allowed_values = { "free-hand", "my-character" },
    order = "a",
  },
}
