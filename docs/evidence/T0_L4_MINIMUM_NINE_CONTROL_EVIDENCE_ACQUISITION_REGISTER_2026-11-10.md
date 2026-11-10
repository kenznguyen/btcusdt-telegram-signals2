# T0 L4-Minimum — Nine-Control Evidence Acquisition Register

Date: 2026-11-10
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Work type: documentary evidence planning and status reconciliation only
Status: **REGISTER COMPLETE — EVIDENCE ACQUISITION NOT PERFORMED — AGGREGATE ACCEPTANCE BLOCKED**

## 1. Controlling policy and source baseline

- Current L4-Minimum matrix: `docs/evidence/p1-8/L4-MINIMUM-PROVENANCE-ACCEPTANCE-MATRIX.md`, blob `2ba85af550fb7e369ea39ade6d73878d78dbf6bc`.
- Owner waiver: `docs/decisions/D-2026-11-10-L4-INDEPENDENT-REVIEW-WAIVER.md`; L4M-09 is OWNER-WAIVED / NOT MANDATORY.
- Historical read-only audit: `docs/evidence/T0_L4_MINIMUM_READ_ONLY_AUDIT_2026-11-10.md`, blob `cfecb7428508adf23e6b9e71dc0dfe1e0e38080c`.
- Historical adversarial review: `docs/evidence/T0_L4_MINIMUM_ADVERSARIAL_REVIEW_2026-11-10.md`, blob `a7aec29330d71cb4d34193d6db81b8e20eb295f1`.
- Current-policy reconciliation: `docs/evidence/T0_L4_MINIMUM_POLICY_HISTORICAL_AUDIT_RECONCILIATION_2026-11-10.md`, blob `531b9b4b42337439697ac27286486ced8d19df25`.

The active denominator is nine controls: L4M-01–08 and L4M-10. L4M-09 remains a historical traceability identifier only. No independent-assurance claim is permitted.

## 2. Evidence acquisition register

| Control | Existing evidence class | Exact remaining evidence needed | Acquisition boundary | Current disposition |
|---|---|---|---|---|
| L4M-01 — Owner custody | GitHub records and short-lived CI artifacts; no qualifying owner copy demonstrated | Owner-controlled package inventory; SHA-256 manifest; custody reference outside both T0/VPS and GitHub; exact readback/integrity result during T0 outage, GitHub outage and simultaneous outage; include latest-head anchor | Owner-supplied sanitized evidence only. Do not access private storage or request secrets | NOT VERIFIED |
| L4M-02 — Signer separation | Synthetic ephemeral-key tests and verifier-only source; no production owner signer proof | Signer identity/fingerprint; custody and recovery boundary; evidence that T0 runtime/admin credentials cannot sign or authorize signing; approved recovery procedure and separately authorized isolated proof | No key generation, import, export, rotation, provider call or permission probe | NOT VERIFIED |
| L4M-03 — Exact binding/freshness | Synthetic event-byte verifier and CI subject-digest checks; T0 has no signed canonical checkpoint | Exact T0 checkpoint/manifest definition; signed envelope and digest binding; authenticated latest-head anchor; exact anchor digest; owner-custody/readback proof; older-valid-checkpoint rollback result against anchor | No canonical T0 schema/write-path change; no signing operation or freshness test | PARTIAL — SYNTHETIC/DESIGN ONLY |
| L4M-04 — Offline verification | Local synthetic Sigstore bundle verifier and CI evidence | Owner-run verification of the exact retained T0 package on a separate environment, with T0/VPS, GitHub, ChatGPT and network unavailable; verifier build/source hash; trust-policy snapshot; complete output and exit status | Do not run verifier or install dependencies without separate authorization | PARTIAL — SYNTHETIC/CI ONLY |
| L4M-05 — Independent readback/recovery | Synthetic file-backed SQLite crash/reopen model | Readback of the owner-controlled evidence copy; package inventory/manifest/signature revalidation; documented non-destructive recovery procedure and observed result; no overwrite of canonical source | No production restore, DB access, overwrite or fault injection | PARTIAL — SYNTHETIC MODEL ONLY |
| L4M-06 — Key/trust lifecycle | Synthetic trust-root snapshots, rotation and unknown/revoked-state logic | Owner-approved versioned trust policy; actual key/trust fingerprints and approval lineage; exact rotation/revocation evidence; separate signature validity/current trust/historical trust-at-time results; explicit UNKNOWN where trusted-time/revocation evidence is absent | No real key/trust-root operation, TSA/OCSP/CRL provider call or trust-policy mutation | PARTIAL — SYNTHETIC POLICY ONLY |
| L4M-07 — Tamper-evident history | Synthetic append-only event/ACK/checkpoint model; Git history and CI artifacts | Exact evidence-record inventory; immutable original bytes; canonical identity/digest linkage; owner-controlled independent manifest/copy; tamper and wholesale-replacement detectability; storage-administrator assumptions | No WORM claim; no archive, cleanup, compaction, vacuum, expiry or deletion | PARTIAL — SYNTHETIC MODEL ONLY |
| L4M-08 — Claim discipline | Historical audit found documentary/synthetic claim limitations appropriately stated | Confirm current package claims remain bounded to exact object, method, time basis, trust assumptions and limitations; preserve explicit exclusions for market-data truth, source completeness, durability and trading correctness | Documentary inspection only; do not infer operational capability | DOCUMENTARY PASS ONLY; revalidate against frozen package |
| L4M-10 — Owner aggregate acceptance | Current matrix defines per-control semantics and owner disposition requirements | Frozen baseline ID; canonical manifest and digest; lineage manifest with exact hashes of matrix/decisions/supporting artifacts; owner assessor identity/role and conflict disclosure; nine per-control dispositions; separate owner disposition referencing exact baseline digest | Do not freeze or issue PASS until evidence is complete; no self-referential matrix digest | NOT VERIFIED / PENDING OWNER ASSESSMENT |

## 3. Dependency and acquisition order

1. **L4M-01 + L4M-03:** establish the exact package boundary and authenticated latest-head anchor together. The anchor must be included in the same independent custody inventory; a sequence number alone is insufficient.
2. **L4M-02:** establish signer identity and separation evidence before treating any signed envelope as an owner-authorized checkpoint.
3. **L4M-04 + L4M-05:** verify the exact retained package offline and perform non-destructive independent readback. These are owner evidence activities, not CI substitutes.
4. **L4M-06 + L4M-07:** establish trust-state evidence and tamper-evident history/independent manifest. Absence of trusted-time/revocation proof leaves historical trust UNKNOWN; absence of an independently retained manifest prevents an immutability/tamper-detection claim.
5. **L4M-08:** review every claim against the exact package and its limitations.
6. **L4M-10:** freeze the complete review-input baseline only after evidence is assembled; perform owner self-assessment and issue a separate disposition against its digest.

This sequence is a dependency plan, not an authorization to perform the activities.

## 4. Evidence quality rules

- Preserve the exact original bytes and source SHA; do not replace historical reports when policy changes.
- Distinguish source/design documentation, synthetic tests, CI artifacts, owner-supplied evidence and production/runtime evidence. These categories are not interchangeable.
- A GitHub Actions artifact or Git history alone is not independent custody outside GitHub.
- A successful upload is not exact-version readback verification.
- A verifier script existing in the repository is not proof that the owner independently verified a T0 package.
- A signature is not proof of market-data truth, source completeness, database durability or trading correctness.
- No missing evidence is inferred from a design description; no UNKNOWN/NOT VERIFIED state is promoted to PASS.
- Do not expose private keys, tokens, credentials, personal account identifiers or sensitive storage details in repository evidence. Use redacted references and fingerprints only.

## 5. Consolidated status

- L4M-01: NOT VERIFIED.
- L4M-02: NOT VERIFIED.
- L4M-03: PARTIAL — synthetic/design only.
- L4M-04: PARTIAL — synthetic/CI only.
- L4M-05: PARTIAL — synthetic model only.
- L4M-06: PARTIAL — synthetic policy only.
- L4M-07: PARTIAL — synthetic model only.
- L4M-08: DOCUMENTARY PASS ONLY; not an operational control pass.
- L4M-09: OWNER-WAIVED / NOT MANDATORY.
- L4M-10: NOT VERIFIED / PENDING OWNER ASSESSMENT.
- Aggregate L4-Minimum: **BLOCKED / NOT VERIFIED**. No qualifying frozen baseline with nine active-control PASS results and owner disposition is evidenced.
- L4-Extended branch creation: **BLOCKED** until an accepted/frozen L4-Minimum commit exists.

## 6. Next gate

The next meaningful input is owner-controlled L4M-01 custody evidence and its L4M-03 latest-head anchor, followed by L4M-02 signer-separation evidence. Without those, further synthetic design work cannot close the central assurance gaps.

## 7. Limits

Documentary register only. No tests, compile, dry-run, fault injection, Actions dispatch or workflow execution. No source/schema/API/runner/adapter/workflow/permission/key/trust/provider/runtime/VPS/database/network/data changes. No owner storage access or evidence readback was performed. No workflow run or artifact is claimed. No archive, cleanup, expiry, vacuum, compaction, backup expiry, replica removal or deletion. Option C — No Destructive Authority remains ACTIVE; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
