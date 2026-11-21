-- Quality that builds (the Captain, 2026-11-21): quality is optional in Space Age since 2.1.7, so this mod changes it
-- from churn into a choice. One quality module in a machine makes its output the highest quality researched, at a cost
-- in time: tier 1 triples the time a craft takes, tier 2 doubles it, tier 3 adds half. A better quality of module slows
-- the machine less. More than one quality module in a machine adds only slowness; skippy-copilot takes the extras out.
--
-- How 2.1 rolls quality (doc-html LuaQualityPrototype): the first step up happens with the module's quality effect times
-- the quality's next_probability; each further step happens with chain_probability (vanilla 0.1). The game never gives
-- a quality the force has not unlocked. Effects are in 2.1 units (0.01 is 1%).
local SPEED = { [1] = -0.667, [2] = -0.5, [3] = -0.333 }      -- 3x, 2x and 1.5x the time of one craft

for _, m in pairs(data.raw.module) do
  if m.category == "quality" then
    m.effect = m.effect or {}
    m.effect.quality = 1.0                                       -- the first step up, every time
    m.effect.speed = SPEED[m.tier or 1] or SPEED[1]
    m.speed_quality_multiplier = -0.4                            -- a better module quality makes the slowdown smaller
    m.quality_quality_multiplier = 0                             -- the effect is already certain
  end
end
for _, q in pairs(data.raw.quality) do
  if q.next then
    q.next_probability = 1
    q.chain_probability = 1                                      -- and every further step, up to the top unlocked
  end
end
