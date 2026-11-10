# Outposts, trains and the new main bus (plan, 2026-11-09)

Order from the Captain: cover all copper and iron outposts, maximum smelt, trains carrying the plates to the main base, pave the outposts too, bring in stone, coal and oil (raw, refined later),
and collect everything into one great main bus where future production grows.

## What exists
- Rails: about 1,050 pieces, 12 stops, 6 trains. Iron depot (load (-171,-411), unload (19,-159)), copper depot (load (165,-295), unload (87,-151)), Coal2 (73,-43)/(143,69), science and pack routes. No rail routing tool yet.
- Plate outposts built by drone: iron south-west (-464,284) 137 drills / 72 furnaces; copper north (-41,-525) 71 drills / 54 furnaces. Their plates sit in provider chests (no belt, no train).
- Patches (unused): iron (-723,-317) 1,420 tiles, (693,488) 1,410, (-1155,256) 1,366, (788,595); copper (317,233) 596, (732,97) 1,039, (-902,-345) 1,115, (469,552) 558, (-1136,618) 1,174.
  Stone: (95,-424) used, (-250,522), (-267,380), (94,-573) unused. Coal: (507,341), (685,342), (775,158), (134,654), (-639,-340) unused. Oil: seven fields, only (-314,-293) used.
- Free ground for a bus: x 160..288, y -128..64 (4 by 6 chunks) east of the base, all land, no entities.

## The numbers that decide the size
- One full outpost (137 drills, 72 electric furnaces) is about 28 MW (drills 12 MW, furnaces 13 MW, inserters and poles the rest) and gives up to 45 plates/s, which is exactly one full express belt (45 items/s, 22.5 per lane).
- Ten outposts would add about 280 MW. The grid today: about 64 MW of turbines, 180 MW of solar at noon and nothing at night; demand was 130 MW at dusk with the silos on. Nuclear (the Captain is building it) is what allows "maximum smelt everywhere".
- A cargo wagon holds 4,000 plates (40 slots x 100), so a train with 6 wagons carries 24,000; one outpost's 45 plates/s fills it in about 9 minutes.

## Plan, in order
0. **Power gate.** Build the outposts to full size but let the autopilot enable them in stages by power headroom (accumulator level, fraction of low-power machines), the same way it guards the silos. Nothing is wasted if nuclear arrives later.
1. **Paving.** `scripts/pave.py` already handles chunks; add `--around X Y R` so each outpost and its rail line gets refined concrete.
2. **Rail tool (the missing piece).** `fx.py rail route A B` that lays straight and curved rail between two points with signals and a chain at junctions, avoiding trees, cliffs, water, entities. Test it on one pair of stops first.
3. **Pilot, one iron outpost by train.** Smelter output goes onto an express belt instead of chests (or both), a load station of 6 wagons with bulk inserters, a train, and an unload station at the bus head. Measure plates/s delivered for an hour of game time.
4. **Roll out:** iron (-464,284) full and second smelter line, (-723,-317); copper north (-41,-525) completed, (317,233), (732,97), (-902,-345). Then stone (-250,522), coal (507,341), crude oil to storage tanks by train (fluid wagons).
5. **The main bus** (east block): 16 lanes of express belt (8 belts): iron plate, copper plate, steel, stone brick, coal, plastic, sulfur, circuits, with room to grow, splitter tap points every 12 tiles, stations feeding the head and the belts running south to north, producers before consumers. Unloading stations at the head deliver raw plates; raw stone, coal and oil arrive at the head and are refined in sections along the bus, later.
6. **Retire** the drone-only plate hubs and long belts once the bus is steady; `fx.py compact` the gaps.

## Decisions needed (asked in chat)
- Power: build everything and let the autopilot stage it by headroom, or build only what current power supports.
- Bus site: the east block above, or somewhere else.
- Pilot first (iron, one train), or build all outposts and rails in one sweep.
