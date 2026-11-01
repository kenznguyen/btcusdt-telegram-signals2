import tempfile
import unittest
from pathlib import Path

from integrations.browser_automation.controller import BrowserAutomationController
from integrations.browser_automation.authorization import (
    AuthorizationContext,
    AuthorizationError,
    authorize_task,
)
from integrations.browser_automation.schema import (
    TaskValidationError,
    validate_task,
)


REPOSITORY = "kenznguyen/btcusdt-telegram-signals2"


def github_read_request():
    return {
        "contract_version": "1.0",
        "idempotency_key": "read-intent-0001",
        "task_type": "GITHUB_READ",
        "execution_mode": "API_ONLY",
        "target": {
            "provider": "github",
            "resource": "repository",
            "repository": REPOSITORY,
        },
        "permissions": {
            "read": True,
            "write": False,
            "upload": False,
            "delete": False,
        },
        "timeout_seconds": 60,
    }


def read_context(**overrides):
    values = {
        "allowed_task_types": frozenset({"GITHUB_READ"}),
        "allowed_providers": frozenset({"github"}),
        "allowed_repositories": frozenset({REPOSITORY}),
        "allowed_branches": frozenset(),
        "allowed_permissions": frozenset({"read"}),
        "allowed_web_origins": frozenset(),
        "allowed_url_prefixes": frozenset(),
        "allowed_workspace_roots": (),
    }
    values.update(overrides)
    return AuthorizationContext(**values)


class BrowserAutomationSchemaTest(unittest.TestCase):
    def test_accepts_a_valid_read_only_github_request(self):
        request = github_read_request()
        validated = validate_task(request)
        self.assertEqual(validated["task_type"], "GITHUB_READ")
        self.assertEqual(validated["target"]["repository"], REPOSITORY)


    def test_rejects_non_json_python_values_and_non_string_object_keys(self):
        request = github_read_request()
        request["timeout_seconds"] = float("nan")
        with self.assertRaises(TaskValidationError):
            validate_task(request)

        request = github_read_request()
        request["target"][1] = "not-a-json-object-key"
        with self.assertRaises(TaskValidationError):
            validate_task(request)

    def test_rejects_unknown_top_level_fields_including_secret_material(self):
        request = github_read_request()
        request["api_token"] = "must-not-be-accepted"
        with self.assertRaises(TaskValidationError):
            validate_task(request)

    def test_rejects_unknown_nested_target_fields(self):
        request = github_read_request()
        request["target"]["access_token"] = "must-not-be-accepted"
        with self.assertRaises(TaskValidationError):
            validate_task(request)

    def test_rejects_a_caller_supplied_controller_task_id(self):
        request = github_read_request()
        request["task_id"] = "caller-chosen-id"
        with self.assertRaises(TaskValidationError):
            validate_task(request)

    def test_rejects_missing_required_fields(self):
        request = github_read_request()
        del request["idempotency_key"]
        with self.assertRaises(TaskValidationError):
            validate_task(request)

    def test_rejects_unknown_contract_versions_and_task_types(self):
        for field, value in (("contract_version", "2.0"), ("task_type", "RUN_SHELL")):
            request = github_read_request()
            request[field] = value
            with self.subTest(field=field), self.assertRaises(TaskValidationError):
                validate_task(request)

    def test_rejects_mismatched_provider_and_resource_for_task_type(self):
        request = github_read_request()
        request["target"]["provider"] = "codemagic"
        with self.assertRaises(TaskValidationError):
            validate_task(request)

    def test_rejects_non_https_browser_targets(self):
        request = {
            "contract_version": "1.0",
            "idempotency_key": "browser-read-0001",
            "task_type": "BROWSER_UI_READ",
            "execution_mode": "PLAYWRIGHT_ONLY",
            "target": {
                "provider": "approved_web_app",
                "resource": "page",
                "url": "http://example.com/settings",
            },
            "permissions": {
                "read": True,
                "write": False,
                "upload": False,
                "delete": False,
            },
            "timeout_seconds": 60,
        }
        with self.assertRaises(TaskValidationError):
            validate_task(request)


class BrowserAutomationAuthorizationTest(unittest.TestCase):

    def test_controller_prepares_only_validated_and_authorized_tasks(self):
        controller = BrowserAutomationController(read_context())
        original = github_read_request()
        prepared = controller.prepare_task(original)
        original["target"]["repository"] = "attacker/changed"
        self.assertTrue(prepared.authorization.allowed)
        self.assertEqual(prepared.request["target"]["repository"], REPOSITORY)

    def test_controller_without_trusted_grants_fails_closed(self):
        controller = BrowserAutomationController()
        with self.assertRaises(AuthorizationError):
            controller.prepare_task(github_read_request())

    def test_denies_every_task_when_no_trusted_authorization_context_is_supplied(self):
        with self.assertRaises(AuthorizationError):
            authorize_task(github_read_request(), AuthorizationContext())

    def test_allows_a_read_only_task_when_every_allowlist_matches(self):
        decision = authorize_task(github_read_request(), read_context())
        self.assertTrue(decision.allowed)

    def test_denies_task_type_not_in_the_trusted_allowlist(self):
        context = read_context(allowed_task_types=frozenset())
        with self.assertRaises(AuthorizationError):
            authorize_task(github_read_request(), context)

    def test_denies_provider_or_repository_outside_the_allowlist(self):
        wrong_provider = read_context(allowed_providers=frozenset({"codemagic"}))
        wrong_repository = read_context(allowed_repositories=frozenset({"other/repository"}))
        for context in (wrong_provider, wrong_repository):
            with self.subTest(context=context), self.assertRaises(AuthorizationError):
                authorize_task(github_read_request(), context)

    def test_denies_permission_escalation_even_when_the_task_type_is_allowed(self):
        request = github_read_request()
        request["permissions"]["write"] = True
        context = read_context(allowed_permissions=frozenset({"read", "write"}))
        with self.assertRaises(AuthorizationError):
            authorize_task(request, context)

    def test_denies_all_delete_requests_even_if_delete_is_claimed_as_granted(self):
        request = github_read_request()
        request["permissions"]["delete"] = True
        context = read_context(allowed_permissions=frozenset({"read", "delete"}))
        with self.assertRaises(AuthorizationError):
            authorize_task(request, context)

    def test_requires_an_explicit_write_grant_for_branch_creation(self):
        request = {
            "contract_version": "1.0",
            "idempotency_key": "branch-create-0001",
            "task_type": "GITHUB_BRANCH_CREATE",
            "execution_mode": "API_ONLY",
            "target": {
                "provider": "github",
                "resource": "branch",
                "repository": REPOSITORY,
                "branch": "feature/approved-change",
                "expected_commit_sha": "9ba7074edde48f50e70c2dfaabb1bc06e3a0196e",
            },
            "permissions": {
                "read": True,
                "write": True,
                "upload": False,
                "delete": False,
            },
            "timeout_seconds": 60,
        }
        context = read_context(
            allowed_task_types=frozenset({"GITHUB_BRANCH_CREATE"}),
            allowed_permissions=frozenset({"read"}),
            allowed_branches=frozenset({"feature/approved-change"}),
        )
        with self.assertRaises(AuthorizationError):
            authorize_task(request, context)

        write_granted = read_context(
            allowed_task_types=frozenset({"GITHUB_BRANCH_CREATE"}),
            allowed_permissions=frozenset({"read", "write"}),
            allowed_branches=frozenset({"feature/approved-change"}),
        )
        self.assertTrue(authorize_task(request, write_granted).allowed)

    def test_denies_playwright_only_for_providers_with_an_api_adapter(self):
        request = github_read_request()
        request["execution_mode"] = "PLAYWRIGHT_ONLY"
        with self.assertRaises(AuthorizationError):
            authorize_task(request, read_context())

    def test_requires_an_exact_allowed_web_origin_and_path_prefix(self):
        request = {
            "contract_version": "1.0",
            "idempotency_key": "browser-read-0002",
            "task_type": "BROWSER_UI_READ",
            "execution_mode": "PLAYWRIGHT_ONLY",
            "target": {
                "provider": "approved_web_app",
                "resource": "page",
                "url": "https://console.example.com/settings/profile",
            },
            "permissions": {
                "read": True,
                "write": False,
                "upload": False,
                "delete": False,
            },
            "timeout_seconds": 60,
        }
        context = AuthorizationContext(
            allowed_task_types=frozenset({"BROWSER_UI_READ"}),
            allowed_providers=frozenset({"approved_web_app"}),
            allowed_permissions=frozenset({"read"}),
            allowed_web_origins=frozenset({"https://console.example.com"}),
            allowed_url_prefixes=frozenset({"https://console.example.com/settings"}),
        )
        self.assertTrue(authorize_task(request, context).allowed)

        request["target"]["url"] = "https://console.example.com.evil.test/settings/profile"
        with self.assertRaises(AuthorizationError):
            authorize_task(request, context)

    def test_denies_browser_target_when_path_prefix_is_not_allowlisted(self):
        request = {
            "contract_version": "1.0",
            "idempotency_key": "browser-read-0003",
            "task_type": "BROWSER_UI_READ",
            "execution_mode": "PLAYWRIGHT_ONLY",
            "target": {
                "provider": "approved_web_app",
                "resource": "page",
                "url": "https://console.example.com/admin",
            },
            "permissions": {
                "read": True,
                "write": False,
                "upload": False,
                "delete": False,
            },
            "timeout_seconds": 60,
        }
        context = AuthorizationContext(
            allowed_task_types=frozenset({"BROWSER_UI_READ"}),
            allowed_providers=frozenset({"approved_web_app"}),
            allowed_permissions=frozenset({"read"}),
            allowed_web_origins=frozenset({"https://console.example.com"}),
            allowed_url_prefixes=frozenset({"https://console.example.com/settings"}),
        )
        with self.assertRaises(AuthorizationError):
            authorize_task(request, context)


    def test_authorizes_github_file_commit_only_inside_an_allowed_workspace(self):
        request = {
            "contract_version": "1.0",
            "idempotency_key": "github-file-commit-0001",
            "task_type": "GITHUB_FILE_COMMIT",
            "execution_mode": "API_ONLY",
            "target": {
                "provider": "github",
                "resource": "repository",
                "repository": REPOSITORY,
                "branch": "feature/approved-change",
                "workspace_path": "docs/architecture/decision.md",
            },
            "permissions": {
                "read": True,
                "write": True,
                "upload": False,
                "delete": False,
            },
            "timeout_seconds": 60,
        }
        with tempfile.TemporaryDirectory() as workspace:
            context = read_context(
                allowed_task_types=frozenset({"GITHUB_FILE_COMMIT"}),
                allowed_permissions=frozenset({"read", "write"}),
                allowed_branches=frozenset({"feature/approved-change"}),
                allowed_workspace_roots=(Path(workspace),),
            )
            self.assertTrue(authorize_task(request, context).allowed)

            request["target"]["workspace_path"] = "../outside/secret.txt"
            with self.assertRaises(AuthorizationError):
                authorize_task(request, context)

    def test_denies_browser_urls_with_query_strings_that_could_carry_credentials(self):
        request = {
            "contract_version": "1.0",
            "idempotency_key": "browser-read-0004",
            "task_type": "BROWSER_UI_READ",
            "execution_mode": "PLAYWRIGHT_ONLY",
            "target": {
                "provider": "approved_web_app",
                "resource": "page",
                "url": "https://console.example.com/settings?access_token=secret",
            },
            "permissions": {
                "read": True,
                "write": False,
                "upload": False,
                "delete": False,
            },
            "timeout_seconds": 60,
        }
        context = AuthorizationContext(
            allowed_task_types=frozenset({"BROWSER_UI_READ"}),
            allowed_providers=frozenset({"approved_web_app"}),
            allowed_permissions=frozenset({"read"}),
            allowed_web_origins=frozenset({"https://console.example.com"}),
            allowed_url_prefixes=frozenset({"https://console.example.com/settings"}),
        )
        with self.assertRaises(AuthorizationError):
            authorize_task(request, context)

    def test_denies_workspace_path_traversal(self):
        request = {
            "contract_version": "1.0",
            "idempotency_key": "browser-upload-0001",
            "task_type": "BROWSER_FILE_UPLOAD",
            "execution_mode": "PLAYWRIGHT_ONLY",
            "target": {
                "provider": "approved_web_app",
                "resource": "file",
                "url": "https://console.example.com/settings/import",
                "workspace_path": "../outside/secret.txt",
            },
            "permissions": {
                "read": True,
                "write": True,
                "upload": True,
                "delete": False,
            },
            "timeout_seconds": 60,
        }
        with tempfile.TemporaryDirectory() as workspace:
            context = AuthorizationContext(
                allowed_task_types=frozenset({"BROWSER_FILE_UPLOAD"}),
                allowed_providers=frozenset({"approved_web_app"}),
                allowed_permissions=frozenset({"read", "write", "upload"}),
                allowed_web_origins=frozenset({"https://console.example.com"}),
                allowed_url_prefixes=frozenset({"https://console.example.com/settings"}),
                allowed_workspace_roots=(Path(workspace),),
            )
            with self.assertRaises(AuthorizationError):
                authorize_task(request, context)


if __name__ == "__main__":
    unittest.main()
