"""Operator scripts and the allowances (mod/skippy_allowances.lua): a script that does a relaxed thing asks the game first.

    from _allowance import require
    require("free-upgrades", apply)          # stops the script when the switch is off, if it was going to change anything

The switch lives in the game as the setting skippy-allow-<id> (mod 0.18.0). A game without the mod, or without the setting,
has no switch: that counts as on, exactly as the mod itself reads it, so the live game keeps behaving as before."""
import sys

OFF = "allowance=off"


def check_lua(allow_id):
    return "local s=settings.global['skippy-allow-%s'] rcon.print((s and s.value==false) and '%s' or 'allowance=on')" % (allow_id, OFF)


def allowed(allow_id, run_lua=None):
    """True unless the game has the switch and it is off. `run_lua` takes Lua and returns what it printed."""
    if run_lua is None:
        from _game import tools
        run_lua = tools["run_lua"]
    return OFF not in str(run_lua(check_lua(allow_id)))


def require(allow_id, acting=True, run_lua=None, out=None):
    """Exit when the allowance is off and the script is about to act; a dry run (acting False) always goes on."""
    if acting and not allowed(allow_id, run_lua):
        print("The allowance '%s' is switched off in this game: this script does the relaxed thing, so it stops. "
              "Switch the allowance on (map settings, or set_allowance) to run it." % allow_id, file=out or sys.stderr)
        raise SystemExit(3)
