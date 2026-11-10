# L4-Extended — Documentary Scope and Boundary Assessment

Date: 2026-11-10 UTC
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/l4-extended-provenance`
Reviewed branch HEAD: `09a031e8bd8662e3e99f9751ef0a5fccd43ef9d2`
Assessment type: read-only documentary/architecture reconciliation
Disposition: **SCOPE NARROWED FOR FUTURE REVIEW — IMPLEMENTATION PARKED / NOT AUTHORIZED**

## 1. Purpose and authorization boundary

This assessment reconciles existing L4 provenance decisions and prior TSA/WORM architecture material after the owner approved creation of this isolated branch.

Branch creation authorization is not implementation authorization. It does not satisfy or waive the L4-Minimum prerequisite.

Current controlling status:
- L4-Minimum: **ADMINISTRATIVELY CLOSED — BLOCKED / NOT VERIFIED**.
- L4M-01: **NOT VERIFIED**.
- L4M-03: **PARTIAL / NOT VERIFIED**; authenticated latest-head/freshness evidence is absent.
- No accepted/frozen L4-Minimum baseline and no owner acceptance exist.
- L4-Extended implementation, tests, workflow dispatch, provider operations and runtime integration remain **PARKED / NOT AUTHORIZED**.

The earlier separation plan said the Extended branch should be cut only from a frozen accepted L4-Minimum baseline. The later explicit owner approval created this branch from the recorded T0 branch base. That later approval authorizes the branch's existence only; it does not convert the base into an accepted baseline or authorize implementation.

## 2. Governing owner decisions reconciled

### 2.1 Personal, non-commercial system

The system is a personal BTCUSDT research/trading system, not SaaS or a multi-customer/commercial evidence product. Reliability, ownership and trustworthy evidence take priority over enterprise-style feature breadth.

Consequences for Extended scope:
- Multi-TSA quorum, cross-provider timestamp ordering, paid WORM purely as an assurance signal, commercial SLA, certification and third-party audit claims are not requirements by default.
- A single TSA may be considered only if a specific personal timestamp-assurance gap is documented and the owner later approves the claim, profile and implementation scope.
- Avoid building features solely to appear enterprise-grade.

### 2.2 Evidence custody is VPS + GitHub only

The controlling owner decision permits the project VPS and GitHub as the required custody locations and states that an additional third-party backup/object store is not required.

Consequences:
- Do not make AWS S3, GCS, Azure Blob, Cloudflare R2 or another external object store a dependency or presumed Extended deliverable.
- Existing WORM provider research is historical research, not provider selection or authorization.
- GitHub Actions artifacts remain in the GitHub failure domain; they are not independent third-party custody and are not WORM.
- The VPS/GitHub decision does not waive exact-object inventory, canonical SHA-256 manifest, provenance, authenticated latest-head anchor, signer separation or readback requirements for L4-Minimum.

### 2.3 No destructive authority

Option C — No Destructive Authority — remains ACTIVE. No retention execution, deletion, cleanup, archive transition, expiry, compaction, vacuum, backup expiry, replica removal or other destructive lifecycle operation is authorized. A future evidence archive proposal must preserve unresolved and unclassified evidence and cannot infer deletion rights from successful consumption or timestamp completion.

## 3. Existing documentary assets and what they establish

| Existing record | Bounded conclusion |
|---|---|
| P1.8.67 provider-neutral TSA architecture | TSA target is optional/asynchronous and outside T0's authoritative write path; no provider selected; design only |
| P1.8.68 static review | Documentary architecture review PASS within E0 scope only; no implementation or operational assurance |
| P1.8.69 evidence-contract decomposition | Logical evidence records and independent verifier responsibilities; not a schema or implementation |
| P1.8.77 T0 source mapping (referenced by TSA/WORM audit) | Current T0 candle store has no signed checkpoint, TSA outbox/client/verifier or RFC3161 archive in the reviewed source scope |
| T0 TSA/WORM read-only audit | TSA production BLOCKED; WORM not implemented/qualified for T0; T0 retention protection is governance, not technical WORM |
| D-2026-11-09 personal scope | Commercially motivated features are deferred; single TSA only if a real gap is justified |
| D-2026-11-10 VPS/GitHub custody decision | No external object store/backup is required; VPS and GitHub are the approved custody locations |

These records are not interchangeable:
- An architecture review PASS is not implementation acceptance.
- Synthetic evidence is not production evidence.
- A timestamp token does not prove source correctness, completeness, event truth, database durability or trading correctness.
- `datasetVersion` is not a signed immutable checkpoint or proof of durable commit.
- T0's canonical SQLite candle database is not WORM-protected.
- Forward-evidence Root A/Root B architecture is not evidence that T0 has two independent roots or immutable candle storage.

## 4. Recommended future L4-Extended scope — narrow and optional

No implementation is authorized by this assessment. If the L4-Minimum prerequisite is later resolved and the owner separately authorizes work, the proportionate candidate scope is:

1. **Single-provider-neutral RFC 3161 evidence path**, only for one explicitly defined immutable evidence object and one narrowly stated proof-of-existence claim.
2. **OCSP/CRL historical status evidence** required to verify the selected TSA signer chain under a versioned trust policy.
3. **Local independent verification and evidence packaging** using raw request/response bytes, exact object digest, certificate chain, historical revocation material, policy/trust snapshot and verifier provenance.
4. **Append-only reconciliation of request attempts**, including unknown submission outcomes, duplicate responses and quarantined evidence.

The existing P1.8.67–P1.8.69 material is a useful starting point for future review, not an approved build specification. A new owner decision must first identify whether the timestamp subject is:
- a dataset/checkpoint proof-of-existence product; or
- an exact signed-object historical-verification product under P1.8.36;
or two separately versioned products. The current T0 source does not provide the checkpoint/signing lifecycle required to assume either product is ready.

## 5. Explicitly excluded from this branch's current authorized scope

- Multi-TSA quorum, cross-provider ordering and failover: deferred by personal/non-commercial scope; no concrete requirement or owner approval.
- Third-party WORM/Object Lock storage: conflicts with the current VPS/GitHub-only custody direction unless the owner changes it. No provider selected or qualified.
- Root A/Root B dual-root topology: separate forward-evidence architecture; not a T0 requirement and not proof of T0 custody independence.
- T0 canonical SQLite mutation, Feeder changes, synchronous TSA calls, schema/migration, outbox, checkpoint/seal implementation, API changes or trading-ledger integration.
- PostgreSQL/TimescaleDB migration, public HTTPS, DNS/reverse proxy, multi-region DR, restore/RPO/RTO qualification and host/storage power-loss qualification; these remain separate workstreams.
- Provider contact, account creation, billing, endpoint/OCSP calls, credential/key/trust-anchor operations, signing or certificate changes.
- Any destructive lifecycle operation.

## 6. Mandatory architecture invariants if reconsidered later

- TSA is optional and asynchronous; T0 ingestion and canonical commit must continue when all TSA providers are unavailable.
- Timestamp only a stable, immutable, precisely defined object after its actual durable-commit boundary has been demonstrated; do not infer that boundary from current source documentation.
- Bind the timestamp imprint to exact canonical bytes and the approved context; preserve the original request and response bytes.
- A network timeout is UNKNOWN, not proof of non-issuance. Every retry is a distinct attempt; retain distinct tokens and verification decisions.
- Provider transport is not trust verification. Verification is local, independent and fail-closed against an explicit versioned profile.
- Preserve original OCSP/CRL bytes and historical time fields; current GOOD status alone does not establish historical validity.
- Missing, stale, contradictory or unauthorized trust/revocation evidence remains INDETERMINATE/QUARANTINED, never VERIFIED.
- Later verification under a new policy appends a new record; it does not overwrite history.
- No claim of WORM, independent custody, durability, legal admissibility, certification or audit acceptance without direct qualifying evidence.

## 7. Gate sequence before any implementation

1. Resolve L4-Minimum owner evidence gaps and obtain all required control verdicts on one frozen baseline; do not infer acceptance from administrative closure.
2. Obtain a separate owner decision authorizing a specific Extended objective and implementation scope.
3. Decide the timestamp subject and exact claim; reconcile with P1.8.36, V07 and V08 without assuming current T0 source compatibility.
4. Define the object/checkpoint contract, commit boundary, canonical serialization, digest/signature policy, nonce/profile and historical revocation semantics.
5. Define storage and retention within VPS/GitHub custody constraints; document availability/failure-domain claims and Option C restrictions.
6. Complete implementation-specific threat model and independent review.
7. Only after explicit authorization, define test fixtures and permitted execution scope. Provider or operational tests require their own authorization.

## 8. Verification and change record

- Branch HEAD read from GitHub before assessment: `09a031e8bd8662e3e99f9751ef0a5fccd43ef9d2`.
- Handoff readback blob: `5aa8c663968fbd1adc07d878b54ad24a4ce91bd2`.
- Branch initialization record blob: `7c944f5a76926ec78df7a8044b82b0f45fe853a0`.
- TSA/WORM audit blob: `4a7b872656ec240ddd6862f7ed6d92ca6c26fcee`.
- Personal-scope decision blob: `6b96c2c37a4989b7ceba291d027a3f8459eecb3b`.
- VPS/GitHub custody decision blob: `2df5bdeb36ec53158c66871b740c43b859a5013c`.
- P1.8.67 blob: `50654f3f4f4caa509598e4393e2634ea977df5dd`.
- P1.8.68 blob: `9ae0c50830644d21d850da4c4d246a2837f62fc6`.
- P1.8.69 blob: `caf0943865b096a0d592ae0718472754424991d0`.
- Assessment work: documentary read-only reconciliation only.
- Source/tests/packages/workflows: unchanged.
- Tests/compile: NOT RUN.
- GitHub Actions: NOT DISPATCHED; no workflow run/artifact claimed.
- VPS/runtime/DB/provider/key/permission/network/data access: NOT PERFORMED.
- Destructive lifecycle operations: NOT PERFORMED.

## 9. Status and next step

- Documentary scope reconciliation: **PASS — bounded documentary assessment only**.
- L4-Minimum: **ADMINISTRATIVELY CLOSED — BLOCKED / NOT VERIFIED**.
- L4-Extended implementation: **PARKED / NOT AUTHORIZED**.
- Provider selection and operational qualification: **NOT SELECTED / NOT PERFORMED**.
- WORM/Object Lock for T0: **NOT IMPLEMENTED / NOT QUALIFIED**.
- Option C: **ACTIVE**.
- Next step: preserve this branch as a documentary isolation branch. Await L4-Minimum owner evidence and a distinct implementation authorization. No source implementation or workflow execution is permitted by this record.
