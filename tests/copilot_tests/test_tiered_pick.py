from copilot.tiered import pick


def test_a_typed_line_from_a_named_player_is_quick_when_short():
    assert pick("how much copper do we have?", "aaronsrhodes") == "quick"
    assert pick("say ok", "someone") == "quick"


def test_a_named_player_asking_for_a_plan_is_deep():
    assert pick("plan a smelter", "aaronsrhodes") == "deep"
    assert pick("x" * 200, "aaronsrhodes") == "deep"


def test_the_bridges_own_sources_are_deep():
    for who in ("game", "goal", "leg", "check"):
        assert pick("hello", who) == "deep"
