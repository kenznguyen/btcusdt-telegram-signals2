# T0 L4-Minimum — Automation Plan and Owner-Only Decision Boundaries

Date: 2026-11-10
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Status: **OWNER-APPROVED PLAN — FIRST LINEAGE CONTRACT GATE IMPLEMENTED — REMAINING AUTOMATION NOT IMPLEMENTED**
Approval: owner approval in conversation on 2026-11-10 to automate L4M-01–08 as far as technically possible and reserve owner participation for real-world custody/control assertions and L4M-10 acceptance.
Controlling matrix: `docs/evidence/p1-8/L4-MINIMUM-PROVENANCE-ACCEPTANCE-MATRIX.md` (current branch blob at plan preparation: `75db0d98134fd656d91a8545bc307c56595aebf7`).
Current register at plan preparation: `docs/evidence/T0_L4_MINIMUM_NINE_CONTROL_EVIDENCE_ACQUISITION_REGISTER_2026-11-10.md` (blob `cee949666da611a4efca7e7b51aea47ab4b13eff`).

## 1. Approved operating principle

Automate collection, hashing, structural validation, cryptographic verification, negative testing, cross-reference checks and report generation wherever the required bytes and trust inputs are available to GitHub Actions or a bounded read-only collector.

Do not make the owner manually perform a test that can be performed deterministically by CI. Do not infer real-world control or owner intent from CI. Owner participation is limited to facts that cannot be established by repository/CI evidence and the final owner disposition.

The nine active controls remain L4M-01–08 and L4M-10. L4M-09 remains OWNER-WAIVED. This plan does not change the acceptance matrix, weaken any PASS criterion, grant operational authority or make L4-Minimum accepted.

## 2. Per-control automation split

| Control | Automatable work | Owner-only assertion / remaining boundary | PASS discipline |
|---|---|---|---|
| L4M-01 — custody | Discover approved GitHub artifacts/files; produce deterministic package inventory; hash every included object; validate manifest schema and duplicate/path anomalies; download exact GitHub artifact bytes and verify digest; compare VPS read-only inventory/readback report when supplied through the approved bounded channel; generate custody report | Confirm which package/copy is owner-designated and attest any VPS custody/readback fact that CI cannot independently observe. No owner action is needed for GitHub bytes already fetched and hashed by automation | CI can mark GitHub-side integrity subchecks PASS. Overall L4M-01 remains NOT VERIFIED until required owner custody assertions and all claimed-copy readbacks satisfy the controlling matrix |
| L4M-02 — signer separation | Parse signer metadata/fingerprints; verify signatures against pinned trust policy; inspect workflow/permission boundaries; run adversarial tests proving ordinary T0 runtime credentials cannot satisfy the verifier's owner-signature policy; produce a separation evidence report | Confirm actual owner control/custody and recovery boundary only where it is not provable from machine-verifiable policy/permissions. No key creation/import/export/rotation or privilege probing | No signer is accepted solely because a test key or CI identity exists. Missing actual approved signer evidence = NOT VERIFIED |
| L4M-03 — exact binding/freshness | Verify exact payload bytes, digest, schema, dataset identity and signed envelope; test single-byte mutation, payload/signature swap, dataset substitution and replay; compare checkpoint with authenticated latest-head anchor; verify anchor digest and lineage | Owner confirms anchor is the designated owner-controlled latest-head reference only if that designation cannot be established cryptographically/documentarily | Missing or unauthenticated anchor => freshness UNKNOWN / NOT VERIFIED; sequence/generation alone is insufficient |
| L4M-04 — offline verification | Build/pin verifier; run in isolated GitHub job with network disabled; verify exact package and pinned trust snapshot; test unknown root, malformed bundle, unavailable verifier, incomplete package and fail-closed behavior; record source SHA and full output | Owner-run offline confirmation remains necessary only if the matrix requires verification in the owner's separate environment. CI offline PASS is a separate subcheck and cannot be relabelled owner-run | Keep CI_OFFLINE_VERIFICATION and OWNER_OFFLINE_VERIFICATION separate. Overall control cannot PASS until the matrix's owner-verification requirement is met |
| L4M-05 — readback/recovery | Read back exact GitHub artifact/object; hash and revalidate manifest/signatures; run non-destructive recovery/readback tests against disposable copies; test missing/truncated/corrupt inputs | Owner confirms readback of any claimed VPS-held copy only if the approved collector cannot produce verifiable machine evidence. No restore-overwrite or canonical DB operation | Disposable recovery tests are not owner custody recovery. Report each source/copy independently |
| L4M-06 — trust lifecycle | Validate versioned trust policy, signer fingerprints, approval records, rotation/revocation test vectors, policy rollback and unknown-state handling; separate cryptographic validity/current trust/historical trust-at-time | Owner approves actual trust-root/key changes and supplies missing authorization lineage; no actual key or trust mutation is performed by this plan | Unknown time/revocation evidence remains UNKNOWN. Synthetic lifecycle tests are only implementation evidence |
| L4M-07 — tamper-evident history | Build canonical event inventory; verify digest links, append-only sequence, duplicate/retry/overwrite/deletion/wholesale-replacement detection; compare history to retained manifest in approved VPS/GitHub custody; test against disposable copies | Owner identifies the designated retained history/manifest copy only where the record does not establish that designation | Claim only tamper-evident, never WORM/absolute immutability without separate evidence |
| L4M-08 — claim discipline | Automatically scan reports/matrix/handoff for unsupported PASS, operational/runtime/independent/WORM/freshness claims; compare claims with exact evidence classes and artifact expiries; generate exceptions list | Owner resolves policy choices and accepts residual limitations; no manual rechecking of mechanically verifiable references | Documentary PASS remains limited to the exact frozen package and claim set |
| L4M-10 — owner acceptance | Generate frozen input inventory, canonical SHA-256 manifest, lineage manifest, nine-control status summary and owner-disposition template; reject self-referential or mismatched baseline hashes | Owner supplies the final identity/role/conflict disclosure and explicit disposition tied to exact baseline digest | AI/CI may prepare the acceptance package but must never issue owner acceptance or mark L4M-10 PASS on the owner's behalf |

## 3. Proposed GitHub Actions architecture

Implement as a separate, path-scoped L4 validation workflow on the existing active branch after source/contract review.

1. **L4 contract and lineage gate** — validate matrix/register versions, decision references, evidence references, required controls and allowed status vocabulary. Fail on stale SHA references, duplicate IDs, missing mandatory controls or contradictions.
2. **L4 package inventory gate** — consume only explicitly selected GitHub evidence artifacts/files; download exact bytes; build inventory and SHA-256 manifest; verify every digest and record artifact ID, source run, source SHA and expiry. Never silently substitute a newer artifact.
3. **L4 cryptographic gate** — verify exact signed objects and pinned trust inputs; run mutation/replay/substitution negative tests. No key generation or signing.
4. **L4 offline gate** — run a network-disabled verifier job on the exact package and pinned trust snapshot. Record CI offline verification separately from owner offline verification.
5. **L4 readback/recovery gate** — verify exact GitHub readback and disposable-copy recovery. A VPS read-only collector may be considered separately only after its access contract, command allowlist, token source and output sanitization are reviewed and explicitly approved.
6. **L4 history/tamper gate** — validate canonical event linkage and detect mutation/replacement against the retained manifest.
7. **L4 claim-discipline gate** — cross-check evidence classes, claims, expiry and statuses; produce a deterministic exceptions report.
8. **L4 aggregate report** — produce per-control subcheck results and aggregate BLOCKED unless all active control requirements pass. Never allow CI success to override owner-only assertions.

### Workflow security and isolation

- GitHub-hosted disposable runners only for the CI stages.
- Least privilege: `contents: read` unless a narrowly justified artifact read requires another read-only permission.
- Checkout exact source SHA; record it in every report.
- No VPS SSH, no secrets, no production database, no exchange API credentials, no T1, no PostgreSQL, no networked signer/TSA/OCSP operation.
- Offline job must explicitly disable network access and prove the condition; if network isolation cannot be established, mark NOT VERIFIED rather than calling it offline.
- No upload of private keys, bearer tokens, credentials or sensitive owner identifiers.
- Artifact outputs are evidence, not automatic owner acceptance. Record retention expiry and exact digest.
- Fail closed on missing inputs, ambiguous identity, expired or unknown trust, malformed evidence, digest mismatch or stale lineage.

## 4. Required output contract

Every run must produce:
- exact branch, event, source SHA and workflow run URL;
- matrix/register/decision blob SHAs used;
- per-control automated subchecks with PASS / BLOCKED / NOT VERIFIED;
- exact input object identities, sizes and SHA-256 digests;
- artifact IDs, names, source run IDs and expiry;
- verifier version/source SHA and trust-policy fingerprint;
- negative-test outcomes;
- owner-only assertions still outstanding;
- aggregate disposition and explicit non-claims.

A successful workflow means only that its declared automated subchecks passed. It does not mean L4-Minimum is accepted, T0 runtime is healthy, data is truthful/complete, the owner controls a key, or any trading operation is safe.

## 5. Implementation sequence

1. Reconcile stale matrix/register/decision SHA references without rewriting historical records.
2. Add workflow contract tests first; prove stale references fail and current references pass.
3. Implement GitHub-side artifact inventory/readback and manifest verification.
4. Add exact-object cryptographic and adversarial verification using existing test fixtures and pinned trust inputs.
5. Add network-disabled offline verification and clearly separated owner offline status.
6. Add non-destructive disposable readback/recovery and tamper-history checks.
7. Add claim-discipline scan and deterministic aggregate report.
8. Run GitHub Actions on exact source SHA; archive artifacts and update handoff with run/job/artifact IDs and digests.
9. Only after all active controls are satisfied, prepare (not sign) the L4M-10 owner acceptance package.

Each implementation increment must be reviewed and tested before proceeding. Do not combine all gates into one unreviewable change.

## 6. Explicitly prohibited by this plan

- No T0 canonical SQLite read/write, schema change, migration, restore, vacuum or compaction.
- No Feeder/API restart, service installation, deployment or runtime configuration change.
- No SSH access expansion, forced-command change, SCP/rsync, probe installation or VPS command dispatch.
- No signer/key generation, import/export, rotation, revocation or signing operation.
- No trust-root mutation or external provider call.
- No artifact deletion, expiry change, cleanup, archive mutation or retention-policy change.
- No T1 activation, PostgreSQL canonical switch, live trading or real order.
- No L4-Extended work until L4-Minimum is frozen and accepted.

## 7. Current disposition

- Approval to automate: **APPROVED**.
- Documentation/design plan: **RECORDED**.
- L4 workflow implementation: **FIRST LINEAGE CONTRACT GATE IMPLEMENTED; ADDITIONAL ACQUISITION/VERIFICATION GATES NOT STARTED**.
- GitHub-side artifact inventory/readback: **NOT VERIFIED / NOT STARTED**.
- VPS-side custody/readback: **NOT VERIFIED**.
- Owner signer/custody assertions: **PENDING EVIDENCE**.
- L4-Minimum aggregate: **BLOCKED / NOT VERIFIED**.
- L4M-09: **OWNER-WAIVED**.
- Option C — No Destructive Authority: **ACTIVE**.
