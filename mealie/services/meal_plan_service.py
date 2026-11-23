from datetime import date, timedelta
from uuid import UUID, uuid4

from sqlalchemy.exc import NoResultFound

from mealie.lang.providers import Translator
from mealie.repos.all_repositories import AllRepositories
from mealie.schema import mapper
from mealie.schema.meal_plan import PlanEntryCreate, PlanEntryOut, PlanEntrySave, PlanEntryUpdate
from mealie.schema.meal_plan.new_meal import WEEK_ENTRY_LENGTH
from mealie.schema.meal_plan.saved_plan import (
    SavedMealEntryOut,
    SavedMealPlanCreate,
    SavedMealPlanOut,
    SavedMealPlanSave,
    SavedMealPlanSummary,
)
from mealie.schema.recipe.recipe import RecipeSummary
from mealie.schema.response.pagination import PaginationBase, PaginationQuery
from mealie.schema.user.user import PrivateUser
from mealie.services._base_service import BaseService
from mealie.services.event_bus_service.event_bus_service import EventBusService
from mealie.services.event_bus_service.event_types import EventMealplanData, EventOperation, EventTypes
from mealie.services.query_filter.builder import QueryFilterBuilder

MEALPLAN_EVENTS = {
    EventOperation.create: EventTypes.mealplan_entry_created,
    EventOperation.update: EventTypes.mealplan_entry_updated,
    EventOperation.delete: EventTypes.mealplan_entry_deleted,
}


def meal_plan_date_filters(start_date: date | None, end_date: date | None) -> list[str]:
    filters = []
    if start_date:
        filters.append(f"(date >= {start_date} OR end_date >= {start_date})")
    if end_date:
        filters.append(f"date <= {end_date}")
    return filters


class MealPlanEntryNotFound(LookupError):
    pass


class SavedMealPlanNotFound(LookupError):
    pass


class MealPlanRecipeNotFound(LookupError):
    pass


class MealPlanService(BaseService):
    def __init__(
        self,
        repos: AllRepositories,
        user: PrivateUser,
        translator: Translator,
        event_bus: EventBusService,
        integration_id: str,
    ) -> None:
        super().__init__()
        self.repos = repos
        self.user = user
        self.translator = translator
        self.event_bus = event_bus
        self.integration_id = integration_id

    def list_entries(
        self,
        query: PaginationQuery,
        start_date: date | None,
        end_date: date | None,
        *,
        include_week_entries: bool,
    ) -> PaginationBase[PlanEntryOut]:
        filters = [query.query_filter, *meal_plan_date_filters(start_date, end_date)]
        if not include_week_entries:
            filters.append("end_date IS NULL")
        query.query_filter = QueryFilterBuilder.combine_filters(*filters)
        return self.repos.meals.page_all(pagination=query)

    def get_entry(self, entry_id: int) -> PlanEntryOut:
        entry = self.repos.meals.get_one(entry_id)
        if entry is None:
            raise MealPlanEntryNotFound
        return entry

    def create_entry(self, data: PlanEntryCreate) -> PlanEntryOut:
        self._require_group_recipe(data.recipe_id)
        save_data = mapper.cast(data, PlanEntrySave, group_id=self.user.group_id, user_id=self.user.id)
        entry = self.repos.meals.create(save_data)
        self.publish_event(EventOperation.create, entry)
        return entry

    def update_entry(self, entry_id: int, data: PlanEntryUpdate) -> PlanEntryOut:
        self._require_group_recipe(data.recipe_id)
        current = self.get_entry(entry_id)
        batch_fields = {"recipe_batch_id", "leftover_batch_id"}
        if (
            data.recipe_id == current.recipe_id
            and data.end_date is None
            and not batch_fields.intersection(data.model_fields_set)
        ):
            data = data.model_copy(update=current.model_dump(include=batch_fields))
        entry = self.repos.meals.update(entry_id, data)
        self.publish_event(EventOperation.update, entry)
        return entry

    def patch_entry(self, entry_id: int, fields: dict) -> PlanEntryOut:
        current = self.get_entry(entry_id)
        validated = PlanEntryCreate.model_validate(current.model_dump() | fields)
        self._require_group_recipe(validated.recipe_id)
        columns = set(fields)
        if columns & {"date", "end_date"}:
            columns.update(("date", "end_date"))
        entry = self.repos.meals.update(entry_id, validated.model_dump(include=columns))
        self.publish_event(EventOperation.update, entry)
        return entry

    def _require_group_recipe(self, recipe_id: UUID | None) -> None:
        if recipe_id is None:
            return
        # Native meal plans can reference the recipe library across households in the same group.
        group_recipes = AllRepositories(self.repos.session, group_id=self.user.group_id, household_id=None).recipes
        if group_recipes.get_one(recipe_id, "id") is None:
            raise MealPlanRecipeNotFound

    def publish_event(self, operation: EventOperation, entry: PlanEntryOut) -> None:
        kind = "range-entry" if entry.end_date else "entry"
        day_type = self.translator.t(f"mealplan.entry-type.{entry.entry_type.value}", default=entry.entry_type.value)
        message = self.translator.t(
            f"notifications.mealplan-{kind}-{operation.value}",
            date=entry.date,
            end_date=entry.end_date,
            entry_type=day_type,
        )
        self.event_bus.dispatch(
            integration_id=self.integration_id,
            group_id=entry.group_id,
            household_id=entry.household_id,
            event_type=MEALPLAN_EVENTS[operation],
            document_data=EventMealplanData(
                operation=operation,
                mealplan_id=entry.id,
                recipe_id=entry.recipe_id,
                recipe_name=entry.recipe.name if entry.recipe else None,
                recipe_slug=entry.recipe.slug if entry.recipe else None,
                date=entry.date,
                end_date=entry.end_date,
            ),
            message=message,
        )

    def _get_saved_plan(self, plan_id: UUID) -> SavedMealPlanSave:
        plan = self.repos.saved_meal_plans.get_one(plan_id)
        if plan is None:
            raise SavedMealPlanNotFound
        return plan

    def list_saved_plans(self) -> list[SavedMealPlanSummary]:
        plans = sorted(self.repos.saved_meal_plans.get_all(), key=lambda plan: plan.name.casefold())
        return [SavedMealPlanSummary(id=plan.id, name=plan.name) for plan in plans]

    def get_saved_plan(self, plan_id: UUID) -> SavedMealPlanOut:
        return self._saved_plan_out(self._get_saved_plan(plan_id))

    def delete_saved_plan(self, plan_id: UUID) -> SavedMealPlanSummary:
        try:
            plan = self.repos.saved_meal_plans.delete(plan_id)
        except NoResultFound:
            raise SavedMealPlanNotFound from None
        return SavedMealPlanSummary(id=plan.id, name=plan.name)

    def _saved_plan_out(self, plan: SavedMealPlanSave) -> SavedMealPlanOut:
        group_recipes = AllRepositories(self.repos.session, group_id=self.user.group_id, household_id=None).recipes
        recipes: dict[UUID, RecipeSummary | None] = {
            recipe_id: group_recipes.get_one(recipe_id, "id", override_schema=RecipeSummary)
            for recipe_id in {entry.recipe_id for entry in plan.entries if entry.recipe_id is not None}
        }
        return SavedMealPlanOut(
            id=plan.id,
            name=plan.name,
            entries=[
                SavedMealEntryOut(
                    **entry.model_dump(), recipe=recipes.get(entry.recipe_id) if entry.recipe_id else None
                )
                for entry in plan.entries
            ],
        )

    def save_plan(self, data: SavedMealPlanCreate, plan_id: UUID | None = None) -> SavedMealPlanOut:
        for recipe_id in {entry.recipe_id for entry in data.entries}:
            self._require_group_recipe(recipe_id)

        payload = data.model_dump(mode="json")
        if plan_id is None:
            plan = self.repos.saved_meal_plans.create(
                payload | {"group_id": self.user.group_id, "household_id": self.user.household_id}
            )
        else:
            self._get_saved_plan(plan_id)
            plan = self.repos.saved_meal_plans.update(plan_id, payload)

        return self._saved_plan_out(plan)

    def import_saved_plan(self, plan_id: UUID, week_start: date) -> list[PlanEntryOut]:
        plan = self._get_saved_plan(plan_id)
        week_start_day = (week_start.weekday() + 1) % 7
        entries = []
        batch_ids = {
            batch_id: uuid4()
            for entry in plan.entries
            for batch_id in (entry.recipe_batch_id, entry.leftover_batch_id)
            if batch_id is not None
        }
        for entry in plan.entries:
            offset = (entry.weekday - week_start_day) % 7 if entry.weekday is not None else 0
            entries.append(
                PlanEntrySave(
                    **entry.model_dump(exclude={"weekday", "recipe_batch_id", "leftover_batch_id"}),
                    recipe_batch_id=batch_ids[entry.recipe_batch_id] if entry.recipe_batch_id else None,
                    leftover_batch_id=batch_ids[entry.leftover_batch_id] if entry.leftover_batch_id else None,
                    date=week_start + timedelta(days=offset),
                    end_date=week_start + WEEK_ENTRY_LENGTH if entry.weekday is None else None,
                    group_id=self.user.group_id,
                    user_id=self.user.id,
                )
            )

        with self.repos.meals.transaction():
            for recipe_id in {entry.recipe_id for entry in entries}:
                self._require_group_recipe(recipe_id)
            created = self.repos.meals.create_many(entries)

        for entry_out in created:
            self.publish_event(EventOperation.create, entry_out)
        return created
