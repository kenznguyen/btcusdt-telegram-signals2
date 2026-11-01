"""Per-build controller entry point for validating and authorizing tasks.

This module deliberately does not start a server, browser, worker, or provider
operation. Execution adapters are added in later delivery phases.
"""

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping

from .authorization import (
    AuthorizationContext,
    AuthorizationDecision,
    authorize_task,
)
from .schema import validate_task


def _freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


@dataclass(frozen=True)
class PreparedTask:
    request: Mapping
    authorization: AuthorizationDecision

    def __post_init__(self):
        object.__setattr__(self, "request", _freeze(self.request))


class BrowserAutomationController:
    """A short-lived coordinator instantiated inside one Codemagic build."""

    def __init__(self, authorization_context=None):
        if authorization_context is None:
            authorization_context = AuthorizationContext()
        if not isinstance(authorization_context, AuthorizationContext):
            raise TypeError("A trusted AuthorizationContext is required")
        self._authorization_context = authorization_context

    def prepare_task(self, request):
        """Validate and authorize a task without executing external actions."""
        validated = validate_task(request)
        decision = authorize_task(validated, self._authorization_context)
        return PreparedTask(request=validated, authorization=decision)
