# T0 L4-Minimum — Nine-Control Evidence Acquisition Register

Date: 2026-11-10
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Work type: evidence acquisition planning and bounded GitHub CI evidence automation
Status: **REGISTER RECONCILED — LINEAGE GATE PASS — SIX-ARTIFACT ACTIONS INVENTORY PASS — 40-FILE REPOSITORY INVENTORY PASS — REFERENCE RECONCILIATION PARTIAL PASS — AGGREGATE ACCEPTANCE BLOCKED**

## 1. Controlling policy and source baseline

- Current L4-Minimum matrix: `docs/evidence/p1-8/L4-MINIMUM-PROVENANCE-ACCEPTANCE-MATRIX.md`, blob `75db0d98134fd656d91a8545bc307c56595aebf7`.
- Owner waiver: `docs/decisions/D-2026-11-10-L4-INDEPENDENT-REVIEW-WAIVER.md`; L4M-09 is OWNER-WAIVED / NOT MANDATORY.
- Historical read-only audit: `docs/evidence/T0_L4_MINIMUM_READ_ONLY_AUDIT_2026-11-10.md`, blob `cfecb7428508adf23e6b9e71dc0dfe1e0e38080c`.
- Historical adversarial review: `docs/evidence/T0_L4_MINIMUM_ADVERSARIAL_REVIEW_2026-11-10.md`, blob `a7aec29330d71cb4d34193d6db81b8e20eb295f1`.
- Current-policy reconciliation: `docs/evidence/T0_L4_MINIMUM_POLICY_HISTORICAL_AUDIT_RECONCILIATION_2026-11-10.md`, blob `017bca148719006b22431d6eafa383fe6337a10c`.

The active denominator is nine controls: L4M-01–08 and L4M-10. L4M-09 remains a historical traceability identifier only. No independent-assurance claim is permitted.

## 2. Evidence acquisition register

| Control | Existing evidence class | Exact remaining evidence needed | Acquisition boundary | Current disposition |
|---|---|---|---|---|
| L4M-01 — Owner custody | GitHub records and short-lived CI artifacts; no qualifying owner copy demonstrated | Owner-controlled package inventory; SHA-256 manifest; custody reference to VPS and/or GitHub; exact readback/integrity result for each claimed copy; include latest-head anchor. No external backup is required. Single-location outage claims require a verified copy in the remaining location; simultaneous VPS+GitHub outage recovery is outside scope | Automate GitHub artifact discovery, exact download/readback, inventory and SHA-256 manifest. Current allowlist contains six explicitly selected GitHub Actions source artifacts (two P1.8.14 CI artifacts and four L4 lineage artifacts); all six are represented in the latest independently re-read manifest. This remains a selected CI inventory, not owner custody. A separate 40-file exact-commit repository-source inventory and reference reconciliation are recorded in the current workflow; neither is a complete L4 package. For VPS, consider a bounded read-only collector only after separate access-contract approval. Owner confirms only real-world designation/control of a copy where machine evidence cannot establish it; never request secrets | PARTIAL — six GitHub Actions source artifacts and 40 repository source files inventoried/read back; owner custody and complete package NOT VERIFIED |
| L4M-02 — Signer separation | Synthetic ephemeral-key tests and verifier-only source; no production owner signer proof | Signer identity/fingerprint; custody and recovery boundary; evidence that T0 runtime/admin credentials cannot sign or authorize signing; approved recovery procedure and separately authorized isolated proof | Automate signer metadata/fingerprint checks and code/permission-boundary tests. Owner confirms actual key custody/recovery only where not machine-verifiable. No key generation, import, export, rotation, provider call or privilege probe | NOT VERIFIED |
| L4M-03 — Exact binding/freshness | Synthetic event-byte verifier and CI subject-digest checks; T0 has no signed canonical checkpoint | Exact T0 checkpoint/manifest definition; signed envelope and digest binding; authenticated latest-head anchor; exact anchor digest; owner-custody/readback proof; older-valid-checkpoint rollback result against anchor | Automate exact-byte/signature/anchor verification and mutation/replay/substitution tests on supplied evidence. Missing anchor remains UNKNOWN. No canonical T0 schema/write-path change or signing operation | PARTIAL — SYNTHETIC/DESIGN ONLY |
| L4M-04 — Offline verification | Local synthetic Sigstore bundle verifier and CI evidence | Owner-run verification of the exact retained T0 package on a separate environment, with T0/VPS, GitHub, ChatGPT and network unavailable; verifier build/source hash; trust-policy snapshot; complete output and exit status | Automate a network-disabled GitHub verification job against exact package and pinned trust snapshot; report CI-offline and owner-offline separately. Owner-run offline evidence remains required only to satisfy the matrix's owner-environment assertion. No VPS or local installation | PARTIAL — SYNTHETIC/CI ONLY |
| L4M-05 — Independent readback/recovery | Synthetic file-backed SQLite crash/reopen model | Readback of the owner-controlled evidence copy; package inventory/manifest/signature revalidation; documented non-destructive recovery procedure and observed result; no overwrite of canonical source | Automate GitHub exact-object readback and disposable-copy recovery tests. Owner confirmation is limited to claimed VPS copy readback if no approved machine-verifiable report exists. No production restore, canonical DB access, overwrite or fault injection | PARTIAL — SYNTHETIC MODEL ONLY |
| L4M-06 — Key/trust lifecycle | Synthetic trust-root snapshots, rotation and unknown/revoked-state logic | Owner-approved versioned trust policy; actual key/trust fingerprints and approval lineage; exact rotation/revocation evidence; separate signature validity/current trust/historical trust-at-time results; explicit UNKNOWN where trusted-time/revocation evidence is absent | Automate trust-policy schema, fingerprint, approval-lineage and synthetic rotation/revocation/unknown-state checks. Owner approval remains necessary for actual trust-root/key changes. No real key/trust-root operation, external provider call or trust-policy mutation | PARTIAL — SYNTHETIC POLICY ONLY |
| L4M-07 — Tamper-evident history | Synthetic append-only event/ACK/checkpoint model; Git history and CI artifacts | Exact evidence-record inventory; immutable original bytes; canonical identity/digest linkage; owner-controlled independent manifest/copy; tamper and wholesale-replacement detectability; storage-administrator assumptions | Automate event inventory, digest linkage, append-only/overwrite/replacement detection and disposable adversarial tests. Owner identifies designated retained copy only where not machine-verifiable. No WORM claim; no archive, cleanup, compaction, vacuum, expiry or deletion | PARTIAL — SYNTHETIC MODEL ONLY |
| L4M-08 — Claim discipline | Historical audit found documentary/synthetic claim limitations appropriately stated | Confirm current package claims remain bounded to exact object, method, time basis, trust assumptions and limitations; preserve explicit exclusions for market-data truth, source completeness, durability and trading correctness | Automate cross-reference, evidence-class, expiry and claim-language checks; owner resolves policy choices/residual limitations. Do not infer operational capability | DOCUMENTARY PASS ONLY; revalidate against frozen package |
| L4M-10 — Owner aggregate acceptance | Current matrix defines per-control semantics and owner disposition requirements | Frozen baseline ID; canonical manifest and digest; lineage manifest with exact hashes of matrix/decisions/supporting artifacts; owner assessor identity/role and conflict disclosure; nine per-control dispositions; separate owner disposition referencing exact baseline digest | Automate frozen inventory, canonical manifest, lineage manifest, status summary and owner-disposition template. Only owner may issue final disposition tied to exact baseline digest; no self-referential matrix digest | NOT VERIFIED / PENDING OWNER ASSESSMENT |

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
- GitHub Actions artifacts and Git history remain within the GitHub failure domain; GitHub is an approved owner custody location but is not an independent third-party provider. No external copy is required under D-2026-11-10-L4-EVIDENCE-CUSTODY-VPS-GITHUB-ONLY.
- A successful upload is not exact-version readback verification.
- A verifier script existing in the repository is not proof that the owner independently verified a T0 package.
- A signature is not proof of market-data truth, source completeness, database durability or trading correctness.
- No missing evidence is inferred from a design description; no UNKNOWN/NOT VERIFIED state is promoted to PASS.
- Do not expose private keys, tokens, credentials, personal account identifiers or sensitive storage details in repository evidence. Use redacted references and fingerprints only.

## 5. Consolidated status

- L4M-01: PARTIAL — four allowlisted GitHub Actions artifacts plus 40 repository source files inventoried/read back; owner custody and complete package NOT VERIFIED.
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

The lineage gate is PASS (latest: 12/12). The six-artifact GitHub Actions inventory/manifest remains PASS for its declared scope (latest 19/19 manifest contract tests; all six source artifacts were read by the collector; the four newly selected/current lineage ZIPs and manifest output readbacks are independently documented). The separate exact-commit repository-file inventory is PASS for 40 explicitly allowlisted source objects (10/10 tests) with a downloaded/re-hashed output artifact. Reference reconciliation is PARTIAL PASS; some unrelated T0/T1/T2 and process references are excluded with reasons. This remains a bounded source inventory, not a complete L4 evidence package or owner custody proof. Next, finalize the control-to-source crosswalk for L4M-01–08 and L4M-10, and reconcile additional eligible Actions artifacts only from authoritative run metadata. Do not invent or silently substitute artifact IDs. Signature/negative verification and network-disabled offline verification remain downstream gates. Owner-supplied assertions remain limited to actual custody/control facts not machine-verifiable from approved sources, and final L4M-10 acceptance. No additional backup outside VPS/GitHub is required.

## 7. Limits

Register/evidence update. GitHub-hosted lineage and three-artifact inventory/manifest workflows were executed and independently read back. No source/schema/API/runtime/VPS/database/data changes, owner storage access, VPS evidence readback, signer/key/trust/provider operation, signature verification or offline verification occurred. No archive, cleanup, expiry, vacuum, compaction, backup expiry, replica removal or deletion. Option C — No Destructive Authority remains ACTIVE; `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.


## 8. Latest GitHub inventory increment — run 42837579509

- Allowlist expanded from three to four source artifacts in commit `5c9941112f24edb213c129a5962187461d8f4308`; allowlist blob: `d481ca0baaca9605cfda1e3ebb79e423b17ac876`.
- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42837579509; event `push`; branch `feature/t0-centralized-data-feeder-p1-20261101`; exact checked-out SHA `5c9941112f24edb213c129a5962187461d8f4308`; conclusion SUCCESS.
- Lineage job `129903788538`: SUCCESS, 12/12 tests PASS. Manifest job `129903905070`: SUCCESS, 19/19 tests PASS. Collector verdict `L4_ARTIFACT_MANIFEST=PASS`.
- The manifest contains four source artifacts: IDs `13546255148`, `13545287609`, `13771662067`, and `13774031418`; total member records: 57 (47 + 2 + 4 + 4). The newest source artifact is run `42836094887`, source SHA `b3a975e151241ba5d5116f49a8d00a056adf9fa4`, artifact ID `13774031418`, ZIP SHA-256 `801bbc22e1979b3e5260371a22db305d37ddd2bc6837aae3c00c99d60595abcf`, expiry `2026-11-17T14:38:12Z`; its bytes and four member hashes were independently re-read and matched.
- Output manifest artifact ID `13774501896`, name `t0-l4-artifact-manifest-42837579509`, 3,038 bytes, expiry `2026-11-17T14:46:58Z`, ZIP SHA-256 `6f121108e6e3f98b84327251bbc965c9d6a9a849f40b2bba6d6efb8b4eff88ba`. The ZIP was downloaded and independently re-hashed; its JSON member SHA-256 is `25b0db3de3fadd9504d030310b4c2243e18cdf4601bd88d2f41c2d1bf86ab07a`, matching the included `.sha256` sidecar.
- Output lineage artifact ID `13772649665`, name `t0-l4-minimum-lineage-42837579509`, 1,151 bytes, expiry `2026-11-17T14:46:58Z`, ZIP SHA-256 `9c4c7fabdf076abb1f719d32e28edf47b2bfaec91fa5528531d178c91a51bfc4`; independently downloaded and re-hashed. It records source SHA `5c9941112f24edb213c129a5962187461d8f4308` and 12/12 lineage tests PASS.
- The four-artifact manifest still does not contain the newly generated output artifacts from run `42837579509` itself; those are outputs and may only be considered as inputs in a subsequent run after exact verification. The manifest is a selected GitHub Actions artifact inventory, not the complete evidence package or owner custody proof.
- Aggregate L4-Minimum remains BLOCKED / NOT VERIFIED. Signature verification, network-disabled offline verification, owner custody/readback and L4M-10 owner disposition remain NOT VERIFIED / NOT STARTED.


## 9. Latest repository-source inventory — run 42914799884

- Workflow run [42914799884](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42914799884), source SHA `9442386151f3ff7ce7c699e00e617b8f4033aa3c`, overall SUCCESS.
- Lineage 12/12 PASS; artifact-manifest 19/19 PASS; repository-file inventory 10/10 PASS; total 41/41 contract tests.
- Repository-file inventory artifact ID `13807289589`, 4,477 bytes, expires `2026-11-17T22:27:57Z`, independently downloaded/re-hashed ZIP SHA-256 `40ec49a9ac0e0f3caa2883c6808cdf150151a0586f46b41901a37b4377fdf6f3`; JSON SHA-256 `a64553ba61414ea15c4d7c97bcd18f192df5b74094b193ae37f86dbd8ebc43b1` matches sidecar. Inventory: 40 unique files, 517,128 source bytes.
- Historical scope/lifecycle references resolved and added: T0 TSA/WORM read-only audit, P1.8.80 retention predecessor, P1.8.121 Option C ratification and P1.8.141 holistic lifecycle assessment. Their exact paths and Git blob SHAs are in the inventory. Separate PostgreSQL/provider/shared-data and generic lifecycle architecture docs are explicitly excluded with exact reasons.
- Aggregate L4-Minimum remains BLOCKED / NOT VERIFIED. No control is promoted by this inventory result.


## 10. Six-artifact allowlist and exact-source validation — run 42922670634

- Current allowlist has six entries: two P1.8.14 synthetic artifacts and four L4 lineage CI artifacts. Current allowlist blob: `0280cd7751c9660baec237242ca7aadef09205a6`; allowlist-update source commit: `0251a8cc7995903d2516fc84cc0a33b73ec02777`.
- Newly selected lineage artifact: run `42917935285`, artifact ID `13810187202`, source SHA `cab8122c94e8bb8f30052ae44483fb1ec7e4de65`, ZIP SHA-256 `db4e86e8b976304ae1daf90b14dc49cd2f4b149c9c2449867d796b515cd76d07`; exact four-member payload independently read and verified.
- Validation run [42922670634](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42922670634), exact source SHA `0251a8cc7995903d2516fc84cc0a33b73ec02777`, overall SUCCESS: lineage 12/12, repository inventory 10/10, artifact manifest 19/19; total 41/41.
- Manifest output `13813280057`: ZIP 3,269 bytes, SHA-256 `cc969116e687792321240e19cfa2125abfb8a884328e03715937746709b9b26d`; JSON SHA-256 `520fd49f87595cd39b412a0533ce579c8ead1456ad0361a712b52786bebad428`, sidecar matches; exactly six source artifacts, no self-inclusion.
- Lineage output `13813120888`: ZIP 1,151 bytes, SHA-256 `4686edd0c1e80f4a5793aa8d79ac4ce232ee64bd59cee2bfa633c14afd3d29d1`; source marker matches run SHA, 12 tests, PASS.
- Repository inventory output `13811119271`: ZIP 4,490 bytes, SHA-256 `ab8944fe9edb3446a50df1b8041743e93bb6bb628dee70956913c54b862222da`; JSON sidecar matches; source commit `0251a8cc7995903d2516fc84cc0a33b73ec02777`; 40 paths / 518,716 bytes.
- All three current-run output ZIPs were independently downloaded and re-hashed. These outputs remain outputs, not source evidence.
- Remaining historical lineage outputs are not bulk-selected. Their metadata places them in the same generated lineage CI class; all remaining historical ZIPs have not been independently payload-rehashed.
- No control disposition is promoted. L4M-01 remains PARTIAL; L4M-02 NOT VERIFIED; L4M-03–07 remain partial synthetic/design states; L4M-08 documentary pass only; L4M-09 owner-waived; L4M-10 not verified. Aggregate L4-Minimum remains BLOCKED / NOT VERIFIED.


## Owner governance update — Option C revoked (2026-11-11)

The owner explicitly revoked **Option C — No Destructive Authority** on 2026-11-11. Its former ACTIVE status in this document is historical and is superseded by this decision. Option C is now **REVOKED**; do not apply it as a blanket prohibition.

This governance revocation is not a blanket instruction to execute deletion or cleanup. Any specific destructive operation still requires a separately scoped plan identifying exact target/data class, operation, retention/impact, preconditions, verification, recovery/rollback and explicit approval. T0 canonical data, lease/fencing state, ledgers, audit/reconstruction/recovery evidence and owner custody records remain protected unless an exact operation is separately approved. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged. Revocation does not promote any L4 control or establish custody/signature/offline-verification assurance.
