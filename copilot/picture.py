"""A picture after every turn (the Captain, 2026-11-21): a run on skippy-core's headless server draws nothing, so the
picture is drawn here from the mod's own `map`, one coloured square per tile: buildings by kind, belts, ghosts as
outlines, ore, water, the spider. It needs no game client, so it works while the Captain plays. The run page puts each
turn's prompt, answer and picture in order."""
import datetime
import html
import json
import pathlib

from PIL import Image, ImageDraw

CELL = 12                                       # pixels a tile
COLOURS = {
    ".": (52, 46, 36), "~": (30, 70, 110), " ": (10, 10, 14), ":": (95, 110, 130), "t": (40, 80, 35), "r": (90, 85, 80),
    "c": (110, 90, 70), "b": (230, 190, 40), "u": (200, 160, 30), "s": (240, 210, 60), "l": (240, 210, 60),
    "i": (90, 200, 220), "p": (150, 150, 160), "q": (120, 120, 130), "j": (150, 150, 160), "J": (60, 130, 200),
    "K": (130, 130, 140), "A": (160, 120, 80), "F": (180, 90, 60), "M": (110, 140, 90), "L": (230, 230, 240),
    "C": (170, 130, 70), "P": (120, 90, 60), "O": (100, 190, 120), "S": (60, 80, 150), "a": (100, 100, 120),
    "G": (140, 140, 150), "B": (150, 110, 90), "N": (200, 120, 60), "h": (180, 100, 60), "R": (150, 150, 150),
    "X": (220, 60, 60), "T": (200, 70, 70), "W": (190, 190, 190), "g": (200, 200, 100), "E": (90, 160, 220),
    "Z": (230, 230, 240), "D": (210, 210, 220), "Y": (120, 120, 170), "H": (220, 120, 60), "U": (200, 200, 220),
    "y": (170, 170, 190), "@": (255, 170, 0), "&": (255, 140, 0), "!": (255, 40, 40), "#": (140, 120, 100),
}
GHOST = (0, 204, 255)


def where(logs, since, until):
    """The last spot the turn's tool calls named (x and y), from every log written in the turn: the bridge's own and
    the MCP server's that purple's tool calls go through. None when no call named one."""
    spot = None
    for path in logs:
        try:
            lines = pathlib.Path(path).read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for raw in lines:
            try:
                e = json.loads(raw)
                at = datetime.datetime.strptime(e.get("time", ""), "%Y-%m-%d %H:%M:%S").timestamp()
            except (ValueError, TypeError):
                continue
            a = e.get("args") or {}
            if e.get("event") == "tool" and since <= at <= until + 1 and isinstance(a.get("x"), (int, float)) and isinstance(a.get("y"), (int, float)):
                spot = (at, float(a["x"]), float(a["y"]), a.get("surface"))
    return None if spot is None else spot[1:]


def draw(game, x, y, surface=None, width=60, height=40, title=""):
    """The window of the map centred on x,y as an image, or None when the game gives no map."""
    args = {"x": int(x - width // 2), "y": int(y - height // 2), "width": width, "height": height}
    if surface:
        args["surface"] = surface
    r = game.call("map", args)
    if not r.get("ok"):
        return None
    rows = r["result"]["picture"].split("\n")[2:]
    band = 22 if title else 0
    img = Image.new("RGB", (width * CELL, len(rows) * CELL + band), (20, 20, 24))
    pen = ImageDraw.Draw(img)
    if title:
        pen.text((6, 5), title[:110], fill=(230, 230, 230))
    for j, row in enumerate(rows):
        for i, ch in enumerate(row[5:5 + width]):
            box = (i * CELL, band + j * CELL, (i + 1) * CELL - 1, band + (j + 1) * CELL - 1)
            if ch == "?":
                pen.rectangle(box, fill=COLOURS["."], outline=GHOST)
            else:
                pen.rectangle(box, fill=COLOURS.get(ch, COLOURS["#"]))
    return img


def page(rows, title):
    """One HTML page: each turn's prompt, answer, counts and picture, in order."""
    parts = ["<!doctype html><meta charset=utf-8><title>%s</title>" % html.escape(title),
             "<style>body{background:#111;color:#ddd;font:15px system-ui;margin:16px;max-width:900px}"
             "h1{font-size:20px}.t{border-top:1px solid #333;padding:12px 0}.p{color:#fff;font-weight:600}"
             ".a{white-space:pre-wrap;color:#00ff88;margin:6px 0}.n{color:#888;font-size:13px}img{max-width:100%%;border:1px solid #333}</style>",
             "<h1>%s</h1>" % html.escape(title)]
    for i, r in enumerate(rows, 1):
        parts.append("<div class=t><div class=p>%d. %s</div><div class=a>%s</div><div class=n>%s tool calls, %s s, %s</div>%s</div>" % (
            i, html.escape(r["prompt"]), html.escape(r.get("answer") or "(no answer: %s)" % r.get("outcome")),
            r.get("calls", 0), r.get("seconds", 0), html.escape(r.get("outcome") or ""),
            ('<img src="%s" alt="the map after turn %d">' % (html.escape(r["picture"]), i)) if r.get("picture") else "<div class=n>no picture</div>"))
    return "\n".join(parts)
