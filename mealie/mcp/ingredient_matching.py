from collections.abc import Callable
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from mealie.db.models.recipe import IngredientFoodModel, IngredientUnitModel
from mealie.schema.recipe.recipe_ingredient import IngredientConfidence, ParsedIngredient
from mealie.services.parser_services.ingredient_parser import NLPParser


class IngredientCandidate(BaseModel):
    id: UUID
    name: str
    match_type: Literal["name", "plural", "abbreviation", "alias"]


class IngredientMatch(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "original_text": "1 lemon, juiced",
                    "quantity": 1,
                    "food": "lemon",
                    "unit": None,
                    "note": "juiced",
                    "food_candidates": [
                        {"id": "c9052338-d59c-4069-9df2-dbe1175e0a49", "name": "lemon", "match_type": "name"}
                    ],
                    "unit_candidates": [],
                    "confidence": {},
                    "parser": "nlp",
                    "requires_review": False,
                }
            ]
        }
    )

    original_text: str
    quantity: float | None
    food: str | None
    unit: str | None
    note: str | None
    food_candidates: list[IngredientCandidate]
    unit_candidates: list[IngredientCandidate]
    confidence: IngredientConfidence
    parser: Literal["nlp"] = "nlp"
    measurement_to_review: str | None = None
    requires_review: bool


class IngredientMatchingParser(NLPParser):
    def find_ingredient_match(self, ingredient: ParsedIngredient) -> ParsedIngredient:
        # Keep the parser's tokens so an alias collision cannot hide a candidate.
        return ingredient

    def _custom_units(self) -> dict[str, str]:
        # Pass through group-specific spellings for candidate lookup after parsing.
        units = super()._custom_units()
        for entry in self.data_matcher.units_by_id.values():
            for spelling in (entry.name, entry.plural_name, entry.abbreviation, entry.plural_abbreviation):
                if spelling:
                    units[spelling] = spelling
            for alias in entry.aliases:
                if alias.name:
                    units.setdefault(alias.name, alias.name)
        return units

    def match(self, original_text: str) -> IngredientMatch:
        sentence = self._parse_sentence(original_text)
        amount = self._extract_amount(sentence)
        measurement_to_review = amount.text if amount.RANGE or amount.APPROXIMATE or amount.MULTIPLIER else None
        parsed = self._convert_ingredient(sentence)
        ingredient = parsed.ingredient
        food = ingredient.food.name if ingredient.food else None
        unit = ingredient.unit.name if ingredient.unit else None
        foods = []
        units = []
        if food:
            key = IngredientFoodModel.normalize(food)
            for entry in self.data_matcher.foods_by_id.values():
                match_type = _match_type(
                    key,
                    IngredientFoodModel.normalize,
                    entry.name,
                    entry.plural_name,
                    [],
                    [alias.name for alias in entry.aliases],
                )
                if match_type:
                    foods.append(IngredientCandidate(id=entry.id, name=entry.name, match_type=match_type))
        if unit:
            key = IngredientUnitModel.normalize(unit)
            for entry in self.data_matcher.units_by_id.values():
                match_type = _match_type(
                    key,
                    IngredientUnitModel.normalize,
                    entry.name,
                    entry.plural_name,
                    [entry.abbreviation, entry.plural_abbreviation],
                    [alias.name for alias in entry.aliases],
                )
                if match_type:
                    units.append(IngredientCandidate(id=entry.id, name=entry.name, match_type=match_type))
        return IngredientMatch(
            original_text=original_text,
            quantity=ingredient.quantity if amount.starting_index >= 0 and not measurement_to_review else None,
            food=food,
            unit=unit,
            note=ingredient.note,
            food_candidates=foods,
            unit_candidates=units,
            confidence=parsed.confidence,
            measurement_to_review=measurement_to_review,
            requires_review=(
                len(foods) != 1
                or (unit is not None and len(units) != 1)
                or bool(ingredient.substitutions)
                or measurement_to_review is not None
            ),
        )


def _match_type(
    key: str,
    normalize: Callable[[str], str],
    name: str,
    plural: str | None,
    abbreviations: list[str | None],
    aliases: list[str],
) -> Literal["name", "plural", "abbreviation", "alias"] | None:
    if name and normalize(name) == key:
        return "name"
    if plural and normalize(plural) == key:
        return "plural"
    if any(value and normalize(value) == key for value in abbreviations):
        return "abbreviation"
    if any(alias and normalize(alias) == key for alias in aliases):
        return "alias"
    return None
