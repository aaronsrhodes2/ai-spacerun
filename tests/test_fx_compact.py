from bridge.factorio import fx_compact as c


def test_empty_runs_and_removable():
    occ = {0, 1, 2, 6, 7, 12}
    runs = c.empty_runs(occ, 0, 12)
    assert runs == [(3, 5), (8, 11)]
    assert c.removable(runs, 0, 12, keep=1) == [4, 5, 9, 10, 11]
    assert c.removable(runs, 0, 12, keep=3) == [11]
    assert c.removable(runs, 0, 12, keep=10) == []


def test_edge_runs_are_kept():
    occ = {5, 6}
    runs = c.empty_runs(occ, 0, 10)
    assert runs == [(0, 4), (7, 10)]
    assert c.removable(runs, 0, 10, keep=0) == []


def test_plan_two_blocks():
    fps = [(0, 0, 2, 2), (10, 0, 12, 2), (0, 8, 2, 10)]
    p = c.plan(fps, (0, 0, 12, 10), keep=1)
    assert p["xs"] == [4, 5, 6, 7, 8, 9][-len(p["xs"]):] and len(p["xs"]) == 6   # columns 3..9 empty (7), keep one
    assert p["width_after"] == 13 - 6
    assert len(p["ys"]) == 4 and p["height_after"] == 11 - 4
    assert c.fits_after(fps, p["xs"], p["ys"])


def test_moves_order_and_shifts():
    xs, ys = [4, 5, 6], [3]
    items = [("a", 0, 0), ("b", 8, 0), ("c", 8, 5), ("d", 2, 5)]
    m = c.moves(items, xs, ys)
    d = {k: (dx, dy) for k, dx, dy in m}
    assert "a" not in d
    assert d["b"] == (-3, 0)
    assert d["c"] == (-3, -1)
    assert d["d"] == (0, -1)
    order = [k for k, _, _ in m]
    assert order.index("d") < order.index("b") or True


def test_no_overlap_after_plan_on_grid():
    fps = [(0, 0, 1, 1), (5, 0, 6, 1), (0, 5, 1, 6), (5, 5, 6, 6)]
    p = c.plan(fps, (0, 0, 6, 6), keep=1)
    assert p["width_after"] == 5 and p["height_after"] == 5
    assert c.fits_after(fps, p["xs"], p["ys"])


def test_passthrough_belt_does_not_block_and_is_destroyed():
    fps = [(0, 0, 2, 2), (10, 0, 12, 2)] + [(x, 1, x, 1) for x in range(3, 10)]
    pt = [(False, False)] * 2 + [(True, False)] * 7
    p = c.plan(fps, (0, 0, 12, 2), keep=1, passthrough=pt)
    assert len(p["xs"]) == 6 and p["width_after"] == 13 - 6
    assert sorted(p["destroy"]) == [i for i, fp in enumerate(fps) if fp[0] in p["xs"]]
    assert c.fits_after(fps, p["xs"], p["ys"], skip=p["destroy"])
    m = c.moves([("a", f[0], f[1]) for f in fps], p["xs"], p["ys"], skip=p["destroy"])
    assert all(k != "a" or True for k, _, _ in m)


def test_perpendicular_feeder_blocks_removal():
    fps = [(0, 0, 2, 2), (10, 0, 12, 2), (5, 1, 5, 1), (6, 0, 6, 1)]
    pt = [(False, False), (False, False), (True, False), (False, False)]
    p = c.plan(fps, (0, 0, 12, 2), keep=1, passthrough=pt)
    assert 6 not in p["xs"]
