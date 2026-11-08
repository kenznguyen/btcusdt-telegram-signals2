# T0 Internal Candle API — Independent Security Review

- Date: 2026-11-08 (Asia/Ho_Chi_Minh)
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Review baseline HEAD: `5c222ffcc79ddfd1a3d99872e78705a03e118486`
- Scope: source and architecture review only; no code changes, tests, workflow runs, network probes, VPS access, secrets, database reads, or runtime changes.
- Verdict: **CONDITIONAL — API SOURCE CONTRACT IS SOUND FOR A LOOPBACK READ SERVICE; DEPLOYMENT MUST REMAIN BLOCKED UNTIL OS-LEVEL READ-ONLY AND WAL LIFECYCLE ARE PROVEN.**

## 1. Sources inspected

| File | Blob SHA | Review scope |
|---|---|---|
| `market_data/api.py` | `81733c9b6de811cbebb2f5d472d41f37f337990c` | WSGI route, auth, validation, response and error handling |
| `market_data/test_api.py` | `970cc303536c9316bd6eadb1c78dd2d5c06a0f7c` | Existing API contract and regression coverage |
| `market_data/store.py` | `4e1b0c54bd56455abe5be0e5c7d0807e63e0bc78` | SQLite read path and connection mode |
| `market_data/storage.py` | `13fe1ae01ebb5318b69e69eef3e512d207f74c49` | Backend selection and side-effect-free store construction |
| `market_data/postgres.py` | `2fe27fe2d066dda0c192a381b72d27404487b800` | PostgreSQL read-only transaction behavior |
| `docs/architecture/T0_CANDLE_API_HTTPS_FRONT_DOOR_DESIGN_2026-11-08.md` | `bd8d0f7dff159494fd954f5f14c7949b74e0c607` | Deployment and hardening proposal |
| `docs/architecture/T0_READ_ONLY_CANDLE_CONTRACT_V1_2026-11-08.md` | `dd19fe6f933a5c8b2a192f7bc65b64a00f205e9d` | Contract ownership and consumer boundary |
| `docs/evidence/t2/T2_LIVE_T0_ENDPOINT_OFFLINE_READINESS_AUDIT_2026-11-08.md` | `51629f6086b8aea4ab606895ec329ecaa435fc91` | Operator-provided VPS evidence and current deployment status |

## 2. Review findings

### F1 — SQLite API query path is application-level read-only: PASS

- `market_data.store.read_window()` resolves the database path and opens SQLite using URI `mode=ro`.
- The query is a parameterized SELECT; no API route invokes schema creation, migration, feeder writes, or write gateway operations.
- `SQLiteCandleStore` construction is side-effect-free. Schema initialization is a separate explicit operation.
- Existing tests cover persisted reads, absent-store fail-closed behavior, and the API contract.

Boundary: this proves the normal API read path is opened read-only. It does not prove the operating-system identity is unable to write the database through another connection or process.

### F2 — OS-level isolation between API and Feeder: BLOCKER / NOT VERIFIED

Operator evidence records:
- Feeder runs as `ubuntu`.
- SQLite database is owned by `ubuntu:ubuntu`, mode `0600`.
- API was previously expected to run as `ubuntu`.

Therefore the API process identity has filesystem-level write authority over the same data directory even though the reviewed API code uses `mode=ro`. A compromised or modified API process running under that identity could bypass the application read path and open a writable connection. The file mode does not isolate the API from the Feeder.

Do not change ownership or permissions blindly. Do not use `immutable=1` for a live database that is concurrently written; that would make assumptions inconsistent with the live WAL lifecycle.

### F3 — SQLite WAL read-only compatibility: NOT VERIFIED

SQLite's official WAL documentation states that a read-only WAL database can be read when the `-wal` and `-shm` files already exist and are readable, when the directory permits creating them, or when immutable mode is used. The API's URI read-only mode therefore needs an explicit test against the actual concurrent Feeder/WAL lifecycle.

Official reference: https://www.sqlite.org/wal.html

Required proof on a disposable database copy:
1. Keep a writer connection open and actively commit representative candle writes so WAL and SHM files exist.
2. Start a read-only API process in a filesystem sandbox that denies writes to the complete data directory.
3. Verify API reads return a consistent snapshot while the writer continues to commit.
4. Verify API startup/restart behavior when the writer is stopped and WAL/SHM files are absent.
5. Verify a write attempt from the API process context is denied and that the canonical logical dataset is unchanged.
6. Verify Feeder writes and checkpointing continue normally after the API reader closes.

No test in this review was run. The current test suite does not prove this systemd/filesystem-sandbox plus concurrent-WAL scenario.

### F4 — PostgreSQL read-only transaction: SOURCE PASS; deployed role NOT VERIFIED

The PostgreSQL read adapter requests a repeatable-read, read-only transaction and applies statement and lock timeouts. This is a good application-level control.

It does not prove the deployed PostgreSQL login role has only SELECT privileges. If PostgreSQL is selected later, verify grants/ownership independently. No role, ACL, schema, or database change is authorized by this review.

### F5 — Authentication and route controls: SOURCE PASS

- Candle route requires configured `MARKET_DATA_TOKEN`.
- Authorization uses `hmac.compare_digest`.
- Missing server token fails closed with 503; invalid or missing Authorization returns 401 once the server token is configured.
- Only GET is accepted; other methods return 405 with `Allow: GET`.
- Token is not accepted as a query parameter.
- The `/health` route is intentionally unauthenticated and returns only minimal liveness information. It must remain loopback-only and must not be proxied publicly.
- No token value was accessed or tested.

Token entropy, provisioning, rotation, and secret-file/environment permissions are not verified.

### F6 — Request and response bounds: SOURCE PASS WITH DEPLOYMENT CONTROLS PENDING

- Query string length is capped at 2,048 characters.
- Parser caps the number of query fields at five and rejects duplicates/unknown fields.
- Only BTCUSDT and supported timeframes are accepted.
- Time values are bounded, nonnegative integers and timeframe-aligned.
- Requested window is capped at 2,000 candles.
- Responses set `Cache-Control: no-store`.
- The reviewed design proposes one Gunicorn worker, four threads, and a 20-second timeout.

No application-level rate limiter is present. For the intended same-host loopback consumer, this is not by itself a deployment blocker if the caller is trusted, the bearer token is protected, request bounds remain enforced, and the service is resource-limited. Do not expose this API publicly on the basis of these controls alone. Pin and review Gunicorn request-header limits, worker/thread count, timeout, graceful shutdown, and service resource controls before deployment.

### F7 — Development server versus production server: REQUIRED DEPLOYMENT GUARD

The module's `__main__` block uses Python's `wsgiref.simple_server`. This is a development entrypoint, not the intended production process.

Production must use the reviewed Gunicorn WSGI entrypoint bound only to `127.0.0.1:8788`. Do not run `python -m market_data.api` as the deployed service. Do not open TCP/8788 on UFW or the cloud firewall.

## 3. Recommended internal deployment shape

For same-VPS T2 consumption:

```text
T2 process
   |
   | HTTP to 127.0.0.1:8788 + Bearer token
   v
Gunicorn (loopback only)
   |
   v
T0 Candle API (GET /v1/candles)
   |
   | SQLite URI mode=ro
   v
T0 SQLite WAL store  <---- T0 Feeder writer
```

No Nginx, Caddy, domain, TLS certificate, public port, or external gateway is required for this same-host loopback phase. The T2 client may use loopback HTTP only; its HTTPS requirement for non-loopback hosts must remain unchanged.

### Candidate OS sandbox — test before adoption

A systemd service sandbox using `ProtectSystem=strict`, `NoNewPrivileges=true`, and a read-only mount for the T0 data directory (for example, `ReadOnlyPaths=/home/ubuntu/t0/app/.data`) may provide process-level write denial without changing the current `0600` ownership model.

This is only a candidate, not an approved configuration. It must pass F3's WAL tests first. In particular, prove that the API can read the live WAL/SHM files without needing to create or modify them, and that restart behavior is understood when the writer is absent. systemd documents that `ReadOnlyPaths=` denies writes inside the service namespace even when ordinary file permissions would otherwise allow them: https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html

If the sandbox cannot support the required WAL lifecycle, keep deployment blocked and evaluate a separately approved storage isolation change or PostgreSQL read-only role. Do not weaken the sandbox or widen file permissions merely to make startup succeed.

## 4. Required test plan before deployment approval

| Test | Required result | Current status |
|---|---|---|
| API contract regression | Existing API tests pass on exact source SHA | NOT RUN in this review |
| SQLite `mode=ro` write rejection | INSERT/UPDATE/DDL through read-only connection fail | NOT VERIFIED as a dedicated assertion |
| WAL concurrent writer + sandboxed reader | API reads while Feeder-equivalent writer commits | NOT RUN |
| API process filesystem write denial | Writes to DB, WAL, SHM and data directory are denied in service namespace | NOT RUN |
| WAL restart with writer absent | Defined fail-closed behavior; no implicit file creation or repair | NOT RUN |
| Feeder regression | Writer/checkpoint continues with API reader present | NOT RUN |
| Gunicorn listener | Exactly loopback `127.0.0.1:8788` | NOT RUN |
| External port exposure | 8788 not allowed by host/cloud firewall | Existing operator snapshot only; refresh required before deployment |
| Auth matrix | Missing/invalid/valid token behavior matches contract | Existing source tests partial; no live probe |
| Resource limits | Header, timeout, concurrency and memory bounds reviewed | NOT VERIFIED |

Tests must run in GitHub Actions against a disposable test database. Do not use the canonical VPS database as a test fixture. Record exact checked-out SHA, workflow run, job conclusions and artifact metadata. Do not rerun historical PASS suites without a specific gap and authorization.

## 5. Decision and status

| Area | Verdict |
|---|---|
| API contract and route implementation | PASS — source review |
| Bearer authentication implementation | PASS — source review |
| Input bounds and no-store response | PASS — source review |
| SQLite query connection read-only | PASS — source review |
| OS-level API/Feeder write isolation | BLOCKED / NOT VERIFIED |
| SQLite WAL + read-only sandbox compatibility | NOT VERIFIED |
| PostgreSQL read-only transaction | PASS — source only |
| Deployed PostgreSQL grants | NOT VERIFIED |
| Production Gunicorn service | NOT DEPLOYED |
| Loopback listener / live API | NOT RUN |
| T2 runtime integration | NOT ACTIVATED |

**Overall: CONDITIONAL — source is suitable for an internal read API, but deployment is blocked by missing OS-level write-isolation and WAL lifecycle evidence.**

## 6. Scope boundaries and next step

No source code, tests, workflows, VPS, systemd, Gunicorn, Feeder, SQLite database, environment, token, firewall, network, DNS, proxy, or T2 runtime was changed or accessed. No tests or workflows were run.

Next permitted increment: add focused regression tests on a disposable SQLite WAL database for read-only write rejection and concurrent writer/read-only reader behavior; then test the proposed systemd sandbox in CI or an isolated disposable Linux environment. Only after those tests pass should a separate deployment approval be requested.

Keep the Feeder running state and current database permissions unchanged. Do not start the API, restart the Feeder, install packages, alter service definitions, expose ports, create secrets, or activate T2. Keep `ai_execution_enabled=false`.
