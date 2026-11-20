import pytest
from mcp.server.fastmcp.exceptions import ToolError

from mealie.mcp.context import current_user_id, tool_context
from tests.utils import TestUser


def test_mcp_context_requires_authenticated_account():
    with pytest.raises(ToolError, match="authentication is required"), tool_context():
        pytest.fail("Unauthenticated tool context")


def test_mcp_context_resolves_current_group_and_household(unique_user: TestUser):
    token = current_user_id.set(unique_user.user_id)
    try:
        with tool_context() as (_, user, repos):
            assert user.id == unique_user.user_id
            assert str(user.group_id) == unique_user.group_id
            assert str(user.household_id) == unique_user.household_id
            assert repos.group_id == user.group_id
            assert repos.household_id == user.household_id
    finally:
        current_user_id.reset(token)


def test_mcp_context_disallows_admin_mapping(unique_admin: TestUser):
    token = current_user_id.set(unique_admin.user_id)
    try:
        with pytest.raises(ToolError, match="account is unavailable"), tool_context():
            pytest.fail("Privileged tool context")
    finally:
        current_user_id.reset(token)
