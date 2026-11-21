-- The cron: one list of every job that runs on a timer to stand in for a mechanism the game lacks or a convenience we
-- allow (the Captain, 2026-11-20). Turning ghosts into requests every few minutes is the first such job. Each job says
-- what it is for, what a good run and a bad run look like, and when it last ran and how that went. The player and the
-- model can read it, pause a job, or remove one that the factory no longer needs ("logistics solve that now").
--   kind "tool"      the mod runs one of its own tools on schedule, with fixed arguments
--   kind "external"  a script outside the mod runs it (an operator script, the bridge); the mod only keeps its entry,
--                    takes its reports (cron_report) and says when one is overdue
-- A job that starts failing, or recovers, is told to the model as news (events_read). Nothing runs while the game is
-- paused, as nothing in the game does.
local R = require("scripts.registry")
local E = require("scripts.events")

local C = {}
local MAX_JOBS = 30
local CHECK_EVERY = 60                                     -- ticks between looks at the timetable
local TICKS_A_MINUTE = 3600
local NOT_ON_A_TIMER = { cron_list = true, cron_add = true, cron_change = true, cron_report = true,
                         say = true, hear = true, panel_type = true, panel_read = true, bridge_settings = true, game_info = true, voice_state = true, set_state = true, chat_read = true, events_read = true, goal_state = true,
                         set_mode = true, lock_mode = true, set_allowance = true, avatar_walk = true, avatar_mine = true,
                         avatar_stop = true, avatar_craft = true, avatar_carry = true, avatar_travel = true }

function C.init()
  storage.cron = storage.cron or {}                        -- name -> job
end

local function jobs() if not storage.cron then C.init() end return storage.cron end

local function copy(t)
  if type(t) ~= "table" then return t end
  local o = {}
  for k, v in pairs(t) do o[k] = copy(v) end
  return o
end

-- A short line from a tool's answer: its error, or its note, or the names of what it returned.
local function summary(res)
  if not res.ok then return "error: " .. tostring(res.error) end
  local r = res.result
  if type(r) ~= "table" then return tostring(r) end
  if r.note then return tostring(r.note) end
  local keys = {}
  for k in pairs(r) do keys[#keys + 1] = k end
  table.sort(keys)
  return "ok: " .. table.concat(keys, ", ")
end

local function record(job, ok, text)
  local was = job.last_ok
  job.last_run, job.last_ok, job.last_summary = game.tick, ok, string.sub(text or "", 1, 240)
  job.runs = (job.runs or 0) + 1
  if not ok then job.fails = (job.fails or 0) + 1 end
  if was ~= false and not ok then
    E.push { kind = "cron_failing", job = job.name, summary = job.last_summary, expect_bad = job.expect_bad }
  elseif was == false and ok then
    E.push { kind = "cron_recovered", job = job.name }
  end
end

local function run(job)
  local res = R.call(job.tool, copy(job.args or {}))
  record(job, res.ok == true, summary(res))
  job.next_tick = game.tick + job.every_minutes * TICKS_A_MINUTE
  return res
end

function C.on_tick(event)
  if event.tick % CHECK_EVERY ~= 0 then return end
  for _, job in pairs(jobs()) do
    if job.active and job.kind == "tool" and game.tick >= (job.next_tick or 0) then run(job) end
  end
end

local function view(job)
  local due = job.next_tick and math.max(0, job.next_tick - game.tick) or nil
  local overdue = nil
  if job.kind == "external" and job.active then
    local since = game.tick - (job.last_run or job.created)
    overdue = since > 2 * job.every_minutes * TICKS_A_MINUTE or nil
  end
  return { name = job.name, kind = job.kind, tool = job.tool, args = job.args, every_minutes = job.every_minutes, enabled = job.active,
           purpose = job.purpose, expect_ok = job.expect_ok, expect_bad = job.expect_bad, retire_when = job.retire_when,
           runs = job.runs or 0, fails = job.fails or 0, last_ok = job.last_ok, last_summary = job.last_summary,
           minutes_since_last = job.last_run and math.floor((game.tick - job.last_run) / TICKS_A_MINUTE) or nil,
           minutes_to_next = (job.kind == "tool" and job.active and due) and math.ceil(due / TICKS_A_MINUTE) or nil,
           overdue = overdue }
end

local function job_of(name)
  local job = jobs()[name]
  if not job then
    local names = {}
    for n in pairs(jobs()) do names[#names + 1] = n end
    table.sort(names)
    return nil, { error = "there is no timed job named '" .. tostring(name) .. "'", hint = (#names > 0) and ("jobs: " .. table.concat(names, ", ")) or "the cron is empty" }
  end
  return job
end

R.register {
  name = "cron_list",
  description = "Every job that runs on a timer (the in-game cron): what each is for, how often it runs, what a good and a bad run look like, when it last ran and how that went, and when it can be retired. Read it before adding a job, and when something a job does looks wrong.",
  params = {},
  run = function()
    local out = {}
    for _, job in pairs(jobs()) do out[#out + 1] = view(job) end
    table.sort(out, function(a, b) return a.name < b.name end)
    return { jobs = out, hint = (#out == 0) and "no timed jobs" or nil }
  end,
}

R.register {
  name = "cron_add",
  description = "Put a mod tool on a timer with fixed arguments (or with external true, list a script outside the mod). Say its purpose, good and bad runs and when it retires. Ask the player before timing anything that changes the world.",
  params = {
    name = { type = "string", required = true, description = "a short name" },
    every_minutes = { type = "number", required = true, description = "game minutes between runs, at least 1" },
    purpose = { type = "string", required = true, description = "what it does and why" },
    expect_ok = { type = "string", required = true, description = "what a good run looks like" },
    expect_bad = { type = "string", required = true, description = "what a bad run looks like and what to do" },
    retire_when = { type = "string", description = "when it is no longer needed" },
    tool = { type = "string", description = "the mod tool to run" },
    args = { type = "table", description = "the tool's arguments" },
    external = { type = "boolean", default = false, description = "a script outside the mod runs it" },
    replace = { type = "boolean", default = false, description = "replace a job of that name" },
  },
  run = function(a)
    local name = string.match(a.name, "^%s*(.-)%s*$")
    if name == "" then return { error = "a job needs a name" } end
    if jobs()[name] and not a.replace then return { error = "there is already a job named '" .. name .. "'", hint = "replace true to change it" } end
    local n = 0
    for _ in pairs(jobs()) do n = n + 1 end
    if not jobs()[name] and n >= MAX_JOBS then return { error = "the cron holds at most " .. MAX_JOBS .. " jobs", hint = "retire one first" } end
    local every = math.floor(a.every_minutes)
    if every < 1 then return { error = "every_minutes must be at least 1" } end
    local job = { name = name, every_minutes = every, purpose = a.purpose, expect_ok = a.expect_ok, expect_bad = a.expect_bad,
                  retire_when = a.retire_when, active = true, created = game.tick, runs = 0, fails = 0 }
    if a.external then
      if a.tool then return { error = "an external job names no tool: the script outside runs it" } end
      job.kind = "external"
    else
      if not a.tool then return { error = "say which tool to run, or external true" } end
      if not R.tools[a.tool] then return { error = "there is no tool named '" .. a.tool .. "'" } end
      if NOT_ON_A_TIMER[a.tool] then return { error = "'" .. a.tool .. "' does not run on a timer", hint = "timed jobs are for tools that look at or tidy the factory" } end
      local spec = R.tools[a.tool]
      for key in pairs(a.args or {}) do
        if not (spec.params and spec.params[key]) then return { error = "'" .. a.tool .. "' has no parameter '" .. tostring(key) .. "'" } end
      end
      job.kind, job.tool, job.args = "tool", a.tool, copy(a.args or {})
      job.next_tick = game.tick + every * TICKS_A_MINUTE
    end
    jobs()[name] = job
    return { job = view(job), note = (job.kind == "tool") and "runs first in " .. every .. " minutes; cron_change run_now runs it at once" or "waiting for the script's first report" }
  end,
}

R.register {
  name = "cron_change",
  description = "Change one timed job: pause it, resume it, run it now (and see its answer), or remove it for good when the factory no longer needs it.",
  params = {
    name = { type = "string", required = true, description = "the job" },
    action = { type = "string", required = true, description = "pause, resume, run_now or remove" },
  },
  run = function(a)
    local job, err = job_of(a.name)
    if not job then return err end
    if a.action == "remove" then
      jobs()[a.name] = nil
      return { removed = view(job) }
    elseif a.action == "pause" or a.action == "resume" then
      job.active = (a.action == "resume")
      if job.active and job.kind == "tool" then job.next_tick = game.tick + job.every_minutes * TICKS_A_MINUTE end
      return { job = view(job) }
    elseif a.action == "run_now" then
      if job.kind ~= "tool" then return { error = "'" .. a.name .. "' is run by a script outside the mod" } end
      local res = run(job)
      return { job = view(job), answer = res }
    end
    return { error = "action must be pause, resume, run_now or remove" }
  end,
}

R.register {
  name = "cron_report",
  description = "For scripts outside the mod: report one run of an external timed job, good or bad, with a short summary.",
  params = {
    name = { type = "string", required = true, description = "the job" },
    ok = { type = "boolean", required = true, description = "whether the run went well" },
    summary = { type = "string", required = true, description = "one line on what it did" },
  },
  run = function(a)
    local job, err = job_of(a.name)
    if not job then return err end
    if job.kind ~= "external" then return { error = "'" .. a.name .. "' is run by the mod itself" } end
    record(job, a.ok, a.summary)
    return { job = view(job) }
  end,
}

return C
