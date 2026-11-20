"""The cron: timed jobs listed in one place with their purpose and what good and bad runs look like; failing and
recovering jobs become news for the model."""
import pytest

from luamod import LuaMod

GHOSTS = {"name": "ghosts-to-requests", "tool": "ghost_needs", "args": {"surface": "nauvis"}, "every_minutes": 5,
          "purpose": "the game turns no ghost into a request", "expect_ok": "a list per surface",
          "expect_bad": "an error: look at the landing pad", "retire_when": "the base requests its building goods itself"}


@pytest.fixture
def mod():
    return LuaMod()


def test_a_job_runs_on_its_timer_and_says_how_it_went(mod):
    r = mod.result("cron_add", GHOSTS)
    assert r["job"]["minutes_to_next"] == 5 and r["job"]["runs"] == 0
    mod.tick(5 * 3600 + 60)
    job = mod.result("cron_list")["jobs"][0]
    assert job["runs"] == 1 and job["last_ok"] is True and job["purpose"] == GHOSTS["purpose"] and job["retire_when"]
    mod.tick(5 * 3600)
    assert mod.result("cron_list")["jobs"][0]["runs"] == 2


def test_pause_run_now_and_remove(mod):
    mod.result("cron_add", GHOSTS)
    mod.result("cron_change", {"name": "ghosts-to-requests", "action": "pause"})
    mod.tick(6 * 3600)
    assert mod.result("cron_list")["jobs"][0]["runs"] == 0
    r = mod.result("cron_change", {"name": "ghosts-to-requests", "action": "run_now"})
    assert r["answer"]["ok"] and r["job"]["runs"] == 1
    mod.result("cron_change", {"name": "ghosts-to-requests", "action": "remove"})
    assert mod.result("cron_list")["hint"] == "no timed jobs"


def test_failing_and_recovering_are_news(mod):
    mod.result("cron_add", dict(GHOSTS, name="bad", args={"surface": "mars"}, every_minutes=1))
    mod.result("cron_change", {"name": "bad", "action": "run_now"})
    news = mod.result("events_read")["events"]
    assert news[-1]["kind"] == "cron_failing" and "no surface named" in news[-1]["summary"] and news[-1]["expect_bad"]
    mod.result("cron_change", {"name": "bad", "action": "run_now"})
    assert len(mod.result("events_read")["events"]) == 1                              # told once, not every run
    mod.result("cron_add", dict(GHOSTS, name="bad", args={"surface": "nauvis"}, every_minutes=1, replace=True))
    mod.run("storage.cron.bad.last_ok = false")
    mod.result("cron_change", {"name": "bad", "action": "run_now"})
    assert mod.result("events_read")["events"][-1]["kind"] == "cron_recovered"


def test_bad_jobs_are_refused(mod):
    assert "no tool named" in mod.call("cron_add", dict(GHOSTS, tool="nope"))["error"]
    assert "does not run on a timer" in mod.call("cron_add", dict(GHOSTS, tool="say", args={}))["error"]
    assert "no parameter" in mod.call("cron_add", dict(GHOSTS, args={"planet": "x"}))["error"]
    assert "at least 1" in mod.call("cron_add", dict(GHOSTS, every_minutes=0))["error"]
    mod.result("cron_add", GHOSTS)
    assert "already a job" in mod.call("cron_add", GHOSTS)["error"]


def test_an_external_job_takes_reports_and_goes_overdue(mod):
    job = {k: v for k, v in GHOSTS.items() if k not in ("tool", "args")}
    mod.result("cron_add", dict(job, name="quality-upgrades", external=True, every_minutes=10, purpose="scripts/upgrade_quality.py after research"))
    mod.result("cron_report", {"name": "quality-upgrades", "ok": True, "summary": "upgraded 40 machines"})
    j = mod.result("cron_list")["jobs"][0]
    assert j["kind"] == "external" and j["last_summary"] == "upgraded 40 machines" and "overdue" not in j
    mod.tick(21 * 3600)
    assert mod.result("cron_list")["jobs"][0]["overdue"] is True
    mod.result("cron_add", GHOSTS)
    assert "run by the mod itself" in mod.call("cron_report", {"name": "ghosts-to-requests", "ok": True, "summary": "s"})["error"]
