"""Round 7: bridge the isolated substation at (-36,-467) to the main grid with a substation at (-53,-472). Dry run unless --apply."""
import json
import sys

from _game import tools

ents = [{"name": "substation", "x": -53, "y": -472}]
dry = "--apply" not in sys.argv
res = json.loads(tools["place_entities"](json.dumps(ents), surface="nauvis", dry_run=dry))
print("DRY RUN" if dry else "APPLY", {k: v for k, v in res.items() if k in ("failed", "placed", "errors")})
