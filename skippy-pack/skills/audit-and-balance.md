# Skill: find the bottleneck, then raise the slowest science

Loop (never more than one change before re-measuring):
1. `audit` (fx.py bottlenecks --json). Fix in this order: power (low_power, accumulators), then starved groups, then lane jams, then outputs backed up.
2. `science-rates` (gap: until it exists read the last line of docs/autopilot.log: made/s for the seven packs). The target is the slowest pack's rate raised to match the others, then all seven raised together.
3. For the slowest pack trace upstream: lab stock -> pack assemblers -> their intermediates -> raw. The first thing short in the logistic network (`network.get_item_count` negative) is the bottleneck. Use `cells` to add a drone-fed row for it, sized from the recipe: machines = rate * recipe time / crafting speed.
4. After building: wait for the drones to fill requester chests (minutes), re-run `audit`.
Rules: red provider at the end of a line, blue requester at the start, no yellow storage outside trash yards. Every new block adds power: check accumulators before and after.
Known balance levers: steel (foundations, LDS, rocket), electronic circuits (processing units), acid (processing units), utility science needs processing units and low density structure, production science needs electric furnaces and rails.
