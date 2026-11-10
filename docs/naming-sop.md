# Naming SOP (the Captain, 2026-11-09)

Everything that can carry a name gets one that says what it moves and where. Apply this at build time; a build is not finished until its names are set. Plain ASCII, no rich-text icons in names (scripts match on them).

## Train stops: `<Cargo> <Site> <Role>`
- Cargo: Iron, Copper, Coal, Stone, Oil, Uranium, Science Packs.
- Site: `Depot` for the original patch of that cargo, then letters `A`, `B`, `C` in the order outposts were built.
- Role: `Load` where the cargo gets on, `Unload` where it gets off, `Yard` for a stop that both loads and unloads mixed cargo.
- The two ends of a route share the prefix: `Copper A Load` and `Copper A Unload`. Where the unload sits (bus yard row) is on the map tag, not in the name.
- Current stops: Iron/Copper/Coal Depot Load+Unload, Copper A, Iron A, Copper B, Stone A, Oil A Load+Unload, Uranium A Load+Unload, Science Packs Load+Unload, Refinery Yard, Hub Chem Yard.
- Renaming by script (`backer_name`) does not rewrite schedules: rewrite every train's `schedule` records in the same call.

## Trains: one train group per route, named as the stop prefix
`Copper A`, `Iron Depot`, `Science Packs`, `Refinery Yard`. Set with `train.group`. A second train on a route joins the group and inherits the schedule. Writing `train.schedule` drops the train out of its group, so set the group last.

## Logistic request groups: `<Role>: <What>`
Every requester or buffer chest request lives in a named group, never a loose section, so one edit changes every chest of that kind.
- `Feed: <product>` chest feeding machines that make the product (`Feed: Steel`, `Feed: Processing Unit`). A second block with other amounts gets a suffix in brackets (`(mall)`).
- `Belt Feed: <item>` chest emptied onto a belt.
- `Rocket Parts: <item>` silo part chests. `Rocket Cargo: <item>` chests whose contents are launched.
- `Train Fuel: <fuel>` locomotive feeder chests. The standard is `Train Fuel: Nuclear` (nuclear fuel, 10 per chest) at every stop with a feeder; all 21 feeder chests are in it.
- `Buffer: <place>` buffer chests. `Relay: <item>` requester that hands on to a provider.
- Platform and ship requests: `<Platform name> Supplies` (the Captain's `Nuclear Ship Supplies`).
- Sections driven by a circuit (not manual) cannot join a group; leave them.
- Script: `section.group = 'name'` on a section from `get_logistic_point(defines.logistic_member_index.logistic_container).sections`; check `section.is_manual` first. A new group keeps the section's requests.

## Robot networks
`LuaLogisticNetwork.custom_name` is writable. `Nauvis Main` is the base network. A detached network is `<Planet> <Site>` (for example `Nauvis Oil A`).

## Space platforms: `<Job>` or `<Job> <Route>`
A stationary platform is named for what it makes (`White Science`). A hauler is named for its route and cargo (`Nauvis-Vulcanus Hauler`), a ship under construction for what it is (`Nuclear Ship`). No icon-only names.

## Map tags
One tag per train stop, text equal to the stop name. Add a tag for each yard, mall block and trash yard when it is built.

## What was applied on 2026-11-09
13 stops renamed and the schedules rewritten, 11 train groups set, 223 chest sections put into 30 named groups (20 circuit-driven sections left alone), main robot network named `Nauvis Main`, the platform named with only an arrow icon renamed `Nuclear Ship`, 22 map tags added. Save before: `pre-naming-sop`.

## Recommendations for space shipping (not applied, the Captain decides)
1. One logistic group per destination, `Ship: <Planet> Bootstrap`, `Ship: <Planet> Resupply`, set on the platform hub. The same group on every hauler for that planet means one edit changes them all.
2. One group per planet's landing pad request (`Import: Vulcanus`), so what a planet asks from orbit is in one place.
3. Train stops: set a train limit on every stop (1 per waiting slot) and give trains a refuel interrupt (fuel below a threshold, go to `Fuel Depot`), instead of a feeder at every stop.
4. Colour by cargo: locomotive and stop colour copper = orange, iron = blue, coal = black, stone = tan, oil = purple, uranium = green.
5. Platform schedules: wait conditions on request satisfied plus an inactivity fallback, never time only.
6. Constant combinators that hold a request list get a description (`combinator_description`) saying which group they mirror.
7. Quality: when quality items start to ship, put quality in the group name (`Ship: Vulcanus Resupply (rare)`).
