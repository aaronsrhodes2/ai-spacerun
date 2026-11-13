"""The asteroid wheels and how the wheel scripts find them. Every wheel script runs its step on each wheel in turn (the Captain,
2026-11-13: one set of scripts, improvements land on both stations). `--only gleba` or `--only nauvis` limits a run to one.
`turrets` is False where the orbit only has chunks (Nauvis): nothing there can hurt the platform."""
import sys

from _game import tools

WHEELS = [("Gleba Wheel", "gleba", True), ("Nauvis Wheel", "nauvis", False)]


def wheels():
    """[(name, planet, surface or None, turrets)] for the wheels this run covers."""
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    out = []
    for name, planet, turrets in WHEELS:
        if only and planet != only:
            continue
        r = tools["run_lua"]("local f=game.forces.player for i,p in pairs(f.platforms) do if p.name=='%s' then rcon.print(p.surface.name) return end end rcon.print('none')" % name).strip()
        out.append((name, planet, None if r == "none" else r, turrets))
    return out


def create(name, planet):
    return tools["run_lua"]("local f=game.forces.player for i,p in pairs(f.platforms) do if p.name=='%s' then rcon.print(p.surface.name..' exists') return end end "
                            "local p=f.create_space_platform{name='%s',planet='%s',starter_pack='space-platform-starter-pack'} p.apply_starter_pack() "
                            "p.surface.request_to_generate_chunks({0,0},20) p.surface.force_generate_chunk_requests() rcon.print(p.surface.name..' created')" % (name, name, planet))


def place_all(ents, surface, apply):
    """Place in batches of 400; returns (placed, failures). Entities named in `skip` are left out by the caller."""
    import json
    ok = bad = 0
    for i in range(0, len(ents), 400):
        r = json.loads(tools["place_entities"](json.dumps(ents[i:i + 400]), surface=surface, dry_run=not apply))
        f = r.get("failed") or []
        ok += r.get("placed", 0)
        bad += len(f)
        if f:
            print("failed", json.dumps(f)[:260])
    return ok, bad


def lay_foundation(tiles, surface):
    ts = sorted(tiles)
    for i in range(0, len(ts), 4000):                    # an RCON command is limited to 65,535 characters
        part = ",".join("{%d,%d}" % t for t in ts[i:i + 4000])
        tools["run_lua"]("local s=game.surfaces['%s'] local add={} for _,p in pairs({%s}) do add[#add+1]={name='space-platform-foundation',position=p} end s.set_tiles(add) rcon.print(#add)" % (surface, part))
    return len(ts)
