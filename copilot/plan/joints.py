"""Joints: the small patterns for where supply lines meet and cross (the Captain, 2026-11-13). These are the hard part
of a layout and the part worth showing: a belt under a belt, a pipe under a belt, a splitter used as a filter, one belt
feeding one lane of another, the row of inserters beside a train wagon. Each solves one kind of meeting and nothing
more; none names a recipe, a count or a place. Whole production lines are never stored: they are made from these.

Every joint is designed with its main flow running NORTH (toward smaller y) and is turned in code for other directions.
"Left" and "right" are as seen looking along the flow: with the flow north, left is west.

Facts of the game these lean on:
  - An underground belt or pipe pair passes under anything; the two ends face along the run.
  - A belt that ends pointing into the SIDE of another belt puts its items on the near lane of that belt only.
  - A splitter is two tiles wide across the flow. With a filter set, the filtered item leaves on the side named by its
    output priority and everything else leaves on the other side. With only a priority set, that side is served first.
  - An inserter's direction is the side it picks up from; it drops on the opposite side.
  - A wagon is six tiles long; one inserter per tile along its side is the most that can reach it."""
from .layout import E, N, S, W, Layout, LayoutError

UNDERGROUND = {"transport-belt": "underground-belt", "fast-transport-belt": "fast-underground-belt",
               "express-transport-belt": "express-underground-belt", "turbo-transport-belt": "turbo-underground-belt"}


def _under(belt):
    if belt not in UNDERGROUND:
        raise LayoutError("no underground belt is known for '%s'" % belt)
    return UNDERGROUND[belt]


def belt_crossing(belt="transport-belt", crossing_belt=None, width=1):
    """One belt crossing another without mixing: the main belt (running north) dives under a belt running east.

        b      main belt, north
        U      underground exit
        > > >  the crossing belt, running east (width rows of it)
        U      underground entrance
        b      main belt

    width is how many belts side by side are crossed (the underground's reach limits it: 4 for the basic belt)."""
    if width < 1:
        raise LayoutError("at least one belt must be crossed")
    crossing_belt = crossing_belt or belt
    lay = Layout()
    lay.put(belt, 0, 0, direction=N, role="main")
    lay.put(_under(belt), 0, 1, direction=N, type="output", role="exit")
    for row in range(width):
        for x in (-1, 0, 1):
            lay.put(crossing_belt, x, 2 + row, direction=E, role="crossing")
    lay.put(_under(belt), 0, 2 + width, direction=N, type="input", role="entrance")
    lay.put(belt, 0, 3 + width, direction=N, role="main")
    return lay


def pipe_crossing(pipe="pipe", underground="pipe-to-ground", belt="transport-belt", width=1):
    """A pipe (running north-south) passing under belts running east. The two pipe-to-ground pieces open outward, away
    from the belts, so the pipe touches nothing in between: no leak into a neighbouring pipe line."""
    if width < 1:
        raise LayoutError("at least one belt must be crossed")
    lay = Layout()
    lay.put(pipe, 0, 0, role="pipe")
    lay.put(underground, 0, 1, direction=N, role="open-north")
    for row in range(width):
        for x in (-1, 0, 1):
            lay.put(belt, x, 2 + row, direction=E, role="crossing")
    lay.put(underground, 0, 2 + width, direction=S, role="open-south")
    lay.put(pipe, 0, 3 + width, role="pipe")
    return lay


def filter_splitter(item, splitter="splitter", belt="transport-belt", to="left"):
    """Take one kind of item off a mixed belt. The mixed belt comes in from the south on the right half of a splitter;
    the filtered item leaves north on the side named by `to`, everything else on the other side.

        L R      two belts out, north: L gets the filtered item when to is 'left'
        S S      the splitter, filter set
        . b      the mixed belt in, from the south

    Unlike a filtered inserter this keeps the belt's full speed."""
    if to not in ("left", "right"):
        raise LayoutError("to must be 'left' or 'right'")
    lay = Layout()
    lay.put(belt, 0, 0, direction=N, role="filtered" if to == "left" else "rest")
    lay.put(belt, 1, 0, direction=N, role="filtered" if to == "right" else "rest")
    lay.put(splitter, 0, 1, 2, 1, direction=N, filter=item, output_priority=to, role="splitter")
    lay.put(belt, 1, 2, direction=N, role="mixed")
    return lay


def priority_merge(splitter="splitter", belt="transport-belt", first="left"):
    """Two belts into one, with one of them always served first (science packs before ore, say). Both come in from the
    south; the output leaves north on the left half. The other output is left empty on purpose.

        b .      one belt out
        S S      the splitter, input priority set
        b b      two belts in: the `first` side is drained before the other gets a turn"""
    if first not in ("left", "right"):
        raise LayoutError("first must be 'left' or 'right'")
    lay = Layout()
    lay.put(belt, 0, 0, direction=N, role="out")
    lay.put(splitter, 0, 1, 2, 1, direction=N, input_priority=first, output_priority="left", role="splitter")
    lay.put(belt, 0, 2, direction=N, role="in-left")
    lay.put(belt, 1, 2, direction=N, role="in-right")
    return lay


def side_load(belt="transport-belt", feeder_belt=None, side="left"):
    """Put one belt's items onto ONE lane of another: the feeder ends pointing into the side of the main belt. Two
    feeders, one from each side, give a belt carrying a different item on each lane.

        b          main belt, north
        > b        the feeder from the left (west) ends against the main belt's side: its items take the left lane
        b          main belt"""
    if side not in ("left", "right"):
        raise LayoutError("side must be 'left' or 'right'")
    feeder_belt = feeder_belt or belt
    lay = Layout()
    for y in range(3):
        lay.put(belt, 0, y, direction=N, role="main")
    if side == "left":
        lay.put(feeder_belt, -1, 1, direction=E, role="feeder")
    else:
        lay.put(feeder_belt, 1, 1, direction=W, role="feeder")
    return lay


def lane_pair(belt="transport-belt"):
    """A belt with a lane each for two items: a feeder from each side, both ending against the main belt."""
    lay = side_load(belt, side="left")
    lay.put(belt, 1, 1, direction=W, role="feeder")
    return lay


def filtered_pick(item, inserter="inserter", belt="transport-belt"):
    """Pick one kind of item off a mixed belt into whatever stands north of the inserter: the inserter picks up from
    the south (the belt) and only takes the filtered item."""
    lay = Layout()
    lay.put(inserter, 0, 0, direction=S, filter=item, role="pick")
    lay.put(belt, 0, 1, direction=E, role="mixed")
    return lay


def wagon_side(action="unload", inserter="inserter", chest="steel-chest", belt="transport-belt", wagons=1, gap=1):
    """The row beside a stopped train's cargo wagons, one inserter per wagon tile, with a chest each as a buffer and a
    belt beyond. The wagons stand along the NORTH edge of this joint, the first wagon's first tile above column 0.

        unload:  i i i i i i    inserters pick up from the north (the wagon)
                 C C C C C C    chests
                 i i i i i i    inserters pick up from the north (the chests)
                 > > > > > >    the belt away, east

        load:    the same shape with every inserter turned round and the belt bringing items in.

    wagons is how many wagons the train has on this side; gap is the tiles between wagons (1, for the coupling)."""
    if action not in ("unload", "load"):
        raise LayoutError("action must be 'unload' or 'load'")
    if wagons < 1:
        raise LayoutError("at least one wagon")
    pick = N if action == "unload" else S
    lay = Layout()
    for w in range(wagons):
        x0 = w * (6 + gap)
        for i in range(6):
            x = x0 + i
            lay.put(inserter, x, 0, direction=pick, role="wagon-inserter")
            lay.put(chest, x, 1, role="buffer")
            lay.put(inserter, x, 2, direction=pick, role="belt-inserter")
    for x in range(wagons * 6 + (wagons - 1) * gap):
        lay.put(belt, x, 3, direction=E, role="belt")
    return lay


def tee(splitter="splitter", belt="transport-belt"):
    """One belt split evenly into two.

        b b      two belts out
        S S      a splitter with nothing set shares evenly
        b .      one belt in"""
    lay = Layout()
    lay.put(belt, 0, 0, direction=N, role="out")
    lay.put(belt, 1, 0, direction=N, role="out")
    lay.put(splitter, 0, 1, 2, 1, direction=N, role="splitter")
    lay.put(belt, 0, 2, direction=N, role="in")
    return lay


def overflow_valve(splitter="splitter", belt="transport-belt", keep="left"):
    """Send on only what the main line cannot take. The main line leaves on the `keep` side and is always served first;
    the other side gets the overflow, and gets nothing while the main line has room. Use it to keep a line full and
    turn only the surplus aside (to storage, or to be voided).

        M O      M: the main line carries on. O: the overflow
        S S      the splitter, output priority on the main side
        b .      the line in"""
    if keep not in ("left", "right"):
        raise LayoutError("keep must be 'left' or 'right'")
    lay = Layout()
    lay.put(belt, 0, 0, direction=N, role="main" if keep == "left" else "overflow")
    lay.put(belt, 1, 0, direction=N, role="main" if keep == "right" else "overflow")
    lay.put(splitter, 0, 1, 2, 1, direction=N, output_priority=keep, role="splitter")
    lay.put(belt, 0 if keep == "left" else 1, 2, direction=N, role="in")
    return lay


def balancer(lanes=4, splitter="splitter", belt="transport-belt"):
    """Belts in, the same number of belts out, each output carrying an equal share of every input. For two belts that
    is one splitter. For four: pair the belts, then pair each belt with one from the other pair, which needs one belt
    to cross the other three.

        . b b b b      four belts out (one column east of where they came in)
        . S S S S      second pairing
        . U U U b      three belts come up from underground; the fourth turns north
        > > > > ^      the first belt runs east over the tunnels
        b U U U .      three belts dive
        S S S S .      first pairing
        b b b b .      four belts in"""
    lay = Layout()
    under = _under(belt)
    if lanes == 2:
        for x in (0, 1):
            lay.put(belt, x, 0, direction=N, role="out")
            lay.put(belt, x, 2, direction=N, role="in")
        lay.put(splitter, 0, 1, 2, 1, direction=N, role="splitter")
        return lay
    if lanes != 4:
        raise LayoutError("a balancer is for 2 or 4 belts")
    for x in range(4):
        lay.put(belt, x, 6, direction=N, role="in")
    lay.put(splitter, 0, 5, 2, 1, direction=N, role="splitter")
    lay.put(splitter, 2, 5, 2, 1, direction=N, role="splitter")
    lay.put(belt, 0, 4, direction=N, role="over")
    for x in (1, 2, 3):
        lay.put(under, x, 4, direction=N, type="input", role="entrance")
        lay.put(under, x, 2, direction=N, type="output", role="exit")
    for x in range(4):
        lay.put(belt, x, 3, direction=E, role="over")
    lay.put(belt, 4, 3, direction=N, role="over")
    lay.put(belt, 4, 2, direction=N, role="over")
    lay.put(splitter, 1, 1, 2, 1, direction=N, role="splitter")
    lay.put(splitter, 3, 1, 2, 1, direction=N, role="splitter")
    for x in range(1, 5):
        lay.put(belt, x, 0, direction=N, role="out")
    return lay


def reach_over(machine, width, height, inserter="long-handed-inserter", belt="transport-belt"):
    """Feed a machine from the FAR one of two belts: a long-handed inserter reaches over the near belt. With an ordinary
    inserter on the near belt beside it, one machine takes from two belts.

        b b b      the far belt
        b b b      the near belt
          L        long-handed inserter: picks up two tiles north (the far belt), drops two tiles south
        . . .      (the tile its hand passes over on the way down; leave it free or put the near belt's inserter beside)
        M M M      the machine"""
    if width < 1 or height < 1:
        raise LayoutError("a machine is at least one tile wide and high")
    lay = Layout()
    for x in range(width):
        lay.put(belt, x, 0, direction=E, role="far")
        lay.put(belt, x, 1, direction=E, role="near")
    lay.put(inserter, width // 2, 2, direction=N, role="reach")
    lay.put(machine, 0, 3, width, height, role="machine")
    return lay


def belt_to_robots(inserter="inserter", belt="transport-belt", chest="passive-provider-chest"):
    """The end of a belt line handed to the robot network: the belt ends at an inserter that fills a provider chest.
    Limit the chest's slots so the line stops when the stock stands.

        C      provider chest (red: the end of a line)
        i      picks up from the south (the belt)
        b      the belt arriving, running north"""
    lay = Layout()
    lay.put(chest, 0, 0, role="stock")
    lay.put(inserter, 0, 1, direction=S, role="hand")
    lay.put(belt, 0, 2, direction=N, role="belt")
    return lay


def robots_to_belt(inserter="inserter", belt="transport-belt", chest="requester-chest"):
    """The start of a belt line fed by the robot network: a requester chest, an inserter, a belt leaving north.

        b      the belt leaving, running north
        i      picks up from the south (the chest)
        C      requester chest (blue: the start of a line); set what it asks for"""
    lay = Layout()
    lay.put(belt, 0, 0, direction=N, role="belt")
    lay.put(inserter, 0, 1, direction=S, role="hand")
    lay.put(chest, 0, 2, role="requests")
    return lay


def long_pipe(length, underground="pipe-to-ground", reach=10):
    """A long pipe run made of underground pairs laid end to end, instead of a pipe on every tile: far fewer pieces,
    nothing for other lines to bump into, and the ground between stays free. `reach` is how many tiles one pair spans
    from end to end including both ends (11 for the basic pipe-to-ground, so 10 is safe; look it up).
    The run goes north. Each pair's lower end opens south and its upper end opens north; where two pairs meet, the
    open ends face each other and join."""
    length = int(length)
    if length < 2:
        raise LayoutError("a pipe run of underground pairs is at least two tiles long")
    if reach < 2:
        raise LayoutError("reach must be at least 2")
    lay = Layout()
    y = length - 1                                       # start at the south end
    while y >= 0:
        top = max(y - reach + 1, 0)
        if top == y:                                     # one tile left over: a pair cannot be made, so the last pair stretches to it
            raise LayoutError("a run of %d tiles leaves one tile over with reach %d; use a length that does not, or end with a plain pipe" % (length, reach))
        lay.put(underground, 0, y, direction=S, role="open-south")
        lay.put(underground, 0, top, direction=N, role="open-north")
        y = top - 1
    return lay


def pole_line(length, pole="medium-electric-pole", spacing=7):
    """Power poles along a line, far enough apart to save poles and close enough to stay wired and to power what stands
    beside the line. `spacing` is tiles from one pole to the next: at most the pole's wire reach, and at most its supply
    width if machines along the line must be covered without gaps (look both up). The line runs north."""
    length, spacing = int(length), int(spacing)
    if length < 1 or spacing < 1:
        raise LayoutError("length and spacing must be at least 1")
    lay = Layout()
    y = 0
    while y < length:
        lay.put(pole, 0, y, role="pole")
        y += spacing
    if (length - 1) % spacing:                           # a pole at the far end too, so the line reaches it
        lay.put(pole, 0, length - 1, role="pole")
    return lay


def machine_ports(machine, width, height, ports, pipe="pipe"):
    """A machine with a short pipe stub on every one of its fluid connections, so it is plain where each fluid goes in
    and comes out. `ports` come from the game (the `fluid_ports` of the machine in `lookup`): each has x, y (the tile
    inside the machine that the connection sits on, measured from the machine's centre, facing north), a direction
    (which way it points out) and whether it is an input or an output.
    Nothing here knows any machine's ports by heart."""
    if not ports:
        raise LayoutError("'%s' has no fluid connections" % machine)
    out = {"north": (0, -1), "east": (1, 0), "south": (0, 1), "west": (-1, 0)}
    lay = Layout()
    lay.put(machine, 0, 0, width, height, role="machine")
    for port in ports:
        if port.get("direction") not in out:
            raise LayoutError("a port of '%s' has no usable direction" % machine)
        ix = int((width / 2.0 + port["x"]) // 1)
        iy = int((height / 2.0 + port["y"]) // 1)
        if not (0 <= ix < width and 0 <= iy < height):
            raise LayoutError("a port of '%s' lies outside the machine: the game's port positions are not what this joint expects" % machine)
        dx, dy = out[port["direction"]]
        tx, ty = ix + dx, iy + dy
        if 0 <= tx < width and 0 <= ty < height:
            raise LayoutError("a port of '%s' points into the machine" % machine)
        if lay.free(tx, ty):
            lay.put(pipe, tx, ty, role=port.get("flow") or "port", fluid=port.get("fluid"))
    return lay


def fluid_machine_on_belts(machine, width, height, ports, belt="transport-belt", inserter="inserter", pipe="pipe", underground="pipe-to-ground", recipe=None):
    """A machine that takes items from a belt AND fluids from pipes, where the pipes have to get past the belts: the
    meeting of three kinds of line at one machine. An input belt runs along the north side and an output belt along
    the south side, as in the plain belt-fed cell. Every fluid connection on those two sides gets an underground pipe
    that starts against the machine and comes up beyond the belt; connections on the east and west sides get a plain
    pipe stub. The inserters stand on columns the pipes do not use.

        q . q      underground pipes come up beyond the belt (their open ends face away from the machine)
        b b b      input belt, running east
        q i q      underground pipes start against the machine's connections; the inserter between them
        M M M
        M M M
        M M M
        q i q
        b b b      output belt
        q . q

    `ports` come from the game (`fluid_ports` in lookup). Barrel filling and emptying are this joint with a recipe."""
    if not ports:
        raise LayoutError("'%s' has no fluid connections; use the plain belt-fed cell" % machine)
    out = {"north": (0, -1), "east": (1, 0), "south": (0, 1), "west": (-1, 0)}
    top = 2                                              # the machine's top row; rows 0 and 1 are the belt and the inserter row
    lay = Layout()
    lay.put(machine, 0, top, width, height, role="machine", **({"recipe": recipe} if recipe else {}))
    north_cols, south_cols = set(), set()
    for port in ports:
        if port.get("direction") not in out:
            raise LayoutError("a port of '%s' has no usable direction" % machine)
        ix = int((width / 2.0 + port["x"]) // 1)
        iy = int((height / 2.0 + port["y"]) // 1)
        if not (0 <= ix < width and 0 <= iy < height):
            raise LayoutError("a port of '%s' lies outside the machine: the game's port positions are not what this joint expects" % machine)
        role, fluid = port.get("flow") or "port", port.get("fluid")
        d = port["direction"]
        if d == "north" and ix not in north_cols:
            north_cols.add(ix)
            lay.put(underground, ix, top - 1, direction=S, role=role, fluid=fluid)        # open end against the machine
            lay.put(underground, ix, top - 3, direction=N, role=role, fluid=fluid)        # comes up beyond the belt
        elif d == "south" and ix not in south_cols:
            south_cols.add(ix)
            lay.put(underground, ix, top + height, direction=N, role=role, fluid=fluid)
            lay.put(underground, ix, top + height + 2, direction=S, role=role, fluid=fluid)
        elif d in ("east", "west"):
            tx = ix + out[d][0]
            if lay.free(tx, top + iy):
                lay.put(pipe, tx, top + iy, role=role, fluid=fluid)

    def free_column(taken):
        order = sorted(range(width), key=lambda c: abs(c - width // 2))                   # nearest the middle first
        for c in order:
            if c not in taken:
                return c
        raise LayoutError("every tile along that side of '%s' is a fluid connection: there is no room for an inserter" % machine)

    lay.put(inserter, free_column(north_cols), top - 1, direction=N, role="in")
    lay.put(inserter, free_column(south_cols), top + height, direction=N, role="out")
    for x in range(width):
        lay.put(belt, x, top - 2, direction=E, role="input")
        lay.put(belt, x, top + height + 1, direction=E, role="output")
    return lay


def robot_machine(machine, width, height, inserter="inserter", recipe=None):
    """A machine run entirely by the robot network: robots bring the ingredients to a requester chest and take the
    product from a provider chest. For things wanted in small numbers (building items above all), where a belt would
    be wasted. Set what the requester asks for (a few crafts' worth of each ingredient) and limit the provider chest's
    slots, so the machine stops when its stock stands.

          R        requester chest (blue: the start of a line)
          i
        M M M
          i
          P        passive provider chest (red: the end of a line)"""
    from . import cells
    return cells.robot_cell(machine, width, height, inserter, recipe)


RULES = {
    "rail_signals": {
        "solves": "trains must share track without colliding or blocking each other at a junction",
        "rules": [
            "A signal belongs on the right-hand side of the track, as seen by a train driving toward it.",
            "Rail signals cut the track into blocks; only one train is ever in a block.",
            "Put a CHAIN signal before a junction or crossing and wherever a train must not stop (on the junction itself).",
            "Put a plain RAIL signal after the junction, with at least one whole train's length of free track behind it, so a train that passes it has left the junction clear.",
            "On a two-way single track every signal needs a partner on the opposite side at the same spot, or trains from one direction cannot pass.",
            "A station on the main line blocks it: give stations their own siding, with a chain signal going in and a rail signal coming out.",
            "A train that says 'no path' usually faces a signal on the wrong side, or a one-way block from its side.",
        ],
        "why_no_layout": "where exactly a signal may stand beside a rail has to be checked in the running game; this is given as rules until that is done",
    },
}


JOINTS = {
    "belt_crossing": {"solves": "one belt has to cross another without their items mixing", "make": belt_crossing,
                      "options": {"width": "how many belts side by side are crossed (default 1)"}},
    "pipe_crossing": {"solves": "a pipe has to cross belts, or pass close to another pipe without joining it", "make": pipe_crossing,
                      "options": {"width": "how many belts side by side are crossed (default 1)"}},
    "filter_splitter": {"solves": "one kind of item has to be taken off a mixed belt at full belt speed", "make": filter_splitter,
                        "options": {"item": "the item to take off (required)", "to": "'left' or 'right': the side the filtered item leaves on (default left)"}},
    "priority_merge": {"solves": "two belts join into one and one of them must always go first", "make": priority_merge,
                       "options": {"first": "'left' or 'right': the input served first (default left)"}},
    "side_load": {"solves": "a belt's items must go onto one lane of another belt, to carry two items on one belt", "make": side_load,
                  "options": {"side": "'left' or 'right': the side the feeder comes from, and the lane it fills (default left)"}},
    "lane_pair": {"solves": "two items must share one belt, a lane each", "make": lane_pair, "options": {}},
    "filtered_pick": {"solves": "a machine or chest must take only one kind of item from a mixed belt", "make": filtered_pick,
                      "options": {"item": "the item to pick (required)"}},
    "wagon_side": {"solves": "a train's cargo wagons must be unloaded onto a belt, or loaded from one", "make": wagon_side,
                   "options": {"action": "'unload' or 'load' (default unload)", "wagons": "how many wagons (default 1)"}},
    "tee": {"solves": "one belt must be shared evenly between two", "make": tee, "options": {}},
    "overflow_valve": {"solves": "a line must stay full and only its surplus be turned aside", "make": overflow_valve,
                       "options": {"keep": "'left' or 'right': the side the main line leaves on (default left)"}},
    "balancer": {"solves": "several belts must each carry an equal share of everything coming in", "make": balancer,
                 "options": {"lanes": "2 or 4 belts (default 4)"}},
    "reach_over": {"solves": "a machine must take from the far one of two belts", "make": reach_over,
                   "options": {"machine": "the machine (required)", "width": "its width in tiles (required)", "height": "its height in tiles (required)"}},
    "belt_to_robots": {"solves": "the end of a belt line must be handed to the robot network", "make": belt_to_robots, "options": {}},
    "robots_to_belt": {"solves": "a belt line must start from items the robots bring", "make": robots_to_belt, "options": {}},
    "long_pipe": {"solves": "a fluid must travel far without a pipe on every tile and without touching other pipes", "make": long_pipe,
                  "options": {"length": "tiles from end to end (required)", "reach": "tiles one underground pair spans, ends included (default 10)"}},
    "pole_line": {"solves": "power must follow a line of machines or reach an outpost with few poles", "make": pole_line,
                  "options": {"length": "tiles from end to end (required)", "pole": "which pole (default medium-electric-pole)", "spacing": "tiles from pole to pole (default 7)"}},
    "fluid_machine_on_belts": {"solves": "a machine takes items from a belt and fluids from pipes, and the pipes must get past the belts", "make": fluid_machine_on_belts,
                               "options": {"machine": "the machine (required)", "width": "its width (required)", "height": "its height (required)", "ports": "its fluid ports from lookup (required)", "recipe": "recipe to set"}},
    "barrel_station": {"solves": "a fluid must be put into barrels or taken out of them, to move it by belt, robot, train or rocket", "make": fluid_machine_on_belts,
                       "options": {"machine": "the machine (required)", "width": "its width (required)", "height": "its height (required)", "ports": "its fluid ports from lookup (required)", "recipe": "the fill or empty recipe"}},
    "robot_machine": {"solves": "an item wanted in small numbers must be made on demand, with robots bringing ingredients and taking the product", "make": robot_machine,
                      "options": {"machine": "the machine (required)", "width": "its width (required)", "height": "its height (required)", "recipe": "recipe to set"}},
    "machine_ports": {"solves": "pipes must be fitted to a machine's fluid inputs and outputs", "make": machine_ports,
                      "options": {"machine": "the machine (required)", "width": "its width (required)", "height": "its height (required)", "ports": "its fluid ports from lookup (required)"}},
}


def catalogue():
    """What the model is shown: each joint, the problem it solves and its options."""
    out = [{"joint": name, "solves": j["solves"], "options": j["options"]} for name, j in JOINTS.items()]
    for name, r in RULES.items():
        out.append({"joint": name, "solves": r["solves"], "rules": r["rules"], "note": "rules only, no layout: " + r["why_no_layout"]})
    return out


def make(name, **options):
    if name in RULES:
        raise LayoutError("'%s' is given as rules, not as a layout (%s). The rules: %s" % (name, RULES[name]["why_no_layout"], " ".join(RULES[name]["rules"])))
    if name not in JOINTS:
        raise LayoutError("there is no joint '%s'; joints are: %s" % (name, ", ".join(list(JOINTS) + list(RULES))))
    spec = JOINTS[name]
    unknown = [k for k in options if k not in spec["options"] and k not in ("belt", "inserter", "splitter", "chest", "pipe", "underground", "crossing_belt", "feeder_belt", "pole")]
    import inspect
    takes = inspect.signature(spec["make"]).parameters
    options = {k: v for k, v in options.items() if k in takes or k in unknown}        # a default belt means nothing to a joint without belts
    if unknown:
        raise LayoutError("the joint '%s' has no option '%s'; its options are: %s" % (name, unknown[0], ", ".join(spec["options"]) or "none"))
    try:
        return spec["make"](**options)
    except TypeError:
        need = [k for k, v in spec["options"].items() if "required" in v and k not in options]
        raise LayoutError("the joint '%s' needs: %s" % (name, ", ".join(need) or "different options"))
