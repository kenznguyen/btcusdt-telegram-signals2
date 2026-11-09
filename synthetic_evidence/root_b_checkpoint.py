"""Synthetic-only Root B observer ACK and checkpoint crash-window model.

This in-memory reference harness is not a durable store, broker, runtime adapter,
or production recovery implementation.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal


class RootBIntegrityError(ValueError):
    """An event, observer acknowledgement, or checkpoint violates its contract."""


class SimulatedCrash(RuntimeError):
    """A deterministic crash injected at a named checkpoint boundary."""


CrashPoint = Literal["before_durable_write", "after_durable_write", "after_ack"]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


@dataclass(frozen=True)
class _Checkpoint:
    checkpoint_id: str
    through_sequence: int
    event_log_sha256: str
    acknowledgement_sha256: str
    checkpoint_sha256: str


class RootBJournal:
    """A deterministic in-memory model for Root B ACK and checkpoint semantics."""

    def __init__(self, *, required_observers: set[str]):
        if not required_observers or any(not isinstance(item, str) or not item for item in required_observers):
            raise ValueError("required_observers must contain non-empty observer IDs")
        self._required_observers = frozenset(required_observers)
        self._events: list[tuple[str, bytes]] = []
        self._event_sequences: dict[str, int] = {}
        self._acks: dict[str, dict[str, str]] = {}
        self._checkpoints: dict[str, _Checkpoint] = {}
        self._checkpoint_acks: set[str] = set()

    def append_event(self, event_id: str, canonical_event_bytes: bytes) -> str:
        if not isinstance(event_id, str) or not event_id:
            raise RootBIntegrityError("event_id must be a non-empty string")
        if not isinstance(canonical_event_bytes, bytes) or not canonical_event_bytes:
            raise RootBIntegrityError("event bytes must be non-empty bytes")
        existing_sequence = self._event_sequences.get(event_id)
        if existing_sequence is not None:
            existing = self._events[existing_sequence - 1][1]
            if existing != canonical_event_bytes:
                raise RootBIntegrityError("same event ID appended with changed bytes")
            return "EVENT_DUPLICATE"
        self._events.append((event_id, canonical_event_bytes))
        self._event_sequences[event_id] = len(self._events)
        self._acks[event_id] = {}
        return "EVENT_APPENDED"

    def event_digest(self, event_id: str) -> str:
        sequence = self._event_sequences.get(event_id)
        if sequence is None:
            raise RootBIntegrityError("acknowledgement references unknown event")
        return _sha256(self._events[sequence - 1][1])

    def acknowledge(self, event_id: str, observer_id: str, event_digest: str) -> str:
        if event_id not in self._event_sequences:
            raise RootBIntegrityError("acknowledgement references unknown event")
        if observer_id not in self._required_observers:
            raise RootBIntegrityError("acknowledgement references unknown observer")
        expected_digest = self.event_digest(event_id)
        if event_digest != expected_digest:
            raise RootBIntegrityError("observer acknowledgement digest does not match event")
        observer_acks = self._acks[event_id]
        previous = observer_acks.get(observer_id)
        if previous is not None:
            if previous != event_digest:
                raise RootBIntegrityError("duplicate observer ACK changed digest")
            return "ACK_DUPLICATE"
        observer_acks[observer_id] = event_digest
        return "ACK_RECORDED"

    def ack_count(self, event_id: str) -> int:
        if event_id not in self._acks:
            raise RootBIntegrityError("unknown event")
        return len(self._acks[event_id])

    def all_observers_acked(self, event_id: str) -> bool:
        if event_id not in self._acks:
            raise RootBIntegrityError("unknown event")
        return set(self._acks[event_id]) == self._required_observers

    def _event_log_digest(self, through_sequence: int) -> str:
        rows = [
            {"sequence": sequence, "event_id": event_id, "event_sha256": _sha256(event_bytes)}
            for sequence, (event_id, event_bytes) in enumerate(self._events[:through_sequence], 1)
        ]
        return _sha256(_canonical(rows))

    def _acknowledgement_digest(self, through_sequence: int) -> str:
        rows = []
        for sequence, (event_id, _event_bytes) in enumerate(self._events[:through_sequence], 1):
            acknowledgements = self._acks[event_id]
            if set(acknowledgements) != self._required_observers:
                raise RootBIntegrityError("checkpoint includes an event without all required observer ACKs")
            rows.append({
                "sequence": sequence,
                "event_id": event_id,
                "observers": [
                    {"observer_id": observer, "event_sha256": acknowledgements[observer]}
                    for observer in sorted(self._required_observers)
                ],
            })
        return _sha256(_canonical(rows))

    @staticmethod
    def _checkpoint_digest(checkpoint_id: str, through_sequence: int,
                            event_log_sha256: str, acknowledgement_sha256: str) -> str:
        return _sha256(_canonical({
            "checkpoint_id": checkpoint_id,
            "through_sequence": through_sequence,
            "event_log_sha256": event_log_sha256,
            "acknowledgement_sha256": acknowledgement_sha256,
        }))

    def commit_checkpoint(self, checkpoint_id: str, *, through_sequence: int,
                          crash_at: CrashPoint | None = None) -> str:
        if not isinstance(checkpoint_id, str) or not checkpoint_id:
            raise RootBIntegrityError("checkpoint_id must be a non-empty string")
        if not isinstance(through_sequence, int) or isinstance(through_sequence, bool):
            raise RootBIntegrityError("checkpoint sequence must be an integer")
        if not 1 <= through_sequence <= len(self._events):
            raise RootBIntegrityError("checkpoint sequence is outside the committed event log")
        if crash_at not in (None, "before_durable_write", "after_durable_write", "after_ack"):
            raise RootBIntegrityError("unknown crash injection point")

        event_digest = self._event_log_digest(through_sequence)
        ack_digest = self._acknowledgement_digest(through_sequence)
        checkpoint_digest = self._checkpoint_digest(
            checkpoint_id, through_sequence, event_digest, ack_digest
        )
        candidate = _Checkpoint(
            checkpoint_id, through_sequence, event_digest, ack_digest, checkpoint_digest
        )

        existing = self._checkpoints.get(checkpoint_id)
        if existing is not None:
            if existing != candidate:
                raise RootBIntegrityError("checkpoint ID reused with different contents")
            if checkpoint_id in self._checkpoint_acks:
                return "CHECKPOINT_ALREADY_COMMITTED"
            self._checkpoint_acks.add(checkpoint_id)
            if crash_at == "after_ack":
                raise SimulatedCrash("crash after checkpoint acknowledgement")
            return "CHECKPOINT_ACK_REPLAYED"

        if crash_at == "before_durable_write":
            raise SimulatedCrash("crash before durable checkpoint write")

        self._checkpoints[checkpoint_id] = candidate
        if crash_at == "after_durable_write":
            raise SimulatedCrash("crash after durable write and before acknowledgement")

        self._checkpoint_acks.add(checkpoint_id)
        if crash_at == "after_ack":
            raise SimulatedCrash("crash after checkpoint acknowledgement")
        return "CHECKPOINT_COMMITTED"

    def checkpoint_is_valid(self, checkpoint: dict[str, object]) -> bool:
        checkpoint_id = checkpoint.get("checkpoint_id")
        stored = self._checkpoints.get(checkpoint_id) if isinstance(checkpoint_id, str) else None
        if stored is None:
            return False
        try:
            sequence = int(checkpoint["through_sequence"])
        except (KeyError, TypeError, ValueError):
            return False
        if sequence != stored.through_sequence or not 1 <= sequence <= len(self._events):
            return False
        try:
            event_digest = self._event_log_digest(sequence)
            ack_digest = self._acknowledgement_digest(sequence)
        except RootBIntegrityError:
            return False
        expected_digest = self._checkpoint_digest(
            stored.checkpoint_id, sequence, event_digest, ack_digest
        )
        return (
            stored.event_log_sha256 == event_digest
            and stored.acknowledgement_sha256 == ack_digest
            and stored.checkpoint_sha256 == expected_digest
            and checkpoint.get("checkpoint_sha256") == expected_digest
        )

    def recover_checkpoint(self) -> dict[str, object] | None:
        if not self._checkpoints:
            return None
        candidates = sorted(
            self._checkpoints.values(),
            key=lambda item: (item.through_sequence, item.checkpoint_id),
        )
        for checkpoint in candidates:
            public = {
                "checkpoint_id": checkpoint.checkpoint_id,
                "through_sequence": checkpoint.through_sequence,
                "event_log_sha256": checkpoint.event_log_sha256,
                "acknowledgement_sha256": checkpoint.acknowledgement_sha256,
                "checkpoint_sha256": checkpoint.checkpoint_sha256,
            }
            if not self.checkpoint_is_valid(public):
                raise RootBIntegrityError("stored checkpoint failed recovery integrity verification")
        latest = candidates[-1]
        return {
            "checkpoint_id": latest.checkpoint_id,
            "through_sequence": latest.through_sequence,
            "event_log_sha256": latest.event_log_sha256,
            "acknowledgement_sha256": latest.acknowledgement_sha256,
            "checkpoint_sha256": latest.checkpoint_sha256,
        }

    def checkpoint_ack_count(self, checkpoint_id: str) -> int:
        return int(checkpoint_id in self._checkpoint_acks)

    def corrupt_event_for_test(self, event_id: str, replacement_bytes: bytes) -> None:
        """Test-only corruption hook; never exposed to a runtime integration."""
        sequence = self._event_sequences.get(event_id)
        if sequence is None:
            raise RootBIntegrityError("cannot corrupt an unknown event")
        self._events[sequence - 1] = (event_id, replacement_bytes)
