"""Read-only T0/T1/PAPER orchestration for immutable Core Bundle v1 inputs."""

import hashlib
import os
from pathlib import Path
import tempfile

import rfc8785

from core_runtime.bundle_inputs import build_core_bundle
from core_runtime.continuous_cadence import latest_eligible_m15_open_ms
from core_runtime.paper_ledger_preflight import inspect_paper_ledger_preflight
from core_runtime.ledger_path_guard import validate_ledger_path_isolated
from core_runtime.preflight import _load_config
from paper_execution.ledger import read_account_risk_snapshot, read_snapshot


_M15_MS = 15 * 60 * 1000
_H1_MS = 60 * 60 * 1000
_WINDOW_CANDLES = 100
_SAFE_INTEGER = 9_007_199_254_740_991


class BundleProviderError(RuntimeError):
    """Stable fail-closed error at the Core Bundle Provider boundary."""


class CoreBundleProvider:
    """Fetch validated T0/T1 inputs and read PAPER state without ledger writes.

    The provider stores canonical bundle bytes under their raw SHA-256 digest.
    The Continuous Runner can consume the returned path and independently
    persist/verify the same immutable object in its own bundle store.
    """

    def __init__(
        self,
        *,
        candle_client,
        orderbook_client,
        config_path,
        bundle_store_dir,
        clock_ms,
        settlement_ms,
        environ=None,
        preflight_fn=None,
        risk_reader=None,
        paper_reader=None,
        bundle_builder=None,
    ):
        if not callable(getattr(candle_client, "fetch_one_page", None)):
            raise BundleProviderError("T0_CLIENT_INVALID")
        if not callable(getattr(orderbook_client, "fetch", None)):
            raise BundleProviderError("T1_CLIENT_INVALID")
        if not callable(clock_ms):
            raise BundleProviderError("CLOCK_INVALID")
        if type(settlement_ms) is not int or settlement_ms < 0:
            raise BundleProviderError("SETTLEMENT_INVALID")
        raw_store = Path(bundle_store_dir).expanduser()
        if raw_store.exists() and raw_store.is_symlink():
            raise BundleProviderError("BUNDLE_STORE_SYMLINK")
        self.bundle_store_dir = raw_store.resolve()
        self.config_path = Path(config_path).expanduser().resolve()
        self.candle_client = candle_client
        self.orderbook_client = orderbook_client
        self.clock_ms = clock_ms
        self.settlement_ms = settlement_ms
        self.environ = os.environ if environ is None else environ
        self.preflight_fn = (
            inspect_paper_ledger_preflight if preflight_fn is None else preflight_fn
        )
        self.risk_reader = (
            read_account_risk_snapshot if risk_reader is None else risk_reader
        )
        self.paper_reader = read_snapshot if paper_reader is None else paper_reader
        self.bundle_builder = (
            build_core_bundle if bundle_builder is None else bundle_builder
        )

    @staticmethod
    def _timestamp(value, code):
        if (type(value) is not int or value < 0
                or value > _SAFE_INTEGER):
            raise BundleProviderError(code)
        return value

    @staticmethod
    def _paper_state(snapshot):
        if not isinstance(snapshot, dict):
            raise BundleProviderError("PAPER_STATE_INVALID")
        strategy = snapshot.get("strategyState")
        if not isinstance(strategy, dict):
            raise BundleProviderError("PAPER_STATE_INVALID")
        if strategy.get("strategyId") != "STRATEGY_CORE":
            raise BundleProviderError("PAPER_STRATEGY_SCOPE_INVALID")
        owner = strategy.get("owner")
        if owner not in (None, "STRATEGY_CORE"):
            raise BundleProviderError("PAPER_STRATEGY_OWNER_INVALID")
        if type(strategy.get("dcaUsed")) is not bool:
            raise BundleProviderError("PAPER_DCA_STATE_INVALID")
        position = snapshot.get("positionBase")
        average = snapshot.get("averageEntryPrice")
        if not isinstance(position, str) or not isinstance(average, str):
            raise BundleProviderError("PAPER_POSITION_STATE_INVALID")
        return {
            "positionBase": position,
            "averageEntryPrice": average,
            "strategyState": {
                "owner": owner,
                "dcaUsed": strategy["dcaUsed"],
                "strategyId": "STRATEGY_CORE",
            },
        }

    @staticmethod
    def _assert_risk_ready(risk):
        if (not isinstance(risk, dict)
                or risk.get("mode") != "PAPER"
                or risk.get("liveTradingSupported") is not False
                or risk.get("available") is not True
                or risk.get("riskReady") is not True):
            raise BundleProviderError("PAPER_RISK_NOT_READY")
        latch = risk.get("killSwitch")
        if (not isinstance(latch, dict)
                or latch.get("killed") is not False
                or latch.get("paused") is not False):
            raise BundleProviderError("PAPER_KILL_SWITCH_NOT_CLEAR")

    def _persist_immutable(self, bundle):
        try:
            raw = rfc8785.dumps(bundle)
        except (TypeError, ValueError, OverflowError):
            raise BundleProviderError("BUNDLE_CANONICALIZATION_FAILED") from None
        digest = hashlib.sha256(raw).hexdigest()
        try:
            self.bundle_store_dir.mkdir(parents=True, exist_ok=True)
            if self.bundle_store_dir.is_symlink() or not self.bundle_store_dir.is_dir():
                raise BundleProviderError("BUNDLE_STORE_INVALID")
            target = self.bundle_store_dir / (digest + ".json")
            if target.is_symlink():
                raise BundleProviderError("BUNDLE_STORE_CONFLICT")
            if target.exists():
                if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                    raise BundleProviderError("BUNDLE_STORE_DIGEST_MISMATCH")
                return target

            fd, temporary = tempfile.mkstemp(
                prefix=".core-bundle-", suffix=".tmp", dir=self.bundle_store_dir
            )
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                try:
                    os.link(temporary, target)
                except FileExistsError:
                    if (target.is_symlink() or not target.is_file()
                            or hashlib.sha256(target.read_bytes()).hexdigest() != digest):
                        raise BundleProviderError("BUNDLE_STORE_CONFLICT")
                return target
            finally:
                try:
                    os.unlink(temporary)
                except FileNotFoundError:
                    pass
        except BundleProviderError:
            raise
        except OSError:
            raise BundleProviderError("BUNDLE_STORE_WRITE_FAILED") from None

    def __call__(self, candle_open_ms):
        candle_open_ms = self._timestamp(
            candle_open_ms, "M15_CANDLE_OPEN_INVALID"
        )
        if candle_open_ms % _M15_MS:
            raise BundleProviderError("M15_CANDLE_OPEN_UNALIGNED")
        decision_at_ms = self._timestamp(
            self.clock_ms(), "DECISION_TIMESTAMP_INVALID"
        )
        try:
            latest = latest_eligible_m15_open_ms(
                decision_at_ms, settlement_ms=self.settlement_ms
            )
        except ValueError:
            raise BundleProviderError("M15_CANDLE_NOT_ELIGIBLE") from None
        if candle_open_ms != latest:
            raise BundleProviderError("M15_CANDLE_NOT_LATEST_ELIGIBLE")

        try:
            preflight = self.preflight_fn(
                self.config_path, now_ms=decision_at_ms, environ=self.environ
            )
            preflight_latch = (
                preflight.get("killSwitch")
                if isinstance(preflight, dict) else None
            )
            if (not isinstance(preflight, dict)
                    or preflight.get("status") != "PAPER_LEDGER_READY"
                    or preflight.get("riskReady") is not True
                    or not isinstance(preflight_latch, dict)
                    or preflight_latch.get("killed") is not False
                    or preflight_latch.get("paused") is not False):
                raise BundleProviderError("PAPER_LEDGER_NOT_READY")

            _, ledger_path = _load_config(self.config_path)
            ledger_path = validate_ledger_path_isolated(
                ledger_path, environ=self.environ
            )
            risk = self.risk_reader(ledger_path, now_ms=decision_at_ms)
            self._assert_risk_ready(risk)
            paper = self._paper_state(
                self.paper_reader(ledger_path, strategy_id="STRATEGY_CORE")
            )

            m15_end = candle_open_ms + _M15_MS
            m15_start = m15_end - _WINDOW_CANDLES * _M15_MS
            h1_end = (candle_open_ms // _H1_MS) * _H1_MS
            h1_start = h1_end - _WINDOW_CANDLES * _H1_MS

            m15 = self.candle_client.fetch_one_page(
                m15_start, m15_end, decision_at_ms, timeframe="15m"
            )
            h1 = self.candle_client.fetch_one_page(
                h1_start, h1_end, decision_at_ms, timeframe="1h"
            )
            book = self.orderbook_client.fetch(decision_at_ms=decision_at_ms)
            bundle = self.bundle_builder(
                decision_at_ms=decision_at_ms,
                m15_payload=m15,
                h1_payload=h1,
                orderbook_snapshot=book,
                paper_snapshot=paper,
                account_risk_snapshot=risk,
            )
            return str(self._persist_immutable(bundle))
        except BundleProviderError:
            raise
        except Exception as exc:
            code = str(exc).strip()
            if code and code.isascii() and len(code) <= 120 and all(
                character.isalnum() or character in "_-" for character in code
            ):
                raise BundleProviderError(code) from None
            raise BundleProviderError("CORE_BUNDLE_PROVIDER_FAILED") from None
