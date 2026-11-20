from datetime import date
from functools import cached_property

from dateutil.tz import tzlocal
from fastapi import APIRouter, Depends

from mealie.core.exceptions import mealie_registered_exceptions
from mealie.repos.all_repositories import get_repositories
from mealie.repos.repository_meals import RepositoryMeals
from mealie.routes._base import controller
from mealie.routes._base.base_controllers import BaseCrudController
from mealie.routes._base.mixins import HttpRepo
from mealie.routes._base.permissions import not_found
from mealie.schema.meal_plan import PlanEntryCreate, PlanEntryOut, PlanEntrySave, PlanEntryUpdate
from mealie.schema.meal_plan.new_meal import PlanEntryPagination, PlanEntryType, RandomPlanEntryCreate
from mealie.schema.meal_plan.plan_rules import PlanRulesDay
from mealie.schema.recipe.recipe import RecipeOut
from mealie.schema.response.pagination import PaginationQuery
from mealie.services.event_bus_service.event_types import EventOperation
from mealie.services.meal_plan_service import MealPlanEntryNotFound, MealPlanRecipeNotFound, MealPlanService
from mealie.services.query_filter.builder import QueryFilterBuilder

router = APIRouter(prefix="/households/mealplans", tags=["Households: Meal Plans"])


@controller(router)
class GroupMealplanController(BaseCrudController):
    @cached_property
    def repo(self) -> RepositoryMeals:
        return self.repos.meals

    @cached_property
    def service(self) -> MealPlanService:
        return MealPlanService(self.repos, self.user, self.translator, self.event_bus, self.integration_id)

    def registered_exceptions(self, ex: type[Exception]) -> str:
        registered = {
            **mealie_registered_exceptions(self.translator),
        }
        return registered.get(ex, self.t("generic.server-error"))

    @cached_property
    def mixins(self):
        return HttpRepo[PlanEntryCreate, PlanEntryOut, PlanEntryUpdate](
            self.repo,
            self.logger,
            self.registered_exceptions,
        )

    def _get_random_recipes_from_mealplan(
        self, plan_date: date, entry_type: PlanEntryType, limit: int = 1, end_date: date | None = None
    ) -> list[RecipeOut]:
        """
        Gets rules for a mealplan and returns a list of random recipes based on the rules.
        May return zero recipes if no recipes match the filter criteria.

        Recipes from all households are included unless the rules specify a household filter.
        """

        # date range entries (e.g. a week) aren't on a specific weekday, so only rules for all days apply to them
        day = PlanRulesDay.unset if end_date else PlanRulesDay.from_date(plan_date)
        rules = self.repos.group_meal_plan_rules.get_rules(day, entry_type.value)
        cross_household_recipes = get_repositories(
            self.session, group_id=self.group_id, household_id=None
        ).recipes.by_user(self.user.id)

        qf_string = QueryFilterBuilder.combine_filters(*[rule.query_filter_string for rule in rules])
        recipes_data = cross_household_recipes.page_all(
            pagination=PaginationQuery(
                page=1,
                per_page=limit,
                query_filter=qf_string,
                order_by="random",
                pagination_seed=self.repo._random_seed(),
            )
        )
        return recipes_data.items

    @router.get("", response_model=PlanEntryPagination)
    def get_all(
        self,
        q: PaginationQuery = Depends(PaginationQuery),
        start_date: date | None = None,
        end_date: date | None = None,
        include_week_entries: bool = False,
    ):
        # Week entries are opt-in for REST clients that expect a meal on a specific day.
        return self.service.list_entries(q, start_date, end_date, include_week_entries=include_week_entries)

    @router.post("", response_model=PlanEntryOut, status_code=201)
    def create_one(self, data: PlanEntryCreate):
        try:
            return self.service.create_entry(data)
        except MealPlanRecipeNotFound:
            raise not_found() from None
        except Exception as error:
            self.mixins.handle_exception(error)

    @router.get("/today")
    def get_todays_meals(self):
        local_tz = tzlocal()
        return self.repo.get_today(tz=local_tz)

    @router.post("/random", response_model=PlanEntryOut)
    def create_random_meal(self, data: RandomPlanEntryCreate):
        """
        `create_random_meal` is a route that provides the randomized functionality for meal planners.
        It operates by following the rules set out in the household's meal plan settings. If no settings
        are set, it will return any random meal.

        Refer to the meal plan settings routes for more information on how rules can be applied
        to the random meal selector.
        """
        random_recipes = self._get_random_recipes_from_mealplan(data.date, data.entry_type, end_date=data.end_date)
        if not random_recipes:
            raise not_found(self.t("mealplan.no-recipes-match-your-rules"))

        recipe = random_recipes[0]
        result = self.mixins.create_one(
            PlanEntrySave(
                date=data.date,
                end_date=data.end_date,
                entry_type=data.entry_type,
                recipe_id=recipe.id,
                group_id=self.group_id,
                user_id=self.user.id,
            )
        )

        self.service.publish_event(EventOperation.create, result)
        return result

    @router.get("/{item_id}", response_model=PlanEntryOut)
    def get_one(self, item_id: int):
        return self.mixins.get_one(item_id)

    @router.put("/{item_id}", response_model=PlanEntryOut)
    def update_one(self, item_id: int, data: PlanEntryUpdate):
        try:
            return self.service.update_entry(item_id, data)
        except MealPlanRecipeNotFound:
            raise not_found() from None
        except MealPlanEntryNotFound:
            raise not_found("Not found.") from None
        except Exception as error:
            self.mixins.handle_exception(error)

    @router.delete("/{item_id}", response_model=PlanEntryOut)
    def delete_one(self, item_id: int):
        result = self.mixins.delete_one(item_id)
        self.service.publish_event(EventOperation.delete, result)
        return result
