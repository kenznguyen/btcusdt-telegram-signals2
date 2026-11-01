"""Browser automation orchestration primitives; no persistent service is created."""

from .authorization import AuthorizationContext, AuthorizationDecision, AuthorizationError
from .controller import (
    BrowserAutomationController,
    ControllerTask,
    IdempotencyConflictError,
    InvalidTaskTransitionError,
    PreparedTask,
    TaskNotFoundError,
    TaskStatus,
)
from .schema import ControllerConfigurationError, TaskValidationError, validate_task

__all__ = [
    "AuthorizationContext",
    "AuthorizationDecision",
    "AuthorizationError",
    "BrowserAutomationController",
    "ControllerTask",
    "ControllerConfigurationError",
    "IdempotencyConflictError",
    "InvalidTaskTransitionError",
    "PreparedTask",
    "TaskNotFoundError",
    "TaskStatus",
    "TaskValidationError",
    "validate_task",
]
