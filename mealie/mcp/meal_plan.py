import datetime
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated
from uuid import UUID

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from starlette.concurrency import run_in_threadpool

from mealie.lang.providers import get_locale_provider
from mealie.mcp.context import tool_context
from mealie.schema.meal_plan.new_meal import PlanEntryCreate, PlanEntryOut, PlanEntryType
from mealie.schema.response.pagination import OrderDirection, PaginationQuery
from mealie.services.event_bus_service.event_bus_service import EventBusService
from mealie.services.meal_plan_service import MealPlanEntryNotFound, MealPlanRecipeNotFound, MealPlanService
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

    @classmethod
    def from_entry(cls, entry: PlanEntryOut, group_slug: str) -> MealPlanEntry:
        recipe = entry.recipe
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
        )


class MealPlanPage(BaseModel):
    entries: list[MealPlanEntry]
    total: int
    next_page: int | None


class MealPlanPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: datetime.date | None = None
    end_date: datetime.date | None = Field(
        default=None,
        description="For a week entry, six days after the start date. Pass null to make it a single-day entry.",
    )
    entry_type: PlanEntryType | None = None
    note: str | None = None
    recipe_id: UUID | None = None
    recipe_scale: RecipeScale | None = None


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
        except ValidationError:
            raise ToolError("Invalid meal. Use a single date or set the end date six days after the start.") from None
        except MealPlanRecipeNotFound:
            raise ToolError("The recipe was not found in your Mealie library.") from None
        except MealPlanEntryNotFound:
            raise ToolError("The meal plan entry was not found in your household.") from None


def register_meal_plan_tools(server: FastMCP) -> None:
    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True))
    async def list_meal_plan(
        start_date: datetime.date,
        end_date: datetime.date,
        page: Annotated[int, Field(ge=1)] = 1,
    ) -> MealPlanPage:
        """List this household's meals in an inclusive date range, including overlapping week entries."""
        if start_date > end_date:
            raise ToolError("Start date must be on or before end date.")

        query = PaginationQuery(page=page, order_by="date,created_at", order_direction=OrderDirection.asc)

        def read() -> MealPlanPage:
            with _meal_plan() as (service, group_slug):
                results = service.list_entries(query, start_date, end_date, include_week_entries=True)
                return MealPlanPage(
                    entries=[MealPlanEntry.from_entry(entry, group_slug) for entry in results.items],
                    total=results.total,
                    next_page=page + 1 if page < results.total_pages else None,
                )

        return await run_in_threadpool(read)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False))
    async def create_meal_plan_entry(
        recipe_id: UUID,
        date: datetime.date,
        entry_type: PlanEntryType,
        end_date: datetime.date | None = None,
        note: str = "",
        recipe_scale: RecipeScale = 1.0,
    ) -> MealPlanEntry:
        """Save one meal from the recipe library.

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
                )
                return MealPlanEntry.from_entry(service.create_entry(data), group_slug)

        return await run_in_threadpool(create)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=True))
    async def update_meal_plan_entry(entry_id: Annotated[int, Field(gt=0)], changes: MealPlanPatch) -> MealPlanEntry:
        """Update fields of one meal while preserving omitted fields. To move a week entry, supply both dates."""
        fields = changes.model_dump(exclude_unset=True)
        if not fields:
            raise ToolError("Supply at least one meal plan field to update.")
        for name, value in fields.items():
            if value is None and name != "end_date":
                raise ToolError("Only end_date can be cleared. Omit other fields to keep their values.")
        if "note" in fields:
            fields["text"] = fields.pop("note")

        def update() -> MealPlanEntry:
            with _meal_plan() as (service, group_slug):
                return MealPlanEntry.from_entry(service.patch_entry(entry_id, fields), group_slug)

        return await run_in_threadpool(update)
