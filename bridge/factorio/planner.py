"""
Layout planner: turns "belt from A to B" and "row of drills here" into entity lists.

Pure Python with no game connection, so everything here can be unit tested. It
works from a map_grid snapshot, and place_entities applies the result.

Tile coordinates are integers. An entity's position is computed from the tiles it
covers. Facts below were measured on the live game (2.1.24):
  - An inserter's `direction` is its PICKUP side. It drops on the opposite side.
  - A burner drill facing north drops onto the tile above its left column; facing
    south it drops onto the tile below its right column.
"""

import heapq
import math

N, E, S, W = 0, 4, 8, 12
VECTORS = {N: (0, -1), E: (1, 0), S: (0, 1), W: (-1, 0)}
_OPPOSITE = {N: S, S: N, E: W, W: E}
_IMPASSABLE = set("~K?E")
_RESOURCES = set("ickosu")


class PlanError(Exception):
    pass


def direction_between(a, b):
    """Direction of the step from tile a to the adjacent tile b."""
    delta = (b[0] - a[0], b[1] - a[1])
    for d, v in VECTORS.items():
        if v == delta:
            return d
    raise PlanError(f"{a} and {b} are not adjacent")


class Grid:
    """A map_grid snapshot: {"x1":..., "y1":..., "rows":[...]}."""

    def __init__(self, snapshot):
        self.x1, self.y1 = snapshot["x1"], snapshot["y1"]
        self.rows = snapshot["rows"]

    def at(self, x, y):
        col, row = x - self.x1, y - self.y1
        if 0 <= row < len(self.rows) and 0 <= col < len(self.rows[row]):
            return self.rows[row][col]
        return "?"

    def all_ore(self, ore, x, y, w=2, h=2):
        return all(self.at(x + i, y + j) == ore for i in range(w) for j in range(h))


class Plan:
    """Entities to place, plus which tiles they take."""

    def __init__(self, grid):
        self.grid = grid
        self.entities = []
        self.taken = {}

    def _take(self, tiles, label):
        for t in tiles:
            if t in self.taken:
                raise PlanError(f"{label} at {t} overlaps {self.taken[t]}")
            if self.grid.at(*t) in _IMPASSABLE:
                raise PlanError(f"{label} at {t} is on impassable tile '{self.grid.at(*t)}'")
        for t in tiles:
            self.taken[t] = label

    def reserve(self, x1, y1, x2, y2, label="reserved"):
        """Keep tiles free of everything, inclusive of both corners."""
        self._take([(x, y) for x in range(x1, x2 + 1) for y in range(y1, y2 + 1)], label)

    def belt(self, x, y, direction):
        self._take([(x, y)], "belt")
        self.entities.append({"name": "transport-belt", "x": x + 0.5, "y": y + 0.5, "direction": direction})

    def inserter(self, x, y, pickup):
        """Burner inserter taking from the `pickup` side, dropping on the opposite side."""
        self._take([(x, y)], "inserter")
        self.entities.append({"name": "burner-inserter", "x": x + 0.5, "y": y + 0.5, "direction": pickup})

    def drill(self, x, y, direction, ore):
        """Burner drill with top-left tile (x, y). Refuses mixed or missing ore."""
        if not self.grid.all_ore(ore, x, y):
            raise PlanError(f"drill at {x},{y} isn't fully on '{ore}'")
        self._take([(x + i, y + j) for i in range(2) for j in range(2)], "drill")
        self.entities.append({"name": "burner-mining-drill", "x": x + 1, "y": y + 1, "direction": direction})

    def machine(self, name, x, y, w, h, direction=0, recipe=None):
        """Any w-by-h building with top-left tile (x, y)."""
        self._take([(x + i, y + j) for i in range(w) for j in range(h)], name)
        entity = {"name": name, "x": x + w / 2, "y": y + h / 2, "direction": direction}
        if recipe:
            entity["recipe"] = recipe
        self.entities.append(entity)

    def line(self, *points, last_direction=None):
        """Straight belts through corner points. The last tile keeps the final
        direction unless last_direction says otherwise."""
        path = []
        for a, b in zip(points, points[1:]):
            if a[0] != b[0] and a[1] != b[1]:
                raise PlanError(f"line segment {a} to {b} isn't straight")
            step = (0 if a[0] == b[0] else (1 if b[0] > a[0] else -1),
                    0 if a[1] == b[1] else (1 if b[1] > a[1] else -1))
            cur = a
            while cur != b:
                path.append(cur)
                cur = (cur[0] + step[0], cur[1] + step[1])
        path.append(points[-1])
        self._lay(path, last_direction)

    def _lay(self, path, last_direction=None):
        for i, tile in enumerate(path):
            if i + 1 < len(path):
                d = direction_between(tile, path[i + 1])
            elif last_direction is not None:
                d = last_direction
            else:
                d = direction_between(path[i - 1], tile)
            self.belt(tile[0], tile[1], d)

    def route(self, start, start_dir, goal, final_dir):
        """Find and lay a belt from start to goal. Start leaves no earlier than
        start_dir allows (no U-turn), and goal's tile points in final_dir, so it never
        arrives head-on against that direction. Returns the tile path."""
        path = find_path(self, start, start_dir, goal, final_dir)
        self._lay(path, final_dir)
        return path


def find_path(plan, start, start_dir, goal, final_dir):
    """A* over tile and heading. Prefers fewer turns, free ground, and staying off ore."""
    grid, taken = plan.grid, plan.taken

    def tile_cost(x, y):
        ch = grid.at(x, y)
        cost = 1.0
        if ch == "T":
            cost += 1.5
        elif ch == "R":
            cost += 4
        elif ch in _RESOURCES:
            cost += 0.3
        if any((x + vx, y + vy) in taken for vx, vy in VECTORS.values()):
            cost += 0.5
        return cost

    def usable(x, y):
        return (x, y) not in taken and grid.at(x, y) not in _IMPASSABLE

    for tile in (start, goal):
        if not usable(*tile):
            raise PlanError(f"route endpoint {tile} isn't free")

    def heuristic(x, y):
        return abs(x - goal[0]) + abs(y - goal[1])

    first = (start[0], start[1], start_dir)
    best = {first: 0.0}
    came = {}
    heap = [(heuristic(*start), 0.0, first)]
    while heap:
        _, cost, state = heapq.heappop(heap)
        if cost > best.get(state, float("inf")):
            continue
        x, y, heading = state
        if (x, y) == goal and heading != _OPPOSITE[final_dir]:
            path = [(x, y)]
            while state in came:
                state = came[state]
                path.append((state[0], state[1]))
            path.reverse()
            return path
        for d, (vx, vy) in VECTORS.items():
            if d == _OPPOSITE[heading]:
                continue
            nx, ny = x + vx, y + vy
            if not usable(nx, ny):
                continue
            ncost = cost + tile_cost(nx, ny) + (0.0 if d == heading else 0.4)
            nstate = (nx, ny, d)
            if ncost < best.get(nstate, float("inf")):
                best[nstate] = ncost
                came[nstate] = state
                heapq.heappush(heap, (ncost + heuristic(nx, ny), ncost, nstate))
    raise PlanError(f"no route from {start} to {goal}: blocked by terrain or earlier belts")


def batches(items, size=400):
    """Split a list so each place_entities call stays within the RCON limit."""
    return [items[i:i + size] for i in range(0, len(items), size)]


def overlay(plan, x1, y1, x2, y2):
    """Draw the plan on the grid for checking by eye. Belts as arrows, D drill, n inserter."""
    arrows = {N: "^", E: ">", S: "v", W: "<"}
    marks = {}
    for e in plan.entities:
        ex, ey = e["x"], e["y"]
        if e["name"] == "transport-belt":
            marks[(math.floor(ex), math.floor(ey))] = arrows[e["direction"]]
        elif e["name"] == "burner-inserter":
            marks[(math.floor(ex), math.floor(ey))] = "n"
        elif e["name"] == "burner-mining-drill":
            for i in (-1, 0):
                for j in (-1, 0):
                    marks[(int(ex) + i, int(ey) + j)] = "D"
    lines = []
    for y in range(y1, y2 + 1):
        lines.append(f"{y:5d} " + "".join(marks.get((x, y), plan.grid.at(x, y)) for x in range(x1, x2 + 1)))
    return "\n".join(lines)
