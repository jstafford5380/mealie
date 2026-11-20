from collections.abc import Sequence
from time import monotonic
from typing import Any
from uuid import uuid4

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ContentBlock
from pydantic import ValidationError

from mealie.core.root_logger import get_logger

logger = get_logger("mcp")


class AuditedMCP(FastMCP):
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Sequence[ContentBlock] | dict[str, Any]:
        started = monotonic()
        request_id = uuid4().hex
        tool_name = name if any(tool.name == name for tool in await self.list_tools()) else "unknown"
        outcome = "error"
        try:
            result = await super().call_tool(name, arguments)
            outcome = "success"
            return result
        except ToolError as exc:
            # The SDK wraps tool exceptions and includes their original messages. Only pass
            # through errors that our tools explicitly prepared for callers.
            cause = exc.__cause__
            if isinstance(cause, ToolError):
                raise cause from None
            if isinstance(cause, ValidationError):
                raise ToolError("Invalid tool arguments. Check the field types and required values.") from None
            if tool_name == "unknown":
                raise ToolError("Unknown Mealie tool.") from None
            raise ToolError(f"Mealie could not complete this request. Reference: {request_id}.") from None
        finally:
            logger.info(
                "MCP tool=%s outcome=%s duration_ms=%.0f request_id=%s",
                tool_name,
                outcome,
                (monotonic() - started) * 1000,
                request_id,
            )
