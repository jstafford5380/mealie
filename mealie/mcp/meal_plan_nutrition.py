import re
from collections.abc import Iterable
from math import fsum, isfinite

from pydantic import BaseModel, Field

from mealie.schema.recipe.recipe import RecipeSummary
from mealie.schema.recipe.recipe_nutrition import Nutrition

_AMOUNT = re.compile(r"\s*(\+?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*([a-zA-Z]*)\s*")
_MILLIGRAM_FIELDS = {"sodium_content", "cholesterol_content"}


class MealNutritionTotals(BaseModel):
    values: dict[str, float] = Field(
        description="Known sums, in kcal for calories, mg for sodium and cholesterol, and g otherwise."
    )
    missing_nutrients: list[str] = Field(
        description="Nutrients missing from at least one entry. Sums for these nutrients are partial or absent."
    )


def get_planned_servings(recipe: RecipeSummary | None, scale: float) -> float | None:
    if recipe is None:
        return None
    servings = (recipe.recipe_servings or recipe.recipe_yield_quantity or 1) * scale
    return servings if isfinite(servings) and servings > 0 else None


def get_portion_nutrition(recipe: RecipeSummary | None, servings: float | None) -> dict[str, float]:
    if recipe is None or recipe.nutrition is None or servings is None:
        return {}

    values = {}
    for name, raw in recipe.nutrition.model_dump(by_alias=False).items():
        if raw is None or (match := _AMOUNT.fullmatch(raw)) is None:
            continue
        amount, unit = match.groups()
        value = float(amount) * servings
        unit = unit.lower()
        if name == "calories":
            if unit not in ("", "kcal", "cal", "calorie", "calories"):
                continue
        elif name in _MILLIGRAM_FIELDS:
            if unit == "g":
                value *= 1000
            elif unit not in ("", "mg"):
                continue
        elif unit == "mg":
            value /= 1000
        elif unit not in ("", "g"):
            continue
        if isfinite(value):
            values[name] = value
    return values


def sum_portion_nutrition(portions: Iterable[dict[str, float]]) -> MealNutritionTotals:
    amounts: dict[str, list[float]] = {}
    missing = set()
    for portion in portions:
        missing.update(Nutrition.model_fields.keys() - portion.keys())
        for nutrient, value in portion.items():
            amounts.setdefault(nutrient, []).append(value)

    totals = {}
    for name, values in amounts.items():
        try:
            totals[name] = round(fsum(values), 6)
        except OverflowError:
            missing.add(name)
    return MealNutritionTotals(values=totals, missing_nutrients=sorted(missing))
