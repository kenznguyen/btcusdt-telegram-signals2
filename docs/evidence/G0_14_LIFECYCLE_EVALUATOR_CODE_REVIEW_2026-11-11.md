# G0.14 — Code Review and Contract-Gap Assessment

Date: 2026-11-11  
Review target source HEAD: `7ddf48c83edffd76b339ca1be6e09b1e300eb73a`  
Verdict: **REQUEST CHANGES — REQUIRED FINDINGS OPEN**

## 1. Review scope and evidence

Reviewed:
- G0.10 synthetic-only lifecycle dry-run contract and SYN-DRY-001–026.
- G0.12 disposition precedence, field semantics and reason-code catalogue.
- G0.13 pure evaluator and its 20 in-memory unit tests.
- G0.13 verification report and current handoff.

Source blobs reviewed:
- `pipeline/lifecycle_disposition.py`: `a528861c342c7c20ae48a9042338fec4ee2afa24`
- `pipeline/test_lifecycle_disposition.py`: `068a22f833ebe922da422df5fba520e36b77586a`
- G0.12 contract: `fa4e595126fe0c59ed2f9d91f274d7707d636b51`

This was a source/spec review only. No source, test, schema, workflow or runtime files were changed. No tests were rerun during G0.14; the G0.13 report records the prior focused 20/20 local test result and compile result. Repository-wide tests and CI remain NOT RUN.

## 2. Findings

### G0.14-R1 — REQUIRED: malformed copy state can raise instead of failing closed

In the copy inventory loop, `item.get("state") not in {"PRESENT", "RETIRED"}` performs set membership without first requiring a string. A list/dict state is unhashable and raises `TypeError`, escaping the evaluator rather than returning `BLOCKED_UNKNOWN`.

The existing malformed-enum tests cover dependency state, but not copy state.

Required remedy:
- Validate copy state type before enum membership.
- Treat malformed copy metadata as `UNK_COPY_LINEAGE` and return `BLOCKED_UNKNOWN`.
- Add list/dict copy-state regression cases.

### G0.14-R2 — REQUIRED: COPY_SPECIFIC_REVIEW does not bind the exact copy to its inventory entry

The copy branch validates the separate `copy_lineage` mapping for non-empty `copy_id`, `source_object_id` and `source_version_id`, but does not require:
- a matching entry in the complete `copies.items` inventory;
- equality between the copy-lineage identity and the evaluated object's exact `object_id` / `version_id` (or an explicitly defined copy identity mapping);
- a matching exact version and copy kind in that inventory entry.

As written, a record can have `copies.items=[]` and an unrelated, syntactically complete `copy_lineage`, yet receive `COPY_SPECIFIC_REVIEW`. This violates G0.12's exact-copy and complete copy-inventory requirements.

Required remedy:
- Define one canonical copy identity relation in the contract.
- Require exactly one matching copy inventory entry for the evaluated copy and version.
- Require source/version/recovery-chain fields to agree across the supplied copy records.
- Add negative tests for empty inventory, mismatched IDs/versions, duplicate matches and sibling/source confusion.

### G0.14-R3 — REQUIRED: protected early return omits required unknown reason codes

The evaluator returns early when it detects a protected class or binding hold. It calls `_unknowns()`, but skips other required fact checks such as hold-registry completeness, source lineage, dependency registry, copy inventory and process state.

G0.12 §3.1 requires a protected object to remain `PROTECTED` despite unrelated missing metadata **and still include the missing-field reason codes**. Example: an exact T0 object with an incomplete hold registry returns PROTECTED but does not include `UNK_HOLD_STATE`; missing dependency/copy/process evidence is likewise omitted.

Required remedy:
- Preserve PROTECTED as the winning disposition.
- Evaluate all independently checkable metadata-quality predicates before serialization.
- Include applicable `UNK_*` reason codes alongside the winning `PROT_*` code.
- Add protected-class tests with each unrelated metadata section missing or malformed.

### G0.14-R4 — REQUIRED: policy/classification contract is only partially represented

G0.12's field map requires a supported functional class **plus sensitivity label** and an exact supported policy ID/version. The implementation has no sensitivity-label field or validation. It also accepts either `RET-01/B` or `RET-02/B` for every review class without checking whether that policy/version is valid for the specific class.

This can produce a positive review disposition from a syntactically accepted but semantically mismatched policy/class pair.

Required remedy:
- Add a closed sensitivity-label vocabulary to the pure input contract.
- Define and enforce the allowed class-to-policy/version mapping from the ratified policy.
- Add missing, unsupported and mismatched policy/class/sensitivity tests.
- Do not invent new policy versions or retention values.

## 3. Additional contract gaps — not independent approvals

These are not reasons to broaden G0.13 into an evidence-authentication service, but must remain explicit limits:

- `identity_verified` and `producer_provenance_verified` are caller-supplied booleans. They are not authenticated by the evaluator.
- `evidence_revision` is checked only for non-empty text; the evaluator does not prove that it binds all supplied facts to one immutable evidence revision.
- SHA-256 format and byte length are checked structurally; no payload is supplied and no digest is recomputed.
- A complete flag and an empty dependency/copy list are trusted as supplied facts; completeness, freshness and source provenance are not independently proven.
- The generic lineage check requires a source object/version and transform ID for all review groups. The contract should confirm whether this is intentionally universal or class-specific before the input contract is frozen.
- The current test suite covers representative cases but does not establish the full 26-case G0.10 matrix or the separate 87-vector TEST-01–07 assurance catalogue.

These limits mean the evaluator is a pure classifier over supplied facts, not an evidence verifier.

## 4. Five-axis review

| Axis | Assessment |
|---|---|
| Correctness | **BLOCKED** — R1–R4 required |
| Readability / simplicity | CONDITIONAL PASS — small, standard-library module; some dense compound predicates should be split when remediating |
| Architecture | PASS within narrow pure-evaluator boundary; no I/O/executor capability found in reviewed source |
| Security | CONDITIONAL — no external I/O or mutation surface; malformed-input and evidence-trust gaps remain |
| Performance | PASS for bounded in-memory record evaluation; no unbounded external operation |

## 5. Verification and status

| Item | Status |
|---|---|
| G0.13 focused tests (reported previously) | 20/20 PASS — not rerun in G0.14 |
| G0.13 Python compile (reported previously) | PASS — not rerun in G0.14 |
| G0.14 source/spec review | PASS — review completed |
| Required findings R1–R4 | OPEN |
| G0.13 implementation approval / merge readiness | **BLOCKED pending remediation and review** |
| Repository-wide tests | NOT RUN |
| GitHub Actions | NOT DISPATCHED |
| Workflow run / artifact | NONE |
| TEST-01–07 / 87-vector catalogue | NOT IMPLEMENTED / NOT VERIFIED; 0/87 executed |
| TEST-08 | NOT GRANTED |
| Runtime/VPS | NOT VERIFIED |
| Destructive executor / data operations | NOT AUTHORIZED / NOT PERFORMED |

## 6. Explicit non-actions

No source/test/fixture/schema/API/registry/adapter/runner/oracle/workflow/scheduler/service/permission/credential/database/storage/VPS/data/model/ledger/runtime changes. No test, compile, dry-run, CI dispatch, inventory, network/provider/database access, archive, quarantine, cleanup, expiry, compaction, vacuum or deletion.

T0 remains independent and protected. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.

## 7. Next bounded step

Request owner approval for G0.15 remediation limited to:
1. R1 malformed copy-state fail-closed validation and regression tests.
2. R2 exact copy-to-inventory identity/version binding and regression tests.
3. R3 complete reason-code collection while preserving protected precedence.
4. R4 sensitivity-label and class-to-policy mapping, but only after the exact closed vocabulary/mapping is confirmed against the owner-ratified policy text.

No CI dispatch, broad TEST-01–07 harness, external evidence authentication, production inventory or destructive executor is included. If the ratified policy does not specify the exact sensitivity vocabulary and class-to-policy mapping, R4 must remain BLOCKED rather than inventing values.
