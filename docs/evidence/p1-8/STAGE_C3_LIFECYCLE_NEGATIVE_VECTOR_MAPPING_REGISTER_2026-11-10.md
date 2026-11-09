# Stage C.3 — Lifecycle Negative-Vector Mapping Register

Date: 2026-11-10  
Repository: kenznguyen/btcusdt-telegram-signals2  
Branch: feature/t0-centralized-data-feeder-p1-20261101  
Mapping baseline: P1.8.90 + P1.8.94  
Work type: read-only traceability analysis

## 1. Scope and counting method

This register reconciles the two source catalogues instead of extracting a denominator from either file alone:
- P1.8.90 deterministic executable specification: 47 distinct IDs; blob `8014ef15f347d255ee3d02f6f28847a02db27aff`.
- P1.8.94 traceability and race supplement: 70 distinct IDs; blob `4588379d8e101ee496bcf8927186c6c989e6c6a6`.
- IDs appearing only in P1.8.90: 17.
- IDs appearing only in P1.8.94: 40.
- Union: **87 distinct lifecycle negative-vector IDs**.

The 87 count is the deduplicated union of the explicit IDs in both source catalogues. It is not a count inferred from a regex scan of P1.8.94 alone.

The existing synthetic test modules were inspected statically. This register identifies nearest candidate test modules only where a domain relationship exists. A candidate is not a direct test mapping, coverage assertion or execution result. No direct executable binding to any lifecycle vector ID was found in the inspected test sources. GitHub code search returned no indexed matches for representative IDs, but that search is not exhaustive for this branch.

## 2. Vector-by-vector register

| Vector ID | Control family | Nearest existing test module(s), if any | Direct lifecycle test binding | Execution |
|---|---|---|---|---|
| NEG-ADP-01 | Adapter/backend residual | test_cross_process_atomicity.py; test_durability_recovery.py (adjacent-domain only) | NOT MAPPED | NOT_RUN |
| NEG-ADP-02 | Adapter/backend residual | test_cross_process_atomicity.py; test_durability_recovery.py (adjacent-domain only) | NOT MAPPED | NOT_RUN |
| NEG-ADP-03 | Adapter/backend residual | test_cross_process_atomicity.py; test_durability_recovery.py (adjacent-domain only) | NOT MAPPED | NOT_RUN |
| NEG-ADP-04 | Adapter/backend residual | test_cross_process_atomicity.py; test_durability_recovery.py (adjacent-domain only) | NOT MAPPED | NOT_RUN |
| NEG-ADP-05 | Adapter/backend residual | test_cross_process_atomicity.py; test_durability_recovery.py (adjacent-domain only) | NOT MAPPED | NOT_RUN |
| NEG-ADP-06 | Adapter/backend residual | test_cross_process_atomicity.py; test_durability_recovery.py (adjacent-domain only) | NOT MAPPED | NOT_RUN |
| NEG-ADP-07 | Adapter/backend residual | test_cross_process_atomicity.py; test_durability_recovery.py (adjacent-domain only) | NOT MAPPED | NOT_RUN |
| NEG-ADP-08 | Adapter/backend residual | test_cross_process_atomicity.py; test_durability_recovery.py (adjacent-domain only) | NOT MAPPED | NOT_RUN |
| NEG-ADP-09 | Adapter/backend residual | test_cross_process_atomicity.py; test_durability_recovery.py (adjacent-domain only) | NOT MAPPED | NOT_RUN |
| NEG-ADP-10 | Adapter/backend residual | test_cross_process_atomicity.py; test_durability_recovery.py (adjacent-domain only) | NOT MAPPED | NOT_RUN |
| NEG-ADP-11 | Adapter/backend residual | test_cross_process_atomicity.py; test_durability_recovery.py (adjacent-domain only) | NOT MAPPED | NOT_RUN |
| NEG-AMB-01 | Ambiguous outcomes | test_durability_recovery.py (adjacent-domain only) | NOT MAPPED | NOT_RUN |
| NEG-AMB-02 | Ambiguous outcomes | test_durability_recovery.py (adjacent-domain only) | NOT MAPPED | NOT_RUN |
| NEG-AMB-03 | Ambiguous outcomes | test_durability_recovery.py (adjacent-domain only) | NOT MAPPED | NOT_RUN |
| NEG-AUTH-01 | Authorization / identity | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-AUTH-02 | Authorization / identity | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-AUTH-03 | Authorization / identity | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-AUTH-04 | Authorization / identity | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-AVAIL-01 | Availability | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-COPY-01 | Copy lineage | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-EVD-01 | Evidence / verifier | test_event_signatures.py; test_provenance.py; test_trust_anchor.py (artifact trust only) | NOT MAPPED | NOT_RUN |
| NEG-EVD-02 | Evidence / verifier | test_event_signatures.py; test_provenance.py; test_trust_anchor.py (artifact trust only) | NOT MAPPED | NOT_RUN |
| NEG-EVD-03 | Evidence / verifier | test_event_signatures.py; test_provenance.py; test_trust_anchor.py (artifact trust only) | NOT MAPPED | NOT_RUN |
| NEG-EVD-04 | Evidence / verifier | test_event_signatures.py; test_provenance.py; test_trust_anchor.py (artifact trust only) | NOT MAPPED | NOT_RUN |
| NEG-EVD-05 | Evidence / verifier | test_event_signatures.py; test_provenance.py; test_trust_anchor.py (artifact trust only) | NOT MAPPED | NOT_RUN |
| NEG-EVD-06 | Evidence / verifier | test_event_signatures.py; test_provenance.py; test_trust_anchor.py (artifact trust only) | NOT MAPPED | NOT_RUN |
| NEG-EVD-07 | Evidence / verifier | test_event_signatures.py; test_provenance.py; test_trust_anchor.py (artifact trust only) | NOT MAPPED | NOT_RUN |
| NEG-EXC-01 | Emergency / policy / privacy | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-EXT-01 | Copy lineage | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-EXT-02 | Copy lineage | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-HOLD-01 | Holds | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-HOLD-02 | Holds | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-HOLD-03 | Holds | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-HOLD-04 | Holds | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-HOLD-05 | Holds | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-HOLD-06 | Holds | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-HOLD-07 | Holds | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-HOLD-08 | Holds | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-ID-01 | Authorization / identity | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-ID-02 | Authorization / identity | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-ID-03 | Authorization / identity | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-ID-04 | Authorization / identity | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-ID-05 | Authorization / identity | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-IDEM-01 | Idempotency | test_durability_recovery.py; test_reservation_lifecycle.py (adjacent-domain only) | NOT MAPPED | NOT_RUN |
| NEG-IDEM-02 | Idempotency | test_durability_recovery.py; test_reservation_lifecycle.py (adjacent-domain only) | NOT MAPPED | NOT_RUN |
| NEG-INV-01 | Inventory | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-MAN-01 | Manifest | test_provenance.py (artifact provenance only) | NOT MAPPED | NOT_RUN |
| NEG-MAN-02 | Manifest | test_provenance.py (artifact provenance only) | NOT MAPPED | NOT_RUN |
| NEG-MAN-03 | Manifest | test_provenance.py (artifact provenance only) | NOT MAPPED | NOT_RUN |
| NEG-MAN-04 | Manifest | test_provenance.py (artifact provenance only) | NOT MAPPED | NOT_RUN |
| NEG-MAN-05 | Manifest | test_provenance.py (artifact provenance only) | NOT MAPPED | NOT_RUN |
| NEG-OBS-01 | Observer | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-OBS-02 | Observer | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-POL-01 | Emergency / policy / privacy | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-PRIV-01 | Emergency / policy / privacy | No direct lifecycle mapping identified | NOT MAPPED | NOT_RUN |
| NEG-RACE-01 | Race/concurrency | test_cross_process_atomicity.py; test_shared_risk.py (different state machine) | NOT MAPPED | NOT_RUN |
| NEG-RACE-02 | Race/concurrency | test_cross_process_atomicity.py; test_shared_risk.py (different state machine) | NOT MAPPED | NOT_RUN |
| NEG-RACE-03 | Race/concurrency | test_cross_process_atomicity.py; test_shared_risk.py (different state machine) | NOT MAPPED | NOT_RUN |
| NEG-REC-01 | Recovery | test_durability_recovery.py; test_root_b_checkpoint.py; test_root_b_checkpoint_store.py (partial domain overlap) | NOT MAPPED | NOT_RUN |
| NEG-REC-02 | Recovery | test_durability_recovery.py; test_root_b_checkpoint.py; test_root_b_checkpoint_store.py (partial domain overlap) | NOT MAPPED | NOT_RUN |
| NEG-REC-03 | Recovery | test_durability_recovery.py; test_root_b_checkpoint.py; test_root_b_checkpoint_store.py (partial domain overlap) | NOT MAPPED | NOT_RUN |
| NEG-REG-01 | Registry | test_trust_lifecycle.py (trust registry only; not consumer/hold registry) | NOT MAPPED | NOT_RUN |
| NEG-REG-02 | Registry | test_trust_lifecycle.py (trust registry only; not consumer/hold registry) | NOT MAPPED | NOT_RUN |
| NEG-REG-03 | Registry | test_trust_lifecycle.py (trust registry only; not consumer/hold registry) | NOT MAPPED | NOT_RUN |
| NEG-REG-04 | Registry | test_trust_lifecycle.py (trust registry only; not consumer/hold registry) | NOT MAPPED | NOT_RUN |
| NEG-REG-05 | Registry | test_trust_lifecycle.py (trust registry only; not consumer/hold registry) | NOT MAPPED | NOT_RUN |
| NEG-REG-06 | Registry | test_trust_lifecycle.py (trust registry only; not consumer/hold registry) | NOT MAPPED | NOT_RUN |
| NEG-REG-07 | Registry | test_trust_lifecycle.py (trust registry only; not consumer/hold registry) | NOT MAPPED | NOT_RUN |
| NEG-STATE-01 | State machine | test_reservation_lifecycle.py (reservation states only) | NOT MAPPED | NOT_RUN |
| NEG-STATE-02 | State machine | test_reservation_lifecycle.py (reservation states only) | NOT MAPPED | NOT_RUN |
| NEG-STATE-03 | State machine | test_reservation_lifecycle.py (reservation states only) | NOT MAPPED | NOT_RUN |
| NEG-STATE-04 | State machine | test_reservation_lifecycle.py (reservation states only) | NOT MAPPED | NOT_RUN |
| NEG-STATE-05 | State machine | test_reservation_lifecycle.py (reservation states only) | NOT MAPPED | NOT_RUN |
| NEG-STATE-06 | State machine | test_reservation_lifecycle.py (reservation states only) | NOT MAPPED | NOT_RUN |
| NEG-STATE-07 | State machine | test_reservation_lifecycle.py (reservation states only) | NOT MAPPED | NOT_RUN |
| NEG-STATE-08 | State machine | test_reservation_lifecycle.py (reservation states only) | NOT MAPPED | NOT_RUN |
| NEG-STATE-09 | State machine | test_reservation_lifecycle.py (reservation states only) | NOT MAPPED | NOT_RUN |
| NEG-STATE-10 | State machine | test_reservation_lifecycle.py (reservation states only) | NOT MAPPED | NOT_RUN |
| NEG-T0-01 | T0 protection | test_t0_checkpoint_contract.py; test_root_b_checkpoint*.py (checkpoint contract only) | NOT MAPPED | NOT_RUN |
| NEG-T0-02 | T0 protection | test_t0_checkpoint_contract.py; test_root_b_checkpoint*.py (checkpoint contract only) | NOT MAPPED | NOT_RUN |
| NEG-T3-01 | T3 ledger separation | test_shared_risk.py; test_reservation_lifecycle.py (not lifecycle lineage proof) | NOT MAPPED | NOT_RUN |
| NEG-T3-02 | T3 ledger separation | test_shared_risk.py; test_reservation_lifecycle.py (not lifecycle lineage proof) | NOT MAPPED | NOT_RUN |
| NEG-TIME-01 | Trusted time | test_event_signatures.py; test_trust_lifecycle.py (no approved freshness policy) | NOT MAPPED | NOT_RUN |
| NEG-TIME-02 | Trusted time | test_event_signatures.py; test_trust_lifecycle.py (no approved freshness policy) | NOT MAPPED | NOT_RUN |
| NEG-TIME-03 | Trusted time | test_event_signatures.py; test_trust_lifecycle.py (no approved freshness policy) | NOT MAPPED | NOT_RUN |
| NEG-VER-01 | Evidence / verifier | test_event_signatures.py; test_provenance.py; test_trust_anchor.py (artifact trust only) | NOT MAPPED | NOT_RUN |
| NEG-VER-02 | Evidence / verifier | test_event_signatures.py; test_provenance.py; test_trust_anchor.py (artifact trust only) | NOT MAPPED | NOT_RUN |

**Register interpretation:** all 87 vectors are NOT MAPPED to a dedicated lifecycle test case in the inspected executable test sources, and all 87 remain NOT_RUN. The nearest-module column records domain adjacency, not coverage.

## 3. Existing tests: allowed interpretation

| Existing module | What it statically exercises | What it does not establish for lifecycle vectors |
|---|---|---|
| `test_cross_process_atomicity.py` | Synthetic concurrent shared-risk admission, atomic state operations and crash points | Hold/registry/adapter lifecycle fencing or independent no-mutation proof |
| `test_durability_recovery.py` | Synthetic file-backed state recovery, retry/idempotency and corruption fail-closed behavior | T0/T3 full copy/recovery lineage or lifecycle mutation oracle |
| `test_event_signatures.py` | Signature verification and trust/revocation edge cases | Trusted-time policy and hold/authorization registry semantics |
| `test_generator.py`, `test_provenance.py` | Deterministic synthetic fixture generation and evidence provenance | Exact lifecycle object inventory or per-object mutation proof |
| `test_reservation_lifecycle.py`, `test_shared_risk.py` | Paper reservation state and CORE/AI shared risk admission | Lifecycle request/hold state machine or CORE/AI ledger disposition authority |
| `test_t0_checkpoint_contract.py`, `test_root_b_checkpoint.py`, `test_root_b_checkpoint_store.py` | Selected checkpoint encoding, persistence, crash/reopen and tamper contracts | Full V08 seal/watermark/correction and restore-chain qualification |
| `test_trust_anchor.py`, `test_trust_lifecycle.py`, `test_trusted_root_pin.py` | Artifact attestation trust, root pinning, trust lifecycle and revocation | Independent lifecycle mutation verifier or effective GitHub permissions |
| `test_workflow_archive_contract.py` | Static assertions about workflow source/archive contract | Effective repository, branch, environment, runner, OIDC or provider permission enforcement |

## 4. Uncovered execution prerequisites

P1.8.90 specifies TEST-01–08 as open. Based on the static evidence reviewed, the required prerequisites remain:

| ID | Prerequisite | Current disposition |
|---|---|---|
| TEST-01 | Test framework and runner contract | OPEN / NOT ESTABLISHED |
| TEST-02 | Synthetic storage adapters | OPEN / NOT ESTABLISHED |
| TEST-03 | Isolation proof preventing access to T0–T4/VPS/real credentials/real ledgers/backups/external recipients | OPEN / NOT ESTABLISHED |
| TEST-04 | Independent oracle outside executor's mutable trust boundary | OPEN / NOT ESTABLISHED |
| TEST-05 | Deterministic concurrency scheduler/barriers and fault points | OPEN / NOT ESTABLISHED |
| TEST-06 | Artifact signing, provenance and source/spec/run binding | Existing workflow has adjacent Sigstore machinery; lifecycle-run binding NOT ESTABLISHED |
| TEST-07 | Synthetic-only cleanup and containment proof | OPEN / NOT ESTABLISHED |
| TEST-08 | Separate explicit authorization for exact test scope | NOT GRANTED by this documentary mapping approval |

No code or test harness should be implemented or run until these prerequisites have evidence and the test scope is separately authorized. Stage C approval is not inferred as permission to touch canonical systems or execute destructive operations.

## 5. LDA-08 permission evidence

Branch-protection API read returned HTTP 403 in Stage C.1. The repository rulesets query returned an empty list, but that does not replace branch-protection evidence. This register does not change LDA-08.

To resolve this single metadata gap, the GitHub integration would need repository **Administration: read-only** (or equivalent branch-protection/rulesets read permission). No such permission grant is asserted here. No request to broaden write permissions is made.

## 6. Status and execution boundary

- LDA-07: **NOT RUN**; 87/87 vectors remain NOT_RUN.
- Direct test mapping: **0 established** in inspected test sources; this is a static mapping result, not a runtime test count.
- Nearest-domain candidate modules: listed as contextual references only; no coverage credit.
- TEST-01–05 and TEST-07: OPEN / NOT ESTABLISHED.
- TEST-06: partial adjacent infrastructure only; lifecycle binding NOT ESTABLISHED.
- TEST-08: separate exact test authorization not granted.
- LDA-06: PARTIAL / NOT VERIFIED; static source crosswalk does not prove runtime/copy completeness.
- LDA-08: HOLD / NOT VERIFIED.
- V07/V08/RET-10/Restore remain BLOCKED or NOT VERIFIED as previously recorded.
- Option C remains active. No archive, deletion, cleanup, expiry, compaction, vacuum, backup/replica removal, export mutation or irreversible transition.

No tests, compile, dry-run, fault injection or GitHub Actions were run/dispatched. No secret values read. No runtime/VPS/database/provider/recipient/backup/replica probes. No permission, secret, workflow, runner, source, schema, adapter, runtime or data changes. No destructive operation.

**Stage C.3 DOCUMENTARY REGISTER COMPLETE — LDA-07 NOT RUN — NO PASS PROMOTION.**
