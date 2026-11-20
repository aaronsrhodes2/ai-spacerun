-- The allowances: every rule the mod, its scripts or the live game deliberately relaxes (the Captain, 2026-11-20: fully
-- vanilla is a long-term goal, not a requirement, and fun to play comes first). One list, here, read by the settings stage
-- (one switch each, default on), by the tools in scripts/allowances.lua and by the model's skill.
--
--   id       the name used everywhere: the setting is skippy-allow-<id>, the tools take it
--   what     what is relaxed, one sentence
--   vanilla  what the vanilla game does or would need instead; what turning the allowance off asks of the player or model
--   kept_by  who keeps the switch honest:
--              mod     the mod refuses the relaxed action when the switch is off
--              skill   the model is told, and its skill says to obey; the mod cannot stop it
--              script  an operator script outside the mod does the relaxed thing; it should check the switch before it does
--
-- Add a relaxation by adding a row; nothing else needs to change for it to appear in the settings and in the tools.
return {
  { id = "free-placement", kept_by = "mod",
    what = "In 'builds on its own' mode pieces appear in the world without their items, once the piece is researched.",
    vanilla = "Every piece comes out of an inventory: the character carries it (the 'moves your character' mode does this) or robots bring it." },
  { id = "remote-exploring", kept_by = "mod",
    what = "The map is revealed round its edge without anyone walking there.",
    vanilla = "Ground is charted by walking, driving or flying there, or by radars; the avatar would have to go." },
  { id = "free-fuel", kept_by = "skill",
    what = "A new machine's first fuel is free.",
    vanilla = "Fuel is carried to it from a chest or belt the factory fills." },
  { id = "free-upgrades", kept_by = "script",
    what = "When a quality level is researched, everything of ours is upgraded at once without the modules or items it would cost.",
    vanilla = "Quality comes only from quality modules on the machines that make the item, and each piece is replaced by hand or by robots." },
  { id = "player-boosts", kept_by = "script",
    what = "The player's character has free crafting of anything researched, 50 times hand speed, 200 tiles of reach and 200 extra inventory slots.",
    vanilla = "Normal hand speed, reach and slots; crafting costs its ingredients and time." },
  { id = "infinite-scrap", kept_by = "script",
    what = "Fulgora's charted scrap tiles are set to the largest amount the game allows.",
    vanilla = "Scrap runs out and the base must reach new patches." },
  { id = "unlimited-wire-reach", kept_by = "script",
    what = "Wires are connected over any distance (no signal wire length limit), for example from a hub to far inserters.",
    vanilla = "A wire reaches only as far as the poles' and machines' own wire distance, so far machines need poles or a nearer controller." },
  { id = "ring-foundations", kept_by = "script",
    what = "Space-platform foundations may be laid in a ring (a doughnut), where the hub is not at the middle of solid ground.",
    vanilla = "Foundation is laid out from the hub in a connected, filled shape." },
}
