from collections.abc import Iterator
from contextlib import contextmanager
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator
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
async def test_meal_plan_patch_schema_matches_nullable_fields(server: FastMCP) -> None:
    tool = next(tool for tool in await server.list_tools() if tool.name == "update_meal_plan_entry")
    schema = Draft202012Validator(tool.inputSchema)
    schema.validate({"entry_id": 1, "changes": {"end_date": None}})
    schema.validate({"entry_id": 1, "changes": {"recipe_batch_id": None, "leftover_batch_id": None}})

    for changes in ({}, *({field: None} for field in ("date", "entry_type", "note", "recipe_id", "recipe_scale"))):
        args = {"entry_id": 1, "changes": changes}
        assert not schema.is_valid(args)
        with pytest.raises(ToolError):
            await server.call_tool(tool.name, args)


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


@pytest.mark.asyncio
async def test_saved_meal_plan_tools_leave_calendar_unchanged(
    server: FastMCP, api_client: TestClient, unique_user: TestUser, h2_user: TestUser
) -> None:
    recipe = create_recipe(api_client, unique_user)
    entries = [
        {"weekday": 1, "entry_type": "dinner", "recipe_id": recipe["id"], "recipe_scale": 2},
        {"weekday": None, "entry_type": "lunch", "title": "Leftovers"},
    ]
    plan = {"name": random_string(), "entries": entries}
    calendar_route = api_routes.households_mealplans
    before = api_client.get(calendar_route, headers=unique_user.token, params={"include_week_entries": True}).json()
    with as_user(unique_user):
        with pytest.raises(ToolError):
            await server.call_tool(
                "create_saved_meal_plan",
                {"plan": {"name": plan["name"], "entries": [entries[0] | {"date": "2040-01-02"}]}},
            )
        _, created = await server.call_tool("create_saved_meal_plan", {"plan": plan})
        plan_id = created["id"]
        _, listed = await server.call_tool("list_saved_meal_plans", {})
        assert {"id": plan_id, "name": plan["name"]} in listed["result"]
        _, loaded = await server.call_tool("get_saved_meal_plan", {"plan_id": plan_id})
        assert loaded == created
        _, updated = await server.call_tool(
            "update_saved_meal_plan", {"plan_id": plan_id, "plan": {"name": "Updated", "entries": entries}}
        )
        assert updated["name"] == "Updated"

    with as_user(h2_user):
        _, listed = await server.call_tool("list_saved_meal_plans", {})
        assert listed["result"] == []
        with pytest.raises(ToolError, match="saved meal plan was not found"):
            await server.call_tool("get_saved_meal_plan", {"plan_id": plan_id})
        with pytest.raises(ToolError, match="saved meal plan was not found"):
            await server.call_tool("update_saved_meal_plan", {"plan_id": plan_id, "plan": plan})

    saved_route = api_routes.households_mealplans_saved_plan_id(plan_id)
    saved = api_client.get(saved_route, headers=unique_user.token).json()
    assert saved["name"] == "Updated"
    assert saved["entries"][0]["recipeScale"] == 2
    assert saved["entries"][1]["weekday"] is None
    after = api_client.get(calendar_route, headers=unique_user.token, params={"include_week_entries": True}).json()
    assert after["items"] == before["items"]


@pytest.mark.asyncio
async def test_live_leftover_tools_discover_and_reserve_portions(
    server: FastMCP, api_client: TestClient, unique_user: TestUser, h2_user: TestUser
) -> None:
    recipe = create_recipe(api_client, unique_user)
    response = api_client.put(
        api_routes.recipes_slug(recipe["slug"]), json={**recipe, "recipeServings": 4}, headers=unique_user.token
    )
    assert response.status_code == 200, response.text
    batch_id = str(uuid4())
    later = {"recipe_id": recipe["id"], "date": "2040-01-03", "entry_type": "lunch"}
    portion = {**later, "leftover_batch_id": batch_id, "recipe_scale": 0.25}

    with as_user(unique_user):
        _, source = await server.call_tool(
            "create_meal_plan_entry",
            {
                "recipe_id": recipe["id"],
                "date": "2040-01-02",
                "entry_type": "dinner",
                "recipe_batch_id": batch_id,
                "recipe_scale": 0.25,
            },
        )
        assert source["recipe_batch_id"] == batch_id
        assert source["leftover_batch_id"] is None
        _, batches = await server.call_tool("list_leftover_batches", later)
        assert batches["result"][0]["base_servings"] == 4
        assert batches["result"][0]["remaining_servings"] == 3
        _, before_source = await server.call_tool("list_leftover_batches", {**later, "date": "2040-01-02"})
        assert before_source["result"] == []

        _, lunch = await server.call_tool("create_meal_plan_entry", portion)
        assert lunch["leftover_batch_id"] == batch_id
        _, listed = await server.call_tool("list_meal_plan", {"start_date": later["date"], "end_date": later["date"]})
        assert listed["entries"] == [lunch]
        _, batches = await server.call_tool("list_leftover_batches", later)
        assert batches["result"][0]["remaining_servings"] == 2
        with pytest.raises(ToolError, match="not have enough"):
            await server.call_tool("create_meal_plan_entry", {**portion, "recipe_scale": 0.75})
        with pytest.raises(ToolError, match="Other meals use this batch"):
            await server.call_tool(
                "update_meal_plan_entry", {"entry_id": source["id"], "changes": {"recipe_batch_id": None}}
            )
        _, changed = await server.call_tool(
            "update_meal_plan_entry", {"entry_id": lunch["id"], "changes": {"recipe_scale": 0.75}}
        )
        assert changed["leftover_batch_id"] == batch_id
        _, batches = await server.call_tool("list_leftover_batches", later)
        assert batches["result"] == []
        _, cleared = await server.call_tool(
            "update_meal_plan_entry", {"entry_id": lunch["id"], "changes": {"leftover_batch_id": None}}
        )
        assert cleared["leftover_batch_id"] is None
        _, batches = await server.call_tool("list_leftover_batches", later)
        assert batches["result"][0]["remaining_servings"] == 3

    with as_user(h2_user):
        _, batches = await server.call_tool("list_leftover_batches", later)
        assert batches["result"] == []
        with pytest.raises(ToolError, match="Choose an earlier full batch"):
            await server.call_tool("create_meal_plan_entry", portion)


@pytest.mark.asyncio
async def test_saved_plan_tools_preserve_and_validate_batch_links(
    server: FastMCP, api_client: TestClient, unique_user: TestUser
) -> None:
    recipe = create_recipe(api_client, unique_user)
    batch_id = str(uuid4())
    source = {
        "weekday": 1,
        "entryType": "dinner",
        "recipeId": recipe["id"],
        "recipeBatchId": batch_id,
        "recipeScale": 0.25,
    }
    lunch = {
        "weekday": 2,
        "entryType": "lunch",
        "recipeId": recipe["id"],
        "leftoverBatchId": batch_id,
        "recipeScale": 0.25,
    }
    with as_user(unique_user):
        _, created = await server.call_tool(
            "create_saved_meal_plan", {"plan": {"name": "Batch", "entries": [source, lunch]}}
        )
        plan_id = created["id"]
        _, loaded = await server.call_tool("get_saved_meal_plan", {"plan_id": plan_id})
        assert loaded["entries"][0]["recipeBatchId"] == loaded["entries"][1]["leftoverBatchId"] == batch_id
        with pytest.raises(ToolError, match="more servings"):
            await server.call_tool(
                "update_saved_meal_plan",
                {"plan_id": plan_id, "plan": {"name": "Batch", "entries": [source, {**lunch, "recipeScale": 1}]}},
            )
        _, updated = await server.call_tool(
            "update_saved_meal_plan",
            {"plan_id": plan_id, "plan": {"name": "Batch", "entries": [source, {**lunch, "recipeScale": 0.5}]}},
        )
        assert updated["entries"][0]["recipeBatchId"] == updated["entries"][1]["leftoverBatchId"] == batch_id
        assert updated["entries"][1]["recipeScale"] == 0.5
        _, batches = await server.call_tool(
            "list_leftover_batches", {"date": "2040-01-03", "entry_type": "lunch", "recipe_id": recipe["id"]}
        )
        assert batches["result"] == []
