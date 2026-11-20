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
