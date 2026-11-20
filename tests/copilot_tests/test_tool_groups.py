"""Tool groups: a small model carries the core tools and opens a group when a turn needs it; a grouped tool called by name
opens its group by itself; every turn starts with the core again."""
from copilot.agent import Agent
from copilot.toolbox import GROUP_OF, GROUPS, Toolbox
from copilot.tools import LocalTools
from fakes import FakeModel
from luamod import LuaMod
from test_bridge_with_mod import LuaGame


def agent(replies, groups=True):
    game = LuaGame(LuaMod())
    return Agent(game, FakeModel(replies), local=LocalTools(game), groups=groups)


def test_every_grouped_tool_exists_and_none_is_in_two_groups():
    game = LuaGame(LuaMod())
    names = {t["name"] for t in Toolbox(game, LocalTools(game)).offered}
    listed = [n for _, (_, members) in GROUPS.items() for n in members]
    assert sorted(set(listed) - names) == [] and len(listed) == len(set(listed))


def test_a_turn_starts_with_the_core_and_the_menu():
    a = agent(["hello"])
    a.handle("hi", light=False)
    first = set(a.model.offered[0])
    assert "open_tools" in first and "lookup" in first and "designs" in first and "cron_list" in first
    assert not first & set(GROUP_OF)


def test_opening_a_group_offers_it_from_the_next_step_for_this_turn_only():
    a = agent([[("open_tools", {"group": "designs"})], "ok", "again"])
    a.handle("save that as a design", light=False)
    assert "design_save" not in a.model.offered[0] and "design_save" in a.model.offered[1]
    assert a.model.seen[1][-1]["content"].count("design_save") == 1                  # the answer names what was opened
    a.handle("next", light=False)
    assert "design_save" not in a.model.offered[2]                                   # a new turn starts small again


def test_a_grouped_tool_called_by_name_runs_and_opens_its_group():
    a = agent([[("ghost_needs", {"surface": "nauvis"})], "done"])
    a.handle("what do the ghosts lack", light=False)
    assert '"ok": true' in a.model.seen[1][-1]["content"] and "ghost_requests" in a.model.offered[1]


def test_an_unknown_group_is_answered_with_the_groups():
    a = agent([[("open_tools", {"group": "magic"})], "ok"])
    a.handle("x", light=False)
    shown = a.model.seen[1][-1]["content"]
    assert "no group named 'magic'" in shown and "designs" in shown


def test_groups_off_offers_every_tool():
    a = agent(["hello"], groups=False)
    a.handle("hi", light=False)
    assert "open_tools" not in a.model.offered[0] and "design_save" in a.model.offered[0]
