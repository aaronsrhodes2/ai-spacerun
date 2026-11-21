"""Two games, never one (the Captain, 2026-11-21: "my live game and the skippy-core test game are treated as separate
games, and purple Skippy doesn't conflate the maps"). Every piece that talks to a game says which: COPILOT_GAME is
'live' (the default: the address in copilot/copilot.env) or 'test' (the test server, scripts/modserver.sh, tunnelled to
127.0.0.1:27116). Plans are kept per game, purple reaches each game through its own MCP server, and a check refuses the
wrong map: the test map always comes from the same seed (modserver.sh SEED), and the live map never does."""
import pathlib

GAMES = ("live", "test")
TEST_SEED = 20261121                                        # scripts/modserver.sh: SEED
TEST_RCON = {"COPILOT_RCON_HOST": "127.0.0.1", "COPILOT_RCON_PORT": "27116", "COPILOT_RCON_PASSWORD_FILE": ".testserver/rcon.pw"}
SERVER = {"live": "skippy-copilot", "test": "skippy-copilot-test"}          # the MCP servers in .mcp.json
ABOUT = {"live": "the Captain's live game on skippy-games, his real factory",
         "test": "the test game on skippy-core, a small fresh map made for checks"}


class WrongGame(Exception):
    """The game that answered is not the one this was set up for."""


def name_of(env):
    name = (env.get("COPILOT_GAME") or "live").strip().lower()
    if name not in GAMES:
        raise WrongGame("COPILOT_GAME is '%s'; it must be live or test" % name)
    return name


def apply(env):
    """The settings for the chosen game: for 'test' the test server's address replaces whatever copilot.env says."""
    env = dict(env)
    if name_of(env) == "test":
        env.update(TEST_RCON)
        env.pop("COPILOT_RCON_PASSWORD", None)
    return env


def check(game, name):
    """(ok, sentence). The map's seed tells the two games apart; a mod too old to say its seed is let through for the
    live game only, and said so."""
    r = game.call("game_info")
    seed = (r.get("result") or {}).get("seed") if r.get("ok") else None
    if seed is None:
        if name == "test":
            return False, "the test game did not say its map seed (game_info), so it cannot be told from the live game"
        return True, "the live game's mod is too old to say its seed; trusting the address"
    if name == "test" and seed != TEST_SEED:
        return False, "this map's seed is %s, not the test map's %s: it is not the test game" % (seed, TEST_SEED)
    if name == "live" and seed == TEST_SEED:
        return False, "this map has the test map's seed %s: it is the test game, not the live one" % seed
    return True, "%s game, map seed %s" % (name, seed)


def title(game):
    """The game's own name, from the save (the player who started it and its map seed, such as 'aaronsrhodes-3141592';
    the Captain, 2026-11-21), or None from a mod too old to say it. The panel's title shows the same name."""
    r = game.call("game_info")
    name = (r.get("result") or {}).get("name") if r.get("ok") else None
    return name if isinstance(name, str) and name else None


def plan_file(logs, name, title=None):
    """Plans are kept per game, so a plan made on one map is never built on the other; by the game's own name when it
    has one."""
    if title:
        return pathlib.Path(logs) / ("plans-%s.json" % "".join(c if c.isalnum() or c in "-_" else "_" for c in title))
    return pathlib.Path(logs) / ("plans.json" if name == "live" else "plans-%s.json" % name)
