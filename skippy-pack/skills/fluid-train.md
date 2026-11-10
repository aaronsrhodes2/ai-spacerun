# Skill: oil (and later acid) by fluid train

Oil field to the main holding tanks:
1. Field box = bounding box of the wells plus 10. Rail: station on x=odd, the train arrives heading north (or mirror), stop on the right-hand side, pumps and header on the same side as the field so no pipe crosses the rail.
2. `fluid-train-oil --area BOX --rail X STOP_Y --apply`: pumpjacks on every well, BFS pipes, header, three pumps, poles, power joined. If a jack's output tile overlaps another jack, turn it and add pipes (done by hand once).
3. Stub and stop as in train-outpost (`--dir S`), then route with `rail-line`.
4. Bus-head unload (inline code so far): yard rail on the next free row, three pumps pointing away from the wagons, a pipe row, two storage tanks joined by a pipe at their shared connection tile (tank at (cx,cy): ports at (cx-1,cy-2), (cx+2,cy-1), (cx+1,cy+2), (cx-2,cy+1)).
5. Train: 2 locomotives and 3 fluid wagons, schedule load (full or 3600) then unload (empty or 900).
Verify: wagons hold crude, tanks fill, no pumpjack in `waiting_for_space_in_destination`.
Not built yet: acid train for uranium mining, refinery lane from the tanks, signals.
