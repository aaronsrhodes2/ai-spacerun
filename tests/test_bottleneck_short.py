"""The ranker's `short` rule (2026-11-17): a shortage must be sustained and not covered by a rising stock. No game needed."""
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.modules.setdefault("_game", types.SimpleNamespace(tools={}))      # the ranker imports the live tools; the rule itself needs none

import worst_bottleneck as W  # noqa: E402


def test_one_minute_burst_is_not_a_shortage():
    # electronic circuits, 2026-11-17: 62/137 in the last minute, 51/50 over the hour
    assert not W.is_short(62.5, 136.7, 51.1, 49.6)


def test_sustained_deficit_is_a_shortage():
    assert W.is_short(60, 130, 55, 120)


def test_hour_deficit_but_quiet_minute_is_not_reported():
    assert not W.is_short(60, 40, 55, 120)


def test_rising_stock_cancels_the_finding():
    # iron plate: 58 made, 87 used for hours, but imports raise the stock
    assert not W.is_short(58, 87, 58, 87, rising=True)


def test_stock_trend_needs_an_old_enough_reference():
    store = {}
    assert not W.stock_rising("iron-plate", 1000, now=0, store=store)          # first reading: no trend yet
    assert not W.stock_rising("iron-plate", 2000, now=100, store=store)        # too soon
    assert W.stock_rising("iron-plate", 2000, now=400, store=store)            # 400 s later, higher: rising
    assert not W.stock_rising("iron-plate", 900, now=400, store=store)         # lower: falling
    assert store["iron-plate"] == [0, 1000]                                     # reference kept


def test_reference_is_replaced_after_an_hour():
    store = {"x": [0, 500]}
    assert W.stock_rising("x", 600, now=3700, store=store)
    assert store["x"] == [3700, 600]
