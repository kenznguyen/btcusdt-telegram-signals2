# L4M-01 / L4M-03 Owner Evidence Intake — Minimal Submission Contract

Date: 2026-11-10
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Status: INTAKE SPECIFICATION ONLY — NO EVIDENCE RECEIVED OR VERIFIED

## Purpose

Make the next owner evidence handoff precise without asking for credentials, private keys, public storage URLs, account identifiers or access to owner systems. This is a submission contract, not an authorization to create, move, sign, read back, test or mutate evidence.

## A. L4M-01 — independent custody package

Supply only sanitized metadata and evidence references for an already-existing owner-controlled copy:

1. **Custody boundary:** identify the storage class/provider generically (for example, owner-controlled offline disk or separately controlled object storage); state explicitly that it is outside both T0/VPS and GitHub failure domains. Do not disclose account ID, bucket name, public URL, precise private location or credentials.
2. **Package identity:** opaque package ID, creation timestamp (UTC), package format/version, total file count and total byte count.
3. **Manifest:** SHA-256 manifest for every retained file, plus the manifest's own SHA-256. Redact sensitive filenames if necessary, but preserve stable opaque item IDs and counts.
4. **Custody provenance:** who/which owner-controlled role placed the copy, when, and how the custody event is evidenced. Do not include personal identifiers.
5. **Readback record:** date, environment class, verifier/tool version, manifest digest, files/bytes checked, result and exit status. A claimed readback must identify the exact package digest.
6. **Availability statement:** distinguish what has actually been observed from planned capability. Do not claim T0-outage, GitHub-outage or simultaneous-outage availability unless such a scenario has already been safely and separately authorized and observed.
7. **Latest-head anchor linkage:** include the exact L4M-03 anchor object ID and digest in the same custody inventory. A statement that the copy is “backed up” is insufficient.

A GitHub repository copy, Actions artifact, CI log, or VPS/T0 copy alone does not satisfy the independent failure-domain requirement.

## B. L4M-03 — exact object and freshness anchor

Supply sanitized metadata for an already-existing, owner-authorized checkpoint/anchor. If no such object exists, state `NOT AVAILABLE`; do not generate one for this intake.

1. Checkpoint object ID and exact byte length.
2. Raw source-byte SHA-256 and canonical payload SHA-256, if both are defined; never substitute one for the other.
3. Schema/profile identifier and version.
4. Dataset identity and scope (symbol/timeframes/range), without disclosing credentials.
5. Sequence/generation and the precise semantics/authority of that field.
6. Signature envelope algorithm/profile, signer fingerprint (not key material), signature byte digest and verification result, if an existing signed object exists.
7. Latest-head anchor object ID, exact digest, issuer/authority class, monotonicity rule and custody inventory entry.
8. Evidence that the anchor is retained/readable in the approved VPS and/or GitHub custody location; reference the same L4M-01 package and exact readback record. No external custody copy is required.
9. Rollback assessment: identify the older checkpoint digest and anchor digest and the observed decision. If no approved test/observation exists, mark `NOT RUN`; do not perform a replay or rollback test.

Sequence/generation alone cannot establish freshness. If anchor authenticity, latest-head authority, monotonicity, approved-location custody or exact readback is absent, freshness is `UNKNOWN / NOT VERIFIED`. Simultaneous VPS+GitHub unavailability is outside the recovery claim.

## C. Required response vocabulary

Use only:
- `AVAILABLE — REFERENCE SUPPLIED`
- `NOT AVAILABLE`
- `NOT APPLICABLE — REASON`
- `NOT RUN`
- `REDACTED — SENSITIVE DETAIL WITHHELD`

Do not convert missing evidence into an inferred PASS. A reference is not itself verification; exact bytes/digests and readback evidence must support the claim.

## D. What must not be supplied or performed

- No passwords, tokens, API keys, private keys, seed phrases, database URLs, authorization headers, account IDs or public IPs.
- No private storage URLs or access grants.
- No SSH/VPS access, runtime/API/DB probes, signing, key generation/export/import/rotation, provider calls, workflow dispatch, tests, fault injection or outage simulation.
- No deletion, cleanup, expiry, archive, compaction, vacuum, backup expiry or replica removal.
- No changes to T0 canonical data, schema, write path or runtime.

## E. Acceptance boundary

L4M-01 cannot PASS until the owner-controlled VPS/GitHub custody location(s), complete manifest, custody provenance and exact readback are evidenced, including the separately authenticated latest-head anchor in the same custody package. No copy outside VPS and GitHub is required. Any single-location outage claim must be supported by a verified copy in the remaining location; simultaneous VPS+GitHub outage recovery is outside scope.

L4M-03 cannot PASS until the exact checkpoint is cryptographically bound and freshness is evaluated against the separately authenticated latest-head anchor retained/read back from an approved VPS/GitHub location. Missing or unverifiable anchor means freshness UNKNOWN, not PASS.

L4M-01 and L4M-03 remain separate controls with shared evidence references. Neither control is promoted by this intake specification.

## F. Current disposition

- L4M-01: NOT VERIFIED — no owner custody package/readback evidence supplied.
- L4M-03: PARTIAL — synthetic/design only; no qualifying T0 signed checkpoint/latest-head anchor evidenced.
- Aggregate L4-Minimum: BLOCKED / NOT VERIFIED.
- Option C — No Destructive Authority: ACTIVE.
- Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders.

Documentary-only. No evidence was received, no owner storage was accessed, and no test or operational action was performed.
