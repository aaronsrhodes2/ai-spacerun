"""
Standard blocks: a block is a function from an anchor to entities PLUS a declared list of ports.

The ports are the contract. Every belt in a row flows EAST, so a block's west-face ports line up
with the east-face ports of the block before it, and blocks chain by simply abutting. After a
build, check_ports() reads the game and confirms every declared port tile really holds the belt
it promises, so a missing link is reported instead of found by eye.

AssemblerRow (n assemblers of one recipe), rows of tiles, y grows south:

    y0        output belt O       flows east, collects products
    y0+1      output inserters    (pick south from the machine, drop north on O)
    y0+2..4   machines            3x3, pitch 3, no gaps
    y0+5      input inserters     normal one picks belt A, long one picks belt B
    y0+6      belt A              flows east
    y0+7      belt B              flows east
    poles     small poles at machine offset 2 in both inserter rows

    ports (west face = x, east face = x + 3n): A, B, O at rows y0+6, y0+7, y0
"""
from dataclasses import dataclass, field

N, E, S, W = 0, 4, 8, 12
AM2 = "assembling-machine-2"
ROW_HEIGHT = 8


@dataclass
class Port:
    name: str
    x: int            # tile of the belt on the block's WEST face
    y: int
    role: str         # "in" (consumed here), "out" (produced here), "through"
    item: str = ""


@dataclass
class Block:
    name: str
    x: int
    y: int
    width: int
    height: int
    entities: list = field(default_factory=list)
    ports: list = field(default_factory=list)

    def east_face(self, port):
        return (self.x + self.width, port.y)


def _belt(x, y):
    return {"name": "transport-belt", "x": x + 0.5, "y": y + 0.5, "direction": E}


def _put(name, x, y, direction=0, w=1, h=1, recipe=None):
    e = {"name": name, "x": x + w / 2, "y": y + h / 2, "direction": direction}
    if recipe:
        e["recipe"] = recipe
    return e


def flipped(entities, y0):
    """Mirror an 8-row block top-to-bottom within rows y0..y0+7 (inserters swap N/S)."""
    out = []
    for e in entities:
        e = dict(e)
        e["y"] = 2 * y0 + ROW_HEIGHT - e["y"]
        if "inserter" in e["name"]:
            e["direction"] = {N: S, S: N}.get(e["direction"], e["direction"])
        out.append(e)
    return out


def assembler_row(x, y, recipe, n, inputs=("", ""), output="", machine=AM2, name=None, flip=False, o_west=False):
    """n machines making `recipe`. inputs = (item on belt A, item on belt B), output = item on O.
    flip=True mirrors the row top-to-bottom (O at the bottom, A and B above): rows can then share an O belt."""
    ya, yb, yo = y + 6, y + 7, y
    ents = []
    for dx in range(3 * n):
        for ty in (ya, yb, yo):
            ents.append(_belt(x + dx, ty))
    for i in range(n):
        x0 = x + 3 * i
        ents.append(_put(machine, x0, y + 2, w=3, h=3, recipe=recipe))
        ents.append(_put("inserter", x0, y + 5, S))                  # picks belt A (south), drops into machine
        ents.append(_put("long-handed-inserter", x0 + 1, y + 5, S))  # picks belt B (2 south)
        ents.append(_put("inserter", x0 + 1, y + 1, S))              # picks machine (south), drops on O
        ents.append(_put("small-electric-pole", x0 + 2, y + 5))
        ents.append(_put("small-electric-pole", x0 + 2, y + 1))
    ports = [Port("A", x, ya, "in", inputs[0]), Port("B", x, yb, "in", inputs[1]),
             Port("O", x, yo, "out", output)]
    if o_west:                                   # output belt flows toward the bus instead of away from it
        for e in ents:
            if e["name"] == "transport-belt" and int(e["y"] - 0.5) == y:
                e["direction"] = 12
    if flip:
        ents = flipped(ents, y)
        for p in ports:
            p.y = 2 * y + ROW_HEIGHT - 1 - p.y
    return Block(name or f"{recipe}-row", x, y, 3 * n, ROW_HEIGHT, ents, ports)


def footprint(entities):
    """Tiles an entity list covers, as {tile: name}; raises on any overlap."""
    taken = {}
    big = {AM2: (3, 3), "assembling-machine-3": (3, 3)}
    for e in entities:
        w, h = big.get(e["name"], (1, 1))
        x0, y0 = int(e["x"] - w / 2), int(e["y"] - h / 2)
        for i in range(w):
            for j in range(h):
                t = (x0 + i, y0 + j)
                if t in taken:
                    raise ValueError(f"{e['name']} overlaps {taken[t]} at {t}")
                taken[t] = e["name"]
    return taken


def chain_ok(a, b):
    """True when block b abuts block a so every shared port lines up (same rows, b starts at a's east face)."""
    if b.x != a.x + a.width:
        return False
    rows_a = {p.name: p.y for p in a.ports}
    return all(rows_a.get(p.name, p.y) == p.y for p in b.ports)


def check_ports(tools, block):
    """Read the game: every port tile must hold a belt flowing east. Returns a list of problems."""
    import json
    problems = []
    for p in block.ports:
        for tx in (p.x, p.x + block.width - 1):
            r = json.loads(tools["run_lua"](
                f"local b=game.surfaces.nauvis.find_entity('transport-belt',{{{tx+0.5},{p.y+0.5}}}) "
                f"rcon.print(helpers.table_to_json({{ok=(b~=nil and b.direction==defines.direction.east)}}))"))
            if not r.get("ok"):
                problems.append(f"{block.name} port {p.name} missing or not east-flowing at {tx},{p.y}")
    return problems
