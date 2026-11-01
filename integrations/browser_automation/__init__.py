"""Browser automation orchestration primitives; no persistent service is created."""

from .authorization import AuthorizationContext, AuthorizationDecision, AuthorizationError
from .controller import BrowserAutomationController, PreparedTask
from .schema import ControllerConfigurationError, TaskValidationError, validate_task

__all__ = [
    "AuthorizationContext",
    "AuthorizationDecision",
    "AuthorizationError",
    "BrowserAutomationController",
    "ControllerConfigurationError",
    "PreparedTask",
    "TaskValidationError",
    "validate_task",
]
