"""`python -m copilot --check`: the setup, one step at a time, in plain words. Written for someone who has never
connected an AI to anything: every step says what it tried, whether it worked, and if not, the one thing to do about it.
It stops at the first step that fails, because the later ones depend on it."""
import pathlib


def run_check(env, out=print, game_factory=None, agent_factory=None):
    """Returns True when everything works. The factories are for tests; by default the real ones are used."""
    from . import __main__ as main
    from .purple import SourceError
    from .tools import LocalTools
    game_factory = game_factory or main.game_from
    agent_factory = agent_factory or main.agent_from
    step = [0]

    def ok(text):
        step[0] += 1
        out("  %d. OK   %s" % (step[0], text))

    def bad(text, fix):
        step[0] += 1
        out("  %d. STOP %s" % (step[0], text))
        out("          What to do: %s" % fix)
        return False

    out("Skippy Copilot setup check")
    if not (main.HERE / "copilot.env").exists() and not env.get("COPILOT_SOURCE") and not env.get("COPILOT_PROVIDER"):
        return bad("there is no settings file yet", "copy copilot/copilot.env.example to copilot/copilot.env and fill in the three parts marked there")
    ok("settings found")

    # 1. the game
    try:
        game = game_factory(env)
    except main.SetupError as e:
        return bad("the game's settings are incomplete: %s" % e, "fill in the RCON lines in copilot.env")
    r = game.call("tools")
    if not r.get("ok"):
        err = r.get("error") or ""
        if "could not be reached" in err:
            return bad("the game does not answer on %s:%s" % (env.get("COPILOT_RCON_HOST", "127.0.0.1"), env.get("COPILOT_RCON_PORT", "27015")),
                       "start the game as a server (or host a multiplayer game) with RCON switched on, and check the port and password match copilot.env")
        return bad("the game answers, but the Skippy Copilot mod does not: %s" % err, "enable the mod 'Skippy Copilot' in the game's mod list and load the save again")
    ok("the game answers and the mod is loaded (%d tools)" % len(r["result"]))
    state = game.call("avatar")
    if state.get("ok"):
        ok("the mod is in '%s' mode: the assistant %s" % (state["result"].get("mode"), state["result"].get("mode_means")))

    # 2. the AI source
    try:
        kind = main.source_of(env)
    except main.SetupError as e:
        return bad(str(e), "set COPILOT_SOURCE in copilot.env")
    ok("the AI source is '%s': one source for every turn" % kind)
    try:
        agent = agent_factory(env, game, LocalTools(game), None)
    except (main.SetupError, SourceError) as e:
        return bad(str(e), "fix that line in copilot.env")
    purple = getattr(agent, "purple", None)
    if purple is not None:
        ready, why = purple.health()
        if not ready:
            return bad("purple Skippy is not ready: %s" % why, "start purple-mcp on this computer (SkippyTel/services/purple-mcp), or fix what is named above")
        ok("purple Skippy answers, workspace '%s'" % purple.workspace)

    # 3. one real question, answered from the game
    out("  ...asking the AI one question (this can take a minute the first time)")
    answer, outcome, stats = agent.handle("What does it take to make an iron gear wheel? Look it up and answer in one sentence.", "check", light=False)
    if not answer:
        fix = getattr(agent, "last_error", None) or "check that the source's address, key and model name in copilot.env are right, and that the server is running"
        return bad("the AI did not answer (%s)" % outcome, fix)
    ok("the AI answered: %s" % answer.strip().split("\n")[0][:160])
    if stats.get("calls", 0) < 1:
        return bad("the AI answered without looking anything up in the game",
                   "this model may not be able to use tools; choose one that supports tool calling" if purple is None
                   else "the workspace may not have the skippy-copilot MCP server; see the README, 'Purple Skippy'")
    ok("it looked the answer up in the game (%d tool calls)" % stats["calls"])
    out("Everything works. Start it with:  python -m copilot")
    return True
