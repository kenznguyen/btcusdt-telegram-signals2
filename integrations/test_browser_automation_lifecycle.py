import unittest

from integrations.browser_automation.controller import (
    BrowserAutomationController,
    IdempotencyConflictError,
    InvalidTaskTransitionError,
    TaskStatus,
)
from integrations.browser_automation.authorization import AuthorizationContext


REPOSITORY = "kenznguyen/btcusdt-telegram-signals2"


def task_request(**overrides):
    request = {
        "contract_version": "1.0",
        "idempotency_key": "lifecycle-intent-0001",
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
    request.update(overrides)
    return request


def authorized_controller():
    context = AuthorizationContext(
        allowed_task_types=frozenset({"GITHUB_READ"}),
        allowed_providers=frozenset({"github"}),
        allowed_repositories=frozenset({REPOSITORY}),
        allowed_branches=frozenset(),
        allowed_permissions=frozenset({"read"}),
        allowed_web_origins=frozenset(),
        allowed_url_prefixes=frozenset(),
        allowed_workspace_roots=(),
    )
    return BrowserAutomationController(context)


class BrowserAutomationLifecycleTest(unittest.TestCase):
    def test_accepts_authorized_task_with_controller_generated_id_and_queued_status(self):
        controller = authorized_controller()

        task = controller.accept_task(task_request())

        self.assertTrue(task.task_id)
        self.assertEqual(task.status, TaskStatus.QUEUED)
        self.assertEqual(task.idempotency_key, "lifecycle-intent-0001")

    def test_same_idempotency_key_and_same_payload_returns_original_task(self):
        controller = authorized_controller()

        first = controller.accept_task(task_request())
        retry = controller.accept_task(task_request())

        self.assertEqual(retry.task_id, first.task_id)
        self.assertEqual(retry.status, TaskStatus.QUEUED)

    def test_same_idempotency_key_with_different_payload_is_rejected(self):
        controller = authorized_controller()
        controller.accept_task(task_request())

        changed = task_request(timeout_seconds=120)
        with self.assertRaises(IdempotencyConflictError):
            controller.accept_task(changed)

    def test_task_transitions_from_queued_to_running(self):
        controller = authorized_controller()
        task = controller.accept_task(task_request())

        running = controller.start_task(task.task_id)

        self.assertEqual(running.status, TaskStatus.RUNNING)

    def test_task_can_pause_for_user_and_resume(self):
        controller = authorized_controller()
        task = controller.accept_task(task_request())
        controller.start_task(task.task_id)

        waiting = controller.wait_for_user(task.task_id)
        resumed = controller.resume_task(task.task_id)

        self.assertEqual(waiting.status, TaskStatus.WAITING_FOR_USER)
        self.assertEqual(resumed.status, TaskStatus.RUNNING)

    def test_succeeded_requires_verified_postconditions(self):
        controller = authorized_controller()
        task = controller.accept_task(task_request())
        controller.start_task(task.task_id)

        with self.assertRaises(InvalidTaskTransitionError):
            controller.finish_task(task.task_id, TaskStatus.SUCCEEDED, verified=False)

        succeeded = controller.finish_task(
            task.task_id, TaskStatus.SUCCEEDED, verified=True,
            result={"observed": "verified"},
        )
        self.assertEqual(succeeded.status, TaskStatus.SUCCEEDED)

    def test_timeout_marks_unknown_and_same_key_retry_does_not_create_second_task(self):
        controller = authorized_controller()
        task = controller.accept_task(task_request())
        controller.start_task(task.task_id)

        unknown = controller.mark_unknown(task.task_id, reason="execution timed out")
        retry = controller.accept_task(task_request())

        self.assertEqual(unknown.status, TaskStatus.UNKNOWN)
        self.assertEqual(retry.task_id, task.task_id)
        self.assertEqual(retry.status, TaskStatus.UNKNOWN)

    def test_unknown_task_requires_reconciliation_before_terminal_success(self):
        controller = authorized_controller()
        task = controller.accept_task(task_request())
        controller.start_task(task.task_id)
        controller.mark_unknown(task.task_id, reason="provider outcome unavailable")

        with self.assertRaises(InvalidTaskTransitionError):
            controller.finish_task(task.task_id, TaskStatus.SUCCEEDED, verified=True)

        reconciled = controller.reconcile_task(
            task.task_id,
            outcome=TaskStatus.SUCCEEDED,
            verified=True,
            result={"provider_state": "complete"},
        )
        self.assertEqual(reconciled.status, TaskStatus.SUCCEEDED)

    def test_queued_task_can_be_cancelled_but_terminal_task_cannot_restart(self):
        controller = authorized_controller()
        task = controller.accept_task(task_request())

        cancelled = controller.cancel_task(task.task_id)

        self.assertEqual(cancelled.status, TaskStatus.CANCELLED)
        with self.assertRaises(InvalidTaskTransitionError):
            controller.start_task(task.task_id)


if __name__ == "__main__":
    unittest.main()
