# Dual Ledger — Manual Owner Attestation v1 (test/CI)

Date: 2026-11-13 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/core-operational-proof-20261112`  
Implementation source SHA: `513978ef314e326195d2ea82ce65c480a27d3b11`  
Disposition: **CODE + DISPOSABLE CI PASS; REAL PROVENANCE AND PRODUCTION BOOTSTRAP BLOCKED**

## 1. Approved scope

Owner approved a dedicated Manual Owner Attestation mechanism for Dual Ledger, limited to tests and GitHub Actions. This approval excludes cryptographic signatures, production database creation, VPS operations, T0 changes, Runner/One-shot execution and order submission.

No real funding/equity statement was supplied or attested in this increment. The attestation object exercised by CI is synthetic fixture data only.

## 2. Contract

Added `paper_execution/owner_attestation.py` and required its separate evidence file in the Dual Ledger bootstrap manifest.

The closed v1 document binds:
- checked-out source SHA;
- funding snapshot ID and exact-byte SHA-256;
- equity cutover snapshot ID and exact-byte SHA-256;
- review timestamp constrained to the evidence/cutover time window;
- fixed review statement and fixed non-claims list.

The loader rejects unknown/missing fields, unsupported version/type/scope, non-owner declaration role, mismatched source/snapshot/hash, invalid timestamps, malformed or duplicate-key JSON, missing/symlinked/oversized files and exact-byte digest mismatch. Bootstrap validates this record before creating its temporary SQLite database. A failed attestation cannot publish or create the target database.

The result explicitly reports:
- `attestationStatus=MANUAL_OWNER_ATTESTATION_PRESENT`;
- `ownerIdentity=NOT_AUTHENTICATED`;
- `sourceAuthenticity=NOT_VERIFIED`;
- `factualTruth=NOT_VERIFIED`;
- `completeness=NOT_VERIFIED`;
- `freshness=NOT_VERIFIED`;
- `privilegedActionAuthorization=NOT_GRANTED`;
- `cryptographicSignature=NOT_USED`.

This is a bounded human declaration record, not identity authentication, source issuer authentication, factual verification, completeness proof, freshness proof, privileged authorization or a cryptographic signature.

## 3. D06 / D09 policy alignment

- D06: manual Owner attestation is the initial policy; it binds a bounded claim but does not prove factual truth or completeness. Autonomous issuer authenticity remains deferred.
- D09: an authenticated GitHub action/commit may be recorded as `PLATFORM_ATTRIBUTED_OWNER_ACTION`. This is platform attribution of the repository action only. It is not a cryptographically signed Owner attestation and does not grant privileged bootstrap authorization or trust-administration rights.
- Review attestation, privileged-action authorization and trust administration remain separate.
- D07 still requires independently defined expected-population enumeration and reconciliation for completeness claims. The attestation does not close this requirement.

## 4. TDD and CI evidence

- RED: run [43442795041](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43442795041), source `cdb0dcfa480cfe125c181ed2817774832ada0647`, failed at compile because the new `owner_attestation.py` module did not yet exist. This was the expected missing-implementation RED.
- Intermediate correction: run [43443340826](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43443340826), source `2fdab4a77e2c29de0309bfd2910d92defe305529`, exposed invalid synthetic review timestamps in the bootstrap fixture. The fixture was corrected to place review time within the declared evidence/cutover window.
- GREEN at source `dfb085d76317ac4408c2804b032fc78715aa1449`:
  - Attestation contract workflow [43443499190](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43443499190): compile PASS; attestation tests 11/11 PASS; bootstrap tests 13/13 PASS; full PaperLedger regression 440/440 PASS.
  - Bootstrap workflow [43443499354](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43443499354): compile PASS; bootstrap tests 13/13 PASS; full PaperLedger regression 440/440 PASS.
- Final explicit identity-boundary assertion at source `513978ef314e326195d2ea82ce65c480a27d3b11`:
  - Bootstrap workflow [43444319736](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43444319736): compile PASS; bootstrap tests 13/13 PASS; full PaperLedger regression 440/440 PASS (135.282s); job SUCCESS.
  - Artifact ID `14046847706`, name `dual-ledger-bootstrap-proof-513978ef314e326195d2ea82ce65c480a27d3b11`, 10,082 bytes, GitHub-reported ZIP digest `sha256:b476a14a78aeda98be2525eb57c3cefe9227b7ef22affb860f03d95a101537c1`, expires 2026-11-20T14:36:25Z. Payload digest has not been independently recomputed.
  - Manual attestation workflow [43444319783](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43444319783): job `131950976034` SUCCESS; compile PASS, attestation tests 11/11 PASS, bootstrap tests 13/13 PASS, full PaperLedger regression 440/440 PASS (138.383s). Artifact ID `14047761865`, name `dual-ledger-owner-attestation-proof-43444319783`, 10,311 bytes, GitHub-reported ZIP digest `sha256:d540ea1fcb6a4a9173dca135b1be199530dd277c796a842a3dfd22f5b2d25138`, expires 2026-11-20T14:36:25Z. Payload digest has not been independently recomputed.

## 5. Status and boundaries

- Manual Owner Attestation v1 schema/validator: **PASS**.
- Bootstrap integration and fail-before-create test: **PASS**.
- Disposable CI at exact implementation source `513978ef314e326195d2ea82ce65c480a27d3b11`: **PASS** (13 focused bootstrap tests; 440 full PaperLedger tests).
- Real Owner identity authentication: **NOT VERIFIED**.
- Real funding/equity source authenticity, factual truth and completeness: **NOT VERIFIED**.
- Real Owner review/attestation of funding/equity evidence: **NOT PROVIDED / NOT VERIFIED**.
- Privileged production bootstrap authorization: **NOT GRANTED**.
- Production bootstrap: **BLOCKED / NOT APPROVED**.

No VPS, production database, T0, Runner, One-shot, exchange credentials or real orders were touched. All databases used in CI are disposable temporary SQLite fixtures. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.

## 6. Next step

Keep production bootstrap blocked. Any real bootstrap requires the actual funding/equity evidence, independently defined population and reconciliation, a separately captured bounded manual Owner review, and a separate explicit production-bootstrap approval. No cryptographic key or signature implementation is implied by this increment.
