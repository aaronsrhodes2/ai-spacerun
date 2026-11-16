"""Seed vault release rule (the Captain, 2026-11-16): release only the seeds above the floor, never below it."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from gleba_cell import VAULT_FLOOR, vault_surplus  # noqa: E402


def test_floor_is_repopulation_amount():
    # 21 agricultural towers x 10 seeds per tower request
    assert VAULT_FLOOR == 210


def test_surplus_above_floor():
    assert vault_surplus(800) == 590


def test_floor_is_never_released():
    assert vault_surplus(210) == 0


def test_below_floor_releases_nothing():
    assert vault_surplus(150) == 0
    assert vault_surplus(0) == 0
