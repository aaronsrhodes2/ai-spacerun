# Factory strategy (the Captain, 2026-11-07)

Goal: an organised, compact factory. Each raw resource is mined at its own patch, smelted at
a **depot** at that patch, and shipped to the central base by train. Anything consumed where it
is made (sulfur at the refinery, plastic at the refinery) stays local.

## Principles
- **Smelt at the depot.** Plates travel, ore does not. A depot is a patch with miners, a furnace
  row (steel furnaces, electric inserters), a coal supply and a loading stop.
- **Trains for long distance**, belts for anything inside a depot or the central base.
- **Fuel where the train is.** Locomotives refuel at the depot they load from (coal from the
  coal depot, or any fuel the depot makes).
- **Clear-cut is allowed** in the central base and at depots. Rebuilding a whole area to
  re-optimise is fine; keep the save before each clearance.
- **Water** is pumped where it is needed (sulfur); a train can carry it only as a fluid wagon
  (fluid-wagon is researched).

## Depots (targets from the Captain's map survey)
| Depot | Product | Patch(es) |
|---|---|---|
| Coal | coal, to fuel the central base and locomotives | (145,62) line 1 (in service), plus others |
| Copper | copper plate | copper patches: (128,-329), (317,233), (-81,422), (-41,-525) and near base (-64,-88) |
| Iron | iron plate | iron: (-27,-103) near base, (-219,-433), (-361,-358), (-464,284) |
| Stone | stone brick | stone: (18,-50) near base, (95,-424), (-267,380) |
| Oil | crude, to refinery | field (-314,-293), already piped |
| Uranium | uranium ore (later) | uranium patches (see survey) |

## Central base
Clear-cut the area between the mines and the lake. Layout bands, north to south: science
assemblers and labs; intermediate products (gears, circuits, cable); the sulfur and plastic
plants stay at the refinery (-150,-115) with a train or belt link.

## Status (2026-11-07)
- Done: coal line 1 (train, 343k patch). Electric iron, copper, coal fields near base. Red and
  green science in service; oil refining; plastic.
- Blue science: engine sets, advanced-circuit chains and pack assemblers built. Engine sets
  make steel in their own furnaces; engine units reach N2.
- **Blocked:** sulfur plant gets no petroleum gas. Water reaches its input pipe; the gas
  underground run ends at the input tile but the plant still reports a fluid shortage. Next
  step is to check which plant input faces which fluid in game. The plastic plant was paused
  for this test and is running again.
- Not started: copper, iron and stone depots with trains; the central clear-cut.

## Decision needed
Clear-cut scope for the central base, and whether to start with the copper depot (train copper
plates in) or the iron depot (more plates; the base's current iron is the constraint).
