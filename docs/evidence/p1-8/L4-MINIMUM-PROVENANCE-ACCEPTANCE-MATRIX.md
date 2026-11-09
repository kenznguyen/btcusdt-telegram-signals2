# L4-Minimum Provenance Acceptance Matrix — Documentation Baseline

Date: 2026-11-09  
Parent decision: `docs/decisions/D-2026-11-09-L4-PROVENANCE-PERSONAL-SCOPE.md`  
Scope: personal, non-commercial BTCUSDT Quant System  
Status: DESIGN / TEST-PLAN ONLY — NOT IMPLEMENTED, NOT EXECUTED, NOT ACCEPTED

## 1. Purpose and boundaries

Translate the owner-approved L4-Minimum profile into falsifiable acceptance requirements. This document defines what evidence must exist before L4 can be accepted. It does not implement controls, authorize operational tests, or close existing P1.8 lifecycle findings.

L4-Minimum is proportionate to a single-owner system. SaaS/multi-tenant features, customer SLA, commercial compliance certification, multi-TSA quorum and dedicated WORM are not acceptance requirements absent a concrete need.

## 2. Acceptance matrix

| ID | Requirement | Positive evidence required | Negative/adversarial cases | PASS condition |
|---|---|---|---|---|
| L4M-01 | Owner-controlled evidence custody | Evidence package exported and retained in an owner-controlled location outside T0/VPS; inventory and SHA-256 manifest | T0/VPS unavailable; GitHub unavailable; one evidence copy corrupted or missing | Owner can locate and integrity-check the retained package without T0 or GitHub |
| L4M-02 | Signing authority separated from T0 | Documented key custody, signer identity, authorization boundary and recovery procedure; proof signer is not an ordinary T0 runtime credential | T0 compromise; signer unavailable; unauthorized signing request; key loss | T0 process/admin credentials alone cannot create an accepted owner signature; recovery path is documented and tested in an authorized isolated test |
| L4M-03 | Exact-object binding | Signed envelope binds exact checkpoint bytes/digest, schema/version, dataset identity, sequence/generation and required context | Modify one byte; swap dataset/version; replay an older valid checkpoint; detach signature from payload | Every mutation or context substitution is rejected; exact original object verifies |
| L4M-04 | Independent offline verification | Verifier runs on a separate environment with a pinned trust-policy snapshot and no ChatGPT/producer runtime/network dependency | ChatGPT unavailable; producer unavailable; network disabled; unknown trust root; malformed package | Owner can independently verify a valid package offline; ambiguous or incomplete inputs fail closed |
| L4M-05 | Independent readback/recovery | Evidence copy restored/read back from its independent custody location; manifest and signatures rechecked | Missing object; truncated object; corrupted object; stale copy; partial restore | Recovery detects every missing/corrupt object and returns a fully verifiable package or an explicit failure |
| L4M-06 | Key and trust lifecycle | Versioned trust policy; approval record for root/key change; rotation/revocation evidence; historical verification semantics | Unknown key; revoked key; substituted root; expired/unknown status; compromised key; policy rollback | Verification distinguishes valid-at-signing-time, currently trusted, revoked, unknown and unverifiable states; no silent trust fallback |
| L4M-07 | Append-only evidence history | Original signed bytes, timestamp intents/attempts, tokens if any, verifier outputs, revocation evidence and manifest are preserved with linked identities | Retry after timeout; duplicate attempt; late token; conflicting verification; attempted overwrite/deletion | Earlier records remain addressable and unmodified; uncertainty is represented explicitly, not overwritten |
| L4M-08 | Claim discipline | Each provenance statement identifies what was actually verified and its trust assumptions | Valid signature but false market data; complete signature but incomplete source coverage; timestamp without durable-commit proof | Reports never infer market-data truth, exchange completeness, DB durability or strategy correctness from a signature/timestamp alone |
| L4M-09 | Independent review | Reviewer identity, independence basis, exact source/evidence SHA, scope, methods, findings and limitations | Same producer reviews own claim; reviewer lacks artifacts; scope silently expands | Review is performed by a reviewer not acting as sole producer/authority and covers exact immutable artifacts |
| L4M-10 | Fail-closed acceptance state | Machine-readable and human-readable verdicts with exact reasons and evidence references | Missing evidence; unknown trust state; verifier crash; dependency outage; mismatched digest | Any required unknown, missing or invalid proof yields NOT VERIFIED/BLOCKED, never PASS |

## 3. Required test groups

### G1 — Integrity and binding
- Valid package verifies.
- Single-byte mutation fails.
- Signature/payload swap fails.
- Dataset identity, schema version, sequence or generation substitution fails.
- Valid old package replay is detected as stale/rollback where freshness is claimed.

### G2 — Custody and availability independence
- Verification works with T0/VPS unavailable.
- Verification works with GitHub unavailable.
- Verification works with ChatGPT unavailable.
- Independent evidence copy can be read back and revalidated.
- Missing/corrupt/partial copies are detected; no silent success.

### G3 — Signer and trust lifecycle
- T0 runtime credentials cannot impersonate the owner-controlled signer.
- Unknown and substituted trust roots fail closed.
- Rotation preserves historical verification according to an explicit policy.
- Revoked/unknown revocation state is distinguished; no claim of current validity without evidence.
- Key loss/compromise response is documented and owner-controlled.

### G4 — Evidence history and uncertainty
- Timeout is recorded as UNKNOWN, not success or definitive failure.
- Retry creates a distinct attempt and preserves the original.
- Late-arriving proof is linked to the exact request/checkpoint.
- Conflicting or incomplete verification records remain visible.
- Original signed bytes remain unchanged.

### G5 — Claim boundaries
- A valid signature is not reported as proof of market-data truth.
- A timestamp is not reported as proof of DB/WAL durability unless the exact durable boundary is independently evidenced.
- A successful verifier is not reported as proof of source completeness, exchange truth or trading performance.

## 4. Evidence package minimum

For each acceptance run, retain:
1. immutable test input package and its SHA-256;
2. exact verifier source/build identity and SHA-256;
3. trust-policy snapshot and root fingerprints;
4. test case ID, expected result and observed result;
5. verifier output and exit status;
6. environment identity and network/availability conditions;
7. independent reviewer report and exact reviewed artifact hashes;
8. final PASS/BLOCKED/NOT VERIFIED disposition and unresolved limitations.

Do not include private signing keys or secrets in the evidence package. Evidence should identify key fingerprints and custody references, not disclose secret material.

## 5. Required state semantics

- **PASS:** all required evidence for the exact claim is present, integrity-checked and independently verified.
- **BLOCKED:** a required prerequisite is known to be unavailable, unsafe or unresolved.
- **NOT VERIFIED:** evidence is absent, incomplete, stale or has not been independently checked.
- **UNKNOWN:** an operation's outcome cannot be established (for example, timeout); UNKNOWN must not be coerced to PASS.
- A document-only/static-review PASS applies only to the reviewed document and scope.

## 6. Execution sequencing and authorization gates

1. Independent review of this matrix and its alignment with P1.8.36 and current lifecycle constraints.
2. Inventory current evidence and implementation without touching runtime or secret material.
3. Design isolated, synthetic fixtures and expected outputs.
4. Obtain explicit owner approval for any test execution that touches keys, trust roots, GitHub permissions, persistent storage, VPS, database, staging, restore or fault injection.
5. Run only the approved test scope; retain exact source SHA, workflow run and artifact where applicable.
6. Independent review of results before changing any acceptance status.

This document does not authorize steps 2–6 where they would cross the existing authorization boundary. In particular, it does not authorize key operations, permission inventory, provider calls, staging, restore, fault injection, workflow dispatch, runtime changes or destructive operations.

## 7. Existing project gates that remain independent

- P1.8.153 remains the next documented lifecycle-design gate from the current handoff; this L4 matrix does not replace or retarget it.
- V07 remains BLOCKED.
- V08 remains OPEN/BLOCKED.
- Restore remains OPEN/BLOCKED.
- Option C — No Destructive Authority — remains in force.
- T0 remains an independent canonical data asset.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.

## 8. Current verdict

- Matrix authored: DOCUMENTATION PASS.
- Requirements implemented: NOT VERIFIED.
- Test fixtures created: NOT RUN / NOT CREATED by this record.
- Tests executed: NOT RUN.
- GitHub Actions: NOT DISPATCHED.
- Independent technical review: PENDING.
- L4 implementation/operational acceptance: BLOCKED.

No code, schema, API, workflow, runtime, VPS, database, T0/T1/T2, feeder, ledger, strategy, risk, key, trust-root or permission changes were made.
