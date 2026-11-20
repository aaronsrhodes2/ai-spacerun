-- The allowances at run time: which relaxed rules are on, and the two tools to read and change them. The list itself is
-- skippy_allowances.lua. A switch the mod keeps itself (kept_by = "mod") is checked by the code that would do the relaxed
-- thing, through M.on(id); the others are reported to the model, whose skill says to obey, and to the scripts that look.
local R = require("scripts.registry")
local ROWS = require("skippy_allowances")

local M = {}
M.rows = ROWS

local BY_ID = {}
for _, row in ipairs(ROWS) do BY_ID[row.id] = row end

local function setting(id)
  return "skippy-allow-" .. id
end

-- Is this allowance on? On when the setting is missing, so a game that never had the setting behaves as before.
function M.on(id)
  local set = settings and settings.global and settings.global[setting(id)]
  if set == nil then return true end
  return set.value ~= false
end

local KEPT = {
  mod = "the mod enforces this switch",
  skill = "the mod cannot stop it: you are told, so obey the switch",
  script = "an operator script does this: obey the switch, and leave the script alone while it is off",
}

local function row_view(row)
  return { id = row.id, on = M.on(row.id), what = row.what, vanilla = row.vanilla, kept_by = row.kept_by, means = KEPT[row.kept_by] }
end

R.register {
  name = "allowances",
  description = "The rules this game deliberately relaxes, each with its switch: what is relaxed, what vanilla would do instead, whether it is on, and who keeps the switch (the mod, or you). Look before you do anything one of them allows. When an allowance is off, behave as vanilla does for that rule.",
  params = {},
  run = function()
    local out, off = {}, 0
    for _, row in ipairs(ROWS) do
      local v = row_view(row)
      if not v.on then off = off + 1 end
      out[#out + 1] = v
    end
    return { allowances = out, off = off, note = (off == 0) and "every allowance is on" or (off .. " allowance(s) are off: follow vanilla for those") }
  end,
}

R.register {
  name = "set_allowance",
  description = "Turn one allowance on or off, only when the player says so ('stop spawning machines', 'allow long wires again'). Use the id from the allowances tool.",
  params = {
    id = { type = "string", required = true, description = "the allowance's id" },
    on = { type = "boolean", required = true, description = "true to allow the relaxation, false for the vanilla rule" },
  },
  run = function(a)
    local row = BY_ID[a.id]
    if not row then return { error = "there is no allowance named '" .. tostring(a.id) .. "'", hint = "call allowances for the list" } end
    local set = settings and settings.global and settings.global[setting(a.id)]
    if set == nil then return { error = "the setting for '" .. a.id .. "' does not exist in this game", hint = "the mod was added before allowances: restart the game with the mod to get it" } end
    local was = M.on(a.id)
    settings.global[setting(a.id)] = { value = a.on and true or false }
    local v = row_view(row)
    v.changed = was ~= v.on
    return v
  end,
}

return M
