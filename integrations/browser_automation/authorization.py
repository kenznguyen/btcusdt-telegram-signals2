"""Fail-closed authorization policy for Browser Automation Controller v1."""

from dataclasses import dataclass, field
from pathlib import Path
import posixpath
from urllib.parse import unquote, urlsplit

from .schema import TaskValidationError, validate_task


class AuthorizationError(PermissionError):
    """A task was denied by the trusted authorization policy."""

    def __init__(self, code="NOT_AUTHORIZED"):
        self.code = code
        super().__init__("Task is not authorized")


@dataclass(frozen=True)
class AuthorizationContext:
    """Trusted grants supplied by the Codemagic workflow, never by task JSON."""

    allowed_task_types: frozenset = field(default_factory=frozenset)
    allowed_providers: frozenset = field(default_factory=frozenset)
    allowed_repositories: frozenset = field(default_factory=frozenset)
    allowed_branches: frozenset = field(default_factory=frozenset)
    allowed_permissions: frozenset = field(default_factory=frozenset)
    allowed_web_origins: frozenset = field(default_factory=frozenset)
    allowed_url_prefixes: frozenset = field(default_factory=frozenset)
    allowed_workspace_roots: tuple = ()

    def __post_init__(self):
        grant_fields = (
            "allowed_task_types",
            "allowed_providers",
            "allowed_repositories",
            "allowed_branches",
            "allowed_permissions",
            "allowed_web_origins",
            "allowed_url_prefixes",
        )
        for name in grant_fields:
            value = getattr(self, name)
            if not isinstance(value, (set, frozenset, tuple, list)) or any(
                not isinstance(item, str) or not item for item in value
            ):
                raise ValueError("Authorization grants must be collections of non-empty strings")
            object.__setattr__(self, name, frozenset(value))

        roots = self.allowed_workspace_roots
        if not isinstance(roots, (tuple, list)) or any(
            not isinstance(root, (str, Path)) or not str(root) for root in roots
        ):
            raise ValueError("Workspace roots must be filesystem paths")
        object.__setattr__(self, "allowed_workspace_roots", tuple(Path(root) for root in roots))



@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    task_type: str
    provider: str
    granted_permissions: tuple


_TASK_PROVIDERS = {
    "CODEMAGIC_BUILD_VERIFY": "codemagic",
    "CODEMAGIC_BUILD_START": "codemagic",
    "CODEMAGIC_BUILD_STATUS": "codemagic",
    "CODEMAGIC_ARTIFACT_VERIFY": "codemagic",
    "GITHUB_READ": "github",
    "GITHUB_BRANCH_CREATE": "github",
    "GITHUB_FILE_COMMIT": "github",
    "BROWSER_UI_READ": "approved_web_app",
    "BROWSER_UI_ACTION": "approved_web_app",
    "BROWSER_FILE_UPLOAD": "approved_web_app",
    "BROWSER_FILE_DOWNLOAD": "approved_web_app",
}
_TASK_RESOURCES = {
    "CODEMAGIC_BUILD_VERIFY": "build",
    "CODEMAGIC_BUILD_START": "build",
    "CODEMAGIC_BUILD_STATUS": "build",
    "CODEMAGIC_ARTIFACT_VERIFY": "artifact",
    "GITHUB_READ": None,
    "GITHUB_BRANCH_CREATE": "branch",
    "GITHUB_FILE_COMMIT": "repository",
    "BROWSER_UI_READ": "page",
    "BROWSER_UI_ACTION": "page",
    "BROWSER_FILE_UPLOAD": "file",
    "BROWSER_FILE_DOWNLOAD": "file",
}
_WRITE_TASKS = frozenset({
    "CODEMAGIC_BUILD_START",
    "GITHUB_BRANCH_CREATE",
    "GITHUB_FILE_COMMIT",
    "BROWSER_UI_ACTION",
    "BROWSER_FILE_UPLOAD",
})
_UPLOAD_TASKS = frozenset({"BROWSER_FILE_UPLOAD"})
_WORKSPACE_TASKS = frozenset({
    "GITHUB_FILE_COMMIT",
    "BROWSER_FILE_UPLOAD",
    "BROWSER_FILE_DOWNLOAD",
})
_BROWSER_TASKS = frozenset({
    "BROWSER_UI_READ",
    "BROWSER_UI_ACTION",
    "BROWSER_FILE_UPLOAD",
    "BROWSER_FILE_DOWNLOAD",
})


def _deny(code="NOT_AUTHORIZED"):
    raise AuthorizationError(code)


def _safe_web_target(url):
    if not isinstance(url, str) or len(url) > 2048 or "\\" in url:
        _deny("INVALID_WEB_TARGET")
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError:
        _deny("INVALID_WEB_TARGET")
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or port not in (None, 443)):
        _deny("INVALID_WEB_TARGET")

    decoded_path = unquote(parsed.path or "/")
    segments = decoded_path.split("/")
    if any(segment in {".", ".."} for segment in segments) or "\\" in decoded_path or "\x00" in decoded_path:
        _deny("INVALID_WEB_TARGET")

    normalized_path = posixpath.normpath(decoded_path)
    origin = "https://" + parsed.hostname.lower()
    return origin, normalized_path


def _path_is_within_prefix(path, prefix):
    base = prefix.rstrip("/") or "/"
    if base == "/":
        return path.startswith("/")
    return path == base or path.startswith(base + "/")


def _authorize_web_target(target, context):
    origin, path = _safe_web_target(target.get("url"))
    if origin not in context.allowed_web_origins:
        _deny("WEB_ORIGIN_NOT_ALLOWED")

    matched = False
    for prefix in context.allowed_url_prefixes:
        try:
            prefix_origin, prefix_path = _safe_web_target(prefix)
        except AuthorizationError:
            continue
        if prefix_origin == origin and _path_is_within_prefix(path, prefix_path):
            matched = True
            break
    if not matched:
        _deny("WEB_PATH_NOT_ALLOWED")


def _authorize_workspace_path(target, context):
    raw_path = target.get("workspace_path")
    if not isinstance(raw_path, str) or not raw_path or "\\" in raw_path:
        _deny("INVALID_WORKSPACE_PATH")
    candidate = Path(raw_path)
    if candidate.is_absolute() or any(part in {".", ".."} for part in candidate.parts):
        _deny("INVALID_WORKSPACE_PATH")
    if not context.allowed_workspace_roots:
        _deny("WORKSPACE_NOT_ALLOWED")

    try:
        for root_value in context.allowed_workspace_roots:
            root = Path(root_value).resolve(strict=False)
            resolved = (root / candidate).resolve(strict=False)
            if resolved != root and root in resolved.parents:
                return
    except (OSError, RuntimeError, TypeError):
        _deny("INVALID_WORKSPACE_PATH")
    _deny("WORKSPACE_NOT_ALLOWED")


def authorize_task(request, context):
    """Authorize a validated request against trusted, explicit grants.

    An empty/missing context denies all work. Task-provided permission flags
    never create grants; they can only request permissions already granted by
    the trusted Codemagic workflow configuration.
    """
    if not isinstance(context, AuthorizationContext):
        _deny("AUTHORIZATION_CONTEXT_REQUIRED")

    try:
        task = validate_task(request)
    except TaskValidationError:
        _deny("INVALID_TASK")

    task_type = task["task_type"]
    target = task["target"]
    provider = target["provider"]
    permissions = task["permissions"]

    expected_provider = _TASK_PROVIDERS.get(task_type)
    if expected_provider is None or provider != expected_provider:
        _deny("TASK_PROVIDER_MISMATCH")
    expected_resource = _TASK_RESOURCES.get(task_type)
    if expected_resource is not None and target["resource"] != expected_resource:
        _deny("TASK_RESOURCE_MISMATCH")
    if task_type not in context.allowed_task_types or provider not in context.allowed_providers:
        _deny("TASK_OR_PROVIDER_NOT_ALLOWED")

    repository = target.get("repository")
    if repository is not None and repository not in context.allowed_repositories:
        _deny("REPOSITORY_NOT_ALLOWED")

    branch = target.get("branch")
    if branch is not None and branch not in context.allowed_branches:
        _deny("BRANCH_NOT_ALLOWED")

    mode = task["execution_mode"]
    if provider in {"github", "codemagic"} and mode == "PLAYWRIGHT_ONLY":
        _deny("API_FIRST_REQUIRED")
    if provider == "approved_web_app" and mode == "API_ONLY":
        _deny("UI_FALLBACK_REQUIRED")

    required_permissions = {"read"}
    if task_type in _WRITE_TASKS:
        required_permissions.add("write")
    if task_type in _UPLOAD_TASKS:
        required_permissions.add("upload")

    requested_permissions = {name for name, enabled in permissions.items() if enabled}
    if "delete" in requested_permissions:
        _deny("DELETE_PROHIBITED")
    if requested_permissions != required_permissions:
        _deny("PERMISSION_MISMATCH")
    if not required_permissions.issubset(context.allowed_permissions):
        _deny("PERMISSION_NOT_GRANTED")

    if provider == "approved_web_app":
        if task_type not in _BROWSER_TASKS:
            _deny("BROWSER_TASK_NOT_ALLOWED")
        _authorize_web_target(target, context)
    elif "url" in target:
        _deny("URL_NOT_ALLOWED_FOR_API_PROVIDER")

    if task_type in _WORKSPACE_TASKS:
        _authorize_workspace_path(target, context)
    elif "workspace_path" in target:
        _deny("WORKSPACE_PATH_NOT_ALLOWED")

    return AuthorizationDecision(
        allowed=True,
        task_type=task_type,
        provider=provider,
        granted_permissions=tuple(sorted(required_permissions)),
    )
