# L4M-01 Evidence Custody — Intake Contract Reconciliation

Date: 2026-11-10
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`

## Scope

Documentary-only reconciliation of the L4M-01/L4M-03 owner intake contract against the controlling owner decision `D-2026-11-10-L4-EVIDENCE-CUSTODY-VPS-GITHUB-ONLY`.

## Finding and correction

The previous intake-contract revision contained superseded language in section A that required custody outside the T0/VPS and GitHub failure domains. That conflicted with the later explicit owner decision permitting VPS and GitHub as the only required custody locations.

The intake contract was corrected to state:
- Approved custody locations are the project VPS and/or project GitHub evidence storage.
- No external custody copy is required.
- If copies are claimed in both locations, each exact copy must be independently read back and checked against the canonical manifest digest.
- A single-location outage claim requires an accessible, verified copy in the remaining approved location.
- Simultaneous VPS + GitHub unavailability/loss is outside the recovery-availability claim.
- GitHub-hosted runners/artifacts remain within the GitHub failure domain.
- Exact package inventory, byte lengths, per-file SHA-256, canonical manifest digest, custody provenance, exact-object readback and L4M-03 anchor linkage remain required.

## GitHub record and readback

- Source branch HEAD before correction: `20a925421b3d9c5a9edd7876df3681045c25ab0e`.
- Updated intake contract: `docs/evidence/T0_L4M01_L4M03_OWNER_EVIDENCE_INTAKE_CONTRACT_2026-11-10.md`.
- Update commit: `71e99f18268efd35a8d025b238624845ba29935b`.
- Readback blob SHA: `914fb398bf6f0e4ef26ae6b706212c5f2969d1c1`.
- Branch HEAD after update: `71e99f18268efd35a8d025b238624845ba29935b`.
- Documentary readback checks: approved locations present; external copy not required; dual-location independent readback required; simultaneous outage excluded; L4M-01 remains NOT VERIFIED; superseded external-failure-domain wording absent.

## Verification and status

- Contract-to-owner-decision consistency: PASS (documentary readback only).
- L4M-01 evidence custody: NOT VERIFIED — no actual owner package inventory, manifest, provenance or exact-object readback evidence has been supplied.
- L4M-03: PARTIAL / NOT VERIFIED — no qualifying authenticated latest-head anchor and exact checkpoint evidence supplied.
- Aggregate L4-Minimum: BLOCKED / NOT VERIFIED.
- Tests/compile/dry-run: NOT RUN.
- GitHub Actions: NOT DISPATCHED; no workflow run or artifact claimed.
- VPS/SSH/runtime/DB/provider/key/permission/network operations: NOT PERFORMED.
- Destructive lifecycle operations: NOT PERFORMED; Option C — No Destructive Authority — ACTIVE.

## Next gate

Receive sanitized owner evidence for the exact existing VPS/GitHub custody object(s): opaque package ID, file inventory, byte lengths, per-file SHA-256, canonical manifest SHA-256, custody provenance, exact object/version references and readback records. Include the exact L4M-03 anchor object ID/digest and its custody/readback linkage.

Do not send secrets, credentials, private keys, private storage URLs, account IDs or access grants. Do not create a new package, perform readback, run tests, dispatch Actions, access VPS/DB/runtime, or perform destructive operations under this documentary correction.
