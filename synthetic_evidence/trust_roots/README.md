# P1.8 Sigstore trust-root history and evidence retention

## Baseline

The initial historical root snapshot was captured by P1.8.15 run
[42305379372](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42305379372)
from source SHA `1f002a1769504d00c0894d67b5e1f35f46c97414`.

- Trusted-root SHA-256:
  `65ca537f6ed8a47fd0e560c421baa1f6c1efb8b25fc200d8c5c02c0e92eb2b9c`
- Historical snapshot: `2026-11-07-trusted_root.jsonl.gz.b64`
- Baseline metadata: `baseline-2026-11-07.json`
- Trust pin: `../trusted_root_pin.py`

The gzip+base64 encoding is used to keep the historical JSONL root compact in Git.
The verifier decodes it and checks the exact raw-byte SHA-256 before parsing it.

## Rotation protocol — fail closed

Every P1.8 synthetic workflow:
1. Obtains a fresh root with `gh attestation trusted-root`, which uses GitHub CLI's TUF trust path.
2. Compares all known TLog, CTLog, certificate-authority and timestamp-authority identities with the checked-in baseline.
3. Checks the exact root-byte digest against the reviewed pin.
4. Blocks the build if the bytes or trust-material inventory change. It emits a rotation diff; it never changes the pin automatically.
5. Captures a timestamped snapshot linked to the previous snapshot digest. The archive job appends it to `docs/evidence/p1-8/trust-root-snapshot-chain.json` and commits the evidence on the existing branch.

For an actual rotation:
- Stop and inspect the generated diff and the authenticated TUF update path.
- Obtain the candidate root through the verified GitHub CLI/TUF client, not an arbitrary URL or copied key.
- Review added/removed keys, certificate chains, validity windows and official Sigstore/GitHub security notices.
- Preserve the previous compressed root and pin under a new versioned filename; do not overwrite historical evidence.
- Update the active root file, `trusted_root_pin.py`, and baseline metadata in a dedicated source commit. The new snapshot must point to the prior chain head.
- Rerun the full synthetic suite and offline verification. Do not accept the new pin unless the exact source SHA and independent runner both pass.

A changed root is not automatically malicious: it may be a planned rotation. It is still a trust change and must remain BLOCKED until reviewed and explicitly repinned.

## Revocation semantics

The Sigstore trusted-root JSONL is a set of trust materials, not a complete per-certificate revocation feed. GitHub documents that an offline verifier cannot learn whether material was revoked after its root snapshot was captured.

This project therefore reports:
- `NOT_CHECKED_OFFLINE` for offline verification without separately authenticated revocation evidence.
- `REVOCATION_STATUS_NOT_EXPOSED` when using the online TUF root but the CLI result does not expose an explicit per-certificate revocation verdict.
- `REVOKED / REJECT` when an authenticated external revocation record is supplied to the policy layer.
- `REVIEWED_CLEAR_AUDIT_ONLY` for a review record whose authenticity is not independently verified. This does not authorize admission and does not support a "not revoked" claim.

Never translate absence of revocation evidence into "not revoked". If a revocation is suspected, block use pending independent review. Historical signatures may remain cryptographically verifiable under an older root; that is not proof that their signing identity remains acceptable today.

## Long-term evidence retention

Each successful run:
- uploads the signed evidence and verification artifacts with `retention-days: 90` (subject to repository retention policy);
- creates a SHA-256 retention manifest covering the subject ZIP, Sigstore bundle, root snapshot, test log and provenance;
- independently rechecks every retained payload before committing the subject ZIP, bundle, sidecar and manifest under `docs/evidence/p1-8/<source-sha>/`;
- appends the trust-root snapshot to the hash-chained snapshot history.

Git history is durable repository storage, but **not WORM**: an administrator can rewrite or delete repository history. For higher assurance, periodically export the retained directory and its manifest to a separately controlled offline medium or independent storage account, then verify the manifest there. That external copy is not automated or claimed by this milestone.

