"""Production arithmetic: how many machines, how much input, how many belts. Pure functions over recipe facts, which the
caller reads from the running game (the mod's `lookup`), so nothing here knows a recipe by heart.

A recipe is the dict `lookup` returns: {"name", "seconds", "ingredients": [{"name", "type", "amount"}],
"products": [{"name", "type", "amount", "probability"?}]}. Rates are per second throughout."""
import math

# Items per second on one belt (both lanes), by belt tier, as the game defines them. Used only as a default when the
# caller has not looked the belt up; `lookup` on the belt entity gives the exact figure for the installed game.
BELT = {"transport-belt": 15.0, "fast-transport-belt": 30.0, "express-transport-belt": 45.0, "turbo-transport-belt": 60.0}


class PlanError(Exception):
    """A plan that cannot be made, with a sentence a model can act on."""


def amount_of(parts, name):
    """Average amount of `name` among a recipe's ingredients or products, counting probability."""
    total = 0.0
    for p in parts or []:
        if p.get("name") == name:
            total += (p.get("amount") or 0) * (p.get("probability") or 1)
    return total


def machine_rate(recipe, product, crafting_speed, productivity=0.0):
    """Units of `product` one machine makes per second. Productivity is a fraction (0.5 for +50%)."""
    out = amount_of(recipe.get("products"), product)
    if out <= 0:
        raise PlanError("the recipe '%s' does not make '%s'" % (recipe.get("name"), product))
    seconds = recipe.get("seconds") or 0
    if seconds <= 0 or crafting_speed <= 0:
        raise PlanError("the recipe '%s' has no crafting time or the machine has no speed" % recipe.get("name"))
    return out * (1 + productivity) * crafting_speed / seconds


def machines_for(recipe, product, per_second, crafting_speed, productivity=0.0):
    """Machines needed for a target rate, and what they consume. Returns exact and rounded-up counts."""
    if per_second <= 0:
        raise PlanError("the target rate must be above zero")
    each = machine_rate(recipe, product, crafting_speed, productivity)
    exact = per_second / each
    crafts = per_second / (amount_of(recipe["products"], product) * (1 + productivity))          # recipe runs per second
    inputs = {}
    for ing in recipe.get("ingredients") or []:
        inputs[ing["name"]] = inputs.get(ing["name"], 0.0) + ing["amount"] * crafts
    return {"recipe": recipe.get("name"), "product": product, "per_second": per_second, "machines_exact": exact,
            "machines": math.ceil(exact - 1e-9), "one_machine_per_second": each, "inputs_per_second": inputs}


def belts_for(per_second, belt_per_second=15.0):
    """Whole belts and lanes needed to carry a flow."""
    if belt_per_second <= 0:
        raise PlanError("the belt speed must be above zero")
    return {"belts": math.ceil(per_second / belt_per_second - 1e-9), "lanes": math.ceil(per_second / (belt_per_second / 2) - 1e-9),
            "fills_one_belt": per_second / belt_per_second}


def chain(product, per_second, recipe_for, speed_for, raw=(), productivity_for=None, depth=30):
    """The whole tree behind a product: every recipe with its machine count, and the raw inputs at the leaves.

    recipe_for(item)        -> the recipe to make the item with, or None if it is a raw input (ore, a fluid from a pump)
    speed_for(recipe)       -> crafting speed of the machine that will run it
    raw                     -> items never broken down further, whatever recipe_for says
    productivity_for(recipe)-> productivity fraction for that recipe (default none)

    Returns {"steps": [machines_for results, deepest first, one per recipe], "raw_per_second": {item: rate}}.
    A recipe that feeds on its own product (a loop) is refused: the caller must pick another recipe."""
    need, order, raw_need, raw_set = {}, [], {}, set(raw)

    def visit(item, rate, trail):
        if len(trail) > depth:
            raise PlanError("the chain behind '%s' is deeper than %d steps" % (product, depth))
        recipe = None if item in raw_set else recipe_for(item)
        if recipe is None:
            raw_need[item] = raw_need.get(item, 0.0) + rate
            return
        if item in trail:
            raise PlanError("the recipe '%s' needs its own product '%s': choose another recipe for it" % (recipe.get("name"), item))
        prod = productivity_for(recipe) if productivity_for else 0.0
        if item not in need:
            need[item] = {"rate": 0.0, "recipe": recipe, "productivity": prod}
            order.append(item)
        need[item]["rate"] += rate
        crafts = rate / (amount_of(recipe["products"], item) * (1 + prod))
        if amount_of(recipe["products"], item) <= 0:
            raise PlanError("the recipe '%s' does not make '%s'" % (recipe.get("name"), item))
        for ing in recipe.get("ingredients") or []:
            visit(ing["name"], ing["amount"] * crafts, trail + [item])

    visit(product, per_second, [])
    steps = []
    for item in reversed(order):                         # ingredients before what they feed
        n = need[item]
        steps.append(machines_for(n["recipe"], item, n["rate"], speed_for(n["recipe"]), n["productivity"]))
    return {"steps": steps, "raw_per_second": raw_need}
