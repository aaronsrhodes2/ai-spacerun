-- Quality modules: 100% chance to raise the quality of a product, and every quality step always chains on to the next one,
-- so a product leaves the machine as legendary (the top tier).
for _, m in pairs(data.raw.module) do
  if m.category == "quality" then
    m.effect = m.effect or {}
    m.effect.quality = 1.0   -- 100% (the vanilla values are 0.01 / 0.02 / 0.025)
  end
end
for _, q in pairs(data.raw.quality) do
  if q.next then
    q.next_probability = 1.0
  end
end
