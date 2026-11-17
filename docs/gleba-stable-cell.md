# Gleba stable science cell (design, 2026-11-15)

## Why the current Gleba stopped
On 2026-11-15 all 10 labs sat idle with every pack except agricultural. The chain died in this order:

1. The yumako seed loop ran at a loss. Over 10 hours the tower planted 202 seeds and processing returned 143.
2. The last seed was planted, the farm emptied, and no yumako seeds were left in any network.
3. With no yumako there was no mash, so no bioflux and no nutrients. Biochambers burn nutrients as fuel, so every biochamber stopped: eggs, packs and fruit processing.
4. Jellynut kept growing, but nothing used it. The tower output filled and the fruit rotted.

The chain cannot restart itself: it takes nutrients to make nutrients, and seeds to grow seeds. Gleba's usual failure has two parts:
- **A loop with a gain of about 1.0** (seeds), which drifts to zero.
- **A loop that dies with no way back** (nutrients).

## Game facts used (read from the live prototypes)
| Recipe | Time | In | Out |
|---|---|---|---|
| yumako-processing | 1 s | 1 yumako | 2 mash + seed at 2% |
| jellynut-processing | 1 s | 1 jellynut | 4 jelly + seed at 2% |
| bioflux | 6 s | 15 mash + 12 jelly | 4 bioflux |
| nutrients-from-bioflux | 2 s | 5 bioflux | 40 nutrients |
| nutrients-from-spoilage | 2 s | 10 spoilage | 1 nutrient (works in a plain assembler) |
| pentapod-egg | 15 s | 30 nutrients + 1 egg + 60 water | 2 eggs |
| agricultural-science-pack | 4 s | 1 bioflux + 1 egg | 1 pack |

- **Biochamber:**
  - Speed 2, with +50% built-in productivity and 4 module slots.
  - Uses 500 kW, burning 0.25 nutrients a second.
- **Trees:** a yumako or jellynut tree grows in 300 s and gives 50 fruit.
- **Spoil times:**

  | Item | Spoils in |
  |---|---|
  | Mash | 3 min |
  | Jelly | 4 min |
  | Nutrients | 5 min |
  | Eggs | 15 min, and they hatch into enemies |
  | Fruit | 1 h |
  | Packs | 1 h |
  | Bioflux | 2 h |
  | Seeds | Never |

- **Soil:** artificial and overgrowth soil are researched, so one cell can carry its own yumako and jellynut soil side by side.

**The seed margin.** One tree gives 50 fruit. At 2% plus 50% productivity, that returns 1.5 seeds per seed planted, but only if every fruit is processed. Any fruit that rots or is used elsewhere eats into that margin. The old farm ran at about 0.7 (143 seeds back for 202 planted).

## Sizing: one cell = 1 agricultural pack a second (3,600 an hour)
The current Gleba made 3,759 packs in 10 hours, so one cell is about 10 times that.

| Stage | Rate needed | Biochambers (speed 2, +50%) |
|---|---|---|
| Packs | 1/s (0.67 bioflux + 0.67 eggs) | 2 |
| Eggs (net 2 per craft) | 0.67/s, 10 nutrients/s | 3 |
| Nutrients from bioflux | about 14/s (eggs + fuel for about 15 chambers) | 1 |
| Bioflux | about 1.85/s | 1 |
| Yumako processing | 1.55 fruit/s, giving 0.046 seeds/s | 1 |
| Jellynut processing | 0.62 fruit/s | 1 |
| **Total** | | **about 10 biochambers** |
| Yumako farm | 0.031 trees/s, about 9–10 trees growing at once | 2 towers (twice the need: the Captain, "grow more trees") |
| Jellynut farm | 0.012 trees/s, about 4 trees growing at once | 2 towers (same) |

**More trees is the main lever.** The old farm planted about 20 trees an hour. One cell needs about 110 yumako and 44 jellynut trees an hour. Twice the need in towers means two things:
- Fruit is never the limit.
- Every extra tree also returns its 1.5 seeds, so a larger farm makes the seed bank grow faster, not slower.

Surplus fruit stays on the trees (rule 6), so the extra towers cost nothing when they aren't needed.
| Seeds | yumako +0.015/s, jellynut +0.006/s spare | |

About half of all bioflux goes to nutrients: egg food plus biochamber fuel. Bioflux is the cell's battery, because it keeps for 2 hours. Nutrients rot in 5 minutes, so they are only ever made just before use.

## The seven rules that keep it alive
1. **Seeds go to the farm first.**
   - Processing seeds go straight back to their own tower by inserter, so seeds are never shipped away.
   - A seed bank chest holds a 100-seed reserve for each fruit. Only seeds above 100 go to the sink.
   - Margin: +50% with no modules. Productivity modules in the two fruit-processing chambers raise it further.
2. **All fruit is processed inside the cell.** Raw fruit has no other consumer, so the 1.5 seed margin is real.
3. **Bioflux is the only store.**
   - A bioflux buffer of about 500 (about 4.5 minutes of the whole cell) sits at the centre.
   - Pack and egg chambers run only while bioflux is above 150. Below that, all bioflux goes to nutrients, so the chambers keep their fuel and the cell never dies.
4. **The cell can restart itself.**
   - A plain electric assembler (needs no nutrients) runs nutrients-from-spoilage.
   - It is fed from a steel chest of spoilage, which is inert per the chest rules.
   - Its nutrients go only to the fruit-processing and bioflux chambers. That is enough to rebuild the bioflux buffer from fruit after a total stop.
   - Spoilage also builds up from normal rot, so the chest keeps refilling.
5. **Eggs are counted, never stored.** The egg chambers run only while eggs on hand are under 20, by circuit, so eggs never sit long enough to hatch. The egg loop starts from 2 eggs kept in the egg chambers. If they are ever lost, a bootstrap egg comes from the existing Gleba line, and that is logged.
6. **Surplus is stopped first, then destroyed** (the void-surplus rule).
   - The towers plant only up to the cell's need, by limiting seeds.
   - Seeds above the reserve, and spoilage above 2,000, go to a heating tower, which also keeps the cell warm at no cost.
   - Fruit over the buffer stays on the trees: towers don't harvest when their output is full, so the fruit isn't wasted.
7. **Belts inside, robots only at the edges.**
   - Mash, jelly and nutrients go by direct insertion or short belts, because they rot in minutes.
   - Robots bring in only water, any starter items, and modules, and take out packs.

## Watchdog and proof
`scripts/gleba_cell_watch.py` will run in the autopilot every cycle and log:
- seeds in each bank;
- the bioflux buffer;
- nutrients on the fuel belt;
- eggs on hand;
- packs per minute;
- trees growing.

It alarms in game and in the log when any of these happens:
- a seed bank stays below 50 for 10 minutes;
- bioflux stays below 150 for 5 minutes;
- eggs reach 0.

**Pass mark (the Captain's warning: prove it over a long run):** 10 hours of game time at at least 0.9 packs a second, with no alarm. The seed banks and bioflux must end the run no lower than they started. Then a cold-start test: empty all nutrients and bioflux on purpose, and the cell must recover with no help within 30 minutes. Only after that is it copied.

## Build plan
1. Save as `skippy`.
2. Pick a free site, not on the Captain's builds:
   - Pave it with artificial yumako and jellynut soil, factory-made.
   - Water by pipe from an offshore pump.
3. Place the cell from one script, `scripts/gleba_cell.py`:
   - a dry run first;
   - every machine at epic quality;
   - circuit conditions included.
4. **Seed start.** No yumako seeds exist now, so the first ones come from fruit:
   - Robots harvest a few of the 286 wild yumako trees near the old tower at (-150,-115). The first test is on one tree.
   - That fruit is processed in the new cell.
   - The cold-start assembler makes the first nutrients from spoilage. Jellynut seeds are already in stock (718).
5. Run the 10-hour proof, then the cold-start test.
6. Once it passes, replicate the cell with the same script at new positions, up to the science target.

## Open points
- **Captain's choice:** whether to leave the old line and old towers alone (my plan) or tear them down once the cell runs.
- **Modules:** no productivity modules are in stock on Gleba. Without them the seed margin is the base +50%, which is enough. Modules would add to it.

## Build log and lessons (2026-11-15)
Built as `scripts/gleba_cell.py` (hub), `scripts/gleba_farms.py` (many towers), watchdog in the autopilot. First run went like this:

1. Cold start worked with no help: the spoilage assembler made the first nutrients, the mash chamber then made its own. Bioflux reached 450+ within minutes.
2. **Robot trips are the hidden limit.** A request of 20 yumako starved a chamber that eats 2 a second, 270 tiles from the farm. Fruit requests are now 250 / 120.
3. **Seed floor was backwards.** Planting only above 20 seeds meant a cold start (about 10 yumako seeds) never replanted. Floor is 0; the locked vault is the reserve.
4. **Chest `bar` is 1-based.** `bar=1` blocks every slot. Egg output chests have `bar=3` (eggs plus the spoilage a chamber also puts out).
5. **`place_entities` ignores a biochamber's facing.** `cfg_lua` sets it after placing (`setdir`).
6. **Pipes need a source.** The water header was built without a link from the pump; nothing flowed.
7. **Eggs have no bootstrap.** Every egg was gone when the old line starved (they hatch in 15 minutes). The Captain allowed one starter egg (2026-11-15). Anything that stalls the egg loop for 15 minutes needs a spare again.

## What other players do (web research, 2026-11-15; forum and Reddit advice, not official)
Sources: Factorio forums threads "Restarting nutrients supply is a pain in the ass", "Remote restart of Gleba?", "Building on gleba"; r/factorio "Notes on Gleba"; wiki.factorio.com Gleba and Agricultural tower.
- Make nutrients where they are eaten. Nutrients spoil in 5 minutes, so central distribution over long belts does not survive the delay. (Our hub makes nutrients beside the chambers that eat them.)
- Keep a bootstrap that does not depend on the machines being restarted: a spoilage-to-nutrients assembler (what we have). One poster switches it off when the biochambers hold nutrients (ours runs only while spoilage is fed in).
- Prioritise nutrients to bioflux production first; the rest can wait.
- Fruit must be processed before it spoils or the seed chance is lost. Biochambers (+50% productivity) are what make seeds out exceed seeds in.
- Trees do not spoil, so leave fruit on them and stop the tower when enough is on hand ("turn off the tower, not the inserters"). Ours stops the fruit inserter so the tower's output fills and it stops harvesting: same effect.
- Surplus seeds and spoilage: recycle or burn in a heating tower.
- Keep spare biochambers in a chest: recycling one gives a chance of an egg back, the only restart for eggs. **To do: a locked reserve of spare biochambers (like the seed vault).**
- **Defence:** towers send out spores when they harvest, which draws pentapod attacks; more towers means more attacks. **To do: check turrets around the new towers.**
- Avoid chest buffers between towers and first-stage processing; keep items moving. (Ours: fruit goes tower -> chest -> robot -> chamber. Watch for spoilage of fruit in chests; the fruit gate stops the towers, so chests stay small.)

## Power (found 2026-11-15, after cell 2)
Gleba's grid is 388 solar panels plus heating towers whose heat runs steam turbines. The towers were fed spoilage on belts by the old line. That feed has been dead
for days and the spoilage assemblers now take what is left, so all 7 towers read "no fuel", 432 accumulators were empty and 9 of the 10 labs ran at low power once
cell 2 added 13 biochambers (about 6.5 MW at full tilt).
- Stopgap (done): the four hot towers have a requester chest + inserter fed **surplus jellynut** (10 MJ each), the inserter open only while the network holds more than
  300 jellynut, so only the surplus burns. This turns idle fruit into heat, it is not a full answer.
- Real answer (the Captain, 2026-11-15: "burn nuclear instead of spoilage"): a nuclear reactor on Gleba feeding the same heat pipes. Needs uranium fuel cells shipped
  to Gleba (about 18 cells an hour per reactor at full heat) through the shuttle fleet, which waits on `all_requests_satisfied`, so the request must be one the
  supply can always fill. Not built.

## Gleba reactor (2026-11-15)
Built after the Captain chose nuclear: a nuclear reactor (epic) at (57.5,3.5), touching the west heat pipes by the first heat exchanger (2 exchanger/turbine pairs, about 11.6 MW; the east group has 3 pairs).
- Fuel: a requester chest at (53.5,3.5) asks for 6 uranium fuel cells; its inserter is wired to the reactor's temperature signal and runs only below 700 degrees.
- Cells reach Gleba through a landing-pad request, section "reactor cells (gleba)": uranium-fuel-cell >= 40, import from Nauvis (13,650 cells there), the pattern the pad already uses for robots and LDS. Not yet delivered: the next Nauvis-Gleba shuttle trip brings them.
- Depleted cells: an inserter on the east side puts them into a provider chest at (61.5,3.5); depleted_return.py carries them home.
- Watchdog alarm: no cell and cold for 20 minutes.
- Limit: five exchanger/turbine pairs is about 29 MW at most. If demand grows, add pairs on the reactor's heat.

## Lab pack buffer (2026-11-15)
The Gleba labs ran out of **utility** science packs (9 of 10 labs had none) while Nauvis held 27,939 and two loaded shuttles sat at Nauvis: the 1,200-pack buffer was used up
before the next trip. Deeper buffer for utility packs, set live (the Captain: "add a deeper utility buffer"):
- Gleba landing pad, manual section: utility-science-pack min 1,200 -> **5,000** (max 2,400 -> 8,000). The pad's circuit-controlled section still adds 1,800 from Nauvis.
- Each Nauvis-Gleba shuttle hub: utility from Nauvis 400 -> **800** per trip (six ships).
- Room: the pad has 280 slots with 182 empty; 5,000 packs take 25 slots. Nauvis can always fill it (27,939 on hand, 1,698 made an hour), so no ship waits on an unmet request.
- Other packs keep 1,200 on the pad and 400 per ship. Use the same two numbers for any pack that runs dry first.

## Second collapse, 2026-11-16 (the Captain: "its still not stable, find the bottlenecks")
- State found: 0 agricultural packs, 10 Gleba labs idle, 0 pentapod eggs anywhere (loop dead), pack chambers with empty fuel slots, 4 egg chambers halted with 24 to 60 spoilage in their output, spoilage converters short of spoilage, nutrients 2,000 in the network but sitting in provider chests (they rot in 5 minutes).
- Chain: spoilage jams an egg chamber output -> chambers stop -> eggs (the catalyst) hatch within 15 minutes -> no egg anywhere -> nothing restarts without help. Rule 5 and lesson 7 above, happening again.
- Fix applied: spoilage moved into the spoilage converters, no_fuel biochambers given 10 nutrients from provider chests, and **4 starter eggs** (the Captain's order, second use after 2026-11-15). Eggs went 4 -> 22 in two minutes, packs 0 -> about 110 a minute, labs missing packs 10 -> 2.
- Kept running: `scripts/gleba_restart.py` (spoilage unjam, fuel, stranded eggs; moves items only, creates nothing) every other autopilot cycle. It cannot make an egg: if the loop dies again for 15 minutes a starter egg is needed again, so the real fix is to stop the jam that kills it.
- Still short (ranker, after the restart): yumako processing missing yumako (4), spoilage converters missing spoilage (4), bioflux chambers missing mash/jelly, restart chamber (mash to nutrients) out of fuel.
