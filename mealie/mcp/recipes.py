from base64 import b64decode
from binascii import Error as Base64Error
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from hashlib import sha256
from io import BytesIO
from json import dumps
from math import isfinite
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4, uuid5

from anyio import run
from fastapi import HTTPException
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from PIL import Image
from pydantic import (
    MISSING,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    TypeAdapter,
    ValidationError,
    field_validator,
    model_validator,
)
from sqlalchemy.exc import IntegrityError, NoResultFound
from starlette.concurrency import run_in_threadpool

from mealie.core import exceptions
from mealie.lang.providers import get_locale_provider
from mealie.mcp.context import offload, tool_context
from mealie.mcp.ingredient_matching import IngredientMatch, IngredientMatchingParser
from mealie.pkgs import safehttp
from mealie.repos.all_repositories import get_repositories
from mealie.schema.recipe.recipe import RecipeDraft, RecipeOut, RecipeSummary
from mealie.schema.recipe.recipe_ingredient import (
    IngredientFoodAliasCreate,
    IngredientFoodOut,
    IngredientFoodSave,
    RecipeIngredient,
)
from mealie.schema.recipe.recipe_notes import RecipeNote
from mealie.schema.recipe.recipe_nutrition import Nutrition
from mealie.schema.recipe.recipe_organizers import OrganizerOut
from mealie.schema.recipe.recipe_step import RecipeStep
from mealie.schema.response.pagination import OrderDirection, PaginationQuery
from mealie.services import urls
from mealie.services.event_bus_service.event_bus_service import EventBusService
from mealie.services.event_bus_service.event_types import EventOperation
from mealie.services.recipe.recipe_data_service import InvalidDomainError, NotAnImageError, RecipeDataService
from mealie.services.recipe.recipe_service import RecipeService
from mealie.services.scraper.scraper import MAX_PUBLIC_RECIPE_IMAGE_BYTES, create_from_html

NUTRITION_PROVENANCE_KEY = "mealie.mcp.nutrition_provenance"
UNKNOWN_BASIS = "unknown"
READ_ONLY = ToolAnnotations(readOnlyHint=True)
WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False)
UPDATE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False)

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Positive = Annotated[float, Field(gt=0, allow_inf_nan=False)]

NUTRITION_EXAMPLE = {
    "values": {"calories": "503", "proteinContent": "37", "carbohydrateContent": "59", "fatContent": "13"},
    "estimated_fields": ["calories", "proteinContent", "carbohydrateContent", "fatContent"],
    "serving_basis": "per serving",
    "estimate_basis": "Calculated from ingredient nutrition estimates.",
}
NUTRITION_GUIDANCE = (
    "Put nutrient amounts inside nutrition.values. Use camelCase keys such as proteinContent. "
    "Use numbers or numeric strings without units. For estimates, list the matching keys in estimated_fields "
    "and provide estimate_basis. Use serving_basis to describe what the amounts cover."
)
ORGANIZER_GUIDANCE = (
    "Use list_categories, list_tags, and list_tools to find existing organizers. Supply their IDs or exact slugs "
    "in categories, tags, and tools. On update, omit a list to keep it, supply the complete list to replace it, "
    "or use [] to clear it."
)


class RecipeToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class IngredientAmount(RecipeToolInput):
    quantity: Annotated[float, Field(ge=0, le=100_000, allow_inf_nan=False)]
    text: Text = Field(description="Ingredient and unit text following the quantity, e.g. 'cups diced apples'.")


class CanonicalIngredient(RecipeToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "food_id": "c9052338-d59c-4069-9df2-dbe1175e0a49",
                    "unit_id": None,
                    "quantity": 1,
                    "note": "juiced",
                    "original_text": "1 lemon, juiced",
                }
            ]
        }
    )

    reference_id: UUID | None = None
    quantity: Annotated[float, Field(ge=0, le=100_000, allow_inf_nan=False)] | None = None
    food_id: UUID
    unit_id: UUID | None = None
    note: str | None = None
    original_text: str | None = None


class ReviewedIngredient(CanonicalIngredient):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "reference_id": "04409abb-e815-4ead-b91e-5c309d1a5989",
                    "food_id": "c9052338-d59c-4069-9df2-dbe1175e0a49",
                    "unit_id": None,
                    "quantity": 1,
                    "note": "juiced",
                }
            ]
        }
    )

    reference_id: UUID
    unit_id: UUID | None
    quantity: Annotated[float, Field(ge=0, le=100_000, allow_inf_nan=False)] | None


class NutritionEntry(BaseModel):
    value: str
    source: Literal["published", "user_provided", "estimated", "unknown"]
    serving_basis: str = UNKNOWN_BASIS
    estimate_basis: str | None = None


class NutritionValues(Nutrition):
    model_config = ConfigDict(extra="forbid")

    @field_validator("*", mode="before", json_schema_input_type=float | str | None)
    @classmethod
    def validate_amount(cls, value: Any) -> Any:
        if value is None:
            return value
        if isinstance(value, bool) or not isinstance(value, str | int | float):
            raise ValueError("Supply a number or numeric string without units")
        try:
            amount = float(value)
        except ValueError, OverflowError:
            raise ValueError("Supply a number or numeric string without units") from None
        if not isfinite(amount) or amount < 0:
            raise ValueError("Nutrition amounts must be finite and nonnegative")
        return value


class NutritionInput(RecipeToolInput):
    values: NutritionValues = Field(
        description=(
            'Supply numbers or numeric strings using camelCase keys such as "proteinContent". '
            "Use kcal for calories, mg for sodium and cholesterol, and g otherwise. "
            "On update, omit a nutrient to keep it or pass null to clear it."
        )
    )
    serving_basis: Text = Field(
        default=UNKNOWN_BASIS,
        description="What the supplied amounts cover, e.g. 'per serving (1 slice)' or 'whole recipe'.",
    )
    estimated_fields: list[str] = Field(
        default_factory=list,
        description="Keys from values that were estimated, e.g. calories or proteinContent. Requires estimate_basis.",
    )
    estimate_basis: Text | None = Field(
        default=None,
        description="Ingredient amounts and reference values used for estimates.",
    )

    @model_validator(mode="after")
    def validate_estimates(self) -> NutritionInput:
        values = self.values.model_dump(exclude_unset=True)
        aliases = {field.alias or name: name for name, field in Nutrition.model_fields.items()}
        self.estimated_fields = [aliases.get(field, field) for field in self.estimated_fields]
        if any(values.get(field) is None for field in self.estimated_fields):
            raise ValueError("Each estimated_fields entry must name a nutrient with a non-null amount in values")
        if self.estimated_fields and not self.estimate_basis:
            raise ValueError("Provide a basis for estimated nutrition")
        return self


class RecipeChanges(RecipeToolInput):
    model_config = ConfigDict(
        json_schema_extra={
            "not": {
                "required": ["image_url", "image_base64"],
                "properties": {"image_url": {"type": "string"}, "image_base64": {"type": "string"}},
            },
        }
    )

    name: Text | MISSING = MISSING
    servings: Positive | MISSING = MISSING
    ingredients: list[Text | IngredientAmount | CanonicalIngredient] | None = None
    instructions: list[Text] | None = None
    description: str | None = None
    yield_quantity: Positive | None = None
    yield_unit: Text | None = None
    prep_time: Text | None = None
    cook_time: Text | None = None
    total_time: Text | None = None
    nutrition: NutritionInput | None = None
    categories: list[Text] | MISSING = Field(
        default=MISSING, description="Existing category IDs or exact slugs. Replaces the list on update."
    )
    tags: list[Text] | MISSING = Field(
        default=MISSING, description="Existing tag IDs or exact slugs. Replaces the list on update."
    )
    tools: list[Text] | MISSING = Field(
        default=MISSING, description="Existing kitchen tool IDs or exact slugs. Replaces the list on update."
    )
    image_url: HttpUrl | None = Field(default=None, description="Public HTTP(S) URL of an image.")
    image_base64: str | None = Field(
        default=None,
        min_length=1,
        max_length=4 * ((MAX_PUBLIC_RECIPE_IMAGE_BYTES + 2) // 3),
        description="Standard base64-encoded image bytes, up to 5 MiB decoded.",
    )

    @model_validator(mode="after")
    def validate_image_source(self) -> RecipeChanges:
        if self.image_url is not None:
            if self.image_base64 is not None:
                raise ValueError("Supply either image_url or image_base64.")
            if self.image_url.username is not None or self.image_url.password is not None:
                raise ValueError("Provide a public image URL without credentials.")
        return self


class RecipeInput(RecipeChanges):
    name: Text
    servings: Positive
    ingredients: list[Text | IngredientAmount | CanonicalIngredient] = Field(min_length=1)
    instructions: list[Text] = Field(min_length=1)


class RecipeResult(BaseModel):
    id: UUID
    slug: str
    name: str
    url: str
    servings: float
    description: str | None


class RecipeSearchResult(BaseModel):
    items: list[RecipeResult]
    page: int
    total_pages: int
    total: int


class FoodResult(BaseModel):
    id: UUID
    name: str
    plural_name: str | None
    aliases: list[str]

    @classmethod
    def from_food(cls, food: IngredientFoodOut) -> FoodResult:
        return cls(
            id=food.id, name=food.name, plural_name=food.plural_name, aliases=[alias.name for alias in food.aliases]
        )


class FoodInput(RecipeToolInput):
    name: Text
    plural_name: Text | None = None
    aliases: list[Text] = Field(default_factory=list)


class FoodChanges(RecipeToolInput):
    name: Text | MISSING = MISSING
    plural_name: Text | None | MISSING = MISSING
    aliases: list[Text] | MISSING = MISSING


class FoodPage(BaseModel):
    items: list[FoodResult]
    total: int
    next_page: int | None


class UnitResult(FoodResult):
    abbreviation: str
    plural_abbreviation: str | None
    standard_unit: str | None
    standard_quantity: float | None


class UnitPage(BaseModel):
    items: list[UnitResult]
    total: int
    next_page: int | None


class RecipeOrganizer(BaseModel):
    id: UUID
    name: str
    slug: str

    @classmethod
    def from_organizer(cls, organizer: OrganizerOut) -> RecipeOrganizer:
        return cls(id=organizer.id, name=organizer.name, slug=organizer.slug)


class RecipeDetails(RecipeResult):
    source_url: str | None
    yield_quantity: float
    yield_unit: str | None
    prep_time: str | None
    cook_time: str | None
    total_time: str | None
    prep_time_seconds: int | None
    cook_time_seconds: int | None
    total_time_seconds: int | None
    ingredients: list[str]
    structured_ingredients: list[RecipeIngredient]
    instructions: list[RecipeStep]
    nutrition: Nutrition
    nutrition_provenance: dict[str, NutritionEntry]
    missing_nutrients: list[str]
    categories: list[RecipeOrganizer]
    tags: list[RecipeOrganizer]
    tools: list[RecipeOrganizer]


class NormalizationLine(BaseModel):
    reference_id: UUID
    status: Literal["exact", "alias", "ambiguous", "unmatched", "measurement_review", "parse_failure"]
    match: IngredientMatch | None = None
    proposed: CanonicalIngredient | None = None


class NormalizationPreview(BaseModel):
    recipe_id: UUID
    name: str
    revision: str
    current: list[RecipeIngredient]
    changes: list[NormalizationLine]


class NormalizationResult(BaseModel):
    recipe: RecipeDetails
    unresolved: list[UUID]


class ScaledIngredient(BaseModel):
    quantity: float | None = None
    unit: str | None = None
    food: str | None = None
    text: str
    unscaled: bool


class RecipeScale(BaseModel):
    id: UUID
    multiplier: float
    servings: float
    yield_quantity: float
    yield_unit: str | None
    ingredients: list[ScaledIngredient]


@contextmanager
def _recipe_errors() -> Iterator[None]:
    try:
        yield
    except exceptions.NoEntryFound:
        raise ToolError("Recipe not found.") from None
    except exceptions.PermissionDenied:
        raise ToolError("You do not have permission to edit this recipe.") from None
    except exceptions.SlugError, IntegrityError:
        raise ToolError("Unable to save the recipe. Check the name and try again.") from None


@contextmanager
def _recipe_service() -> Iterator[RecipeService]:
    with tool_context() as (_, user, repos), _recipe_errors():
        household = repos.households.get_one(user.household_id)
        if household is None:
            raise ToolError("The configured Mealie household is unavailable.")
        yield RecipeService(repos, user, household, get_locale_provider("en-US"))


def _group_slug(service: RecipeService) -> str:
    group = service.repos.groups.get_one(service.user.group_id)
    if group is None:
        raise ToolError("The configured Mealie group is unavailable.")
    return group.slug


def _read_provenance(recipe: RecipeOut | RecipeDraft, nutrition: Nutrition) -> dict[str, NutritionEntry]:
    raw = recipe.extras.get(NUTRITION_PROVENANCE_KEY)
    try:
        saved = TypeAdapter(dict[str, NutritionEntry]).validate_json(raw) if isinstance(raw, str) else {}
    except ValidationError:
        saved = {}

    return {
        field: saved[field]
        if field in saved and saved[field].value == value
        else NutritionEntry(value=value, source="unknown")
        for field, value in nutrition.model_dump().items()
        if value is not None
    }


def _apply_nutrition(
    draft: RecipeOut | RecipeDraft,
    nutrition: NutritionInput | None,
    *,
    published: bool = False,
    serving_size: str | None = None,
) -> dict[str, Any]:
    base = draft.nutrition or Nutrition()
    if published:
        provenance = {
            field: NutritionEntry(
                value=value,
                source="published",
                serving_basis=f"per {serving_size}" if serving_size else UNKNOWN_BASIS,
            )
            for field, value in base.model_dump(exclude_none=True).items()
        }
    else:
        provenance = _read_provenance(draft, base)

    if nutrition is not None:
        for field, value in nutrition.values.model_dump(exclude_unset=True).items():
            if published and field in provenance:
                continue
            if value is None:
                provenance.pop(field, None)
                continue
            estimated = field in nutrition.estimated_fields
            provenance[field] = NutritionEntry(
                value=value,
                source="estimated" if estimated else "user_provided",
                serving_basis=nutrition.serving_basis,
                estimate_basis=nutrition.estimate_basis if estimated else None,
            )

    extras = draft.extras.copy()
    if provenance:
        extras[NUTRITION_PROVENANCE_KEY] = TypeAdapter(dict[str, NutritionEntry]).dump_json(provenance).decode()
    else:
        extras.pop(NUTRITION_PROVENANCE_KEY, None)

    assert draft.id is not None
    reference_id = uuid5(draft.id, NUTRITION_PROVENANCE_KEY)
    notes = [note for note in draft.notes if note.reference_id != reference_id]
    estimates = [
        f"- {field.replace('_content', '').replace('_', ' ').capitalize()}: {entry.value} "
        f"({entry.serving_basis}). Basis: {entry.estimate_basis}"
        for field, entry in provenance.items()
        if entry.source == "estimated"
    ]
    if estimates:
        notes.append(RecipeNote(title="Estimated nutrition", text="\n".join(estimates), reference_id=reference_id))
    return {
        "nutrition": Nutrition.model_validate({field: entry.value for field, entry in provenance.items()}),
        "extras": extras,
        "notes": notes,
    }


def _resolve_organizers(
    references: list[str], kind: str, find: Callable[[str | UUID, str], OrganizerOut | None]
) -> list[OrganizerOut]:
    resolved = {}
    for reference in references:
        try:
            organizer_id = UUID(reference)
        except ValueError:
            organizer = find(reference, "slug")
        else:
            organizer = find(organizer_id, "id")
        if organizer is None:
            raise ToolError(f"Unknown {kind} {reference!r}. Use an existing ID or exact slug from your group.")
        resolved[organizer.id] = organizer
    return list(resolved.values())


def _resolve_ingredients(
    inputs: list[str | IngredientAmount | CanonicalIngredient],
    service: RecipeService,
    existing: RecipeOut | None,
) -> list[RecipeIngredient]:
    previous = {item.reference_id: item for item in existing.recipe_ingredient} if existing else {}
    used: set[UUID] = set()
    ingredients: list[RecipeIngredient] = []
    for item in inputs:
        if isinstance(item, str):
            ingredients.append(RecipeIngredient(note=item, quantity=None))
            continue
        if isinstance(item, IngredientAmount):
            ingredients.append(RecipeIngredient(quantity=item.quantity, note=item.text))
            continue

        base: dict[str, Any] = {}
        if item.reference_id is not None:
            if item.reference_id not in previous or item.reference_id in used:
                raise ToolError("Supply each existing ingredient reference ID at most once.")
            base = previous[item.reference_id].model_dump()
            used.add(item.reference_id)

        food = service.repos.ingredient_foods.get_one(item.food_id)
        if food is None:
            raise ToolError("The ingredient food was not found in your group.")
        unit = service.repos.ingredient_units.get_one(item.unit_id) if item.unit_id else None
        if item.unit_id and unit is None:
            raise ToolError("The ingredient unit was not found in your group.")

        changes = item.model_dump(exclude_unset=True, exclude={"food_id", "unit_id", "reference_id"})
        changes.update(food=food, display="")
        if "unit_id" in item.model_fields_set:
            changes["unit"] = unit
        if not base and "quantity" not in changes:
            changes["quantity"] = None
        ingredients.append(RecipeIngredient.model_validate(base | changes))
    return ingredients


def _draft_fields(data: RecipeChanges, service: RecipeService, existing: RecipeOut | None = None) -> dict[str, Any]:
    values = data.model_dump(
        exclude_unset=True,
        exclude={
            "ingredients",
            "instructions",
            "nutrition",
            "image_url",
            "image_base64",
            "categories",
            "tags",
            "tools",
        },
    )
    rename = {
        "servings": "recipe_servings",
        "yield_quantity": "recipe_yield_quantity",
        "yield_unit": "recipe_yield",
        "cook_time": "perform_time",
    }
    fields = {rename.get(field, field): value for field, value in values.items()}
    if data.ingredients is not None:
        fields["recipe_ingredient"] = _resolve_ingredients(data.ingredients, service, existing)
    if data.instructions is not None:
        fields["recipe_instructions"] = [RecipeStep(text=step) for step in data.instructions]
    if data.categories is not MISSING:
        fields["recipe_category"] = _resolve_organizers(data.categories, "category", service.repos.categories.get_one)
    if data.tags is not MISSING:
        fields["tags"] = _resolve_organizers(data.tags, "tag", service.repos.tags.get_one)
    if data.tools is not MISSING:
        fields["tools"] = _resolve_organizers(data.tools, "tool", service.repos.tools.get_one)
    return fields


def _result(recipe: RecipeSummary, group_slug: str) -> RecipeResult:
    return RecipeResult(
        id=recipe.id,
        slug=recipe.slug,
        name=recipe.name,
        url=urls.recipe_url(group_slug, recipe.slug, None),
        servings=recipe.recipe_servings,
        description=recipe.description,
    )


def _details(recipe: RecipeOut, group_slug: str) -> RecipeDetails:
    provenance = _read_provenance(recipe, recipe.nutrition)
    return RecipeDetails(
        **_result(recipe, group_slug).model_dump(),
        source_url=recipe.org_url,
        yield_quantity=recipe.recipe_yield_quantity,
        yield_unit=recipe.recipe_yield,
        prep_time=recipe.prep_time,
        cook_time=recipe.perform_time,
        total_time=recipe.total_time,
        prep_time_seconds=recipe.prep_time_seconds,
        cook_time_seconds=recipe.perform_time_seconds,
        total_time_seconds=recipe.total_time_seconds,
        ingredients=[item.display for item in recipe.recipe_ingredient],
        structured_ingredients=recipe.recipe_ingredient,
        instructions=recipe.recipe_instructions,
        nutrition=recipe.nutrition,
        nutrition_provenance=provenance,
        missing_nutrients=[field for field in Nutrition.model_fields if field not in provenance],
        categories=[RecipeOrganizer.from_organizer(item) for item in recipe.recipe_category],
        tags=[RecipeOrganizer.from_organizer(item) for item in recipe.tags],
        tools=[RecipeOrganizer.from_organizer(item) for item in recipe.tools],
    )


def _scale_recipe(recipe: RecipeOut, multiplier: float) -> RecipeScale:
    ingredients = [
        ScaledIngredient(
            quantity=item.quantity * multiplier if item.quantity is not None else None,
            unit=item.unit.name if item.unit else None,
            food=item.food.name if item.food else item.referenced_recipe.name if item.referenced_recipe else None,
            text=item.note or item.original_text or "",
            unscaled=not bool(item.quantity),
        )
        for item in recipe.recipe_ingredient
    ]
    servings = recipe.recipe_servings * multiplier
    yield_quantity = recipe.recipe_yield_quantity * multiplier
    if not all(isfinite(value) for value in (servings, yield_quantity, *(item.quantity or 0 for item in ingredients))):
        raise ToolError("Choose a smaller scale to keep ingredient and yield quantities finite.")
    return RecipeScale(
        id=recipe.id,
        multiplier=multiplier,
        servings=round(servings, 3),
        yield_quantity=round(yield_quantity, 3),
        yield_unit=recipe.recipe_yield,
        ingredients=ingredients,
    )


def _register_ingredient_tools(server: FastMCP) -> None:
    @server.tool(annotations=WRITE)
    @offload
    def create_food(data: FoodInput) -> FoodResult:
        """Create a canonical food in your Mealie group. Use list_foods to find existing foods first."""
        with tool_context() as (_, user, repos):
            if not user.can_organize:
                raise ToolError("You do not have permission to organize foods in this group.")
            try:
                food = repos.ingredient_foods.create(
                    IngredientFoodSave(
                        group_id=user.group_id,
                        name=data.name,
                        plural_name=data.plural_name,
                        aliases=[IngredientFoodAliasCreate(name=alias) for alias in dict.fromkeys(data.aliases)],
                    )
                )
            except IntegrityError:
                raise ToolError("A food with this name already exists in your group.") from None
            return FoodResult.from_food(food)

    @server.tool(annotations=UPDATE)
    @offload
    def update_food(food_id: UUID, changes: FoodChanges) -> FoodResult:
        """Edit a food by ID. Omit fields to keep them. Supply the complete alias list, or [] to clear it."""
        with tool_context() as (_, user, repos):
            if not user.can_organize:
                raise ToolError("You do not have permission to organize foods in this group.")
            if not changes.model_fields_set:
                raise ToolError("Supply at least one food field to update.")
            try:
                food = repos.ingredient_foods.update_identity(
                    food_id,
                    name=None if changes.name is MISSING else changes.name,
                    plural_name=None if changes.plural_name is MISSING else changes.plural_name,
                    replace_plural_name=changes.plural_name is not MISSING,
                    aliases=None if changes.aliases is MISSING else list(dict.fromkeys(changes.aliases)),
                )
            except NoResultFound:
                raise ToolError("The food was not found in your group.") from None
            except IntegrityError:
                raise ToolError("A food with this name already exists in your group.") from None
            return FoodResult.from_food(food)

    @server.tool(annotations=READ_ONLY)
    @offload
    def list_units(
        search: str | None = None,
        page: Annotated[int, Field(ge=1)] = 1,
        per_page: Annotated[int, Field(ge=1, le=100)] = 50,
    ) -> UnitPage:
        """List canonical measurement units in your group. Follow next_page for more."""
        with tool_context() as (_, _, repos):
            results = repos.ingredient_units.page_all(
                pagination=PaginationQuery(
                    page=page, per_page=per_page, order_by="name", order_direction=OrderDirection.asc
                ),
                search=search,
            )
            return UnitPage(
                items=[
                    UnitResult(
                        id=unit.id,
                        name=unit.name,
                        plural_name=unit.plural_name,
                        aliases=[alias.name for alias in unit.aliases],
                        abbreviation=unit.abbreviation,
                        plural_abbreviation=unit.plural_abbreviation,
                        standard_unit=unit.standard_unit,
                        standard_quantity=unit.standard_quantity,
                    )
                    for unit in results.items
                ],
                total=results.total,
                next_page=page + 1 if page < results.total_pages else None,
            )

    @server.tool(annotations=READ_ONLY)
    @offload
    def match_ingredient(text: Text) -> IngredientMatch:
        """Parse ingredient text and return all exact food and unit candidates in your group."""
        with tool_context() as (session, user, _):
            parser = IngredientMatchingParser(user.group_id, session, get_locale_provider("en-US"))
            return parser.match(text)

    @server.tool(annotations=READ_ONLY)
    @offload
    def preview_recipe_ingredient_normalization(recipe_id: UUID) -> NormalizationPreview:
        """Review proposed changes without saving. Pass the revision and selected changes to apply."""
        with _recipe_service() as service:
            recipe = service.get_one(recipe_id)
            parser = IngredientMatchingParser(service.user.group_id, service.repos.session, service.translator)
            return NormalizationPreview(
                recipe_id=recipe.id,
                name=recipe.name,
                revision=_recipe_revision(recipe),
                current=recipe.recipe_ingredient,
                changes=[
                    _preview_ingredient(parser, ingredient)
                    for ingredient in recipe.recipe_ingredient
                    if _needs_normalization(ingredient)
                ],
            )

    @server.tool(annotations=UPDATE)
    @offload
    def apply_recipe_ingredient_normalization(
        recipe_id: UUID,
        revision: str,
        changes: Annotated[list[ReviewedIngredient], Field(min_length=1)],
    ) -> NormalizationResult:
        """Apply only reviewed changes. Set unit_id to null for a unitless ingredient."""
        with _recipe_service() as service:
            return _apply_ingredient_changes(service, recipe_id, revision, changes)


def _recipe_revision(recipe: RecipeOut) -> str:
    snapshot = recipe.model_dump(mode="json")
    return sha256(dumps(snapshot, sort_keys=True).encode()).hexdigest()


def _needs_normalization(ingredient: RecipeIngredient) -> bool:
    return (
        not ingredient.referenced_recipe
        and not (ingredient.title and not ingredient.display)
        and (not ingredient.food or not ingredient.food.id or bool(ingredient.unit and not ingredient.unit.id))
    )


def _preview_ingredient(parser: IngredientMatchingParser, ingredient: RecipeIngredient) -> NormalizationLine:
    ref = ingredient.reference_id
    source = ingredient.original_text if ingredient.original_text is not None else ingredient.display
    try:
        match = parser.match(source) if source else None
    except ValueError:
        match = None
    if match is None:
        return NormalizationLine(reference_id=ref, status="parse_failure")
    if match.measurement_to_review:
        return NormalizationLine(reference_id=ref, status="measurement_review", match=match)
    if match.requires_review:
        ambiguous = len(match.food_candidates) > 1 or len(match.unit_candidates) > 1
        return NormalizationLine(reference_id=ref, status="ambiguous" if ambiguous else "unmatched", match=match)

    food = match.food_candidates[0]
    unit = next(iter(match.unit_candidates), None)
    alias = food.match_type == "alias" or (unit is not None and unit.match_type == "alias")
    return NormalizationLine(
        reference_id=ref,
        status="alias" if alias else "exact",
        match=match,
        proposed=CanonicalIngredient(
            reference_id=ref,
            food_id=food.id,
            unit_id=unit.id if unit else None,
            quantity=match.quantity,
            note=match.note,
            original_text=source,
        ),
    )


def _apply_ingredient_changes(
    service: RecipeService, recipe_id: UUID, revision: str, changes: list[ReviewedIngredient]
) -> NormalizationResult:
    with service.group_recipes.transaction():
        service.group_recipes.lock_for_ingredient_normalization(recipe_id)
        recipe = service.get_one(recipe_id)
        if _recipe_revision(recipe) != revision:
            raise ToolError("The recipe changed after preview. Preview it again before applying changes.")
        eligible = {item.reference_id for item in recipe.recipe_ingredient if _needs_normalization(item)}
        if any(change.reference_id not in eligible for change in changes):
            raise ToolError("Each approved change must refer to an unresolved ingredient in this recipe.")
        replacements = {item.reference_id: item for item in _resolve_ingredients(list(changes), service, recipe)}
        ingredients = []
        for item in recipe.recipe_ingredient:
            replacement = replacements.get(item.reference_id)
            if replacement is not None:
                replacement.original_text = item.original_text if item.original_text is not None else item.display
            ingredients.append(replacement or item)
        updated = service.patch_one(recipe_id, RecipeDraft(recipe_ingredient=ingredients))
    return NormalizationResult(
        recipe=_publish_and_format(service, updated, EventOperation.update),
        unresolved=[item.reference_id for item in updated.recipe_ingredient if _needs_normalization(item)],
    )


def register_recipe_tools(server: FastMCP) -> None:
    _register_ingredient_tools(server)

    @server.tool(annotations=READ_ONLY)
    @offload
    def list_foods(
        search: Text | None = None,
        page: Annotated[int, Field(ge=1)] = 1,
        per_page: Annotated[int, Field(ge=1, le=100)] = 50,
    ) -> FoodPage:
        """List canonical foods in your Mealie group. Search by food name or omit search to browse.

        Each result contains the stored food ID, name, plural name, and aliases. Follow next_page for more.
        """
        with tool_context() as (_, _, repos):
            results = repos.ingredient_foods.page_all(
                pagination=PaginationQuery(
                    page=page, per_page=per_page, order_by="name", order_direction=OrderDirection.asc
                ),
                search=search,
            )
            return FoodPage(
                items=[FoodResult.from_food(food) for food in results.items],
                total=results.total,
                next_page=page + 1 if page < results.total_pages else None,
            )

    @server.tool(annotations=READ_ONLY)
    @offload
    def list_categories() -> list[RecipeOrganizer]:
        """List all existing recipe categories in your group, including their IDs, names, and slugs."""
        with tool_context() as (_, _, repos):
            return [
                RecipeOrganizer.from_organizer(item)
                for item in repos.categories.get_all(order_by="name", order_descending=False)
            ]

    @server.tool(annotations=READ_ONLY)
    @offload
    def list_tags() -> list[RecipeOrganizer]:
        """List all existing recipe tags in your group, including their IDs, names, and slugs."""
        with tool_context() as (_, _, repos):
            return [
                RecipeOrganizer.from_organizer(item)
                for item in repos.tags.get_all(order_by="name", order_descending=False)
            ]

    @server.tool(annotations=READ_ONLY)
    @offload
    def list_tools() -> list[RecipeOrganizer]:
        """List all existing kitchen tools in your group, including their IDs, names, and slugs."""
        with tool_context() as (_, _, repos):
            return [
                RecipeOrganizer.from_organizer(item)
                for item in repos.tools.get_all(order_by="name", order_descending=False)
            ]

    @server.tool(annotations=READ_ONLY)
    @offload
    def search_recipes(
        search: str | None = None,
        tags: list[str] | None = None,
        categories: list[str] | None = None,
        cookbook: str | None = None,
        page: Annotated[int, Field(ge=1)] = 1,
        per_page: Annotated[int, Field(ge=1, le=50)] = 20,
    ) -> RecipeSearchResult:
        """Search recipes in your group by text, tag and category slugs or IDs, and cookbook slug or ID."""
        with tool_context() as (session, user, repos):
            group = repos.groups.get_one(user.group_id)
            if group is None:
                raise ToolError("The configured Mealie group is unavailable.")
            group_repos = get_repositories(session, group_id=user.group_id, household_id=None)
            cookbook_result = None
            if cookbook:
                try:
                    cookbook_id = UUID(cookbook)
                except ValueError:
                    cookbook_result = group_repos.cookbooks.get_one(cookbook, "slug")
                else:
                    cookbook_result = group_repos.cookbooks.get_one(cookbook_id, "id")
                if cookbook_result is None:
                    raise ToolError("Cookbook not found.")

            result = group_repos.recipes.by_user(user.id).page_all(
                pagination=PaginationQuery(page=page, per_page=per_page),
                search=search,
                tags=tags,
                categories=categories,
                cookbook=cookbook_result,
            )
            return RecipeSearchResult(
                items=[_result(recipe, group.slug) for recipe in result.items],
                page=result.page,
                total_pages=result.total_pages,
                total=result.total,
            )

    @server.tool(annotations=READ_ONLY)
    @offload
    def get_recipe(recipe: str) -> RecipeDetails:
        """Get a recipe by ID or slug, with ingredients, instructions, nutrition provenance, and organizers."""
        with _recipe_service() as service:
            return _details(service.get_one(recipe), _group_slug(service))

    @server.tool(
        annotations=WRITE,
        description=(
            f"Save a complete recipe. For a photo, supply image_url or image_base64. {ORGANIZER_GUIDANCE} "
            f"{NUTRITION_GUIDANCE}\n"
            "Example request:\n"
            + dumps(
                {
                    "data": {
                        "name": "Chicken and rice",
                        "servings": 1,
                        "ingredients": ["4 oz chicken", "1 cup cooked rice"],
                        "instructions": ["Cook the chicken and serve it with the rice."],
                        "nutrition": NUTRITION_EXAMPLE,
                    }
                }
            )
        ),
    )
    @offload
    def create_recipe(data: RecipeInput) -> RecipeDetails:
        with _recipe_service() as service:
            draft = RecipeDraft(id=uuid4(), **_draft_fields(data, service))
            if data.nutrition is not None:
                draft = RecipeDraft.model_validate(draft.model_dump() | _apply_nutrition(draft, data.nutrition))
            if data.image_url is None and data.image_base64 is None:
                return _save_recipe(service, draft)
            assert draft.id is not None
            image_service = RecipeDataService(draft.id)
            try:
                image = _load_image(data, image_service)
                with service.repos.recipes.transaction():
                    recipe = service.create_one(draft)
                    _store_image(service, recipe, image)
            except Exception:
                image_service.delete_all_data()
                raise
            return _publish_and_format(service, recipe, EventOperation.create)

    @server.tool(annotations=WRITE)
    async def import_recipe_url(url: HttpUrl, nutrition: NutritionInput | None = None) -> RecipeDetails:
        """Import structured recipe data and an available photo from a public recipe page.

        Optional estimates fill gaps in source nutrition.
        """
        if url.username or url.password:
            raise ToolError("Provide a public recipe URL without credentials.")
        return await run_in_threadpool(run, _import_recipe, str(url), nutrition)

    @server.tool(
        annotations=UPDATE,
        description=(
            "Update a recipe by ID. Supply only changed fields and give full lists to replace ingredients or steps. "
            "Include reference_id on retained structured ingredients to preserve instruction links. "
            "Legacy ingredient inputs create new rows. To replace the photo, supply image_url or image_base64. "
            f"{ORGANIZER_GUIDANCE} "
            f"{NUTRITION_GUIDANCE} Omit a nutrient to keep it or pass null to clear it.\n"
            "Example request:\n"
            + dumps(
                {
                    "recipe_id": "00000000-0000-4000-8000-000000000000",
                    "changes": {"nutrition": NUTRITION_EXAMPLE},
                }
            )
        ),
    )
    @offload
    def update_recipe(recipe_id: UUID, changes: RecipeChanges) -> RecipeDetails:
        return _update_recipe(recipe_id, changes)

    @server.tool(annotations=READ_ONLY)
    @offload
    def preview_recipe_scale(
        recipe: str,
        multiplier: Positive | None = None,
        target_servings: Positive | None = None,
    ) -> RecipeScale:
        """Preview scaled quantities without modifying the recipe.

        Supply exactly one of multiplier or target_servings. Use multiplier if the recipe has no serving count.
        Pass the returned multiplier to a meal-plan tool.
        """
        if (multiplier is None) == (target_servings is None):
            raise ToolError("Provide either a multiplier or a target serving count.")
        with _recipe_service() as service:
            saved = service.get_one(recipe)
            if multiplier is None:
                if not saved.recipe_servings > 0:
                    raise ToolError("This recipe has no serving count. Provide a multiplier.")
                assert target_servings is not None
                multiplier = target_servings / saved.recipe_servings
            if not isfinite(multiplier) or multiplier <= 0:
                raise ToolError("Choose a positive, finite scale multiplier.")
            return _scale_recipe(saved, multiplier)


def _update_recipe(recipe_id: UUID, changes: RecipeChanges) -> RecipeDetails:
    with _recipe_service() as service:
        recipe = service.get_one(recipe_id)
        fields = _draft_fields(changes, service, recipe)
        if changes.nutrition is not None:
            fields.update(_apply_nutrition(recipe, changes.nutrition))
        has_image = changes.image_url is not None or changes.image_base64 is not None
        if not fields and not has_image:
            raise ToolError("Provide at least one recipe field to update.")
        image = None
        if has_image:
            if not service.can_update([recipe.slug]):
                raise exceptions.PermissionDenied("You do not have permission to edit this recipe.")
            image = _load_image(changes, RecipeDataService(recipe.id))
        with service.repos.recipes.transaction():
            updated = service.patch_one(recipe_id, RecipeDraft(**fields)) if fields else recipe
            if image is not None:
                _store_image(service, updated, image)
        return _publish_and_format(service, updated, EventOperation.update)


def _load_image(data: RecipeChanges, image_service: RecipeDataService) -> bytes:
    if data.image_url is not None:
        try:
            downloaded = run(
                lambda: image_service.fetch_image(
                    str(data.image_url), max_bytes=MAX_PUBLIC_RECIPE_IMAGE_BYTES, public_only=True
                )
            )
        except InvalidDomainError:
            raise ToolError("The image URL must resolve to a public HTTP(S) endpoint.") from None
        except NotAnImageError:
            raise ToolError("The URL does not point to an image.") from None
        except safehttp.ResponseTooLargeError:
            raise ToolError("The image must be 5 MiB or smaller.") from None
        if downloaded is None:
            raise ToolError("Mealie could not download the image.")
        content, _ = downloaded
    else:
        assert data.image_base64 is not None
        try:
            content = b64decode(data.image_base64, validate=True)
        except Base64Error, ValueError:
            raise ToolError("Provide valid base64-encoded image bytes.") from None

    if len(content) > MAX_PUBLIC_RECIPE_IMAGE_BYTES:
        raise ToolError("The image must be 5 MiB or smaller.")
    return content


def _store_image(service: RecipeService, recipe: RecipeOut, content: bytes) -> None:
    try:
        with Image.open(BytesIO(content)) as source:
            if source.width * source.height > 25_000_000:
                raise ToolError("The image must be 25 megapixels or smaller.")
        recipe.image = service.update_recipe_image(recipe.slug, content, "webp")
    except OSError, Image.DecompressionBombError, SyntaxError, ValueError:
        raise ToolError("Provide a valid image that Mealie can open.") from None


def _publish_and_format(service: RecipeService, recipe: RecipeOut, operation: EventOperation) -> RecipeDetails:
    group_slug = _group_slug(service)
    event_bus = EventBusService(session=service.repos.session, translator=service.translator)
    service.publish_change(event_bus, "mcp", group_slug, recipe, operation)
    return _details(recipe, group_slug)


def _save_recipe(service: RecipeService, draft: RecipeDraft) -> RecipeDetails:
    with service.repos.recipes.transaction():
        recipe = service.create_one(draft)
    return _publish_and_format(service, recipe, EventOperation.create)


async def _import_recipe(url: str, nutrition: NutritionInput | None) -> RecipeDetails:
    with _recipe_service() as service:
        try:
            draft, extras = await create_from_html(url, service.repos, service.translator, structured_only=True)
        except safehttp.InvalidDomainError:
            raise ToolError("The recipe URL must resolve to a public HTTP(S) endpoint.") from None
        except HTTPException, safehttp.ResponseTooLargeError:
            raise ToolError("Mealie could not extract structured recipe data from this page.") from None
        if not draft.recipe_ingredient or not draft.recipe_instructions:
            raise ToolError("This page lacks a complete recipe. Supply the ingredients and instructions directly.")
        fields = _apply_nutrition(
            draft, nutrition, published=True, serving_size=extras.nutrition_serving_size if extras else None
        )
        draft = RecipeDraft.model_validate(draft.model_dump() | fields)
        return _save_recipe(service, draft)
