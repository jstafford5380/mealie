import pytest
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from mealie.mcp.shopping_lists import register_shopping_list_tools
from tests.integration_tests.mcp_tests.test_meal_plan_tools import as_user
from tests.utils.fixture_schemas import TestUser


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
