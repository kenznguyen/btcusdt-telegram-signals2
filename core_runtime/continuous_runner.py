"""Paper-only Continuous Core orchestration over the existing One-shot Runner."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile

from core_runtime.continuous_cadence import (
    cycle_key_for_bundle,
    latest_eligible_m15_open_ms,
    next_m15_deadline_ms,
    wait_until_deadline,
)
from core_runtime.continuous_journal import CycleConflict, JournalError
from core_runtime.input_bundle import BundleValidationError, validate_bundle
from core_runtime.preflight import _load_config, _preflight


class ContinuousInputError(ValueError):
    """A bundle or persisted cycle input cannot be trusted."""


class CycleNotReady(RuntimeError):
    """The expected closed M15 candle has not passed settlement."""


class ContinuousCoreRunner:
    """Orchestrate one immutable Bundle v1 per closed M15 candle in PAPER mode."""

    _TERMINAL = {
        "NO_SIGNAL", "PAPER_ACCEPTED", "RISK_REJECTED", "INPUT_REJECTED", "FAILED",
    }

    def __init__(
        self,
        *,
        config_path,
        journal,
        bundle_store_dir,
        source_sha,
        config_sha256,
        settlement_ms,
        max_book_age_ms=5_000,
        run_once_fn=None,
        audit_reader=None,
        preflight_fn=None,
    ):
        self.config_path = Path(config_path).expanduser().resolve()
        self.journal = journal
        self.bundle_store_dir = Path(bundle_store_dir).expanduser().resolve()
        self.source_sha = self._text(source_sha, "SOURCE_SHA")
        self.config_sha256 = self._text(config_sha256, "CONFIG_SHA256")
        self.settlement_ms = self._nonnegative_int(settlement_ms, "SETTLEMENT_MS")
        self.max_book_age_ms = self._positive_int(max_book_age_ms, "MAX_BOOK_AGE_MS")
        if run_once_fn is None:
            from core_runtime.one_shot import run_once
            run_once_fn = run_once
        if audit_reader is None:
            from paper_execution.ledger import read_audit
            audit_reader = read_audit
        self.run_once_fn = run_once_fn
        self.audit_reader = audit_reader
        self.preflight_fn = _preflight if preflight_fn is None else preflight_fn
        self._stop_requested = False
        self._lock_fd = None

    @staticmethod
    def _text(value, code):
        if not isinstance(value, str) or not value.strip() or not value.isprintable():
            raise ValueError(f"CONTINUOUS_{code}_INVALID")
        return value

    @staticmethod
    def _nonnegative_int(value, code):
        if type(value) is not int or value < 0:
            raise ValueError(f"CONTINUOUS_{code}_INVALID")
        return value

    @staticmethod
    def _positive_int(value, code):
        if type(value) is not int or value <= 0:
            raise ValueError(f"CONTINUOUS_{code}_INVALID")
        return value

    @staticmethod
    def _strict_bundle(raw):
        def unique_object(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("DUPLICATE_JSON_KEY")
                result[key] = value
            return result

        try:
            bundle = json.loads(
                raw.decode("utf-8"),
                object_pairs_hook=unique_object,
                parse_constant=lambda _: (_ for _ in ()).throw(
                    ValueError("JSON_CONSTANT_INVALID")
                ),
            )
        except (UnicodeError, json.JSONDecodeError, ValueError):
            raise ContinuousInputError("CONTINUOUS_BUNDLE_FILE_INVALID") from None
        if not isinstance(bundle, dict):
            raise ContinuousInputError("CONTINUOUS_BUNDLE_OBJECT_INVALID")
        return bundle

    def _store_immutable_bundle(self, raw):
        digest = "sha256:" + hashlib.sha256(raw).hexdigest()
        target = self.bundle_store_dir / (digest.split(":", 1)[1] + ".json")
        self.bundle_store_dir.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.is_symlink() or not target.is_file():
                raise ContinuousInputError("CONTINUOUS_BUNDLE_STORE_CONFLICT")
            existing = target.read_bytes()
            if "sha256:" + hashlib.sha256(existing).hexdigest() != digest:
                raise ContinuousInputError("CONTINUOUS_BUNDLE_STORE_DIGEST_MISMATCH")
            return target, digest

        fd, temporary = tempfile.mkstemp(prefix=".bundle-", suffix=".tmp",
                                          dir=self.bundle_store_dir)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
            directory_fd = os.open(self.bundle_store_dir, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except Exception:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise
        return target, digest

    def _assert_config_digest(self):
        try:
            raw = self.config_path.read_bytes()
        except OSError:
            raise ContinuousInputError("CONTINUOUS_CONFIG_UNAVAILABLE") from None
        actual = "sha256:" + hashlib.sha256(raw).hexdigest()
        if actual != self.config_sha256:
            raise ContinuousInputError("CONTINUOUS_CONFIG_DIGEST_MISMATCH")
        return actual

    def _validated_bundle(self, raw):
        bundle = self._strict_bundle(raw)
        try:
            validate_bundle(bundle, max_book_age_ms=self.max_book_age_ms)
            cycle_key = cycle_key_for_bundle(
                bundle, max_book_age_ms=self.max_book_age_ms
            )
        except (BundleValidationError, KeyError, TypeError, ValueError) as exc:
            reason = str(exc) or "BUNDLE_VALIDATION_FAILED"
            raise ContinuousInputError(reason) from None
        return bundle, cycle_key

    def process_bundle(self, bundle_path, *, now_ms):
        """Validate, persist, claim and execute one immutable M15 cycle at most once."""
        now_ms = self._nonnegative_int(now_ms, "NOW_MS")
        self._assert_config_digest()
        self.preflight_fn(self.config_path, now_ms=now_ms)
        try:
            raw = Path(bundle_path).expanduser().read_bytes()
        except (OSError, ValueError):
            raise ContinuousInputError("CONTINUOUS_BUNDLE_FILE_UNAVAILABLE") from None
        bundle, cycle_key = self._validated_bundle(raw)
        candle = bundle["marketData"]["m15"]["candles"][-1]
        eligible_at = candle["closeTimeMs"] + self.settlement_ms
        if now_ms < eligible_at:
            raise CycleNotReady("CONTINUOUS_M15_SETTLEMENT_PENDING")
        expected_open = latest_eligible_m15_open_ms(
            now_ms, settlement_ms=self.settlement_ms
        )
        if candle["openTimeMs"] != expected_open:
            raise ContinuousInputError("CONTINUOUS_BUNDLE_NOT_LATEST_ELIGIBLE_M15")

        stored_path, bundle_digest = self._store_immutable_bundle(raw)
        try:
            claimed = self.journal.claim_cycle(
                cycle_key=cycle_key,
                bundle_id=bundle["bundleId"],
                bundle_sha256=bundle_digest,
                bundle_path=str(stored_path),
                source_sha=self.source_sha,
                config_sha256=self.config_sha256,
                claimed_at_ms=now_ms,
            )
        except (CycleConflict, JournalError):
            raise

        if not claimed:
            existing = self.journal.get_cycle(cycle_key)
            return {
                "cycleKey": cycle_key,
                "status": "DUPLICATE_CYCLE",
                "existingStatus": existing["status"] if existing else None,
            }

        self.journal.transition_cycle(
            cycle_key,
            expected_status="CLAIMED",
            status="VALIDATING",
            updated_at_ms=now_ms,
        )
        self.journal.transition_cycle(
            cycle_key,
            expected_status="VALIDATING",
            status="EXECUTING",
            updated_at_ms=now_ms,
        )
        return self._execute_claimed(
            cycle_key, stored_path, now_ms=now_ms
        )

    def _execute_claimed(self, cycle_key, bundle_path, *, now_ms):
        def persist_intent(intent):
            if not isinstance(intent, dict):
                raise ValueError("CONTINUOUS_INTENT_INVALID")
            intent_id = intent.get("intentId")
            if not isinstance(intent_id, str) or not intent_id.strip():
                raise ValueError("CONTINUOUS_INTENT_ID_REQUIRED")
            self.journal.record_intent(
                cycle_key, intent_id, updated_at_ms=now_ms
            )

        try:
            result = self.run_once_fn(
                self.config_path,
                bundle_path,
                now_ms=now_ms,
                on_intent_prepared=persist_intent,
            )
            if not isinstance(result, dict):
                raise ValueError("CONTINUOUS_ONE_SHOT_RESULT_INVALID")
        except Exception:
            cycle = self.journal.get_cycle(cycle_key)
            status = (
                "UNKNOWN_REQUIRES_RECONCILIATION"
                if cycle and cycle["intentId"] else "FAILED"
            )
            self.journal.transition_cycle(
                cycle_key,
                expected_status="EXECUTING",
                status=status,
                updated_at_ms=now_ms,
                terminal_result="ONE_SHOT_EXCEPTION",
            )
            return {"cycleKey": cycle_key, "status": status}

        cycle = self.journal.get_cycle(cycle_key)
        intent_id = cycle["intentId"] if cycle else None
        run_status = result.get("runStatus")
        if run_status in self._TERMINAL:
            status = run_status
        elif run_status in ("RUN_FAILED", "PAPER_COMMIT_FAILED"):
            status = (
                "UNKNOWN_REQUIRES_RECONCILIATION"
                if intent_id else "FAILED"
            )
        else:
            status = (
                "UNKNOWN_REQUIRES_RECONCILIATION"
                if intent_id else "FAILED"
            )

        ledger_ref = result.get("paperLedgerReference")
        ledger_ref = ledger_ref if isinstance(ledger_ref, dict) else {}
        terminal_result = result.get("reasonCode") or run_status or status
        self.journal.transition_cycle(
            cycle_key,
            expected_status="EXECUTING",
            status=status,
            updated_at_ms=now_ms,
            run_id=result.get("runId"),
            order_id=ledger_ref.get("orderId"),
            terminal_result=terminal_result,
        )
        return {"cycleKey": cycle_key, "status": status, "result": result}

    def _read_ledger_intent(self, intent_id):
        _, ledger_path = _load_config(self.config_path)
        before_id = None
        while True:
            page = self.audit_reader(ledger_path, limit=100, before_id=before_id)
            if not isinstance(page, dict) or not isinstance(page.get("events"), list):
                raise ValueError("CONTINUOUS_LEDGER_AUDIT_INVALID")
            for event in page["events"]:
                document = event.get("document") if isinstance(event, dict) else None
                if isinstance(document, dict) and document.get("intentId") == intent_id:
                    return document
            next_before = page.get("nextBeforeId")
            if next_before is None:
                return None
            if type(next_before) is not int or next_before <= 0:
                raise ValueError("CONTINUOUS_LEDGER_AUDIT_CURSOR_INVALID")
            if before_id is not None and next_before >= before_id:
                raise ValueError("CONTINUOUS_LEDGER_AUDIT_CURSOR_STALLED")
            before_id = next_before

    def _verify_persisted_cycle(self, cycle):
        self._assert_config_digest()
        try:
            path = Path(cycle["bundlePath"]).resolve(strict=True)
            if path.parent != self.bundle_store_dir or path.is_symlink() or not path.is_file():
                raise ContinuousInputError("CONTINUOUS_PERSISTED_BUNDLE_PATH_INVALID")
            raw = path.read_bytes()
        except (OSError, KeyError, ValueError):
            raise ContinuousInputError("CONTINUOUS_PERSISTED_BUNDLE_UNAVAILABLE") from None
        digest = "sha256:" + hashlib.sha256(raw).hexdigest()
        if digest != cycle["bundleSha256"]:
            raise ContinuousInputError("CONTINUOUS_PERSISTED_BUNDLE_DIGEST_MISMATCH")
        bundle, cycle_key = self._validated_bundle(raw)
        if cycle_key != cycle["cycleKey"] or bundle["bundleId"] != cycle["bundleId"]:
            raise ContinuousInputError("CONTINUOUS_PERSISTED_BUNDLE_IDENTITY_MISMATCH")
        if (cycle["sourceSha"] != self.source_sha
                or cycle["configSha256"] != self.config_sha256):
            raise ContinuousInputError("CONTINUOUS_RECOVERY_PROVENANCE_MISMATCH")
        return path

    def recover_incomplete(self, *, now_ms):
        """Reconcile known ledger commits; resume only cycles proven pre-submit."""
        now_ms = self._nonnegative_int(now_ms, "NOW_MS")
        recovered = []
        cycles = self.journal.list_cycles()
        try:
            self._assert_config_digest()
        except ContinuousInputError:
            return [{
                "cycleKey": cycle["cycleKey"], "status": "BLOCKED",
                "reason": "CONFIG_PROVENANCE_MISMATCH",
            } for cycle in cycles]
        for cycle in cycles:
            cycle_key = cycle["cycleKey"]
            if cycle["status"] in self._TERMINAL:
                if cycle["status"] in ("PAPER_ACCEPTED", "RISK_REJECTED"):
                    try:
                        self._verify_persisted_cycle(cycle)
                        if not cycle["intentId"]:
                            raise ValueError("TERMINAL_INTENT_MISSING")
                        order = self._read_ledger_intent(cycle["intentId"])
                    except Exception:
                        recovered.append({
                            "cycleKey": cycle_key, "status": "BLOCKED",
                            "reason": "LEDGER_RECONCILIATION_UNAVAILABLE",
                        })
                        continue
                    expected_status = (
                        "REJECTED" if cycle["status"] == "RISK_REJECTED"
                        else ("FILLED", "OPEN", "PARTIALLY_FILLED")
                    )
                    order_status = order.get("status") if order else None
                    status_matches = (
                        order_status == expected_status
                        if isinstance(expected_status, str)
                        else order_status in expected_status
                    )
                    if (not order or not status_matches
                            or order.get("orderId") != cycle["orderId"]):
                        recovered.append({
                            "cycleKey": cycle_key, "status": "BLOCKED",
                            "reason": "TERMINAL_LEDGER_DISAGREEMENT",
                        })
                    else:
                        recovered.append({
                            "cycleKey": cycle_key, "status": "VERIFIED",
                        })
                continue
            try:
                bundle_path = self._verify_persisted_cycle(cycle)
                if cycle["status"] in (
                    "EXECUTING", "UNKNOWN_REQUIRES_RECONCILIATION"
                ) and cycle["intentId"]:
                    try:
                        order = self._read_ledger_intent(cycle["intentId"])
                    except Exception:
                        recovered.append({
                            "cycleKey": cycle_key, "status": "BLOCKED",
                            "reason": "LEDGER_RECONCILIATION_UNAVAILABLE",
                        })
                        continue
                    if order is not None:
                        order_status = order.get("status")
                        terminal = (
                            "RISK_REJECTED" if order_status == "REJECTED"
                            else "PAPER_ACCEPTED"
                            if order_status in ("FILLED", "OPEN", "PARTIALLY_FILLED")
                            else None
                        )
                        if terminal is None:
                            recovered.append({
                                "cycleKey": cycle_key, "status": "BLOCKED",
                                "reason": "LEDGER_ORDER_STATUS_UNKNOWN",
                            })
                            continue
                        self.journal.transition_cycle(
                            cycle_key,
                            expected_status=cycle["status"],
                            status=terminal,
                            updated_at_ms=max(now_ms, cycle["updatedAtMs"]),
                            order_id=order.get("orderId"),
                            terminal_result=order_status,
                        )
                        recovered.append({"cycleKey": cycle_key, "status": terminal})
                        continue
                    if cycle["intentId"]:
                        recovered.append({
                            "cycleKey": cycle_key, "status": "BLOCKED",
                            "reason": "INTENT_NOT_FOUND_REQUIRES_RECONCILIATION",
                        })
                        continue

                if cycle["status"] == "CLAIMED":
                    self.journal.transition_cycle(
                        cycle_key, expected_status="CLAIMED", status="VALIDATING",
                        updated_at_ms=max(now_ms, cycle["updatedAtMs"]),
                    )
                    cycle = self.journal.get_cycle(cycle_key)
                if cycle["status"] == "VALIDATING":
                    self.journal.transition_cycle(
                        cycle_key, expected_status="VALIDATING", status="EXECUTING",
                        updated_at_ms=max(now_ms, cycle["updatedAtMs"]),
                    )
                elif cycle["status"] != "EXECUTING":
                    recovered.append({
                        "cycleKey": cycle_key, "status": "BLOCKED",
                        "reason": "CYCLE_STATE_REQUIRES_OPERATOR",
                    })
                    continue

                result = self._execute_claimed(
                    cycle_key, bundle_path, now_ms=now_ms
                )
                recovered.append(result)
            except Exception:
                recovered.append({
                    "cycleKey": cycle_key, "status": "BLOCKED",
                    "reason": "RECOVERY_VALIDATION_FAILED",
                })
        return recovered

    def acquire_process_lock(self):
        """Acquire exclusive OS ownership for this runner-state directory."""
        if self._lock_fd is not None:
            return True
        self.bundle_store_dir.mkdir(parents=True, exist_ok=True)
        lock_path = self.bundle_store_dir / "continuous-runner.lock"
        flags = os.O_CREAT | os.O_RDWR
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(lock_path, flags, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(fd)
            return False
        except Exception:
            os.close(fd)
            raise
        os.ftruncate(fd, 0)
        os.write(fd, f"{os.getpid()}\\n".encode("ascii"))
        os.fsync(fd)
        self._lock_fd = fd
        return True

    def release_process_lock(self):
        fd = self._lock_fd
        if fd is None:
            return
        self._lock_fd = None
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)

    def request_stop(self):
        self._stop_requested = True

    def run_forever(
        self,
        *,
        bundle_provider,
        wall_clock_ms,
        monotonic,
        sleep,
        stop_requested,
        max_sleep_seconds=1.0,
    ):
        """Explicitly invoked scheduler loop; never started by import or deployment."""
        if not self.acquire_process_lock():
            return "BLOCKED"
        try:
            now_ms = wall_clock_ms()
            self._assert_config_digest()
            self.preflight_fn(self.config_path, now_ms=now_ms)
            recovery = self.recover_incomplete(now_ms=now_ms)
            if any(item.get("status") == "BLOCKED" for item in recovery):
                return "BLOCKED"
            while not self._stop_requested and not stop_requested():
                now_ms = wall_clock_ms()
                deadline = next_m15_deadline_ms(
                    now_ms, settlement_ms=self.settlement_ms
                )
                completed = wait_until_deadline(
                    deadline_ms=deadline,
                    wall_now_ms=now_ms,
                    monotonic=monotonic,
                    sleep=sleep,
                    stop_requested=lambda: self._stop_requested or stop_requested(),
                    max_sleep_seconds=max_sleep_seconds,
                )
                if not completed or self._stop_requested or stop_requested():
                    return "STOPPED"
                candle_open = latest_eligible_m15_open_ms(
                    wall_clock_ms(), settlement_ms=self.settlement_ms
                )
                try:
                    bundle_path = bundle_provider(candle_open)
                except Exception:
                    return "BLOCKED"
                if bundle_path is not None:
                    try:
                        self.process_bundle(bundle_path, now_ms=wall_clock_ms())
                    except (ContinuousInputError, CycleNotReady):
                        return "BLOCKED"
            return "STOPPED"
        finally:
            self.release_process_lock()
