from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from mealie.mcp.context import current_user_id
from mealie.mcp.meal_plan import register_meal_plan_tools
from tests.utils import api_routes
from tests.utils.factories import random_string
from tests.utils.fixture_schemas import TestUser


@contextmanager
def as_user(user: TestUser) -> Iterator[None]:
    token = current_user_id.set(user.user_id)
    try:
        yield
    finally:
        current_user_id.reset(token)


@pytest.fixture
def server() -> FastMCP:
    server = FastMCP()
    register_meal_plan_tools(server)
    return server


def create_recipe(api_client: TestClient, user: TestUser) -> dict:
    response = api_client.post(api_routes.recipes, json={"name": random_string()}, headers=user.token)
    assert response.status_code == 201
    response = api_client.get(api_routes.recipes_slug(response.json()), headers=user.token)
    assert response.status_code == 200
    return response.json()


@pytest.mark.asyncio
async def test_meal_plan_tools_use_native_entries_and_scale(
    server: FastMCP, api_client: TestClient, unique_user: TestUser
):
    recipe = create_recipe(api_client, unique_user)
    replacement_recipe = create_recipe(api_client, unique_user)
    with as_user(unique_user):
        _, entry = await server.call_tool(
            "create_meal_plan_entry",
            {
                "recipe_id": recipe["id"],
                "date": "2026-03-02",
                "end_date": "2026-03-08",
                "entry_type": "dinner",
                "recipe_scale": 2.5,
                "note": "Cook on Monday",
            },
        )
        _, page = await server.call_tool("list_meal_plan", {"start_date": "2026-03-05", "end_date": "2026-03-05"})
        assert page["entries"] == [entry]
        assert entry["recipe_name"] == recipe["name"]
        assert entry["recipe_url"].endswith(f"/r/{recipe['slug']}")
        assert entry["recipe_scale"] == 2.5

        with pytest.raises(ToolError, match="six days"):
            await server.call_tool(
                "update_meal_plan_entry", {"entry_id": entry["id"], "changes": {"date": "2026-03-03"}}
            )

        _, updated = await server.call_tool(
            "update_meal_plan_entry",
            {"entry_id": entry["id"], "changes": {"end_date": None, "recipe_scale": 0.5}},
        )
        assert updated["note"] == "Cook on Monday"
        assert updated["recipe_id"] == recipe["id"]
        assert updated["end_date"] is None

        _, updated = await server.call_tool(
            "update_meal_plan_entry",
            {"entry_id": entry["id"], "changes": {"recipe_id": replacement_recipe["id"]}},
        )
        assert updated["recipe_id"] == replacement_recipe["id"]
        assert updated["recipe_name"] == replacement_recipe["name"]
        assert updated["recipe_scale"] == 0.5

        _, page = await server.call_tool("list_meal_plan", {"start_date": "2026-03-05", "end_date": "2026-03-05"})
        assert page["entries"] == []

    response = api_client.get(api_routes.households_mealplans_item_id(entry["id"]), headers=unique_user.token)
    assert response.status_code == 200
    assert response.json()["recipeScale"] == 0.5
    assert response.json()["endDate"] is None


@pytest.mark.asyncio
async def test_meal_plan_tools_isolate_households_and_reject_other_groups(
    server: FastMCP, api_client: TestClient, unique_user: TestUser, h2_user: TestUser, g2_user: TestUser
):
    own_recipe = create_recipe(api_client, unique_user)
    other_group_recipe = create_recipe(api_client, g2_user)
    payload = {"date": "2026-04-01", "entry_type": "dinner"}
    dates = {"start_date": payload["date"], "end_date": payload["date"]}

    with as_user(unique_user):
        _, own_meal = await server.call_tool("create_meal_plan_entry", {**payload, "recipe_id": own_recipe["id"]})
        with pytest.raises(ToolError, match="recipe was not found"):
            await server.call_tool("create_meal_plan_entry", {**payload, "recipe_id": other_group_recipe["id"]})

    with as_user(h2_user):
        _, page = await server.call_tool("list_meal_plan", dates)
        assert own_meal["id"] not in [item["id"] for item in page["entries"]]
        with pytest.raises(ToolError, match="entry was not found"):
            await server.call_tool(
                "update_meal_plan_entry", {"entry_id": own_meal["id"], "changes": {"recipe_scale": 2}}
            )

    with as_user(unique_user):
        with pytest.raises(ToolError, match="recipe was not found"):
            await server.call_tool(
                "update_meal_plan_entry",
                {"entry_id": own_meal["id"], "changes": {"recipe_id": other_group_recipe["id"]}},
            )
        _, page = await server.call_tool("list_meal_plan", dates)
        assert [own_meal] == page["entries"]
