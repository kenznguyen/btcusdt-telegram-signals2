# D-2026-11-10 — L4 Evidence Custody Scope: VPS and GitHub Only

Date: 2026-11-10
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Authority: explicit owner direction in the 2026-11-10 project conversation
Status: **OWNER-DIRECTED STORAGE-SCOPE DECISION — DOCUMENTARY ONLY**

## 1. Decision

The project does not require or plan an additional backup/custody copy outside the existing VPS and GitHub environments for L4-Minimum evidence.

Permitted evidence-custody locations for this scope are:
- the project VPS; and
- the project GitHub repository / GitHub Actions evidence storage, subject to the existing artifact-retention limits and exact-object readback requirements.

No third-party object store, external backup provider, separate paid custody service, or additional off-platform backup is required by this decision.

## 2. Assurance consequences

- This decision narrows the L4M-01/L4M-03 custody-location requirement; it does not waive package inventory, exact-byte SHA-256 manifests, custody provenance, authenticated latest-head anchoring, signer separation, integrity checks, or readback evidence.
- Where copies exist in both VPS and GitHub, each copy must be identified by exact object/version and independently checked against the canonical manifest digest. A successful upload is not readback verification.
- The remaining location must be used for readback when the other location is unavailable, where the required copy is actually present and accessible.
- **Simultaneous unavailability or loss of both VPS and GitHub is outside the accepted recovery-availability claim.** No evidence may claim recovery under that combined outage.
- A GitHub-hosted runner remains within the GitHub service/failure domain. It must not be described as an independent third-party custody provider.
- This decision does not establish that the VPS and GitHub have independent credentials, administrators, regions, providers, or failure domains beyond what is actually evidenced.
- L4M-03 freshness remains UNKNOWN / NOT VERIFIED until an authenticated latest-head anchor is bound to the exact checkpoint and verified under the revised custody scope.
- L4M-04 offline verification, L4M-05 readback/recovery, L4M-06 trust lifecycle, and L4M-07 tamper-evident history retain their substantive requirements, with custody location limited to VPS/GitHub.

## 3. Explicit non-decisions

This decision does not:
- declare L4M-01 or L4M-03 PASS;
- freeze an L4 evidence baseline or issue L4M-10 owner acceptance;
- authorize new storage provisioning, VPS access, SSH, runtime/DB probes, GitHub permission changes, provider calls, key/signing operations, workflow dispatch, or tests;
- authorize data deletion, cleanup, archive, expiry, compaction, vacuum, backup expiry, replica removal, or any other destructive lifecycle operation;
- alter T0 canonical SQLite, T0's independent asset boundary, PostgreSQL PARKED status, paper-only operation, or `AI_EXECUTION_ENABLED=false`.

## 4. Status

- Storage-location policy: **OWNER-DIRECTED — VPS + GITHUB ONLY**.
- Additional external backup: **NOT REQUIRED**.
- L4M-01: **NOT VERIFIED** pending exact inventory, manifest, custody and readback evidence under this scope.
- L4M-03: **PARTIAL / NOT VERIFIED**; authenticated latest-head anchor and exact-object freshness evidence remain outstanding.
- Aggregate L4-Minimum: **BLOCKED / NOT VERIFIED**.
- Option C — No Destructive Authority: **ACTIVE**.

This is a documentary owner-scope decision only. No storage, runtime, network, permission, data, key, test, workflow or destructive operation was performed.
