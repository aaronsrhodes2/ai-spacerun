"""
Yellow (utility) science block, west of the bus. Layout found by scripts/solve_yellow.py (a 2x6 grid with direct insertion):

    row 0 (north belts N1 iron|copper, N2 steel|plastic):   .  LDS  battery  .  gear  .
    row 1 (south belts S1 EC|iron,     S2 steel|AC):        PU pack FRF      EEU engine pipe

Tile coordinates. Column c has machines at x = X0 + 4c. Belts flow WEST from the sorter zone at the east end (the taps arrive from the bus at x=68).
Fluids: acid for PU (south) and battery (north), lubricant for EEU (south), through pipe-to-ground pieces that pass under the belts.
Entities are returned as place_entities dicts.
"""

N, E, S, W = 0, 4, 8, 12
X0 = 20
Y_N2, Y_N1, Y_INS_N, Y_R0 = -121, -120, -119, -118      # north belts, north inserter row, row 0 top
Y_GAP, Y_R1, Y_INS_S, Y_S1, Y_S2 = -115, -114, -111, -110, -109


def belt(x, y, d):
    return {"name": "transport-belt", "x": x + 0.5, "y": y + 0.5, "direction": d}


def ug(x, y, d, kind):
    return {"name": "underground-belt", "x": x + 0.5, "y": y + 0.5, "direction": d, "params": {"type": kind}}


def ins(x, y, d, name="inserter"):
    return {"name": name, "x": x + 0.5, "y": y + 0.5, "direction": d}


def machine(x, y, recipe, d=0):
    return {"name": "assembling-machine-2", "x": x + 1.5, "y": y + 1.5, "direction": d, "recipe": recipe}


def pole(x, y):
    return {"name": "medium-electric-pole", "x": x + 0.5, "y": y + 0.5}


def ptg(x, y, d):
    return {"name": "pipe-to-ground", "x": x + 0.5, "y": y + 0.5, "direction": d}


def cx(c):
    return X0 + 4 * c


def machines_and_inserters():
    e = []
    r0 = {1: "low-density-structure", 2: "battery", 4: "iron-gear-wheel"}
    r1 = {0: "processing-unit", 1: "utility-science-pack", 2: "flying-robot-frame", 3: "electric-engine-unit", 4: "engine-unit", 5: "pipe"}
    south_facing = {0, 3}                      # fluid machines in row 1 take the pipe on their south side
    for c, rec in r0.items():
        e.append(machine(cx(c), Y_R0, rec, 0))
    for c, rec in r1.items():
        e.append(machine(cx(c), Y_R1, rec, S if c in south_facing else 0))
    e.append(ins(cx(1), Y_INS_N, N))                              # LDS: copper from N1
    e.append(ins(cx(1) + 2, Y_INS_N, N, "long-handed-inserter"))  # LDS: steel + plastic from N2
    e.append(ins(cx(2), Y_INS_N, N))                              # battery: iron + copper from N1
    e.append(ins(cx(4), Y_INS_N, N))                              # gear: iron from N1
    for c in (1, 2, 4):
        e.append(ins(cx(c) + 1, Y_GAP, N))                        # picks the row 0 machine (north), drops into row 1
    e.append(ins(cx(0), Y_INS_S, S))                              # PU: EC from S1
    e.append(ins(cx(0) + 2, Y_INS_S, S, "long-handed-inserter"))  # PU: AC from S2
    e.append(ins(cx(2), Y_INS_S, S))                              # FRF: EC from S1
    e.append(ins(cx(2) + 2, Y_INS_S, S, "long-handed-inserter"))  # FRF: steel from S2
    e.append(ins(cx(3), Y_INS_S, S))                              # EEU: EC from S1
    e.append(ins(cx(4) + 2, Y_INS_S, S, "long-handed-inserter"))  # engine: steel from S2
    e.append(ins(cx(5), Y_INS_S, S))                              # pipe: iron from S1
    ym = Y_R1 + 1
    e.append(ins(cx(0) + 3, ym, W))                               # PU -> pack (picks west)
    e.append(ins(cx(2) - 1, ym, E))                               # FRF -> pack (picks east)
    e.append(ins(cx(3) - 1, ym, E))                               # EEU -> FRF
    e.append(ins(cx(4) - 1, ym, E))                               # engine -> EEU
    e.append(ins(cx(5) - 1, ym, E))                               # pipe -> engine
    e.append(ins(cx(1) + 1, Y_INS_S, N))                          # pack output: picks the pack machine, drops on the belt south of it
    return e


def belts():
    e = []
    for x in range(67, 62, -1):
        e.append(belt(x, Y_N1, W))
    e.append(ug(62, Y_N1, W, "input"))                            # hop so the plastic feeder can reach N2's head from the south
    e.append(ug(58, Y_N1, W, "output"))
    for x in range(57, cx(1) - 1, -1):
        e.append(belt(x, Y_N1, W))
    e.append(belt(61, Y_N2, W))                                   # dummy so the head side-loads
    for x in range(60, cx(1) - 1, -1):
        e.append(belt(x, Y_N2, W))
    for x in range(67, 59, -1):
        e.append(belt(x, Y_S2, W))
    e.append(ug(59, Y_S2, W, "input"))                            # hop so the iron feeder can reach S1's head from the south
    e.append(ug(55, Y_S2, W, "output"))
    for x in range(54, cx(2) - 1, -1):
        e.append(belt(x, Y_S2, W))
    e.append(belt(58, Y_S1, W))                                   # dummy
    for x in range(57, cx(2) - 1, -1):
        e.append(belt(x, Y_S1, W))
    for row in (Y_S1, Y_S2):                                      # hop under the pack column
        e.append(ug(cx(2) - 1, row, W, "input"))
        e.append(ug(cx(1) - 1, row, W, "output"))
        for x in range(cx(1) - 2, cx(0) - 1, -1):
            e.append(belt(x, row, W))
    px = cx(1) + 1
    e.append(belt(px, Y_S1, S))
    e.append(belt(px, Y_S2, S))
    e.append(belt(px, Y_S2 + 1, S))
    return e


def sorter_feeds():
    e = []
    for x in (63, 62, 61):                                        # steel from the T0b sorter to N2's head (from the north)
        e.append(belt(x, -122, W))
    e.append(belt(60, -122, S))
    e.append(belt(63, -123, W))                                   # AC leftover stub
    for x in (62, 61):                                            # plastic from the T2 sorter, up into N2's head from the south
        e.append(belt(x, -117, W))
    e.append(belt(60, -117, N))
    e.append(belt(60, -118, N))
    e.append(belt(60, -119, N))
    e.append(belt(60, Y_N1, N))
    for x in (62, 61, 60, 59, 58):                                # EC from the same sorter, to S1's head from the north
        e.append(belt(x, -116, W))
    for y in (-116, -115, -114, -113, -112, -111):
        e.append(belt(57, y, S))
    for x in (62, 61, 60, 59, 58):                                # iron from the T1b sorter, to S1's head from the south
        e.append(belt(x, -106, W))
    for y in (-106, -107, -108, -109):
        e.append(belt(57, y, N))
    return e


SPLITTERS = [  # (x, top row, filter item, output priority). Facing west: covers rows y and y+1; left = south, right = north
    (64, -123, "steel-plate", "left"),
    (63, -117, "plastic-bar", "right"),
    (63, -106, "iron-plate", "right"),
]


def splitter_entities():
    return [{"name": "splitter", "x": x + 0.5, "y": y + 1.0, "direction": W} for x, y, _, _ in SPLITTERS]


def poles():
    return [pole(x, y) for x, y in ((22, -115), (27, -115), (31, -115), (35, -115), (39, -115),
                                    (23, -111), (31, -111), (34, -111), (41, -111),
                                    (25, -119), (31, -119), (38, -119),
                                    (47, -114), (52, -114), (56, -114), (62, -114))]


def all_entities():
    return machines_and_inserters() + belts() + sorter_feeds() + splitter_entities() + poles()
