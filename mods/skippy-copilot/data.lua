-- Listening to the player's own controls, so the assistant lets go of the character the moment the player takes it
-- back (the Captain, 2026-11-13: moving between playing by hand and being moved must be smooth). Each entry fires
-- when the player presses the game control it is linked to; it has no key of its own and takes nothing away.
local CONTROLS = { "move-up", "move-down", "move-left", "move-right", "mine", "build" }
local inputs = {}
for _, control in ipairs(CONTROLS) do
  inputs[#inputs + 1] = { type = "custom-input", name = "skippy-hands-" .. control, key_sequence = "", linked_game_control = control }
end
-- The Talk to Skippy key: puts the cursor in the Skippy panel's text box, so the player talks without the mouse
-- (the Captain, 2026-11-21: hands-free). Enter by default; it takes nothing away from the game's own use of the key.
inputs[#inputs + 1] = { type = "custom-input", name = "skippy-talk", key_sequence = "RETURN" }   -- consumes nothing (the default)
data:extend(inputs)
