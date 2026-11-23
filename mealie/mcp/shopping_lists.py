from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import HTTPException
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import MISSING, BaseModel, ConfigDict, Field, StringConstraints
from sqlalchemy.exc import NoResultFound

from mealie.lang.providers import get_locale_provider
from mealie.mcp.context import offload, tool_context
from mealie.schema.household.group_shopping_list import (
    ShoppingAmount,
    ShoppingListAddRecipeParamsBulk,
    ShoppingListCreate,
    ShoppingListFromMealPlan,
    ShoppingListItemCreate,
    ShoppingListItemUpdateBulk,
    ShoppingListOut,
    ShoppingListSummary,
)
from mealie.services.event_bus_service.event_bus_service import EventBusService
from mealie.services.event_bus_service.event_types import EventOperation, EventShoppingListData, EventTypes
from mealie.services.household_services.shopping_lists import ShoppingListService

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Quantity = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Scale = Annotated[float, Field(gt=0, allow_inf_nan=False)]
READ = ToolAnnotations(readOnlyHint=True)
ADD = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False)
EDIT = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=True)


class ListSummary(BaseModel):
    id: UUID
    name: str | None

    @classmethod
    def from_list(cls, shopping_list: ShoppingListSummary | ShoppingListOut) -> ListSummary:
        return cls(id=shopping_list.id, name=shopping_list.name)


class ListItemRecipe(BaseModel):
    recipe_id: UUID
    scale: float | None
    quantity_per_recipe: float | None


class ListItem(BaseModel):
    id: UUID
    display: str
    note: str | None
    quantity: float
    measured_quantity: float | None
    shopping_amount: ShoppingAmount | None = Field(
        description="Suggested grocery amount. Use quantity and unit on the item for the exact amount."
    )
    checked: bool
    food: str | None
    food_id: UUID | None
    unit: str | None
    unit_id: UUID | None
    label: str | None
    recipe_references: list[ListItemRecipe]


class ListRecipe(BaseModel):
    recipe_id: UUID
    recipe_name: str
    scale: float


class ListDetails(ListSummary):
    items: list[ListItem]
    recipes: list[ListRecipe]

    @classmethod
    def from_details(cls, shopping_list: ShoppingListOut) -> ListDetails:
        return cls(
            id=shopping_list.id,
            name=shopping_list.name,
            items=[
                ListItem(
                    id=item.id,
                    display=item.display,
                    note=item.note,
                    quantity=item.quantity,
                    measured_quantity=None if item.recipe_references and item.quantity == 0 else item.quantity,
                    shopping_amount=item.shopping_amount,
                    checked=item.checked,
                    food=item.food.name if item.food else None,
                    food_id=item.food_id,
                    unit=item.unit.name if item.unit else None,
                    unit_id=item.unit_id,
                    label=item.label.name if item.label else None,
                    recipe_references=[
                        ListItemRecipe(
                            recipe_id=ref.recipe_id,
                            scale=ref.recipe_scale,
                            quantity_per_recipe=ref.recipe_quantity or None,
                        )
                        for ref in item.recipe_references
                    ],
                )
                for item in shopping_list.list_items
            ],
            recipes=[
                ListRecipe(recipe_id=ref.recipe_id, recipe_name=ref.recipe.name, scale=ref.recipe_quantity)
                for ref in shopping_list.recipe_references
            ],
        )


class NewShoppingItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Text
    quantity: Quantity = 1


class ShoppingItemChanges(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"minProperties": 1})
    note: str | MISSING = MISSING
    quantity: Quantity | MISSING = MISSING
    checked: bool | MISSING = MISSING


class ShoppingRecipeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recipe_id: UUID
    scale: Scale = 1


@contextmanager
def _shopping_lists() -> Iterator[tuple[ShoppingListService, UUID, EventBusService]]:
    with tool_context() as (session, user, repos):
        event_bus = EventBusService(session=session, translator=get_locale_provider("en-US"))
        try:
            yield ShoppingListService(repos), user.id, event_bus
        except NoResultFound:
            raise ToolError("The shopping list or item was not found in your household.") from None
        except HTTPException as error:
            if error.status_code == 404:
                raise ToolError("The shopping list, item, or recipe was not found in the available scope.") from None
            raise


def _get_list(service: ShoppingListService, list_id: UUID) -> ShoppingListOut:
    result = service.shopping_lists.get_one(list_id)
    if result is None:
        raise ToolError("The shopping list was not found in your household.")
    return result


def _publish(event_bus: EventBusService, shopping_list: ShoppingListOut, operation: EventOperation) -> None:
    event_type = {
        EventOperation.create: EventTypes.shopping_list_created,
        EventOperation.update: EventTypes.shopping_list_updated,
        EventOperation.delete: EventTypes.shopping_list_deleted,
    }[operation]
    event_bus.dispatch(
        integration_id="mcp",
        group_id=shopping_list.group_id,
        household_id=shopping_list.household_id,
        event_type=event_type,
        document_data=EventShoppingListData(operation=operation, shopping_list_id=shopping_list.id),
    )


def register_shopping_list_tools(server: FastMCP) -> None:
    @server.tool(annotations=READ)
    @offload
    def list_shopping_lists() -> list[ListSummary]:
        """List the names and IDs of shopping lists in your household."""
        with _shopping_lists() as (service, _, _):
            return [
                ListSummary.from_list(item)
                for item in service.shopping_lists.get_all(
                    order_by="name", order_descending=False, override=ShoppingListSummary
                )
            ]

    @server.tool(annotations=READ)
    @offload
    def get_shopping_list(list_id: UUID) -> ListDetails:
        """Read a shopping list by ID, including item IDs, quantities, and checked states."""
        with _shopping_lists() as (service, _, _):
            return ListDetails.from_details(_get_list(service, list_id))

    @server.tool(annotations=ADD)
    @offload
    def create_shopping_list(name: Text, start_date: date | None = None, end_date: date | None = None) -> ListDetails:
        """Create a shopping list. Omit both dates for an empty list or supply an inclusive meal-plan date range.

        A meal-plan list uses the household's live calendar, scales recipe ingredients, and skips leftover meals.
        After a timeout, check list_shopping_lists before retrying.
        """
        if (start_date is None) != (end_date is None) or (start_date and end_date and end_date < start_date):
            raise ToolError("Supply both dates, with the end date on or after the start date.")
        with _shopping_lists() as (service, owner_id, event_bus):
            if start_date and end_date:
                result = service.create_list_from_meal_plan(
                    ShoppingListFromMealPlan(name=name, start_date=start_date, end_date=end_date), owner_id
                )
                if result is None:
                    raise ToolError("There are no meals that need ingredients in this date range.")
                shopping_list, _ = result
            else:
                shopping_list = service.create_one_list(ShoppingListCreate(name=name), owner_id)
                if shopping_list is None:
                    raise ToolError("Could not create the shopping list.")
            _publish(event_bus, shopping_list, EventOperation.create)
            return ListDetails.from_details(shopping_list)

    @server.tool(annotations=EDIT)
    @offload
    def rename_shopping_list(list_id: UUID, name: Text) -> ListSummary:
        """Rename a shopping list by ID and keep its items."""
        with _shopping_lists() as (service, _, event_bus):
            updated = service.shopping_lists.update(list_id, {"name": name})
            _publish(event_bus, updated, EventOperation.update)
            return ListSummary.from_list(updated)

    @server.tool(annotations=EDIT)
    @offload
    def delete_shopping_list(list_id: UUID) -> ListSummary:
        """Permanently delete a shopping list and its items. Ask the user to confirm which list to delete."""
        with _shopping_lists() as (service, _, event_bus):
            deleted = service.shopping_lists.delete(list_id)
            _publish(event_bus, deleted, EventOperation.delete)
            return ListSummary.from_list(deleted)

    @server.tool(annotations=ADD)
    @offload
    def add_shopping_list_items(
        list_id: UUID, items: Annotated[list[NewShoppingItem], Field(min_length=1)]
    ) -> ListDetails:
        """Add grocery items by name and quantity. Similar unchecked items may merge. Check the list before retrying."""
        with _shopping_lists() as (service, _, event_bus):
            with service.shopping_lists.recipe_change(list_id):
                shopping_list = _get_list(service, list_id)
                position = max((item.position for item in shopping_list.list_items), default=-1) + 1
                service.bulk_create_items(
                    [
                        ShoppingListItemCreate(
                            shopping_list_id=list_id, note=item.name, quantity=item.quantity, position=position + index
                        )
                        for index, item in enumerate(items)
                    ]
                )
                updated = _get_list(service, list_id)
            _publish(event_bus, updated, EventOperation.update)
            return ListDetails.from_details(updated)

    @server.tool(annotations=ADD)
    @offload
    def add_recipes_to_shopping_list(
        list_id: UUID, recipes: Annotated[list[ShoppingRecipeInput], Field(min_length=1)]
    ) -> ListDetails:
        """Add ingredients for recipes by ID. Scale multiplies the recipe quantities. Check the list before retrying."""
        with _shopping_lists() as (service, _, event_bus):
            updated, _ = service.add_recipe_ingredients_to_list(
                list_id,
                [
                    ShoppingListAddRecipeParamsBulk(recipe_id=recipe.recipe_id, recipe_increment_quantity=recipe.scale)
                    for recipe in recipes
                ],
            )
            _publish(event_bus, updated, EventOperation.update)
            return ListDetails.from_details(updated)

    @server.tool(annotations=EDIT)
    @offload
    def update_shopping_list_item(list_id: UUID, item_id: UUID, changes: ShoppingItemChanges) -> ListDetails:
        """Change an item's note, quantity, or checked state. Read the list for item IDs and supply only changes."""
        fields = changes.model_dump(exclude_unset=True)
        if not fields:
            raise ToolError("Supply at least one item field to update.")
        with _shopping_lists() as (service, _, event_bus):
            with service.shopping_lists.recipe_change(list_id):
                item = next((item for item in _get_list(service, list_id).list_items if item.id == item_id), None)
                if item is None:
                    raise ToolError("The item was not found on this shopping list.")
                service.bulk_update_items([ShoppingListItemUpdateBulk.model_validate(item.model_dump() | fields)])
                updated = _get_list(service, list_id)
            _publish(event_bus, updated, EventOperation.update)
            return ListDetails.from_details(updated)

    @server.tool(annotations=EDIT)
    @offload
    def remove_shopping_list_items(list_id: UUID, item_ids: Annotated[list[UUID], Field(min_length=1)]) -> ListDetails:
        """Remove items by ID. Read the list for item IDs. To keep items and mark them purchased, set checked."""
        with _shopping_lists() as (service, _, event_bus):
            with service.shopping_lists.recipe_change(list_id):
                existing = {item.id for item in _get_list(service, list_id).list_items}
                if not existing.issuperset(item_ids):
                    raise ToolError("At least one item was not found on this shopping list.")
                service.bulk_delete_items(item_ids)
                updated = _get_list(service, list_id)
            _publish(event_bus, updated, EventOperation.update)
            return ListDetails.from_details(updated)
