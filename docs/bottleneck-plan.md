# Finding and fixing production bottlenecks like bugs (plan, 2026-11-08)

## What the last day of manual debugging showed
Every stall was one of five bug classes, and every one was found by the same three questions: which machines are not working, what exactly are they missing, and where is that item stuck upstream.
1. **Contamination**: the wrong item on a lane (iron on the copper lane, plastic on the circuit lane, sulfur on the plastic lane). A lane jams because nothing downstream eats the intruder.
2. **Wrong direction / orphan**: an inserter facing the wrong way (4 steel furnaces idle), a belt that ends in nothing (yellow packs), a machine whose input faces the wrong side.
3. **Upstream-of-producer**: a consumer tapping a trunk north of where the item is put on it (EC and AC for yellow). Trunks flow south, so this can never work.
4. **Wrong machine type or recipe unset**: battery in an assembling machine (needs a chemical plant).
5. **Real capacity**: genuinely not enough plates, steel, trains, or machines. Only after 1-4 are ruled out.

## The tool: scripts/bottleneck.py (proposed, one command, read-only)
A. **Ledger** (production statistics, 1 min): made vs used for every item on the science tree. Lists items where used > made (true shortage) and items where made >> used (surplus backing up = somewhere downstream is blocked).
B. **Machine census** by recipe: counts per status, and for every machine in item/fluid shortage the exact missing ingredient (already prototyped, one Lua call). Output example: `4x military-science-pack <- missing piercing-rounds-magazine`. Follow the arrow upstream automatically: the missing item's producer becomes the next row to inspect, until it reaches a producer that is working (the real limiter), idle with full output (blocked downstream), or missing a raw input.
C. **Lane audit**: a table of every belt trunk and branch with its design lanes (T0 steel|AC, T1 copper|iron, T2 EC|plastic ...). Sample each lane every few tiles; flag any item outside its allowed set, and any lane that is full and stationary with no consumer for its head item.
D. **Wiring lint**: inserters whose pickup target is a machine output and drop target is a machine input for the same machine (backwards), belts whose last tile has no consumer and a stationary lane, machines whose fluid recipe has no connected pipe, recipes unset, chemistry recipes in assembling machines, consumers tapping a trunk north of the item's give row.
E. **Flow check**: for each science pack, trace pack machine -> belt -> port -> wagon -> lab: first place where the count of packs on the path is zero downstream of a non-zero.

## Fixing like bugs
Each finding is a ticket: `id, class (1-5), where (x,y), evidence (the numbers), proposed fix, status`. Fix recipes already known:
- contamination: add a side-load dummy belt (never let a curve carry a two-lane feed into a shared trunk), add a filtered splitter at the entry, clear the jam with a one-off Lua `remove_item` on all lines (including underground lines 3,4).
- backwards inserter: rotate it.
- upstream-of-producer: new tap below the give row plus a filtered sorter and a belt back (done for EC and AC into the yellow block).
- capacity: add machines/trains only when the ledger says used > made with every stage upstream working.
Regression: every fix adds one check to the lint (so the same bug cannot come back silently), and the tool runs after each build and prints "0 new findings".

## Decision for the Captain
Build scripts/bottleneck.py (A+B+C first, about an hour, read-only, no risk), then add D and E. Option: run it on a schedule and have it tell you in-game (`tell_player`) when a class 1-3 bug appears.
