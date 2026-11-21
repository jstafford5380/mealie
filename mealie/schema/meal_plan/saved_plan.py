from datetime import date
from typing import Annotated, Self
from uuid import UUID

from pydantic import ConfigDict, Field, StringConstraints, field_validator, model_validator

from mealie.schema._mealie import MealieModel
from mealie.schema._mealie.mealie_model import MealieOutModel
from mealie.schema.recipe.recipe import RecipeSummary

from .new_meal import WEEK_ENTRY_LENGTH, PlanEntryType


class SavedMealEntryCreate(MealieModel):
    # Sunday is 0. A null weekday is an entry for the whole week.
    weekday: Annotated[int | None, Field(ge=0, le=6)]
    entry_type: PlanEntryType
    title: str = ""
    text: str = ""
    recipe_id: UUID | None = None
    recipe_scale: Annotated[float, Field(gt=0, allow_inf_nan=False)] = 1

    @model_validator(mode="after")
    def require_recipe_or_title(self) -> Self:
        if self.recipe_id is None and not self.title.strip():
            raise ValueError("A recipe or a meal title is required")
        return self


class SavedMealEntryOut(SavedMealEntryCreate, MealieOutModel):
    recipe: RecipeSummary | None = None


class SavedMealPlanCreate(MealieModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    entries: list[SavedMealEntryCreate]


class SavedMealPlanSummary(MealieOutModel):
    id: UUID
    name: str
    model_config = ConfigDict(from_attributes=True)


class SavedMealPlanSave(SavedMealPlanCreate, SavedMealPlanSummary):
    pass


class SavedMealPlanOut(SavedMealPlanSummary):
    entries: list[SavedMealEntryOut]


class SavedMealPlanImport(MealieModel):
    week_start: date

    @field_validator("week_start")
    @classmethod
    def require_full_week(cls, value: date) -> date:
        if value > date.max - WEEK_ENTRY_LENGTH:
            raise ValueError("The destination week must fit within the calendar")
        return value
