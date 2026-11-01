"""Per-build controller lifecycle for validated, authorized automation tasks.

This module owns in-memory task state only. Provider execution adapters are
intentionally implemented in later delivery phases.
"""

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from threading import RLock
from types import MappingProxyType
from uuid import uuid4

from .authorization import (
    AuthorizationContext,
    AuthorizationDecision,
    authorize_task,
)
from .schema import validate_task


class TaskStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"


class IdempotencyConflictError(ValueError):
    """Raised when one idempotency key is reused for a different request."""


class InvalidTaskTransitionError(ValueError):
    """Raised when a task lifecycle transition is not permitted."""


class TaskNotFoundError(KeyError):
    """Raised when a controller-local task ID is unknown."""


_TERMINAL_STATUSES = frozenset({
    TaskStatus.SUCCEEDED,
    TaskStatus.FAILED,
    TaskStatus.CANCELLED,
})


def _freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _plain(value):
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _request_digest(request):
    canonical = json.dumps(
        _plain(request), sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True)
class PreparedTask:
    request: Mapping
    authorization: AuthorizationDecision

    def __post_init__(self):
        object.__setattr__(self, "request", _freeze(deepcopy(dict(self.request))))


@dataclass(frozen=True)
class ControllerTask:
    task_id: str
    idempotency_key: str
    status: TaskStatus
    prepared: PreparedTask
    result: Mapping | None = None
    error: str | None = None

    def __post_init__(self):
        if self.result is not None:
            object.__setattr__(self, "result", _freeze(deepcopy(dict(self.result))))


class BrowserAutomationController:
    """A short-lived, in-memory coordinator instantiated inside one Codemagic build."""

    def __init__(self, authorization_context=None):
        if authorization_context is None:
            authorization_context = AuthorizationContext()
        if not isinstance(authorization_context, AuthorizationContext):
            raise TypeError("A trusted AuthorizationContext is required")
        self._authorization_context = authorization_context
        self._tasks = {}
        self._idempotency = {}
        self._lock = RLock()

    def prepare_task(self, request):
        """Validate and authorize a task without executing external actions."""
        validated = validate_task(request)
        decision = authorize_task(validated, self._authorization_context)
        return PreparedTask(request=validated, authorization=decision)

    def accept_task(self, request):
        """Accept an authorized task once per idempotency key and payload."""
        prepared = self.prepare_task(request)
        key = prepared.request["idempotency_key"]
        digest = _request_digest(dict(prepared.request))

        with self._lock:
            existing = self._idempotency.get(key)
            if existing is not None:
                existing_digest, task_id = existing
                if existing_digest != digest:
                    raise IdempotencyConflictError(
                        "Idempotency key was already used for a different task"
                    )
                return self._tasks[task_id]

            task = ControllerTask(
                task_id=str(uuid4()),
                idempotency_key=key,
                status=TaskStatus.QUEUED,
                prepared=prepared,
            )
            self._tasks[task.task_id] = task
            self._idempotency[key] = (digest, task.task_id)
            return task

    def get_task(self, task_id):
        with self._lock:
            return self._require_task(task_id)

    def get_task_status(self, task_id):
        return self.get_task(task_id).status

    def start_task(self, task_id):
        return self._transition(task_id, {TaskStatus.QUEUED}, TaskStatus.RUNNING)

    def wait_for_user(self, task_id):
        return self._transition(task_id, {TaskStatus.RUNNING}, TaskStatus.WAITING_FOR_USER)

    def resume_task(self, task_id):
        return self._transition(task_id, {TaskStatus.WAITING_FOR_USER}, TaskStatus.RUNNING)

    def mark_unknown(self, task_id, reason):
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("A non-empty reconciliation reason is required")
        return self._transition(
            task_id,
            {TaskStatus.RUNNING, TaskStatus.WAITING_FOR_USER},
            TaskStatus.UNKNOWN,
            error=reason.strip(),
        )

    def finish_task(self, task_id, status, verified=False, result=None, error=None):
        status = self._coerce_status(status)
        if status not in {TaskStatus.SUCCEEDED, TaskStatus.FAILED}:
            raise InvalidTaskTransitionError("Finish status must be SUCCEEDED or FAILED")
        if status is TaskStatus.SUCCEEDED and verified is not True:
            raise InvalidTaskTransitionError(
                "Successful completion requires verified postconditions"
            )
        if result is not None and not isinstance(result, Mapping):
            raise TypeError("Task result must be a mapping")
        if error is not None and (not isinstance(error, str) or not error.strip()):
            raise ValueError("Task error must be a non-empty string when supplied")

        return self._transition(
            task_id,
            {TaskStatus.RUNNING, TaskStatus.WAITING_FOR_USER},
            status,
            result=result,
            error=error.strip() if error else None,
        )

    def reconcile_task(self, task_id, outcome, verified=False, result=None, error=None):
        outcome = self._coerce_status(outcome)
        if outcome not in _TERMINAL_STATUSES:
            raise InvalidTaskTransitionError("Reconciliation requires a terminal outcome")
        if outcome is TaskStatus.SUCCEEDED and verified is not True:
            raise InvalidTaskTransitionError(
                "Successful reconciliation requires verified postconditions"
            )
        if result is not None and not isinstance(result, Mapping):
            raise TypeError("Task result must be a mapping")
        return self._transition(
            task_id,
            {TaskStatus.UNKNOWN},
            outcome,
            result=result,
            error=error.strip() if isinstance(error, str) and error.strip() else None,
        )

    def cancel_task(self, task_id):
        return self._transition(task_id, {TaskStatus.QUEUED}, TaskStatus.CANCELLED)

    def _transition(self, task_id, allowed_from, new_status, result=None, error=None):
        with self._lock:
            current = self._require_task(task_id)
            if current.status not in allowed_from:
                raise InvalidTaskTransitionError(
                    f"Cannot transition task from {current.status.value} to {new_status.value}"
                )
            updated = ControllerTask(
                task_id=current.task_id,
                idempotency_key=current.idempotency_key,
                status=new_status,
                prepared=current.prepared,
                result=result if result is not None else current.result,
                error=error,
            )
            self._tasks[task_id] = updated
            return updated

    def _require_task(self, task_id):
        try:
            return self._tasks[task_id]
        except KeyError:
            raise TaskNotFoundError("Unknown controller task ID") from None

    @staticmethod
    def _coerce_status(status):
        try:
            return status if isinstance(status, TaskStatus) else TaskStatus(status)
        except (TypeError, ValueError):
            raise InvalidTaskTransitionError("Unknown task status") from None
