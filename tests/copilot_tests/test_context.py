"""Keeping the model's context small (the Captain, 2026-11-13: a local model has about 130k of context, so the skill, the
joints, the planners and the game knowledge must fit comfortably). What a model always carries is the skill text and the
tool descriptions. Everything else is fetched when asked for: game facts by lookup, the joints by their catalogue, plans
by id. These tests hold that line."""
import json
import pathlib

from copilot.agent import MAX_RESULT, MEMORY_CHARS, MEMORY_TURNS, Agent
from copilot.models import schema
from copilot.plan import joints
from copilot.toolbox import Toolbox
from copilot.tools import LocalTools
from fakes import FakeGame, FakeModel
from luamod import LuaMod
from test_bridge_with_mod import LuaGame

ROOT = pathlib.Path(__file__).resolve().parents[2]
WINDOW = 130000                 # tokens
TOKEN = 4                       # characters, roughly


def fixed_context():
    game = LuaGame(LuaMod())
    box = Toolbox(game, LocalTools(game))
    tools = json.dumps(schema(box.offered))
    prompt = (ROOT / "copilot" / "prompt.md").read_text(encoding="utf-8")
    return len(prompt) // TOKEN, len(tools) // TOKEN, box


def test_what_a_model_always_carries_stays_under_a_tenth_of_the_window():
    skill, tools, _ = fixed_context()
    assert skill + tools < WINDOW // 10, "the skill (%d tokens) and tool descriptions (%d) have outgrown a tenth of a 130k window" % (skill, tools)
    assert skill < 2500, "the skill text alone is %d tokens: condense it" % skill


def test_no_single_tool_description_runs_away():
    _, _, box = fixed_context()
    sizes = sorted(((len(json.dumps(t)) // TOKEN, t["function"]["name"]) for t in schema(box.offered)), reverse=True)
    assert sizes[0][0] < 700, "the description of %s is %d tokens" % (sizes[0][1], sizes[0][0])


def test_the_joints_are_not_in_the_model_until_it_asks():
    skill = (ROOT / "copilot" / "prompt.md").read_text(encoding="utf-8")
    _, _, box = fixed_context()
    carried = skill + json.dumps(schema(box.offered))
    for name, spec in joints.JOINTS.items():
        assert spec["solves"] not in carried, "the joint '%s' is spelled out in what the model always carries" % name
    catalogue = json.dumps(joints.catalogue())
    assert len(catalogue) // TOKEN < 3000                           # and the whole catalogue, when asked for, is small


def test_no_game_facts_are_written_into_the_skill():
    """Recipes and numbers come from the game by lookup. The skill may name one item as an example of the name format."""
    skill = (ROOT / "copilot" / "prompt.md").read_text(encoding="utf-8")
    for fact in ("copper-cable", "iron-plate", "assembling-machine", "0.75", "steam-engine", "crude-oil"):
        assert fact not in skill, "the skill carries the game fact '%s'" % fact


def test_one_tool_result_cannot_flood_the_context():
    assert MAX_RESULT // TOKEN <= 2000
    game = FakeGame({"diagnose": {"ok": True, "result": "x" * 400000}})
    agent = Agent(game, FakeModel([[("diagnose", {})], "ok"]))
    agent.handle("q", light=False)
    assert len(agent.model.seen[1][-1]["content"]) < MAX_RESULT + 100


def test_each_turn_starts_fresh_but_remembers_what_was_said():
    agent = Agent(FakeGame(), FakeModel(["I suggest electronics. Shall I queue it?", [("diagnose", {})], "Queued."]))
    agent.handle("research has stopped", who="game", light=False)
    agent.handle("yes, do that", light=False)
    second = agent.model.seen[1]
    assert len(second) == 2                                         # system and the new line: no old tool results carried along
    note = second[0]["content"]
    assert "Earlier in this conversation" in note and "I suggest electronics. Shall I queue it?" in note and "you were told (game): research has stopped" in note
    assert second[1]["content"] == "yes, do that"
    first = agent.model.seen[0][0]["content"]
    assert "Earlier in this conversation" not in first              # nothing to remember on the first turn


def test_memory_is_words_only_short_and_bounded():
    replies = []
    for i in range(10):
        replies += [[("diagnose", {})], "answer %d " % i + "y" * 2000]
    game = FakeGame({"diagnose": {"ok": True, "result": "TOOL-RESULT-" + "z" * 3000}})
    agent = Agent(game, FakeModel(replies))
    for i in range(10):
        agent.handle("question %d " % i + "x" * 2000, light=False)
    assert len(agent.memory) == MEMORY_TURNS
    note = agent.remembered()
    assert "question 9" in note and "question 3" not in note and "TOOL-RESULT" not in note
    assert len(note) <= MEMORY_TURNS * (2 * MEMORY_CHARS + 60) + 80
    assert len(note) // TOKEN < 2000


def test_a_turn_that_failed_is_not_remembered_as_an_answer():
    agent = Agent(FakeGame(), FakeModel([RuntimeError("down"), "Hello."]))
    agent.handle("first", light=False)
    agent.handle("second", light=False)
    assert agent.memory == [("player", "second", "Hello.")]
