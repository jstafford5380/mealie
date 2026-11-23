from math import ceil, isclose, isfinite

# Standard units map to a ladder and a factor in its smallest unit.
_STANDARD_UNITS = {
    "teaspoon": ("kitchen_volume", 1),
    "tablespoon": ("kitchen_volume", 3),
    "fluid_ounce": ("kitchen_volume", 6),
    "cup": ("kitchen_volume", 48),
    "pint": ("kitchen_volume", 96),
    "quart": ("kitchen_volume", 192),
    "gallon": ("kitchen_volume", 768),
    "milligram": ("metric_mass", 0.001),
    "gram": ("metric_mass", 1),
    "kilogram": ("metric_mass", 1000),
    "milliliter": ("metric_volume", 1),
    "centiliter": ("metric_volume", 10),
    "deciliter": ("metric_volume", 100),
    "liter": ("metric_volume", 1000),
    "ounce": ("customary_mass", 1),
    "pound": ("customary_mass", 16),
}

# Each step specifies the threshold in base units, the displayed unit, its size,
# and the increment to buy. Recheck the threshold after rounding up.
_LADDERS = {
    "kitchen_volume": (
        (0, "tsp", 1, 0.5),
        (3, "tbsp", 3, 0.5),
        (24, "cup", 48, 0.25),
        (96, "pt", 96, 0.25),
        (192, "qt", 192, 0.25),
        (768, "gal", 768, 0.25),
    ),
    "metric_mass": (
        (0, "mg", 0.001, 1),
        (1, "g", 1, 1),
        (10, "g", 1, 5),
        (100, "g", 1, 10),
        (1000, "kg", 1000, 0.1),
    ),
    "metric_volume": ((0, "mL", 1, 1), (10, "mL", 1, 5), (100, "mL", 1, 10), (1000, "L", 1000, 0.1)),
    "customary_mass": ((0, "oz", 1, 0.5), (16, "lb", 16, 0.25)),
}


def _round_up(quantity: float, increment: float) -> float:
    steps = quantity / increment
    if not isfinite(steps):
        return quantity
    nearest = round(steps)
    count = nearest if nearest > 0 and isclose(steps, nearest, rel_tol=0, abs_tol=1e-9) else ceil(steps)
    return round(count * increment, 2)


def shopping_quantity(
    quantity: float, standard_unit: str | None, standard_quantity: float | None
) -> tuple[float, str] | None:
    if quantity <= 0 or not isfinite(quantity):
        return None
    if not standard_quantity or standard_unit not in _STANDARD_UNITS:
        # Counts, packages, and informal measures have no fixed conversion.
        return _round_up(quantity, 1), ""

    ladder, factor = _STANDARD_UNITS[standard_unit]
    base_quantity = quantity * standard_quantity * factor
    if not isfinite(base_quantity) or base_quantity <= 0:
        return None
    amounts = _LADDERS[ladder]
    selected_quantity = amount = base_quantity
    unit = amounts[0][1]
    for threshold, candidate, unit_size, increment in amounts:
        if selected_quantity < threshold:
            break
        amount = _round_up(base_quantity / unit_size, increment)
        selected_quantity = amount * unit_size
        unit = candidate
    return amount, unit
