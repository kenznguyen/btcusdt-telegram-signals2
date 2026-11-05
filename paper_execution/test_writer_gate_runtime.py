"""Process-level SWG-F runtime acceptance tests.

RED-stage contract tests: the production writer gate is intentionally absent.
All tests use disposable temporary paths and synthetic SQLite data only.
"""
import importlib
import importlib.util
import multiprocessing
import os
from pathlib import Path
import platform
import queue
import signal
import sqlite3
import sys
import tempfile
import time
import unittest
from unittest import mock


MODULE_NAME = "paper_execution.writer_gate"


def _load_gate_module():
    spec = importlib.util.find_spec(MODULE_NAME)
    if spec is None:
        raise AssertionError(
            "SWG-F runtime contract: paper_execution.writer_gate is not implemented"
        )
    return importlib.import_module(MODULE_NAME)


def _result_state(result):
    return getattr(result, "state", result)


def _child_hold_writer(paper_db_path, ready, release):
    try:
        module = _load_gate_module()
        gate = module.PaperWriterGate.initialize(paper_db_path=paper_db_path)
        token = gate.admit_writer()
        ready.put(("ADMITTED", getattr(token, "generation", None)))
        if not release.wait(10):
            raise TimeoutError("parent did not release test writer")
        gate.validate_writer_token(token)
        gate.release_writer(token)
        ready.put(("RELEASED", None))
    except BaseException as exc:
        ready.put(("ERROR", repr(exc)))
        raise


def _child_try_admission(paper_db_path, start, result):
    try:
        if not start.wait(10):
            raise TimeoutError("start barrier was not released")
        module = _load_gate_module()
        gate = module.PaperWriterGate.initialize(paper_db_path=paper_db_path)
        token = gate.admit_writer()
        gate.release_writer(token)
        result.put(("ADMITTED", getattr(token, "generation", None)))
    except BaseException as exc:
        result.put(("REJECTED", type(exc).__name__))


def _child_commit_then_crash(paper_db_path, ready):
    module = _load_gate_module()
    gate = module.PaperWriterGate.initialize(paper_db_path=paper_db_path)
    token = gate.admit_writer()
    connection = sqlite3.connect(paper_db_path, timeout=5)
    try:
        connection.execute("BEGIN IMMEDIATE")
        gate.validate_writer_token(token)
        connection.execute(
            "INSERT INTO crash_probe(commit_id, value) VALUES (?, ?)",
            ("commit-before-crash", "committed"),
        )
        gate.validate_writer_token(token)
        connection.commit()
        ready.put("COMMITTED")
        # Simulate process death after the DB commit but before token cleanup.
        os._exit(73)
    finally:
        connection.close()


class PaperWriterGateRuntimeContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="swgf-runtime-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.paper_db = self.root / "paper.sqlite3"
        self.ctx = multiprocessing.get_context("spawn")

    def require_gate(self):
        return _load_gate_module()

    def gate(self, module=None):
        module = module or self.require_gate()
        return module.PaperWriterGate.initialize(paper_db_path=str(self.paper_db))

    def assert_drain_state(self, result, expected):
        self.assertEqual(str(_result_state(result)), expected)

    def test_multiprocess_admission_is_atomic_with_drain_transition(self):
        module = self.require_gate()
        gate = self.gate(module)
        start = self.ctx.Event()
        results = self.ctx.Queue()
        workers = [
            self.ctx.Process(
                target=_child_try_admission,
                args=(str(self.paper_db), start, results),
            )
            for _ in range(4)
        ]
        for worker in workers:
            worker.start()
        start.set()
        drain_result = gate.begin_drain(timeout_seconds=0.2)
        outcomes = [results.get(timeout=5) for _ in workers]
        for worker in workers:
            worker.join(timeout=5)
            self.assertFalse(worker.is_alive(), "admission worker did not exit")
            self.assertEqual(worker.exitcode, 0)
        self.assertTrue(all(item[0] in {"ADMITTED", "REJECTED"} for item in outcomes))
        with self.assertRaises(Exception):
            gate.admit_writer()
        state = str(_result_state(drain_result))
        if state == "DRAIN_TIMEOUT":
            drain_result = gate.wait_for_drain(timeout_seconds=5)
        self.assert_drain_state(drain_result, "DRAINED")

    def test_drain_waits_for_admitted_writer_in_another_process(self):
        module = self.require_gate()
        gate = self.gate(module)
        ready, release = self.ctx.Queue(), self.ctx.Event()
        writer = self.ctx.Process(
            target=_child_hold_writer,
            args=(str(self.paper_db), ready, release),
        )
        writer.start()
        self.assertEqual(ready.get(timeout=5)[0], "ADMITTED")
        result = gate.begin_drain(timeout_seconds=0.2)
        self.assert_drain_state(result, "DRAIN_TIMEOUT")
        release.set()
        self.assertEqual(ready.get(timeout=5)[0], "RELEASED")
        writer.join(timeout=5)
        self.assertFalse(writer.is_alive())
        self.assertEqual(writer.exitcode, 0)
        self.assert_drain_state(gate.wait_for_drain(timeout_seconds=5), "DRAINED")

    def test_new_process_is_rejected_after_draining_is_persisted(self):
        module = self.require_gate()
        gate = self.gate(module)
        self.assert_drain_state(
            gate.begin_drain(timeout_seconds=1), "DRAINED"
        )
        start, result = self.ctx.Event(), self.ctx.Queue()
        worker = self.ctx.Process(
            target=_child_try_admission,
            args=(str(self.paper_db), start, result),
        )
        worker.start()
        start.set()
        outcome = result.get(timeout=5)
        worker.join(timeout=5)
        self.assertEqual(worker.exitcode, 0)
        self.assertEqual(outcome[0], "REJECTED")

    @unittest.skipUnless(os.name == "posix", "SIGKILL lock recovery is POSIX-specific")
    def test_sigkill_releases_writer_lock_and_orphan_token_is_reconciled(self):
        module = self.require_gate()
        gate = self.gate(module)
        ready, release = self.ctx.Queue(), self.ctx.Event()
        writer = self.ctx.Process(
            target=_child_hold_writer,
            args=(str(self.paper_db), ready, release),
        )
        writer.start()
        self.assertEqual(ready.get(timeout=5)[0], "ADMITTED")
        writer.kill()
        writer.join(timeout=5)
        self.assertFalse(writer.is_alive())
        self.assertEqual(writer.exitcode, -signal.SIGKILL)
        self.assert_drain_state(
            gate.begin_drain(timeout_seconds=5), "DRAINED"
        )
        with self.assertRaises(Exception):
            gate.admit_writer()

    def test_crash_after_commit_before_release_recovers_without_duplicate_commit(self):
        module = self.require_gate()
        gate = self.gate(module)
        with sqlite3.connect(self.paper_db) as connection:
            connection.execute(
                "CREATE TABLE crash_probe(commit_id TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
        ready = self.ctx.Queue()
        writer = self.ctx.Process(
            target=_child_commit_then_crash,
            args=(str(self.paper_db), ready),
        )
        writer.start()
        self.assertEqual(ready.get(timeout=5), "COMMITTED")
        writer.join(timeout=5)
        self.assertFalse(writer.is_alive())
        self.assertEqual(writer.exitcode, 73)
        self.assert_drain_state(
            gate.begin_drain(timeout_seconds=5), "DRAINED"
        )
        with sqlite3.connect(self.paper_db) as connection:
            rows = connection.execute(
                "SELECT commit_id, value FROM crash_probe"
            ).fetchall()
        self.assertEqual(rows, [("commit-before-crash", "committed")])

    def test_drain_timeout_remains_draining_until_explicit_wait(self):
        module = self.require_gate()
        gate = self.gate(module)
        ready, release = self.ctx.Queue(), self.ctx.Event()
        writer = self.ctx.Process(
            target=_child_hold_writer,
            args=(str(self.paper_db), ready, release),
        )
        writer.start()
        self.assertEqual(ready.get(timeout=5)[0], "ADMITTED")
        self.assert_drain_state(
            gate.begin_drain(timeout_seconds=0.1), "DRAIN_TIMEOUT"
        )
        with self.assertRaises(Exception):
            gate.admit_writer()
        release.set()
        self.assertEqual(ready.get(timeout=5)[0], "RELEASED")
        writer.join(timeout=5)
        self.assertEqual(writer.exitcode, 0)
        self.assert_drain_state(gate.wait_for_drain(timeout_seconds=5), "DRAINED")

    def test_reopen_requires_settled_outcome_and_advances_generation(self):
        module = self.require_gate()
        gate = self.gate(module)
        old_token = gate.admit_writer()
        old_generation = old_token.generation
        gate.release_writer(old_token)
        self.assert_drain_state(
            gate.begin_drain(timeout_seconds=1), "DRAINED"
        )
        with self.assertRaises(Exception):
            gate.reopen(authorized=True, settled_outcome=None)
        gate.reopen(
            authorized=True, settled_outcome="ABORTED/NOT_STARTED"
        )
        new_token = gate.admit_writer()
        self.assertGreater(new_token.generation, old_generation)
        with self.assertRaises(Exception):
            gate.validate_writer_token(old_token)
        gate.release_writer(new_token)

    def test_old_process_token_cannot_commit_or_release_after_reopen(self):
        module = self.require_gate()
        gate = self.gate(module)
        stale = gate.admit_writer()
        gate.release_writer(stale)
        self.assert_drain_state(
            gate.begin_drain(timeout_seconds=1), "DRAINED"
        )
        gate.reopen(
            authorized=True, settled_outcome="ABORTED/NOT_STARTED"
        )
        with self.assertRaises(Exception):
            gate.validate_writer_token(stale)
        self.assertFalse(gate.release_writer(stale))

    def test_denied_admission_does_not_create_or_open_paper_db(self):
        module = self.require_gate()
        gate = self.gate(module)
        self.assertFalse(self.paper_db.exists())
        self.assert_drain_state(
            gate.begin_drain(timeout_seconds=1), "DRAINED"
        )
        with self.assertRaises(Exception):
            with gate.writer_transaction(paper_db_path=str(self.paper_db)):
                self.fail("a drained gate must not enter a Paper transaction")
        self.assertFalse(self.paper_db.exists())

    def test_platform_lock_adapters_fail_closed_when_unsupported(self):
        module = self.require_gate()
        gate_type = module.PaperWriterGate
        with mock.patch.object(sys, "platform", "unsupported-os"), mock.patch.object(
            platform, "system", return_value="UnsupportedOS"
        ):
            with self.assertRaises(Exception):
                gate_type.initialize(paper_db_path=str(self.paper_db))
        self.assertFalse(self.paper_db.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
