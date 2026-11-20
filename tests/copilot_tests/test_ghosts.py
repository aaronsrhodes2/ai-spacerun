"""Ghosts to requests: the shortfall of a network's ghosts, written into a landing pad's request list or a requester chest.
The ghosts, the network, the pad and the chest are stand-ins built here in Lua on top of the fake game."""
import pytest

from luamod import LuaMod

WORLD = """
defines.logistic_mode = { requester = 1, buffer = 2 }
defines.logistic_member_index = { logistic_container = 7 }
defines.inventory.cargo_landing_pad_main = 91
prototypes.item['transport-belt'] = { stack_size = 100 }
prototypes.item['stone-brick'] = { stack_size = 100 }
prototypes.item['rocket-fuel'] = { stack_size = 10 }
local s = game.surfaces.nauvis
local f = game.forces.player
W = { have = { ['transport-belt normal'] = 3 }, onpad = {} }
local net = { network_id = 1, cells = {}, get_item_count = function(q) return W.have[q.name .. ' ' .. q.quality] or 0 end }
W.net = net
s.find_logistic_network_by_position = function(pos, force) if pos.x < 100 then return net end end

local function point()
  local pt = { mode = defines.logistic_mode.requester, sections = {}, sections_count = 0 }
  function pt.add_section(group)
    local sec = { group = group, slots = {}, filters = {} }
    function sec.set_slot(i, filter) sec.slots[i] = filter end
    pt.sections[#pt.sections + 1] = sec
    pt.sections_count = #pt.sections
    return sec
  end
  function pt.remove_section(i) table.remove(pt.sections, i) pt.sections_count = #pt.sections end
  return pt
end
W.point = point()
local inv = { get_item_count = function(q) return W.onpad[q.name .. ' ' .. q.quality] or 0 end }
s.entities[#s.entities + 1] = { name = 'cargo-landing-pad', type = 'cargo-landing-pad', force = f, valid = true, position = { x = 0, y = 0 },
  bounding_box = { left_top = { x = 0, y = 0 }, right_bottom = { x = 1, y = 1 } }, logistic_network = net,
  get_logistic_point = function() return { W.point } end, get_inventory = function() return inv end }

W.chest_point = point()
s.entities[#s.entities + 1] = { name = 'requester-chest', type = 'logistic-container', force = f, valid = true, position = { x = 10.5, y = 10.5 },
  bounding_box = { left_top = { x = 10, y = 10 }, right_bottom = { x = 11, y = 11 } }, logistic_network = net,
  get_logistic_point = function() return W.chest_point end }

function W.ghost(kind, items, x, quality)
  s.entities[#s.entities + 1] = { name = kind, type = kind, force = f, valid = true, position = { x = x, y = 0 }, quality = { name = quality or 'normal' },
    bounding_box = { left_top = { x = x, y = 0 }, right_bottom = { x = x + 1, y = 1 } }, ghost_prototype = { items_to_place_this = items } }
end
"""


@pytest.fixture
def mod():
    m = LuaMod()
    m.run(WORLD)
    return m


def ghost(mod, kind, items, x, quality="normal"):
    lit = "{" + ",".join("{name='%s',count=%d}" % (n, c) for n, c in items) + "}"
    mod.run("W.ghost('%s', %s, %d, '%s')" % (kind, lit, x, quality))


def test_needs_are_totalled_per_item_and_quality_and_outside_ghosts_are_counted_apart(mod):
    ghost(mod, "entity-ghost", [("transport-belt", 2)], 5)
    ghost(mod, "entity-ghost", [("transport-belt", 2)], 6)
    ghost(mod, "tile-ghost", [("stone-brick", 1)], 7)
    ghost(mod, "entity-ghost", [("transport-belt", 1)], 8, "rare")                   # a ghost asks for its own quality
    ghost(mod, "entity-ghost", [("transport-belt", 9)], 500)                         # outside every roboport
    r = mod.result("ghost_needs", {"surface": "nauvis"})["surfaces"][0]
    assert (r["ghosts_inside"], r["ghosts_outside_coverage"], r["kinds"]) == (4, 1, 3)
    items = {(i["item"], i["quality"]): i for i in r["items"]}
    assert items[("transport-belt", "normal")] == {"item": "transport-belt", "quality": "normal", "need": 4, "have": 3, "short": 1}
    assert items[("transport-belt", "rare")]["short"] == 1 and items[("stone-brick", "normal")]["short"] == 1


def test_a_dry_run_writes_nothing_and_apply_writes_our_section_only(mod):
    ghost(mod, "entity-ghost", [("transport-belt", 10)], 5)
    mod.run("W.onpad['transport-belt normal'] = 2; local o = W.point.add_section('someone-elses') W.point.add_section('ghost-auto')")
    r = mod.result("ghost_requests", {"surface": "nauvis"})
    assert r["applied"] is False and r["surfaces"][0]["slots"] == 1 and mod.run("return #W.point.sections") == 2
    r = mod.result("ghost_requests", {"surface": "nauvis", "apply": True})
    assert r["surfaces"][0]["wrote"] == 1
    groups = list(mod.run("local g = {} for _, s in ipairs(W.point.sections) do g[#g + 1] = s.group end return table.concat(g, ',')").split(","))
    assert groups == ["someone-elses", "ghost-auto-nauvis"]                                # the old shared group went, the other stayed
    slot = mod.run("local s = W.point.sections[2].slots[1] return s.value.name .. ' ' .. s.value.quality .. ' ' .. s.min .. ' ' .. s.max")
    assert slot == "transport-belt normal 9 9"                                             # short 7 plus the 2 already on the pad
    mod.result("ghost_requests", {"surface": "nauvis", "apply": True})                     # again: rewritten, not stacked
    assert mod.run("return #W.point.sections") == 2


def test_the_stack_cap_takes_the_biggest_shortfalls_first(mod):
    ghost(mod, "entity-ghost", [("transport-belt", 1000)], 5)                              # 10 stacks short
    ghost(mod, "entity-ghost", [("rocket-fuel", 25)], 6)                                   # 3 stacks short
    r = mod.result("ghost_requests", {"surface": "nauvis", "max_stacks": 4})["surfaces"][0]
    assert [i["item"] for i in r["items"]] == ["rocket-fuel"] and r["stacks"] == 3         # the belts alone would break the cap


def test_apply_needs_the_allowance_but_a_dry_run_does_not(mod):
    ghost(mod, "entity-ghost", [("transport-belt", 10)], 5)
    mod.result("set_allowance", {"id": "ghost-requests", "on": False})
    assert "ghost-requests" in mod.call("ghost_requests", {"surface": "nauvis", "apply": True})["error"]
    assert mod.result("ghost_requests", {"surface": "nauvis"})["surfaces"][0]["slots"] == 1
    assert mod.run("return #W.point.sections") == 0


def test_a_requester_chest_can_be_the_target(mod):
    ghost(mod, "entity-ghost", [("transport-belt", 10)], 5)
    mod.run("local pt = W.chest_point local first = pt.add_section() first.slots = {} ")
    r = mod.result("ghost_requests", {"surface": "nauvis", "apply": True, "chest_x": 10.5, "chest_y": 10.5})["surfaces"][0]
    assert r["wrote"] == 1 and "chest" in r["network"]
    assert mod.run("local s = W.chest_point.sections[1].slots[1] return s.value.name .. ' ' .. s.min") == "transport-belt 7"
    assert "needs surface, chest_x and chest_y" in mod.call("ghost_requests", {"chest_x": 1, "chest_y": 1})["error"]
    assert "no requester chest" in mod.result("ghost_requests", {"surface": "nauvis", "chest_x": 50.5, "chest_y": 50.5})["surfaces"][0]["skipped"]


def test_surfaces_without_a_pad_are_skipped_with_a_reason(mod):
    r = mod.result("ghost_requests", {})
    assert r["surfaces"][0]["surface"] == "nauvis" and r["surfaces"][0]["slots"] == 0
    assert "no surface named" in mod.call("ghost_needs", {"surface": "mars"})["error"]
