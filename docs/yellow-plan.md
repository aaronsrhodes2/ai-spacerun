# Yellow (utility) science plan (2026-11-08)

Recipe: 2 processing units + 1 flying robot frame + 3 low density structure -> 3 packs (21 s).
Sub-recipes: PU = 20 EC + 2 AC + 5 acid; FRF = 1 steel + 2 battery + 3 EC + 1 electric engine unit; battery = 1 iron + 1 copper + 20 acid;
EEU = 2 EC + 1 engine unit + 15 lubricant; engine unit = 1 steel + 1 gear + 2 pipe; LDS = 20 copper + 2 steel + 5 plastic.
Target about 2 crafts/min (6 packs/min): one machine per recipe is enough.

## Where the inputs are (found 2026-11-08, after the Captain rebuilt oil)
- Lubricant tank (25,000) at (-252,-130); sulfuric acid tank (25,000) at (-264,-130) (fluid train "Eviber -> Benhotwheels" unloads there).
- Plastic is back on the plastic belt (about 950 on it, 354 on trunk 2).
- Raw items on the bus (trunk: west lane | east lane): T0 steel|AC, T1 iron|copper, T2 plastic|EC, T3 free|cable, T7 free|coal. All other lanes are used.

## Why not rows on the bus
Lane budget is spent (only T3 west and T7 west are free) and there are 6 new products (engine, EEU, battery, FRF, LDS, PU), several with 3+ inputs.
Plan: a local yellow block in the free west area (x 18..66, y -128..-100), fed by three mirrored taps (T1, T0, T2). Filtered splitters
(the Captain prefers splitters) split each mixed belt into its two items; side-loading re-pairs lanes as each stage needs:
 1 engine sets [pipe][engine][gear]  (steel|iron)            -> engines
 2 electric engine unit              (engines|EC) + lubricant -> EEU
 3 battery                           (iron|copper) + acid    -> batteries
 4 flying robot frame                (steel|EC) and (EEU|battery) -> FRF
 5 LDS                               (copper|steel), plastic -> LDS
 6 processing unit                   (EC|AC) + acid          -> PU
 7 utility pack                      (PU|FRF), LDS           -> packs onto the pack belt (sorted to port 2 by the filtered splitter)
Fluid rows are single machines rotated to face east so the pipe enters at the east centre tile. Fluids come by underground pipe from the two tanks.
