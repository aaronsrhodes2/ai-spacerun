-- The tool registry. Every tool the model can call is registered here with its parameters, so the list the model
-- sees and the checks its calls go through come from one place. A bad call is answered with what would have been
-- right (the tool names, or that tool's parameters), because a small model corrects itself from the answer.
local R = { tools = {}, order = {} }

-- spec = { name, description, params = { key = { type, required, default, description } }, run = function(args) }
-- run returns a table (the result) or { error = "...", hint = "..." }.
function R.register(spec)
  R.tools[spec.name] = spec
  R.order[#R.order + 1] = spec.name
end

local function describe(spec)
  local params = {}
  for key, p in pairs(spec.params or {}) do
    params[key] = { type = p.type, required = p.required or false, default = p.default, description = p.description }
  end
  return { name = spec.name, description = spec.description, parameters = params }
end

function R.describe_all()
  local out = {}
  for _, name in ipairs(R.order) do out[#out + 1] = describe(R.tools[name]) end
  return out
end

-- Tools that change the world. In advise mode the player builds and the assistant only looks and says what it would
-- do, so these refuse, except as a dry run.
local HANDS = { build = true, remove = true, set_recipe = true, reveal_map = true }

function R.call(name, args)
  local spec = R.tools[name]
  if not spec then
    return { ok = false, error = "there is no tool named '" .. tostring(name) .. "'", tools = R.order }
  end
  args = args or {}
  for key in pairs(args) do
    if not (spec.params and spec.params[key]) then
      return { ok = false, error = "'" .. spec.name .. "' has no parameter '" .. tostring(key) .. "'", tool = describe(spec) }
    end
  end
  for key, p in pairs(spec.params or {}) do
    local v = args[key]
    if v == nil then
      if p.required then
        return { ok = false, error = "'" .. spec.name .. "' needs the parameter '" .. key .. "'", tool = describe(spec) }
      end
      args[key] = p.default
    elseif type(v) ~= p.type then
      return { ok = false, error = "parameter '" .. key .. "' must be a " .. p.type .. ", got a " .. type(v), tool = describe(spec) }
    end
  end
  if storage.mode == "advise" and HANDS[name] and not args.dry_run then
    return { ok = false, error = "the mod is in advise mode: the player plays by hand and you only look and advise",
             hint = "tell the player exactly what to place and where (a dry run still works, to check it first). They can say 'go do it yourself' to let you build." }
  end
  local ok, res = pcall(spec.run, args)
  if not ok then
    return { ok = false, error = "the tool failed inside the mod: " .. tostring(res) }
  end
  if type(res) == "table" and res.error then
    res.ok = false
    return res
  end
  return { ok = true, result = res }
end

return R
