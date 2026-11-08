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

---
## Update 2026-11-07 (evening): the train circuit

The Captain's order of loading is **water, coal, iron, copper, oil, stone, uranium**, on a circuit of
trains whose cars are mobile storage and balancing. Everything visible is to be mined.

### What "everything visible" costs (from scripts/survey.py, snapshots/survey.json)
29,045 ore tiles in 41 patches (iron 8,855, copper 7,580, coal 6,043, stone 5,657, uranium 910),
7 oil fields (70 wells) and 25 lakes, with 431 enemy spawners scattered between them.
Covering every tile means about 2,400 electric drills: 218 MW, about 120 boilers, 1,200 ore/s.
That is far more than the base could use, so coverage is sized to a **target rate per resource**,
and the cap on drills is the power plant.

### Two layers
1. **Long haul**: one shuttle train per patch group (the coal line 1 pattern, already proven),
   loading drill-to-wagon at the patch, unloading at the depot district.
2. **The circuit**: a short, compact loop round a cleared depot district next to the base. Mixed
   trains (fluid wagons for water and oil, cargo wagons for the rest, in the Captain's order)
   pass the seven loading stops in order, then the base's unloading stops. Adding a train adds
   capacity; cars buffer between supply and demand.

### Power is the real limit
Steam is 9 MW now. Remote drills need power too: local solar (solar-energy is researched) or the
coal cars fuelling burner drills. Nuclear waits on uranium, which is 580+ tiles away.

### Build order proposed
1. Re-clear and lay out the depot district and its circuit.
2. Water (pumps on the south lake, fluid wagons). 3. Coal: line 1 delivers to the depot.
4. Iron (near patch first, then remote). 5. Copper. 6. Oil (crude by fluid wagon from the NW field).
7. Stone. 8. Uranium. Nests near a patch are destroyed before building there.

### Revision (the Captain, same evening): ONE loop, extended outward
Supersedes the "two layers" idea above. There is a single closed, one-way railway. Trains with
mixed cars (fluid wagons for water and oil, cargo wagons for the rest, in loading order) circle
it and each stop loads only its own cars. To add a patch, the loop is extended outward so it
runs through the new patch: one segment is replaced by a longer path that passes the patch and
rejoins. No spur lines and no separate shuttles.

What that implies:
- **One-way track, so one locomotive per train** is enough (no reversing) and signals keep trains apart.
  Needs rail signals/chain signals (both researched) at every stop and junction.
- **Refuelling** happens at one stop on the loop (coal from the coal wagon into the locomotive).
- **A stop per resource, in order**: water, coal, iron, copper, oil, stone, uranium; several stops of the
  same resource can sit side by side when a resource has more than one patch on the loop.
- **Extending the loop is a router job**: pick the segment to replace, route out to the patch
  (corners are the four-curve turn), run through it so drills load straight into the wagons, route back.
- **Loop v1** covers the patches near the base (water, coal, iron, copper, stone are all within about
  200 tiles); oil and uranium are 370-580+ tiles out and come later, by extension.
