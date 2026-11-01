# T0 Operational Contract & Release Gate

## Purpose

This branch adds a static, SHA-bound release gate for the T0 feeder. It checks
that Codemagic still registers the previously accepted T0 test inventory and
that the canonical feeder source still expresses the agreed market, storage,
and fencing invariants.

This is a configuration/source audit. It is not a feeder runtime smoke test,
a production deployment, or a new execution of the historical T0 suites.

## Branch and base

- Branch: `feature/t0-operational-contract-release-gate-20261102`
- Base: `7a717c0bbcd621545f9c0fe27407d3f020f961d9`
- Merge: not authorized; this branch remains unmerged.

## Preserved evidence

| Contract area | Historical evidence | Release-gate treatment |
|---|---|---|
| Six original P1 GREEN groups | Previously supplied Codemagic evidence; preserved in the lifecycle regression suite | Verify module registration only |
| Runtime Integration | 85/85 at `8b196d2720eab804728df7c0227c606c094b16ad` | Verify module registration only |
| Atomic Fencing hardening | 99 tests at `5022acad52b9c3d237b3ab24c996080d4f8dcbae` | Verify workflow inventory and count assertion only |
| SIGKILL Recovery | 100 tests at `5aa15019cf5767d944aba0ef5bdb33924db7d4de` | Verify workflow inventory and count assertion only; do not execute |
| Health Runtime–API Integration | 106 tests at `7a717c0bbcd621545f9c0fe27407d3f020f961d9` | Verify workflow inventory and count assertion only |

The historical GREEN results remain tied to their original source SHAs. A
static audit on this branch does not recreate or upgrade those test results.

## Operational invariants checked from source

1. Production feeder selects Binance USD-M through CCXT `binanceusdm`.
2. Canonical market identity is Binance / USDT perpetual / BTCUSDT.
3. Only closed candles are eligible for ingestion.
4. Production feeder rejects non-SQLite storage.
5. The lease database and canonical candle database must resolve to the same
   file for the atomic fencing transaction.
6. Recovery and scheduler writes use the canonical sync callback and
   `insert_fenced` path.
7. Codemagic T0 workflows publish `ci-source-sha.txt` and register the
   historical test modules and expected count assertions.

OKX/Bybit remain shadow sources only; this gate does not introduce fallback,
data mixing, or a second canonical writer.

## Codemagic execution boundary

The new `t0-operational-contract-release-gate` workflow runs only:

- `ci.test_t0_operational_contract`
- `ci/t0_operational_contract.py`

It does not start `market_data.feeder_service`, call an exchange, modify SQLite
data, or execute any `market_data.test_feeder_*` suite. In particular, it
does not rerun SIGKILL Recovery.

The existing historical T0 workflows are not retargeted to this branch. Their
configuration is inspected as data by the static audit.

## Explicitly not certified

- Controlled Runtime Health Smoke remains paused and is not performed here.
- Continuous production runtime operation is not established.
- T1-T4 read-only enforcement is outside this T0-only gate and is not certified
  by this report.
- A static source check does not prove exchange connectivity, real-time candle
  freshness, or production availability.
- No merge or release approval is implied by a passing static gate.

## Result artifacts

Codemagic should publish:

- `ci-source-sha.txt`
- `t0-operational-contract-tests.log`
- `t0-operational-contract-audit.log`
- `t0-operational-contract-report.json`
- `t0-operational-contract-report.md`

A Release Gate PASS is valid only when the artifact SHA equals the branch commit
that Codemagic actually built.
