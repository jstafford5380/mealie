from collections.abc import Callable, Coroutine, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from typing import Any
from uuid import UUID

from mcp.server.fastmcp.exceptions import ToolError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from mealie.db.db_setup import session_context
from mealie.repos.all_repositories import AllRepositories, get_repositories
from mealie.schema.user.user import PrivateUser

current_user_id: ContextVar[UUID | None] = ContextVar("mcp_user_id", default=None)


def offload[**P, R](func: Callable[P, R]) -> Callable[P, Coroutine[Any, Any, R]]:
    @wraps(func)
    async def execute(*args: P.args, **kwargs: P.kwargs) -> R:
        return await run_in_threadpool(func, *args, **kwargs)

    return execute


@contextmanager
def tool_context() -> Iterator[tuple[Session, PrivateUser, AllRepositories]]:
    user_id = current_user_id.get()
    if user_id is None:
        raise ToolError("Mealie authentication is required.")

    with session_context() as session:
        user = get_repositories(session, group_id=None, household_id=None).users.get_one(user_id)
        if user is None or user.admin or user.is_locked:
            raise ToolError("The configured Mealie account is unavailable.")

        session.commit()  # Release the account lookup transaction before domain work.
        repos = get_repositories(session, group_id=user.group_id, household_id=user.household_id)
        yield session, user, repos
