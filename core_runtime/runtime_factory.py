"""Fail-closed construction of the explicitly invoked Continuous Core runtime."""

from dataclasses import dataclass
import os
import re
import time

from core_runtime.continuous_dry_run import (
    ContinuousDryRunError,
    inspect_continuous_dry_run,
)
from core_runtime.continuous_journal import ContinuousJournal
from core_runtime.continuous_runner import ContinuousCoreRunner
from core_runtime.orderbook_http import (
    OrderBookHttpClient,
    OrderBookHttpConfig,
    OrderBookHttpError,
)
from core_runtime.paper_ledger_preflight import (
    PaperLedgerPreflightError,
    inspect_paper_ledger_preflight,
)
from core_runtime.preflight import _load_config
from core_runtime.bundle_provider import CoreBundleProvider, BundleProviderError
from freqai_bridge.http_candles import (
    CandleHttpClient,
    CandleHttpConfig,
    CandleHttpError,
)


class RuntimeFactoryError(RuntimeError):
    """Stable, credential-safe failure while constructing Continuous Core."""


@dataclass(frozen=True)
class ContinuousRuntime:
    """The paired provider and runner; construction does not start the loop."""

    runner: ContinuousCoreRunner
    bundle_provider: CoreBundleProvider


_REQUIRED_ENDPOINT_ENV = (
    "T0_CANDLE_API_BASE_URL",
    "T0_CANDLE_API_TOKEN",
    "T0_CANDLE_MAX_LAG_MS",
    "T1_ORDERBOOK_API_BASE_URL",
    "T1_ORDERBOOK_API_TOKEN",
)
_SOURCE_SHA = re.compile(r"[0-9a-f]{40}\\Z")


def _required(env, key):
    value = env.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeFactoryError("RUNTIME_ENDPOINT_CONFIG_REQUIRED:" + key)
    return value.strip()


def build_continuous_runtime(
    *,
    config_path,
    journal_path,
    bundle_store_dir,
    source_sha,
    environ=None,
    clock_ms=None,
):
    """Validate all gates, then construct a PAPER-only provider/runner pair.

    The function performs read-only static/path and PAPER Ledger preflight
    checks before creating the durable Continuous Journal. It never invokes
    the provider, One-shot Runner, or Continuous Runner loop.
    """
    env = os.environ if environ is None else environ
    clock = clock_ms if clock_ms is not None else lambda: time.time_ns() // 1_000_000

    if not isinstance(source_sha, str) or not _SOURCE_SHA.fullmatch(source_sha):
        raise RuntimeFactoryError("SOURCE_SHA_INVALID")
    if not callable(clock):
        raise RuntimeFactoryError("CLOCK_INVALID")

    try:
        static = inspect_continuous_dry_run(
            config_path,
            journal_path=journal_path,
            bundle_store_dir=bundle_store_dir,
            environ=env,
        )
        now_ms = clock()
        if type(now_ms) is not int or now_ms < 0:
            raise RuntimeFactoryError("CLOCK_INVALID")
        inspect_paper_ledger_preflight(
            config_path, now_ms=now_ms, environ=env
        )

        endpoint = {key: _required(env, key) for key in _REQUIRED_ENDPOINT_ENV}
        try:
            max_lag_ms = int(endpoint["T0_CANDLE_MAX_LAG_MS"], 10)
        except (TypeError, ValueError):
            raise RuntimeFactoryError("T0_MAX_LAG_CONFIG_INVALID") from None
        if str(max_lag_ms) != endpoint["T0_CANDLE_MAX_LAG_MS"]:
            raise RuntimeFactoryError("T0_MAX_LAG_CONFIG_INVALID")

        candle_client = CandleHttpClient(CandleHttpConfig(
            base_url=endpoint["T0_CANDLE_API_BASE_URL"],
            token=endpoint["T0_CANDLE_API_TOKEN"],
            max_lag_ms=max_lag_ms,
        ))
        orderbook_client = OrderBookHttpClient(OrderBookHttpConfig(
            base_url=endpoint["T1_ORDERBOOK_API_BASE_URL"],
            token=endpoint["T1_ORDERBOOK_API_TOKEN"],
        ))

        config, _ = _load_config(config_path)
        journal = ContinuousJournal(journal_path)
        bundle_provider = CoreBundleProvider(
            candle_client=candle_client,
            orderbook_client=orderbook_client,
            config_path=config_path,
            bundle_store_dir=bundle_store_dir,
            clock_ms=clock,
            settlement_ms=0,
            environ=env,
        )
        runner = ContinuousCoreRunner(
            config_path=config_path,
            journal=journal,
            bundle_store_dir=bundle_store_dir,
            source_sha=source_sha,
            config_sha256=static["configSha256"],
            settlement_ms=0,
            max_book_age_ms=config["max_book_age_ms"],
        )
        return ContinuousRuntime(
            runner=runner,
            bundle_provider=bundle_provider,
        )
    except RuntimeFactoryError:
        raise
    except (ContinuousDryRunError, PaperLedgerPreflightError) as exc:
        raise RuntimeFactoryError(str(exc) or "RUNTIME_PREFLIGHT_FAILED") from None
    except (CandleHttpError, OrderBookHttpError, BundleProviderError):
        raise RuntimeFactoryError("RUNTIME_ENDPOINT_CONFIG_INVALID") from None
    except Exception:
        raise RuntimeFactoryError("RUNTIME_FACTORY_FAILED") from None
