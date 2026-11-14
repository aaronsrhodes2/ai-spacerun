"""Scores a run from the bridge's logs. A run is clean when the model never missed a tool call, never had to be stopped
from repeating itself, never ran out of steps and the model server never failed. Counted by code, never judged by the model.

    python -m copilot.score runs/            every log in the folder, one line each and a total
    python -m copilot.score runs/x.jsonl     one log, with each miss listed
"""
import json
import pathlib
import sys


def read(path):
    out = []
    for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except ValueError:
                out.append({"event": "unreadable"})
    return out


def score(entries):
    """Totals for one log. 'misses' are tool calls the game or the bridge refused; 'repeats' are the subset refused for
    being the same call a third time; 'stalls' are requests that ended without an answer."""
    s = {"requests": 0, "answered": 0, "stalls": 0, "model_errors": 0, "calls": 0, "misses": 0, "repeats": 0,
         "unknown_tools": 0, "unreadable": 0, "seconds": 0.0, "tokens_in": 0, "tokens_out": 0, "miss_list": [], "milestones": 0}
    for e in entries:
        kind = e.get("event")
        if kind == "request":
            s["requests"] += 1
        elif kind == "tool":
            s["calls"] += 1
            if not e.get("ok"):
                s["misses"] += 1
                err = e.get("error") or ""
                if "this exact call" in err:
                    s["repeats"] += 1
                if err.startswith("there is no tool named"):
                    s["unknown_tools"] += 1
                s["miss_list"].append({"name": e.get("name"), "args": e.get("args"), "error": err})
        elif kind == "answer":
            if e.get("outcome") == "answered":
                s["answered"] += 1
            elif e.get("outcome") == "model error":
                s["model_errors"] += 1
            else:
                s["stalls"] += 1
            s["seconds"] += e.get("seconds") or 0
            s["tokens_in"] += e.get("tokens_in") or 0
            s["tokens_out"] += e.get("tokens_out") or 0
        elif kind == "stall":                       # the milestone watch saw no progress for too long
            s["stalls"] += 1
        elif kind == "milestone":
            s["milestones"] = max(s["milestones"], e.get("done") or 0)
        elif kind == "unreadable":
            s["unreadable"] += 1
    s["clean"] = s["requests"] > 0 and s["misses"] == 0 and s["stalls"] == 0 and s["model_errors"] == 0 and s["unreadable"] == 0
    s["miss_rate"] = round(s["misses"] / s["calls"], 3) if s["calls"] else 0.0
    return s


def total(scores):
    keys = ["requests", "answered", "stalls", "model_errors", "calls", "misses", "repeats", "unknown_tools", "unreadable", "seconds", "tokens_in", "tokens_out"]
    t = {k: sum(s[k] for s in scores) for k in keys}
    t["clean"] = bool(scores) and all(s["clean"] for s in scores)
    t["miss_rate"] = round(t["misses"] / t["calls"], 3) if t["calls"] else 0.0
    return t


def line(name, s):
    return "%-28s %s  requests %d answered %d stalls %d  calls %d misses %d (%.0f%%) repeats %d  %.0f s" % (
        name, "CLEAN" if s["clean"] else "dirty", s["requests"], s["answered"], s["stalls"] + s["model_errors"], s["calls"], s["misses"],
        100 * s["miss_rate"], s["repeats"], s["seconds"])


def main(argv):
    target = pathlib.Path(argv[1] if len(argv) > 1 else "runs")
    files = sorted(target.glob("*.jsonl")) if target.is_dir() else [target]
    scores = []
    for f in files:
        s = score(read(f))
        scores.append(s)
        print(line(f.name, s))
        if len(files) == 1:
            for m in s["miss_list"]:
                print("   miss:", m["name"], json.dumps(m["args"]), "->", m["error"])
    if len(files) > 1:
        print(line("TOTAL (%d logs)" % len(files), total(scores)))
    return 0 if scores and all(s["clean"] for s in scores) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
