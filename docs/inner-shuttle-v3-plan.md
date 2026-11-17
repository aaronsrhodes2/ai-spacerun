# Inner shuttle v3 plan (2026-11-16, the Captain: "redesign our inner planet shuttles to be much more robust in storage and speed")

## What flies now (read from the live game)
| Ship group | Hull | Cargo slots | Thrusters | Weight |
|---|---|---|---|---|
| Nine Nauvis-Gleba/Vulcanus/Fulgora 1..6 Shuttles | old hull (`build_shuttle2.py`) | 109 (1 bay) or 159 (2 bays) | 4 | 267 t |
| Courier 1 | new hull (`inner_shuttle.py`, 7 bays) | 409 | 4 | 389 t |
| Aquilo ships | `aquilo_shuttle.py` | 509 | 4 | 553 t |

The new hull (`inner_shuttle.py`) was designed 2026-11-13 for exactly this and was never rolled out to the nine.

## Where the time goes
- A leg is about 60 to 90 s. The cycle is 15 to 30 minutes: the ship waits at Nauvis for propellant (SKILL.md, "Vulcanus Shuttle": "the cycle is fuel-bound"). Nauvis orbit gives a few hundred fuel a minute; a round trip burns 7,000 to 21,000.
- So "speed" is two things: cruise speed (small win) and propellant per trip against propellant made per minute (the real one).

## Physics, from the game's own formula (utility constants, read live)
acceleration = (thrust / (1 + weight/1e7) - (90 v^2 (weight/200)^0.8 + 10000)) / weight
Top speed is about sqrt(thrust) / weight^0.4. Thruster effectivity is 0.51 at full flow and 1.0 at minimum flow (prototype, read live), so more thrusters at lower flow give more thrust per unit of fuel.
Model fitted to the old hull (4 thrusters, 267 t, about 5.5): per-thruster thrust about 225 kN (a fit, not a prototype value; to be checked by a measured flight).

| Thrusters | 267 t (old hull) | 389 t (7-bay hull) |
|---|---|---|
| 4 | 5.5 | 4.7 |
| 6 | 6.8 | 5.8 |
| 8 | 7.8 | 6.7 |

The 7-bay hull with 4 thrusters is slower than the old ship (4.7 vs 5.5). With 8 thrusters it is 22% faster than the old ship and carries 2.6 times the cargo.

## Design
1. Hull: the `inner_shuttle.py` hull (7 bays, 409 slots at legendary), not the old one.
2. Thrusters: 8 instead of 4, at lower flow each (better effectivity, so fewer propellant per km, not more). Open: does a second thruster row fit behind the first (exhaust clearance)? Test on a fresh platform before any live ship.
3. Propellant: tank buffer already 187,500 per fluid on Courier. The cycle fix is production at Nauvis: more collectors and a second fuel and oxidizer plant on the hull (fuel plant makes 75 per 2 s per plant, so plants are not the limit; chunk intake is).
4. Hull trim: foundation is 227 of the 267 t. Dropping the unused apron (every entity footprint plus a ring) cuts weight and raises speed as weight^-0.4.
5. Rollout: one new ship first (`inner_shuttle.py create/build/config/adopt/route`), fly it a full round trip, compare against an old ship, then retire old ships one planet at a time (`adopt` moves cargo and stock across).

## Not known yet (measure before building)
- Real thrust per thruster and fuel burn per km at 8 thrusters.
- Whether a second thruster row is blocked by the first one's exhaust.
- Chunk intake per minute in Nauvis orbit for 2 versus 6 collectors.

## Result of the prototype (2026-11-16)
- Built `Nauvis-Proto 1 Shuttle` (index 40, surface platform-2) with `inner_shuttle.py build --apply`: 510 entities, 2,030 tiles, 325 hub slots (epic bays; legendary bays give more), 8 thrusters in one row (x -23..22), weight 446 t. Modelled top speed about 6.3 against 5.5 for an old hull (+15%) with three times the cargo.
- **A thruster needs EMPTY space behind it** (a foundation tile there makes placement fail), so a second row is impossible; the row is widened instead. `aquilo_shuttle.py` has a `THR8` switch (set by `inner_shuttle.py`): fuel and oxidizer headers on rows 17 and 19 cross at the fuel columns x -12, 0, 12 by pipe to ground; the 6 panels the header displaced moved to an outer column a side.
- Plumbing checked: 6,000 of each propellant moved from Nauvis-Gleba 1 Shuttle (which held 125,000 of each) and all eight thrusters filled with both fluids.
- Correction to "Where the time goes": nine shuttles parked at Nauvis hold 67,000 to 125,000 of each propellant, so the wait is not (only) propellant; check which departure condition holds them (magazines 800, science requests) before blaming fuel.
- Still to do: magazines for the prototype (the 14 turrets have no ammo; it makes them from ore it collects), `route`, one measured round trip (speed, fuel per leg), then retire old ships a planet at a time.
