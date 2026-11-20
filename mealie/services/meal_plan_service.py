from datetime import date
from uuid import UUID

from mealie.lang.providers import Translator
from mealie.repos.all_repositories import AllRepositories
from mealie.schema import mapper
from mealie.schema.meal_plan import PlanEntryCreate, PlanEntryOut, PlanEntrySave, PlanEntryUpdate
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


class MealPlanEntryNotFound(LookupError):
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
        filters = [query.query_filter]
        if not include_week_entries:
            filters.append("end_date IS NULL")
        if start_date:
            filters.append(f"(date >= {start_date} OR end_date >= {start_date})")
        if end_date:
            filters.append(f"date <= {end_date}")
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
        self.get_entry(entry_id)
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
