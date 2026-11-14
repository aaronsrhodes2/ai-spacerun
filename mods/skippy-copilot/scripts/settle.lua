-- The settings a piece carries besides its place: a machine's recipe, a splitter's filter and priorities, an
-- inserter's filter. Applied the same way whether the piece was placed freely or by the avatar's hands.
-- Each is tried on its own: a setting the game refuses must not undo the others.
local function settle(e, piece)
  if piece.recipe then pcall(function() e.set_recipe(piece.recipe) end) end
  if piece.output_priority then pcall(function() e.splitter_output_priority = piece.output_priority end) end
  if piece.input_priority then pcall(function() e.splitter_input_priority = piece.input_priority end) end
  if piece.filter then
    if e.type == "splitter" then
      pcall(function() e.splitter_filter = piece.filter end)
    elseif e.type == "inserter" then
      pcall(function()
        e.use_filters = true
        e.inserter_filter_mode = "whitelist"
        e.set_filter(1, piece.filter)
      end)
    end
  end
end

return settle
