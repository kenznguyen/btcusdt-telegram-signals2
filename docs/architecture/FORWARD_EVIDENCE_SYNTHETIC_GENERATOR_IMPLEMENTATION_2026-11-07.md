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
