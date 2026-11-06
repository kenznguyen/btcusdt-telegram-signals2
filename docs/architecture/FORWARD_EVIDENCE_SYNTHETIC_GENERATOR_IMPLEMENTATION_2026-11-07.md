# Forward Evidence Synthetic Generator Implementation (P1.8)

Date: 2026-11-07  
Scope: standalone deterministic synthetic fixture generator and local-only test harness.  
Status: **LOCAL TESTS PASS; GITHUB ACTIONS EXACT-HEAD RESULT PENDING/NOT VERIFIED.**

## 1. Approved boundary

Implemented only under `synthetic_evidence/` with a dedicated GitHub Actions workflow. The package uses Python standard library only.

Explicitly excluded and not accessed:
- T0/T1 or account databases, account history, persistent ledgers, external artifacts or VPS.
- Exchange endpoints, API credentials, paper execution, order generation or live execution.
- Cloud providers, buckets, credentials, purchases, provisioning, persistent capture or storage retention.
- T0/T1 production source, schema, database migrations, runtime configuration or risk policy.
- Production signing keys or private-key persistence.

`ai_execution_enabled=false` remains unchanged. Local replay is only `LOCAL_REPLAY_SIMULATION`, not independent Root B evidence.

## 2. Implemented package

| File | Purpose |
|---|---|
| `synthetic_evidence/generator.py` | Deterministic PRF, strict canonical JSON subset, fixture/scenario generation, hashes, segments, manifests, measurements, local replay and safe output writer |
| `synthetic_evidence/__main__.py` | CLI entry point |
| `synthetic_evidence/test_generator.py` | Isolated `unittest` contracts |
| `synthetic_evidence/README.md` | Local invocation and limitations |
| `.github/workflows/p1-8-synthetic-evidence.yml` | Synthetic-only GitHub Actions acceptance workflow |

No package installation or external dependency is required.

### Deterministic data contract

- Fixed 32-byte seed; exact P1.7 HMAC-SHA-256 message framing and block counter.
- UUIDv5 event/scenario/intent/order/position/manifest identities using a fixed namespace.
- Restricted synthetic stream names for Core, AI and Legacy.
- Fixed UTC base time and deterministic per-stream sequence/timestamps.
- Exact decimal strings for generated amounts; no floating-point financial values.
- Scenario-driven event sequences for Core/AI and separate Legacy/account-level events.
- SMALL/MEDIAN/LARGE payload cohorts, with clean volume measurements separated from 13 negative-vector catalog entries.
- Event-core hash and manifest-core hash use separate P1.5 domain separators.
- One stream per segment; contiguous sequences; framing bytes included in the segment cap.
- Immutable pre-upload manifest only. No fabricated provider version ID, retention receipt or storage durability claim.
- Existing output directory is rejected; the writer never overwrites prior local fixture output.

### Measurement output

The fixture writes:
- `run_descriptor.json`
- `events.jsonl`
- `segments/*.jsonl`
- `manifests.jsonl`
- `measurements.json`
- `negative_vectors.json`
- `fixture.sha256`

Measurements include event-core size by class/cohort and overall, arithmetic mean, nearest-rank p50/p90/p95/p99, min/max/total, event counts, segment count/bytes and manifest count/bytes. Compression is explicitly `NOT_MEASURED`.

### Replay and negative cases

Local replay checks stream sequence, scenario transition, previous hash, causation chain, nondecreasing commit time, event hash and duplicate event delivery:
- Identical duplicate delivery is idempotently ignored.
- Same event ID with changed bytes is rejected.
- Sequence gaps, wrong predecessor hashes and tampering are rejected.

The 13 negative-vector catalog records expected dispositions for invalid/unknown/revoked signatures, late pre-boundary events, partial-fill cancel/replace, reversal ordering, UNKNOWN fee/funding, stale/missing marks and Root B duplicate-ack/crash cases. The catalog is not equivalent to execution of every fault path: signature validation, late-boundary checkpoint invalidation and observer crash recovery remain NOT IMPLEMENTED/NOT TESTED.

## 3. Canonicalization and cryptographic limits

The implementation labels its canonicalization profile `RFC8785-JCS-STRICT-SUBSET/1`: UTF-8, UTF-16 property ordering, duplicate-key rejection during parsing, safe integers only, and no floating-point values. This is not a claim of complete RFC 8785 conformance. Independent cross-language RFC vectors remain NOT VERIFIED.

SHA-256 event and manifest hashes are implemented and locally checked. Ed25519 signing, verification, key rotation/revocation enforcement and signed storage receipts are NOT IMPLEMENTED. Local manifests are explicitly unsigned. No private/test signing key is generated or persisted.

## 4. Local verification

Executed in a disposable local workspace using Python 3.13:

| Check | Result |
|---|---:|
| Focused `unittest` | 19/19 PASS |
| `py_compile synthetic_evidence/*.py` | PASS |
| PRF fixed known-answer vector | PASS |
| Canonical JSON / duplicate-key / numeric rejection | PASS |
| UUID, sequence, event hash and causation checks | PASS |
| Segment boundary and byte-cap tests | PASS |
| Manifest hash and segment digest checks | PASS |
| Replay duplicate, tamper, gap and wrong-hash tests | PASS |
| 1,000-event generation repeated twice | Byte-identical |
| Fixture SHA-256 manifest verification | All listed files PASS |
| 10,000-event exploratory generation + local replay | PASS |

Exploratory local measurements (single run, not a performance certification):
- 1,000 events: 0.438 s, approximately 2,282 events/s, 12 segments, 2,063,059 event-core bytes.
- 10,000 events: 4.693 s, approximately 2,131 events/s, 102 segments, 20,635,426 event-core bytes.
- These figures are local synthetic measurements only; they are not production throughput, a five-run benchmark, or a cloud/provider cost input until the required environment and repeated samples are captured.

## 5. GitHub Actions workflow

`.github/workflows/p1-8-synthetic-evidence.yml`:
- Runs on pushes to the existing P1 branch when the isolated package/workflow/implementation report changes; also supports manual dispatch.
- Checks out the exact triggering SHA with persisted credentials disabled.
- Uses Python 3.11 and installs no packages.
- Sets DB and exchange credential environment variables to empty; asserts `AI_EXECUTION_ENABLED=false`.
- Compiles the package, runs the focused test module, generates two 1,000-event fixtures, compares their full output trees and verifies the SHA-256 manifest.
- Uploads a synthetic-only artifact with 7-day retention.

Workflow source has been committed. Exact-head workflow run ID, job conclusion and artifact identity must be added after GitHub reports them; until then GitHub Actions status is **NOT VERIFIED**.

## 6. Specification correction discovered during implementation

The P1.6 §3.2 event-class weights add to **94**, not 100 as the original heading claimed. They are therefore treated as relative target weights and normalized by 94 for largest-remainder target counts. The generator reports both normalized target counts and actual scenario-driven counts; it does not force causal scenarios to match the target distribution. P1.6 and the Acceptance Test Plan must retain this correction.

## 7. Remaining NOT VERIFIED / NOT AUTHORIZED

- Full RFC 8785 conformance and independent implementation comparison.
- Ed25519 signatures, key custody, rotation and revocation enforcement.
- Execution of every catalogued negative/fault vector.
- 100,000-event scale, burst, recovery, spool and cold restore profiles.
- Five-run warm-up/measurement matrix and robust p95 throughput.
- Root B independent process/admin/storage proof.
- Provider qualification, provider cost quotes, region/retention selection and cloud restore.
- Persistent capture, T0/T1 runtime integration or any account DB access.

Next bounded step: verify the exact GitHub Actions run and artifact on the resulting source SHA, then update the handoff/evidence inventory. No provider or runtime step is implied.


## 8. P1.8.1 run-descriptor environment completeness

Follow-up hardening:
- Generator source commit: `b55c851a5db3eb698d3ac68b073a825abcf55026`.
- Environment descriptor test commit: `bd558f0041302ef521ea6837e87923c17e3fceaa`.

The run descriptor now records OS, architecture, CPU model/count, sysconf-reported total memory where available, storage medium as `NOT_MEASURED`, and Python/runtime tool versions. It also explicitly records `hash_signature_profile=SHA256_EVENT_AND_MANIFEST_UNSIGNED_LOCAL/1`, so unsigned local hash-only evidence is not confused with signed production evidence.

Re-verification after this change:
- Focused tests: 19/19 PASS.
- Python compile: PASS.
- Two 1,000-event fixtures: byte-identical.
- SHA-256 manifest: all listed files PASS.

The workflow push path filter includes `synthetic_evidence/**`; exact GitHub Actions run metadata for this latest source SHA remains NOT VERIFIED until its run and artifact can be inspected.



## 9. GitHub Actions acceptance evidence — verified 2026-11-07

- Workflow run: [42288889345](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42288889345).
- Job: `128136820125` — `Deterministic local fixture contracts`, conclusion **success**.
- Triggered branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Exact checked-out/source SHA: `90cd3cfe64bcac2f1fb238660e5264431c69d419`; checkout log, `git rev-parse HEAD`, smoke summary and fixture descriptor agree.
- Synthetic-only preflight: PASS; all database and exchange credential environment variables were empty; `AI_EXECUTION_ENABLED=false`.
- Python 3.11 compile: PASS.
- Focused unit tests: **19/19 PASS**.
- Deterministic regeneration: two 1,000-event outputs compared byte-for-byte equal; local replay verified 1,000 events across 3 streams; 12 segments generated.
- SHA-256 manifest: 17/17 entries passed in the workflow. The downloaded artifact was independently rechecked in this review: 17/17 entries match.
- Artifact: `p1-8-synthetic-evidence-90cd3cfe64bcac2f1fb238660e5264431c69d419`; artifact ID `13539350402`; size 298,473 bytes; SHA-256 `7adee2525ab7690d8ce1792eb809b93a6a4b7cf02adb8f234bbc45793fe4dd76`; expires `2026-11-13T20:30:14Z`.
- Artifact contains 24 files, including source SHA, preflight, compile/test logs, smoke summary, fixture events, manifests, measurements, run descriptor, negative-vector catalog and 12 segments.
- The descriptor records `RFC8785-JCS-STRICT-SUBSET/1`, unsigned local hash profile, and storage medium `NOT_MEASURED`. Provider tests are `NOT_RUN`; runtime integration is `NOT_AUTHORIZED`.

**Acceptance status:** GitHub Actions P1.8 synthetic fixture CI = **PASS** for the exact SHA above. This PASS is limited to the isolated synthetic fixture contracts and reproducibility checks. It does not certify full RFC 8785 conformance, signatures/key management, all 13 fault-vector execution paths, 100k/burst/recovery/restore, independent Root B, provider durability, or production performance. T0 remains PAUSED; no persistent capture, provider access, T0/T1 runtime integration, or live execution is authorized; `ai_execution_enabled=false`.

Next bounded step: update the project handoff with this exact run and artifact provenance. Keep remaining cryptographic/canonicalization/fault-path gaps as separate synthetic-only work.


## 10. P1.8.2 — synthetic-only independent integrity vectors

### Approval and scope

User approval: `APPROVE P1.8.2 — SYNTHETIC-ONLY INTEGRITY TESTS`.

Only `synthetic_evidence/test_generator.py` was changed. No generator behavior, production runtime, T0/T1 source, database, exchange, credentials, provider, persistent capture, signing key, or execution policy was changed. The workflow remained the existing GitHub Actions workflow on the existing feature branch.

### Independent vector sources and coverage

- RFC 8785 §3.2.3 property-order example, including UTF-16 ordering across BMP and non-BMP characters: https://www.rfc-editor.org/rfc/rfc8785.html
- RFC 4231 §4.2 HMAC-SHA-256 test case 1: https://www.rfc-editor.org/rfc/rfc4231.html
- SHA-256 known-answer vector for `abc`.
- Independent event-vs-manifest domain-separation expected digests.
- Additional strict-subset tests for string escaping, nested object ordering, array-order preservation, float rejection, invalid UTF-8, duplicate/invalid numeric input, event-hash tampering and stream-sequence reordering.

The initial test-only commit `eeb68bf602d4967d769d47594337fc9f3ec38f7a` failed at Python compilation because of incorrectly escaped test literals. This was a test-source defect, not a generator failure. The literals were corrected in commit `de0602dfb3daa999b06280e2044eecb1d76d45d1`; the corrected exact source was then checked by GitHub Actions.

### Exact GitHub Actions evidence

- Workflow run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42289567234
- Run ID: `42289567234`; run number: 12; event: `push`; conclusion: **success**.
- Job ID: `128139126406`, `Deterministic local fixture contracts`; conclusion: **success**.
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Exact head/checked-out/source SHA: `de0602dfb3daa999b06280e2044eecb1d76d45d1`.
- Synthetic-only preflight: PASS; DB/exchange credential environment variables empty; `AI_EXECUTION_ENABLED=false`.
- Python 3.11 compile: PASS.
- Focused suite: **29/29 PASS** (19 existing + 10 added).
- Two 1,000-event fixtures: byte-identical; replay verified 1,000 events over 3 streams; 12 segments.
- SHA-256 fixture manifest: 17/17 PASS in workflow and independently after artifact download.
- Artifact ID: `13539715524`; name: `p1-8-synthetic-evidence-de0602dfb3daa999b06280e2044eecb1d76d45d1`; size: 298,854 bytes; SHA-256: `4a2678b4e80aae0fc94681e42d8183f0a0a7548713dd5aed388bcca8e96c49c3`; expires: `2026-11-13T20:34:57Z`.
- Downloaded ZIP was independently hashed; its digest matches GitHub artifact metadata. ZIP contains 24 files. All 17 entries in `fixture.sha256` independently verified.

### Acceptance and remaining limits

**P1.8.2 synthetic-only integrity test increment: PASS** for the exact source SHA above.

This proves only the published primitive/canonicalization-subset vectors and listed synthetic replay faults. It does NOT establish full RFC 8785 conformance: the implementation intentionally rejects floating-point JSON values, so RFC 8785 ECMAScript number-serialization Appendix B remains outside the supported subset. No independent second-language implementation was run. The other catalogued negative vectors are not all executable or verified. Ed25519 signing/verification, key lifecycle, signed receipts, Root B, 100k/burst/recovery/restore, provider durability, and performance qualification remain NOT IMPLEMENTED, NOT RUN, or NOT AUTHORIZED as applicable.

T0 remains PAUSED. No database, exchange, provider, persistent capture, runtime integration, or live execution was accessed or enabled. `ai_execution_enabled=false` remains unchanged.

### Next step

Keep the P1.8.2 result recorded and review the next gap separately. Do not enable full RFC 8785 floating-point support, introduce signing/key custody, or begin provider/runtime work without a separate explicit approval.


## 11. P1.8.3 — synthetic-only fault injection harness (implementation in progress)

### Approval and exact scope

User explicitly approved `APPROVE P1.8.3 — SYNTHETIC-ONLY FAULT INJECTION` on 2026-11-07.

The increment is restricted to deterministic, local synthetic reference models and GitHub Actions. It does not import or call T0/T1 runtime code and does not access a database, exchange, provider, VPS, credentials, persistent capture, signing keys, or any execution adapter. `ai_execution_enabled=false` remains required.

### Source changes

- `synthetic_evidence/fault_injection.py`: isolated reference-model contracts for unknown fee/funding, mark freshness, late-event checkpoint invalidation, and accepted/partial/cancel/replace/fill replay.
- `synthetic_evidence/generator.py`: renamed three catalog vector identifiers to the approved executable names `CHECKPOINT_BOUNDARY`, `STALE_MARK`, and `RECOVERY`; retained `UNKNOWN_FEE_FUNDING`.
- `synthetic_evidence/test_generator.py`: added seven unittest cases; total focused suite is now 36 tests (29 prior + 7 new).

### Implemented synthetic contracts

- `UNKNOWN_FEE_FUNDING`: a missing fee or funding amount raises an incomplete-equity error; it is never silently coerced to numeric zero.
- `STALE_MARK`: missing/non-positive marks, stale timestamps, unsafe future timestamps and excessive clock uncertainty are rejected.
- `CHECKPOINT_BOUNDARY`: a late-committed event whose event time is at/before the checkpoint boundary invalidates that checkpoint; events after the boundary do not.
- `RECOVERY`: replay is idempotent for identical duplicate delivery, rejects changed bytes under the same event ID and late fills against inactive/cancelled orders, and models partial fill -> cancel -> replacement -> final fill. The crash/restart test compares replayed state with uninterrupted replay.

These are synthetic reference-model tests, not proof that the T0/T1 production ledger or recovery coordinator implements these semantics.

### Exact source and current verification state

- Test/catalog coverage commit: `16ccd8a3747ce9bf98e795d522d52a5adeca8155`.
- Generator blob SHA: `ba179aebe14aabb177d05f36236a75d0cdfd6d88`.
- Test blob SHA: `fdb3369f916672173b681870c9f310b1872d5982`.
- Fault harness blob SHA: `0af64d3625e88e8e1334182364094b1227faec58`.
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- GitHub Actions run ID, job ID, checked-out SHA confirmation and artifact digest: **NOT VERIFIED** at the time of this update.
- Compile and 36-test execution: **NOT VERIFIED** until GitHub Actions evidence is inspected.

### Status and remaining boundaries

**Implementation: IN PROGRESS. CI acceptance: NOT VERIFIED.** Do not label P1.8.3 PASS until the workflow checks out exact source SHA `16ccd8a3747ce9bf98e795d522d52a5adeca8155`, compilation and all 36 tests pass, and the artifact/provenance are reconciled.

No T0/T1 runtime, database, strategy, provider, VPS, persistent capture, signing/key lifecycle, Root B, or live execution work is included. T0 remains PAUSED and `ai_execution_enabled=false`.


### CI result — workflow run 42291124242 (2026-11-06 UTC)

- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42291124242
- Job ID: `128144496660`, conclusion: **FAILURE**.
- Exact checkout SHA: `311e6810ab5c7388daefb34373e58b1271dcb592` (verified in job log).
- Synthetic-only preflight: PASS; Python compile: PASS.
- Unit suite: 36 tests executed; 35 passed, 1 failed.
- Failure: `test_recovery_after_crash_matches_uninterrupted_partial_fill_cancel_replace` expected `active_order_id == "O2"` after O2 was fully filled. The replay model correctly returned `None` because a terminal FILLED order is no longer active. This is a test expectation defect, not evidence of an unfinished active order.
- Artifact ID `13540216092`, name `p1-8-synthetic-evidence-311e6810ab5c7388daefb34373e58b1271dcb592`, size 2,529 bytes, SHA-256 `07ad0fa8301f16522cc671d7304f7986b0e0c65bdf9974660f5b8c4161a21674`, expires 2026-11-13T20:46:07Z. It contains only the partial test/source/preflight/compile/smoke evidence; reproducibility step was skipped after test failure. It is not a passing fixture artifact.
- Environment log confirms DB/exchange credential variables empty and `AI_EXECUTION_ENABLED=false`.

### Correction after failed CI

- Test-only correction commit: `101b4be4d868d64aca5c7d49c7758a52b888a83a`.
- Updated assertion now requires `active_order_id is None`, and separately verifies O2 has terminal `FILLED` status and filled quantity `7`.
- No production/reference-model behavior was changed in this correction.
- A new push-triggered workflow run is expected; its run ID and result are pending verification.

**Current P1.8.3 status: BLOCKED pending rerun CI.** Do not mark PASS until the rerun checks out the corrected source SHA and all tests, reproducibility, replay and artifact checks pass.


### CI verification — P1.8.3 PASS (2026-11-07)

- Workflow run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42291352255
- Job ID: `128145290479`, `Deterministic local fixture contracts`, conclusion **SUCCESS**.
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Exact checked-out/source SHA: `a64d7366a5d19dd0e8d70b8aa27db2b5e30aa841`; checkout log and `git rev-parse HEAD` agree.
- Corrected test source blob: `7303eb823305f94cce17763acbc79dee458c59ab`; exact source contains the terminal FILLED assertions (`active_order_id is None`, O2 status FILLED, filled quantity 7).
- Synthetic-only preflight: PASS. Python 3.11.18 compile: PASS. Unit tests: **36/36 PASS**.
- Two independently generated 1,000-event fixture directories were byte-identical according to the workflow reproducibility check.
- Both local replay smoke checks: PASS; 1,000 events, 3 streams, 12 segments each.
- Fixture manifest: 17/17 SHA-256 entries passed in workflow; artifact downloaded and independently checked again, 17/17 PASS.
- Artifact ID `13539157781`; name `p1-8-synthetic-evidence-a64d7366a5d19dd0e8d70b8aa27db2b5e30aa841`; 299,039 bytes; SHA-256 `d9ea3cd456999c7948143a59b2166f702abc3e47ffd2c3a92f3bd6fea4c7321c`; expires `2026-11-13T20:47:44Z`. Downloaded ZIP hash independently matches GitHub artifact metadata and upload log.
- Artifact contains 24 files; its run descriptor records source SHA `a64d7366a5d19dd0e8d70b8aa27db2b5e30aa841`, 1,000 events (Core 334, AI 333, Legacy 333), Python 3.11.18 / CPython / Linux x86_64, storage medium NOT_MEASURED, canonicalization `RFC8785-JCS-STRICT-SUBSET/1`, and unsigned local SHA-256 evidence profile.
- Workflow log confirms database/exchange credential environment variables empty and `AI_EXECUTION_ENABLED=false`.

**P1.8.3 status: PASS — synthetic-only fault injection harness and CI contract verified for the exact source SHA above.** This does not certify production T0/T1 behavior or broader durability/recovery properties. T0 remains PAUSED; no provider, VPS, persistent capture, database/runtime integration, signing/key lifecycle, Root B, live order or execution work was performed or authorized.
