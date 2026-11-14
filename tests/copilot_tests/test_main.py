import copilot.__main__ as main
from fakes import FakeGame


def test_long_answers_go_out_in_pieces():
    game = FakeGame()
    main.say(game, "a" * 800)
    assert [len(a["text"]) for a in game.named("say")] == [380, 380, 40]


def test_news_prompt_carries_the_unlocks_and_the_note():
    p = main.news_prompt({"technology": "automation-2", "unlocks_recipes": ["assembling-machine-2"], "design_note": "Faster machines."})
    assert "automation-2" in p and "assembling-machine-2" in p and "Faster machines." in p and "nothing" in p
    assert "none written" in main.news_prompt({"technology": "x"})


def test_settings_file_does_not_override_the_environment(tmp_path, monkeypatch):
    (tmp_path / "copilot.env").write_text("# comment\nCOPILOT_MODEL=\"from-file\"\nCOPILOT_PROVIDER=openai\n", encoding="utf-8")
    monkeypatch.setattr(main, "HERE", tmp_path)
    monkeypatch.setenv("COPILOT_MODEL", "from-env")
    monkeypatch.delenv("COPILOT_PROVIDER", raising=False)
    env = main.settings()
    assert env["COPILOT_MODEL"] == "from-env" and env["COPILOT_PROVIDER"] == "openai"
