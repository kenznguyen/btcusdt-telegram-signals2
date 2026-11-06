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
