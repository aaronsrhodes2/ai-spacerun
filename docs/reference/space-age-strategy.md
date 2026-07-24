# Space Age strategy reference

Sourced from a 101-agent deep-research pass (2026-07-24), adversarially
verified (25 claims checked, 24 confirmed, 1 refuted — noted below). Primary
sources: official wiki (wiki.factorio.com), official Lua API docs, FFF-376,
Factorio forums; supplemented by community guides. Full findings/citations:
see `docs/progress.md` 2026-07-24 entry, or re-run via the `deep-research`
skill for the raw report.

## Recommended planet order

**Vulcanus → Fulgora → Gleba → Aquilo → Solar System Edge.**

- **Vulcanus first**, specifically because the **Foundry**'s compounding
  efficiency gains make every later planet's buildout easier — confidence:
  medium (single strong blog source, informally cross-corroborated; treat as
  community consensus, not a rule the game enforces).
- **Fulgora vs. Gleba second is genuinely debated** among experienced
  players (a Factorio-forums thread exists specifically arguing reverse
  order) — don't treat "Fulgora then Gleba" as settled.
- **Aquilo is last by design** — it's the harshest planet and gates the
  actual ending.
- ⚠️ **One claim was checked and refuted**: "Foundry gives 225% efficiency
  and big mining drills run 5x speed with 50% less depletion" — voted 1-2,
  do not rely on this specific figure.

## Victory condition

Reaching the **Solar System Edge** (100,000 km out from Aquilo) is the
actual win condition — arriving triggers the win screen and unlocks
uploading to the "Galaxy of Fame." **Confidence: high**, multiple
primary-source (official wiki) confirmations.

- Gated behind a dedicated **solar system edge** research, which itself
  requires prerequisite tech from **all three** prior planets (Gleba: heating
  towers + advanced asteroid processing; Vulcanus: asteroid reprocessing;
  Fulgora: electromagnetic science pack) plus rocket turrets — meaning all
  four planets are mandatory, sequential gates, not optional side content.
- **Known gotcha** (forums, pre-2.0.25): the win only triggers if "Solar
  system edge" is explicitly **set as the space platform's destination** —
  merely flying past the location did not trigger it for some players before
  a bug was addressed. Set it as an explicit destination.
- Beyond the edge (4,000,000 km further) sits the **Shattered Planet** — not
  required to win, post-victory infinite-research content only.

## Planet-by-planet mechanics

| Planet | Defining challenge | Signature building |
|---|---|---|
| **Vulcanus** | Lava processing instead of ore mining in places; molten-metal casting | **Foundry** — 5x5, Vulcanus-exclusive to *craft* (usable elsewhere once shipped), 50% built-in productivity, base crafting speed 4, 2500 kW, 4 module slots. Converts ore+lava to molten iron/copper, casts plates/gears/pipes/cables at higher efficiency than furnaces. |
| **Fulgora** | **No minable ore patches at all** — production is 100% built on recycling scrap from ruins | **Recycler** (scrap processing) + **Electromagnetic Plant** — 4x4, Space-Age-exclusive, crafting speed 2, 5 module slots, 2 MW. Recipe: 150 holmium plate + 50 processing units + 50 refined concrete + 50 steel plate (10s). Holmium is itself Fulgora-derived (scrap + fulgorite deposits). |
| **Gleba** | Biological economy with **spoilage** — products expire (1 min–2 hrs), forcing throughput over stockpiling | **Biochamber** — runs on **Nutrients**, not electricity (0.25 nutrients/s active, 2 MJ/nutrient = 4s runtime), 4 module slots, base speed 2, built-in 50% productivity. Built from 20 iron plate, 5 electronic circuit, 5 nutrients, 1 pentapod egg, 1 landfill. |
| **Aquilo** | No native iron/copper/stone (only crude oil); ~1% solar efficiency; **freeze mechanic** — buildings stop below a heat threshold without heat pipes/heating towers/nuclear reactors | **Cryogenic Plant** — 5x5, 1.5 MW, 8 module slots, **no** innate productivity bonus (unlike the other three signature buildings). Specialized chemical plant for fluoroketone, fusion power cells, railguns, cryogenic science packs. Lithium recipe (50 ammonia + 1 holmium plate + 50 lithium brine → 5 lithium, 20s) is effectively Aquilo-locked since ammonia/lithium brine can't be barreled — holmium plate must be imported from Fulgora. |

## Open questions (not resolved by this research pass — investigate before relying on them)

- **Space platform logistics** (thruster fuel, hub tiers, platform speed
  requirements for inter-planet travel) — not covered by this pass at all.
  Needed before actually planning travel between planets.
- **Fulgora-vs-Gleba ordering** — how firm is this among high-level
  players, and does an AI-driven playthrough's risk profile (spoilage
  failure is arguably worse for scripted play than for a human paying
  attention) argue for a different choice than human-guide consensus?
- **The `craft-item` research-trigger / LuaPlayer question is still open.**
  See `modding-notes.md` — official docs (Lua API reference + FFF-376) are
  confirmed *silent* on whether a non-player character can satisfy these
  triggers, which neither confirms nor refutes our in-game observation that
  it didn't work. No documented workaround exists. Treat "have the human
  player hand-craft trigger items" as the working assumption until proven
  otherwise, not as a confirmed requirement.
