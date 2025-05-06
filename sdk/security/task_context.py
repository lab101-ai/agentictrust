"""Shared context for parent-token information during an AgenticTrust task tree.

A *task* is the top-level operation on behalf of a user / system that an agent
is going to perform.  All secure tools that run as part of that task will
request *child* tokens delegated from the *parent* token stored here.

The context is intentionally **process-wide** but thread-local / async-task-local
thanks to ``contextvars.ContextVar``.
"""
from __future__ import annotations

from contextvars import ContextVar
from typing import Optional, Dict, Any, TypedDict


class _TaskContext(TypedDict):
    parent_token: str
    parent_task_id: str
    client: "AgenticTrustClient"  # forward reference, runtime type is the real class


# The global context variable – default is ``None`` meaning *no active task*.
_task_ctx: ContextVar[Optional[_TaskContext]] = ContextVar("agentictrust_task_ctx", default=None)


def get_context() -> Optional[_TaskContext]:
    """Return the current task context or *None* if no task is active."""
    return _task_ctx.get()


def set_context(ctx: _TaskContext) -> None:
    """Replace the current context **unconditionally** (advanced use only)."""
    _task_ctx.set(ctx)


# Public re-export so other modules can simply ``from .task_context import task_context``
# without caring about the helper getters.
# We expose the *ContextVar* itself; users can still call .get() / .set().
# pylint: disable=invalid-name
task_context = _task_ctx

__all__ = [
    "task_context",
    "get_context",
    "set_context",
]
