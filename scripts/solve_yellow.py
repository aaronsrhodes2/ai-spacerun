"""Offline puzzle: place the nine yellow machines on a 2-row grid with direct insertion between neighbours and 4+4 belt lanes."""
import itertools
import sys

M = {"gear": {"iron"}, "pipe": {"iron"}, "engine": {"steel"}, "battery": {"iron", "copper"}, "EEU": {"EC"},
     "FRF": {"steel", "EC"}, "LDS": {"copper", "steel", "plastic"}, "PU": {"EC", "AC"}, "pack": set()}
EDGES = [("gear", "engine"), ("pipe", "engine"), ("engine", "EEU"), ("EEU", "FRF"), ("battery", "FRF"),
         ("FRF", "pack"), ("PU", "pack"), ("LDS", "pack")]
FLUID = set()
COLS = int(sys.argv[1]) if len(sys.argv) > 1 else 6


def adjacent(a, b):
    return (a[0] == b[0] and abs(a[1] - b[1]) == 1) or (a[1] == b[1] and a[0] != b[0])


def solve():
    names = list(M)
    cells = [(r, c) for r in (0, 1) for c in range(COLS)]
    sols = []
    def place(i, used, pos):
        if i == len(names):
            yield dict(pos)
            return
        n = names[i]
        for cell in cells:
            if cell in used:
                continue
            if n in FLUID and cell[0] != 1:
                continue
            pos[n] = cell
            ok = True
            for a, b in EDGES:
                if a in pos and b in pos and not adjacent(pos[a], pos[b]):
                    ok = False
                    break
            if ok:
                yield from place(i + 1, used | {cell}, pos)
            del pos[n]
    for pos in place(0, frozenset(), {}):
        # lanes: each side needs the union of raws of its machines in at most 4 distinct items
        for side in (0, 1):
            need = set()
            for n, (r, c) in pos.items():
                if r == side:
                    need |= M[n]
            if len(need) > 4:
                break
        else:
            # pack needs an end column for its output inserter
            r, c = pos["pack"]
            if c not in (0, COLS - 1):
                continue
            sols.append(pos)
            if len(sols) >= 5:
                return sols
    return sols


if __name__ == "__main__":
    for s in solve():
        print(s)
        for side in (0, 1):
            need = set()
            for n, (r, c) in s.items():
                if r == side:
                    need |= M[n]
            print("  side", side, "lanes", sorted(need))
