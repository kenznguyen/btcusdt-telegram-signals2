"""Strict JSON Schema validation for Browser Automation Controller task requests."""

import copy
import json
import math
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


class TaskValidationError(ValueError):
    """A task request is invalid or violates the v1 request contract."""


class ControllerConfigurationError(RuntimeError):
    """The controller cannot safely load or validate its trusted schema."""


def _is_json_value(value):
    if value is None or isinstance(value, (str, bool, int)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_is_json_value(item) for item in value)
    if isinstance(value, dict):
        return all(type(key) is str and _is_json_value(item) for key, item in value.items())
    return False


@lru_cache(maxsize=1)
def _validator():
    schema_path = Path(__file__).resolve().parents[2] / "schemas" / "browser-automation-task-v1.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        return Draft202012Validator(schema, format_checker=FormatChecker())
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, TypeError):
        raise ControllerConfigurationError("Controller task schema is unavailable or invalid") from None


def validate_task(request):
    """Return a defensive copy of a valid external task request.

    The controller-generated task_id is deliberately absent from the request
    schema, and additional properties are rejected at every object boundary.
    """
    if not isinstance(request, dict) or not _is_json_value(request):
        raise TaskValidationError("Task request must be a JSON object")

    validator = _validator()
    if not validator.is_valid(request):
        # Do not echo invalid values: they may contain credential-like material.
        raise TaskValidationError("Task request does not match contract v1")

    return copy.deepcopy(request)
