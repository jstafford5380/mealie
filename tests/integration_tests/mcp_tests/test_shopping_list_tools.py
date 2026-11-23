from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from mealie.mcp.meal_plan import register_meal_plan_tools
from mealie.mcp.recipes import register_recipe_tools
from mealie.mcp.shopping_lists import register_shopping_list_tools
from mealie.schema.recipe.recipe_ingredient import IngredientFoodSave, IngredientUnitSave
from tests.integration_tests.mcp_tests.test_meal_plan_tools import as_user
from tests.utils import api_routes
from tests.utils.fixture_schemas import TestUser


@pytest.mark.asyncio
async def test_shopping_amount_promotes_merged_volume_without_changing_exact_total(
    unique_user: TestUser, api_client: TestClient
) -> None:
    server = FastMCP()
    register_recipe_tools(server)
    register_shopping_list_tools(server)
    food = unique_user.repos.ingredient_foods.create(IngredientFoodSave(name="sugar", group_id=unique_user.group_id))
    units = {
        name: unique_user.repos.ingredient_units.create(
            IngredientUnitSave(
                name=f"sugar test {name}",
                group_id=unique_user.group_id,
                standard_unit="fluid_ounce",
                standard_quantity=factor,
            )
        )
        for name, factor in (("tablespoon", 0.5), ("teaspoon", 1 / 6))
    }
    with as_user(unique_user):
        refs = []
        for index, (amount, unit) in enumerate(((2, "tablespoon"), (3, "teaspoon"), (5, "tablespoon"))):
            _, recipe = await server.call_tool(
                "create_recipe",
                {
                    "data": {
                        "name": f"Sugar recipe {index}",
                        "servings": 1,
                        "ingredients": [{"food_id": str(food.id), "unit_id": str(units[unit].id), "quantity": amount}],
                        "instructions": ["Add sugar."],
                    }
                },
            )
            refs.append({"recipe_id": recipe["id"]})
        _, shopping_list = await server.call_tool("create_shopping_list", {"name": "Sugar"})
        args = {"list_id": shopping_list["id"]}
        _, result = await server.call_tool("add_recipes_to_shopping_list", args | {"recipes": refs[:2]})
        (sugar,) = result["items"]
        assert sugar["shopping_amount"] == {"quantity": 3, "unit": "tbsp", "display": "3 tbsp sugar"}
        _, result = await server.call_tool("add_recipes_to_shopping_list", args | {"recipes": refs[2:]})
        (sugar,) = result["items"]
        assert sugar["quantity"] == pytest.approx(8)
        assert sugar["unit_id"] == str(units["tablespoon"].id)
        assert sugar["shopping_amount"] == {"quantity": 0.5, "unit": "cup", "display": "0.5 cup sugar"}
        assert sorted(ref["quantity_per_recipe"] for ref in sugar["recipe_references"]) == [2, 3, 5]

    response = api_client.get(
        api_routes.households_shopping_lists_item_id(shopping_list["id"]), headers=unique_user.token
    )
    assert response.status_code == 200
    (rest_sugar,) = response.json()["listItems"]
    assert rest_sugar["shoppingAmount"] == sugar["shopping_amount"]


@pytest.mark.asyncio
async def test_shopping_list_consolidates_canonical_ingredients_with_scales(unique_user: TestUser) -> None:
    server = FastMCP()
    register_recipe_tools(server)
    register_shopping_list_tools(server)
    register_meal_plan_tools(server)
    food = unique_user.repos.ingredient_foods.create(
        IngredientFoodSave(name="olive oil", group_id=unique_user.group_id)
    )
    unit = unique_user.repos.ingredient_units.create(
        IngredientUnitSave(name="tablespoon", abbreviation="tbsp", group_id=unique_user.group_id)
    )
    with as_user(unique_user):
        recipes = []
        for name, quantity, scale in (("Dressing", 1, 2), ("Marinade", 2, 0.5)):
            _, recipe = await server.call_tool(
                "create_recipe",
                {
                    "data": {
                        "name": name,
                        "servings": 4,
                        "ingredients": [
                            {"food_id": str(food.id), "unit_id": str(unit.id), "quantity": quantity},
                            "Salt to taste",
                        ],
                        "instructions": ["Mix the ingredients."],
                    }
                },
            )
            recipes.append({"recipe_id": recipe["id"], "scale": scale})
        _, shopping_list = await server.call_tool("create_shopping_list", {"name": "Groceries"})
        _, result = await server.call_tool(
            "add_recipes_to_shopping_list", {"list_id": shopping_list["id"], "recipes": recipes}
        )
        batch_id = str(uuid4())
        for recipe, day, details in (
            (recipes[0], 2, {"recipe_batch_id": batch_id, "recipe_scale": 0.25}),
            (recipes[0], 3, {"leftover_batch_id": batch_id, "recipe_scale": 0.25}),
            (recipes[1], 4, {"recipe_scale": 0.5}),
        ):
            await server.call_tool(
                "create_meal_plan_entry",
                {"recipe_id": recipe["recipe_id"], "date": f"2040-01-0{day}", "entry_type": "dinner", **details},
            )
        _, calendar_list = await server.call_tool(
            "create_shopping_list", {"name": "Calendar groceries", "start_date": "2040-01-02", "end_date": "2040-01-04"}
        )
    (oil,) = [item for item in result["items"] if item["food_id"] == str(food.id)]
    assert oil["unit_id"] == str(unit.id)
    assert oil["quantity"] == oil["measured_quantity"] == 3
    assert {(ref["recipe_id"], ref["scale"]) for ref in oil["recipe_references"]} == {
        (recipe["recipe_id"], recipe["scale"]) for recipe in recipes
    }
    (salt,) = [item for item in result["items"] if item["food_id"] is None]
    assert salt["quantity"] == 0
    assert salt["measured_quantity"] is None
    (calendar_oil,) = [item for item in calendar_list["items"] if item["food_id"] == str(food.id)]
    assert calendar_oil["measured_quantity"] == 2
    assert calendar_oil["shopping_amount"]["quantity"] == 2
    assert {recipe["recipe_id"]: recipe["scale"] for recipe in calendar_list["recipes"]} == {
        recipes[0]["recipe_id"]: 1,
        recipes[1]["recipe_id"]: 0.5,
    }


@pytest.mark.asyncio
async def test_shopping_list_tools_read_and_modify_household_items(unique_user: TestUser, h2_user: TestUser) -> None:
    server = FastMCP()
    register_shopping_list_tools(server)
    with as_user(unique_user):
        _, created = await server.call_tool("create_shopping_list", {"name": "Groceries"})
        list_id = created["id"]
        _, lists = await server.call_tool("list_shopping_lists", {})
        assert {"id": list_id, "name": "Groceries"} in lists["result"]
        _, added = await server.call_tool(
            "add_shopping_list_items", {"list_id": list_id, "items": [{"name": "Apples", "quantity": 3}]}
        )
        item_id = added["items"][0]["id"]
        _, updated = await server.call_tool(
            "update_shopping_list_item", {"list_id": list_id, "item_id": item_id, "changes": {"checked": True}}
        )
        assert updated["items"][0]["checked"] is True
        assert updated["items"][0]["quantity"] == 3
        assert updated["items"][0]["shopping_amount"] is None
        await server.call_tool("rename_shopping_list", {"list_id": list_id, "name": "Weekend groceries"})
        _, loaded = await server.call_tool("get_shopping_list", {"list_id": list_id})
        assert loaded["name"] == "Weekend groceries"
        assert loaded["items"] == updated["items"]

    with as_user(h2_user):
        _, lists = await server.call_tool("list_shopping_lists", {})
        assert list_id not in {item["id"] for item in lists["result"]}
        with pytest.raises(ToolError, match="not found"):
            await server.call_tool("get_shopping_list", {"list_id": list_id})
        with pytest.raises(ToolError, match="not found"):
            await server.call_tool("delete_shopping_list", {"list_id": list_id})

    with as_user(unique_user):
        _, emptied = await server.call_tool("remove_shopping_list_items", {"list_id": list_id, "item_ids": [item_id]})
        assert emptied["items"] == []
        _, deleted = await server.call_tool("delete_shopping_list", {"list_id": list_id})
        assert deleted["id"] == list_id
        with pytest.raises(ToolError, match="not found"):
            await server.call_tool("get_shopping_list", {"list_id": list_id})
