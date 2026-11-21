from collections.abc import Callable, Coroutine, Iterator
from contextlib import contextmanager
from functools import wraps
from math import isfinite
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4, uuid5

from anyio import run
from fastapi import HTTPException
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
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
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool

from mealie.core import exceptions
from mealie.lang.providers import get_locale_provider
from mealie.mcp.context import tool_context
from mealie.pkgs import safehttp
from mealie.repos.all_repositories import get_repositories
from mealie.schema.recipe.recipe import RecipeDraft, RecipeOut, RecipeSummary
from mealie.schema.recipe.recipe_ingredient import RecipeIngredient
from mealie.schema.recipe.recipe_notes import RecipeNote
from mealie.schema.recipe.recipe_nutrition import Nutrition
from mealie.schema.recipe.recipe_step import RecipeStep
from mealie.schema.response.pagination import PaginationQuery
from mealie.services import urls
from mealie.services.event_bus_service.event_bus_service import EventBusService
from mealie.services.event_bus_service.event_types import EventOperation
from mealie.services.recipe.recipe_service import RecipeService
from mealie.services.scraper.scraper import create_from_html

NUTRITION_PROVENANCE_KEY = "mealie.mcp.nutrition_provenance"
UNKNOWN_BASIS = "unknown"
READ_ONLY = ToolAnnotations(readOnlyHint=True)
WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False)
UPDATE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False)

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Positive = Annotated[float, Field(gt=0, allow_inf_nan=False)]


class RecipeToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class IngredientAmount(RecipeToolInput):
    quantity: Annotated[float, Field(ge=0, le=100_000, allow_inf_nan=False)]
    text: Text = Field(description="Ingredient and unit text following the quantity, e.g. 'cups diced apples'.")


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
    name: Text | MISSING = MISSING
    servings: Positive | MISSING = MISSING
    ingredients: list[Text | IngredientAmount] | None = None
    instructions: list[Text] | None = None
    description: str | None = None
    yield_quantity: Positive | None = None
    yield_unit: Text | None = None
    prep_time: Text | None = None
    cook_time: Text | None = None
    total_time: Text | None = None
    nutrition: NutritionInput | None = None


class RecipeInput(RecipeChanges):
    name: Text
    servings: Positive
    ingredients: list[Text | IngredientAmount] = Field(min_length=1)
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
    instructions: list[RecipeStep]
    nutrition: Nutrition
    nutrition_provenance: dict[str, NutritionEntry]
    missing_nutrients: list[str]


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


def _offload[**P, R](func: Callable[P, R]) -> Callable[P, Coroutine[Any, Any, R]]:
    @wraps(func)
    async def execute(*args: P.args, **kwargs: P.kwargs) -> R:
        return await run_in_threadpool(func, *args, **kwargs)

    return execute


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


def _draft_fields(data: RecipeChanges) -> dict[str, Any]:
    values = data.model_dump(exclude_unset=True, exclude={"ingredients", "instructions", "nutrition"})
    rename = {
        "servings": "recipe_servings",
        "yield_quantity": "recipe_yield_quantity",
        "yield_unit": "recipe_yield",
        "cook_time": "perform_time",
    }
    fields = {rename.get(field, field): value for field, value in values.items()}
    if data.ingredients is not None:
        fields["recipe_ingredient"] = [
            RecipeIngredient(note=item, quantity=None)
            if isinstance(item, str)
            else RecipeIngredient(quantity=item.quantity, note=item.text)
            for item in data.ingredients
        ]
    if data.instructions is not None:
        fields["recipe_instructions"] = [RecipeStep(text=step) for step in data.instructions]
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
        instructions=recipe.recipe_instructions,
        nutrition=recipe.nutrition,
        nutrition_provenance=provenance,
        missing_nutrients=[field for field in Nutrition.model_fields if field not in provenance],
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


def register_recipe_tools(server: FastMCP) -> None:
    @server.tool(annotations=READ_ONLY)
    @_offload
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
    @_offload
    def get_recipe(recipe: str) -> RecipeDetails:
        """Get a recipe by ID or slug, including ingredients, instructions, and nutrition provenance."""
        with _recipe_service() as service:
            return _details(service.get_one(recipe), _group_slug(service))

    @server.tool(annotations=WRITE)
    @_offload
    def create_recipe(data: RecipeInput) -> RecipeDetails:
        """Save a complete recipe. If nutrition values are estimated, identify the estimates and their basis."""
        with _recipe_service() as service:
            draft = RecipeDraft(id=uuid4(), **_draft_fields(data))
            if data.nutrition is not None:
                draft = RecipeDraft.model_validate(draft.model_dump() | _apply_nutrition(draft, data.nutrition))
            return _save_recipe(service, draft)

    @server.tool(annotations=WRITE)
    async def import_recipe_url(url: HttpUrl, nutrition: NutritionInput | None = None) -> RecipeDetails:
        """Import structured recipe data from a public recipe page. Optional estimates fill gaps in source nutrition."""
        if url.username or url.password:
            raise ToolError("Provide a public recipe URL without credentials.")
        return await run_in_threadpool(run, _import_recipe, str(url), nutrition)

    @server.tool(annotations=UPDATE)
    @_offload
    def update_recipe(recipe_id: UUID, changes: RecipeChanges) -> RecipeDetails:
        """Update a recipe by ID. Supply only changed fields and give full lists to replace ingredients or steps."""
        fields = _draft_fields(changes)
        with _recipe_service() as service:
            recipe = service.get_one(recipe_id)
            if changes.nutrition is not None:
                fields.update(_apply_nutrition(recipe, changes.nutrition))
            if not fields:
                raise ToolError("Provide at least one recipe field to update.")
            updated = service.patch_one(recipe_id, RecipeDraft(**fields))
            return _publish_and_format(service, updated, EventOperation.update)

    @server.tool(annotations=READ_ONLY)
    @_offload
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
