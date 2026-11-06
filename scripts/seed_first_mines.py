"""Give the first mines their one approved load of starter coal."""
from _game import tools

print(tools["seed_starter_fuel"](-85, -115, 45, -40))
print(tools["tell_player"](
    "First mines built: iron, copper, coal and stone run by belt to the hub. Fuel is on its way down the coal lines.",
    x=-20, y=-62))
