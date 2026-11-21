import datetime
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated
from uuid import UUID

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import MISSING, BaseModel, ConfigDict, Field, StringConstraints, ValidationError
from starlette.concurrency import run_in_threadpool

from mealie.lang.providers import get_locale_provider
from mealie.mcp.context import tool_context
from mealie.mcp.meal_plan_nutrition import (
    MealNutritionTotals,
    get_planned_servings,
    get_portion_nutrition,
    sum_portion_nutrition,
)
from mealie.schema.meal_plan.new_meal import PlanEntryCreate, PlanEntryOut, PlanEntryType
from mealie.schema.meal_plan.saved_plan import (
    SavedMealEntryCreate,
    SavedMealEntryOut,
    SavedMealPlanCreate,
    SavedMealPlanOut,
    SavedMealPlanSummary,
)
from mealie.schema.response.pagination import OrderDirection, PaginationQuery
from mealie.services.event_bus_service.event_bus_service import EventBusService
from mealie.services.meal_plan_service import (
    MealPlanEntryNotFound,
    MealPlanRecipeNotFound,
    MealPlanService,
    SavedMealPlanNotFound,
)
from mealie.services.urls.url_constructors import recipe_url

RecipeScale = Annotated[float, Field(gt=0, allow_inf_nan=False)]


class MealPlanEntry(BaseModel):
    id: int
    date: datetime.date
    end_date: datetime.date | None
    entry_type: PlanEntryType
    title: str
    note: str
    recipe_id: UUID | None
    recipe_name: str | None
    recipe_url: str | None
    recipe_scale: float
    recipe_batch_id: UUID | None
    leftover_batch_id: UUID | None
    planned_servings: float | None
    nutrition: dict[str, float] = Field(
        description="Known nutrition for the planned portion, in kcal, mg for sodium and cholesterol, and g otherwise."
    )

    @classmethod
    def from_entry(cls, entry: PlanEntryOut, group_slug: str) -> MealPlanEntry:
        recipe = entry.recipe
        servings = get_planned_servings(recipe, entry.recipe_scale)
        return cls(
            id=entry.id,
            date=entry.date,
            end_date=entry.end_date,
            entry_type=entry.entry_type,
            title=entry.title,
            note=entry.text,
            recipe_id=entry.recipe_id,
            recipe_name=recipe.name if recipe else None,
            recipe_url=recipe_url(group_slug, recipe.slug, None) if recipe else None,
            recipe_scale=entry.recipe_scale,
            recipe_batch_id=entry.recipe_batch_id,
            leftover_batch_id=entry.leftover_batch_id,
            planned_servings=servings,
            nutrition=get_portion_nutrition(recipe, servings),
        )


class MealPlanPage(BaseModel):
    entries: list[MealPlanEntry]
    total: int
    next_page: int | None
    nutrition_totals: MealNutritionTotals = Field(description="Totals across the full date range, regardless of page.")


class SavedMealEntryWithNutrition(SavedMealEntryOut):
    planned_servings: float | None
    nutrition: dict[str, float]


class SavedMealPlanWithNutrition(SavedMealPlanSummary):
    entries: list[SavedMealEntryWithNutrition]
    nutrition_totals: MealNutritionTotals

    @classmethod
    def from_plan(cls, plan: SavedMealPlanOut) -> SavedMealPlanWithNutrition:
        entries = []
        for entry in plan.entries:
            servings = get_planned_servings(entry.recipe, entry.recipe_scale)
            entries.append(
                SavedMealEntryWithNutrition(
                    **entry.model_dump(),
                    planned_servings=servings,
                    nutrition=get_portion_nutrition(entry.recipe, servings),
                )
            )
        return cls(
            id=plan.id,
            name=plan.name,
            entries=entries,
            nutrition_totals=sum_portion_nutrition(entry.nutrition for entry in entries),
        )


class LeftoverBatch(BaseModel):
    batch_id: UUID
    source_entry_id: int
    cooked_on: datetime.date
    cooked_for: PlanEntryType
    recipe_id: UUID
    recipe_name: str
    base_servings: float
    remaining_servings: float


class MealPlanPatch(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"minProperties": 1})

    date: datetime.date | MISSING = MISSING
    end_date: datetime.date | None = Field(
        default=None,
        description="For a week entry, six days after the start date. Pass null to make it a single-day entry.",
    )
    entry_type: PlanEntryType | MISSING = MISSING
    note: str | MISSING = MISSING
    recipe_id: UUID | MISSING = MISSING
    recipe_scale: RecipeScale | MISSING = MISSING
    recipe_batch_id: UUID | None = Field(
        default=None, description="UUID identifying this full batch. Pass null to stop cooking a full batch."
    )
    leftover_batch_id: UUID | None = Field(
        default=None, description="Existing source batch UUID to use. Pass null to stop using leftovers."
    )


class SavedMealEntryInput(SavedMealEntryCreate):
    model_config = ConfigDict(extra="forbid")
    recipe_batch_id: UUID | None = Field(default=None, description="Fresh UUID for an entry that cooks one full batch.")
    leftover_batch_id: UUID | None = Field(
        default=None, description="Use the recipeBatchId of an earlier meal for the same recipe within this saved plan."
    )


class SavedMealPlanInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    entries: list[SavedMealEntryInput] = Field(
        description="Meals in the reusable week. Set weekday to 0 for Sunday through 6 for Saturday, "
        "or null for the whole week. Supply a recipe_id or a title for each meal."
    )

    def to_create(self, service: MealPlanService) -> SavedMealPlanCreate:
        batches = {}
        for entry in self.entries:
            if entry.recipe_batch_id is not None:
                if entry.recipe_batch_id in batches or entry.recipe_scale > 1:
                    raise ToolError("Each full batch needs a unique UUID and a recipeScale of at most 1.")
                batches[entry.recipe_batch_id] = entry
        totals = {batch_id: entry.recipe_scale for batch_id, entry in batches.items()}
        preferences = service.repos.household_preferences.get_one(service.user.household_id) if totals else None
        first_day = preferences.first_day_of_week if preferences else 0
        for entry in self.entries:
            batch_id = entry.leftover_batch_id
            if batch_id is not None:
                source = batches.get(batch_id)
                if source is None or source.recipe_id != entry.recipe_id:
                    raise ToolError(
                        "A leftover entry must reference a full batch of the same recipe in this saved plan."
                    )
                if source.weekday is not None and entry.weekday is not None:
                    source_slot = ((source.weekday - first_day) % 7, MEAL_ORDER.index(source.entry_type))
                    target_slot = ((entry.weekday - first_day) % 7, MEAL_ORDER.index(entry.entry_type))
                    if source_slot > target_slot:
                        raise ToolError("In Meal Configurator, put the full batch before its leftover meals.")
                totals[batch_id] += entry.recipe_scale
                if totals[batch_id] > 1 + 1e-6:
                    raise ToolError("The saved plan allocates more servings than the full batch provides.")
        return SavedMealPlanCreate(name=self.name, entries=list(self.entries))


MEAL_ORDER = tuple(PlanEntryType)
BATCH_FIELDS = {"recipe_batch_id", "leftover_batch_id"}


def _precedes(source: PlanEntryCreate, date: datetime.date, entry_type: PlanEntryType) -> bool:
    return (source.date, MEAL_ORDER.index(source.entry_type)) <= (date, MEAL_ORDER.index(entry_type))


def _batch_entries(service: MealPlanService) -> list[PlanEntryOut]:
    query = PaginationQuery(per_page=-1, query_filter="recipe_batch_id IS NOT NULL OR leftover_batch_id IS NOT NULL")
    return service.list_entries(query, None, None, include_week_entries=False).items


def _batch_uses(
    source: PlanEntryCreate, entries: list[PlanEntryOut], exclude_id: int | None = None
) -> list[PlanEntryOut]:
    return [entry for entry in entries if entry.id != exclude_id and entry.leftover_batch_id == source.recipe_batch_id]


def _available_batches(
    entries: list[PlanEntryOut], date: datetime.date, entry_type: PlanEntryType, recipe_id: UUID | None
) -> list[LeftoverBatch]:
    batches = []
    for source in entries:
        recipe = source.recipe
        if (
            not source.recipe_batch_id
            or not source.recipe_id
            or not recipe
            or (recipe_id is not None and source.recipe_id != recipe_id)
            or not _precedes(source, date, entry_type)
        ):
            continue
        base_servings = recipe.recipe_servings or recipe.recipe_yield_quantity or 1
        allocated = source.recipe_scale + sum(entry.recipe_scale for entry in _batch_uses(source, entries))
        remaining = round(base_servings * (1 - allocated), 6)
        if remaining > 0:
            batches.append(
                LeftoverBatch(
                    batch_id=source.recipe_batch_id,
                    source_entry_id=source.id,
                    cooked_on=source.date,
                    cooked_for=source.entry_type,
                    recipe_id=source.recipe_id,
                    recipe_name=recipe.name,
                    base_servings=base_servings,
                    remaining_servings=remaining,
                )
            )
    return sorted(batches, key=lambda batch: (batch.cooked_on, batch.source_entry_id))


def _validate_calendar_batch(
    service: MealPlanService, entry: PlanEntryCreate, current: PlanEntryOut | None = None
) -> None:
    if not (entry.recipe_batch_id or entry.leftover_batch_id or (current and current.recipe_batch_id)):
        return
    entries = _batch_entries(service)
    current_id = current.id if current else None
    if current and current.recipe_batch_id and current.recipe_batch_id != entry.recipe_batch_id:
        if _batch_uses(current, entries):
            raise ToolError("Other meals use this batch. Reassign those entries before clearing or changing its UUID.")
    if entry.recipe_batch_id:
        if any(source.recipe_batch_id == entry.recipe_batch_id and source.id != current_id for source in entries):
            raise ToolError("This full batch UUID is already in use. Generate a fresh UUID.")
        consumers = _batch_uses(entry, entries, current_id)
        if any(
            consumer.recipe_id != entry.recipe_id or not _precedes(entry, consumer.date, consumer.entry_type)
            for consumer in consumers
        ):
            raise ToolError("A batch must use the same recipe as its leftover meals and precede them.")
        if entry.recipe_scale > 1 or entry.recipe_scale + sum(meal.recipe_scale for meal in consumers) > 1 + 1e-6:
            raise ToolError("The planned servings exceed what this full batch provides.")
    if entry.leftover_batch_id:
        source = next((meal for meal in entries if meal.recipe_batch_id == entry.leftover_batch_id), None)
        if (
            source is None
            or source.id == current_id
            or source.recipe_id != entry.recipe_id
            or not _precedes(source, entry.date, entry.entry_type)
        ):
            raise ToolError("Choose an earlier full batch of the same recipe from list_leftover_batches.")
        used_scale = source.recipe_scale + sum(meal.recipe_scale for meal in _batch_uses(source, entries, current_id))
        if used_scale + entry.recipe_scale > 1 + 1e-6:
            raise ToolError("This batch does not have enough unallocated servings. Check list_leftover_batches.")


@contextmanager
def _meal_plan() -> Iterator[tuple[MealPlanService, str]]:
    with tool_context() as (session, user, repos):
        group = repos.groups.get_one(user.group_id)
        if group is None:
            raise ToolError("The Mealie account has no available group.")
        translator = get_locale_provider("en-US")
        service = MealPlanService(
            repos, user, translator, EventBusService(session=session, translator=translator), "mcp"
        )
        try:
            yield service, group.slug
        except ValidationError as error:
            first = error.errors(include_input=False, include_context=False, include_url=False)[0]
            if first["loc"] == ("end_date",):
                raise ToolError(
                    "Invalid meal. Use a single date or set the end date six days after the start."
                ) from None
            message = first["msg"]
            raise ToolError(f"Invalid meal. {message.removeprefix('Value error, ')}") from None
        except MealPlanRecipeNotFound:
            raise ToolError("The recipe was not found in your Mealie library.") from None
        except SavedMealPlanNotFound:
            raise ToolError("The saved meal plan was not found in your household.") from None
        except MealPlanEntryNotFound:
            raise ToolError("The meal plan entry was not found in your household.") from None


def register_meal_plan_tools(server: FastMCP) -> None:
    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True))
    async def list_meal_plan(
        start_date: datetime.date,
        end_date: datetime.date,
        page: Annotated[int, Field(ge=1)] = 1,
    ) -> MealPlanPage:
        """List household meals in an inclusive date range, with planned portion nutrition and full-range totals.

        Every page repeats the same totals. Count overlapping whole-week entries once. Missing nutrient values
        are omitted and flagged in the totals. Nutrition reflects the portion eaten, including for leftovers.
        Use list_leftover_batches for unallocated servings available for a new meal.
        """
        if start_date > end_date:
            raise ToolError("Start date must be on or before end date.")

        page_size = PaginationQuery().per_page
        start = (page - 1) * page_size
        stop = start + page_size
        query = PaginationQuery(per_page=-1, order_by="date,created_at", order_direction=OrderDirection.asc)

        def read() -> MealPlanPage:
            with _meal_plan() as (service, group_slug):
                results = service.list_entries(query, start_date, end_date, include_week_entries=True)
                return MealPlanPage(
                    entries=[MealPlanEntry.from_entry(entry, group_slug) for entry in results.items[start:stop]],
                    total=results.total,
                    next_page=page + 1 if stop < results.total else None,
                    nutrition_totals=sum_portion_nutrition(
                        get_portion_nutrition(entry.recipe, get_planned_servings(entry.recipe, entry.recipe_scale))
                        for entry in results.items
                    ),
                )

        return await run_in_threadpool(read)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True))
    async def list_leftover_batches(
        date: datetime.date,
        entry_type: PlanEntryType,
        recipe_id: UUID | None = None,
    ) -> list[LeftoverBatch]:
        """Find live-calendar batches with unallocated servings for a proposed date and meal type.

        Already planned portions, including later meals, are reserved. Use a result's batch_id as
        leftover_batch_id and set recipe_scale to desired servings divided by base_servings.
        Saved Meal Configurator plans have separate batches. Read them with get_saved_meal_plan.
        """

        def read() -> list[LeftoverBatch]:
            with _meal_plan() as (service, _):
                return _available_batches(_batch_entries(service), date, entry_type, recipe_id)

        return await run_in_threadpool(read)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False))
    async def create_meal_plan_entry(
        recipe_id: UUID,
        date: datetime.date,
        entry_type: PlanEntryType,
        end_date: datetime.date | None = None,
        note: str = "",
        recipe_scale: RecipeScale = 1.0,
        recipe_batch_id: Annotated[
            UUID | None, Field(description="Fresh UUID when cooking one full recipe batch.")
        ] = None,
        leftover_batch_id: Annotated[
            UUID | None, Field(description="Source batch UUID from list_leftover_batches when using leftovers.")
        ] = None,
    ) -> MealPlanEntry:
        """Add one meal to the live calendar. Use create_saved_meal_plan to build a reusable week.

        recipe_scale is the portion eaten, even when cooking a full batch. Set recipe_batch_id to a fresh
        UUID to cook one full batch, leftover_batch_id to spend from an earlier batch, or omit both to cook
        only the planned portions. Batch links require a specific day.
        For a week entry, set end_date to six days after date. After a timeout, check list_meal_plan
        for the intended entry before retrying.
        """

        def create() -> MealPlanEntry:
            with _meal_plan() as (service, group_slug):
                data = PlanEntryCreate(
                    recipe_id=recipe_id,
                    date=date,
                    end_date=end_date,
                    entry_type=entry_type,
                    text=note,
                    recipe_scale=recipe_scale,
                    recipe_batch_id=recipe_batch_id,
                    leftover_batch_id=leftover_batch_id,
                )
                _validate_calendar_batch(service, data)
                return MealPlanEntry.from_entry(service.create_entry(data), group_slug)

        return await run_in_threadpool(create)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=True))
    async def update_meal_plan_entry(entry_id: Annotated[int, Field(gt=0)], changes: MealPlanPatch) -> MealPlanEntry:
        """Update one live calendar meal. Omitted fields stay the same. Pass null to clear either batch ID.

        recipe_scale is the portion eaten and changes how many servings remain in a linked batch.
        When switching batch modes, clear the previous ID in the same update. To move a week entry, supply both dates.
        """
        fields = changes.model_dump(exclude_unset=True)
        if not fields:
            raise ToolError("Supply at least one meal plan field to update.")
        if "note" in fields:
            fields["text"] = fields.pop("note")

        def update() -> MealPlanEntry:
            with _meal_plan() as (service, group_slug):
                if fields.keys() & (BATCH_FIELDS | {"recipe_id", "recipe_scale", "date", "end_date", "entry_type"}):
                    current = service.get_entry(entry_id)
                    if current.recipe_batch_id or current.leftover_batch_id or fields.keys() & BATCH_FIELDS:
                        candidate = PlanEntryCreate.model_validate(current.model_dump() | fields)
                        _validate_calendar_batch(service, candidate, current)
                return MealPlanEntry.from_entry(service.patch_entry(entry_id, fields), group_slug)

        return await run_in_threadpool(update)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True))
    async def list_saved_meal_plans() -> list[SavedMealPlanSummary]:
        """List the names and IDs of reusable weekly plans in this household's Meal Configurator."""

        def read() -> list[SavedMealPlanSummary]:
            with _meal_plan() as (service, _):
                return service.list_saved_plans()

        return await run_in_threadpool(read)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True))
    async def get_saved_meal_plan(plan_id: UUID) -> SavedMealPlanWithNutrition:
        """Read meals, batch links, planned portion nutrition, and totals for a saved Meal Configurator plan.

        Batch IDs are local to the saved plan. Each import into Meal Planner creates new batch IDs.
        """

        def read() -> SavedMealPlanWithNutrition:
            with _meal_plan() as (service, _):
                return SavedMealPlanWithNutrition.from_plan(service.get_saved_plan(plan_id))

        return await run_in_threadpool(read)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False))
    async def create_saved_meal_plan(plan: SavedMealPlanInput) -> SavedMealPlanWithNutrition:
        """Create a named, date-free weekly plan in Meal Configurator.

        To cook a full batch, set recipeBatchId to a new UUID on a dated weekday entry. Set leftoverBatchId
        on later entries to use that batch of the same recipe. The total recipeScale across linked meals
        must fit in one batch (1.0). Entries for the whole week cannot use batch links.
        The user can import it into a calendar week from Meal Planner. After a timeout, check
        list_saved_meal_plans for the intended plan before retrying.
        """

        def create() -> SavedMealPlanWithNutrition:
            with _meal_plan() as (service, _):
                return SavedMealPlanWithNutrition.from_plan(service.save_plan(plan.to_create(service)))

        return await run_in_threadpool(create)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=True))
    async def update_saved_meal_plan(plan_id: UUID, plan: SavedMealPlanInput) -> SavedMealPlanWithNutrition:
        """Replace a saved plan's name and full list of meals.

        Read it first and include all meals to keep, preserving their batch IDs and portion scales.
        To add or change leftovers, keep the source batch and consumers in this plan.
        """

        def update() -> SavedMealPlanWithNutrition:
            with _meal_plan() as (service, _):
                return SavedMealPlanWithNutrition.from_plan(service.save_plan(plan.to_create(service), plan_id))

        return await run_in_threadpool(update)
