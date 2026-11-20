import pytest
from mcp.server.fastmcp.exceptions import ToolError

from mealie.mcp.audit import AuditedMCP


@pytest.mark.asyncio
async def test_tool_errors_and_logs_hide_payloads(caplog: pytest.LogCaptureFixture):
    server = AuditedMCP()

    @server.tool()
    def lookup(quantity: int) -> int:
        if quantity < 1:
            raise ToolError("Quantity must be positive.")
        raise RuntimeError("private database details")

    with caplog.at_level("INFO"):
        with pytest.raises(ToolError, match="Quantity must be positive"):
            await server.call_tool("lookup", {"quantity": 0})
        with pytest.raises(ToolError, match="Reference:"):
            await server.call_tool("lookup", {"quantity": 1})
        with pytest.raises(ToolError, match="Invalid tool arguments"):
            await server.call_tool("lookup", {"quantity": "private argument"})

    assert "MCP tool=lookup outcome=error" in caplog.text
    assert "request_id=" in caplog.text
    assert "private database details" not in caplog.text
    assert "private argument" not in caplog.text
