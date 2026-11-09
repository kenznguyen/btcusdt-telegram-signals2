# Project Session Handoff

Updated: 2026-11-09 UTC  
Active branch: \`feature/t0-centralized-data-feeder-p1-20261101\`

## Latest completed work — P1.8.22 / P1.8.23

- P1.8.22: existing synthetic Ed25519 verifier and negative tests were audited; no duplicate signing helper was retained.
- P1.8.23: added a file-backed synthetic SQLite test for duplicate observer ACK, process death after durable checkpoint write/before checkpoint ACK, reopen, duplicate ACK replay, and idempotent checkpoint ACK recovery.
- Final source SHA tested by CI: \`082cc68b14148829c01fc63558f6781fa006756b\`.
- GitHub Actions run: [42557957929](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42557957929), SUCCESS, 3/3 jobs PASS, 162/162 tests PASS.
- Primary artifact: \`13648297207\`; independent verification artifact: \`13648187759\`; both expire \`2026-11-16T03:43:37Z\`.
- Attested bundle SHA-256: \`283f807f92850893b7cb0aa180b84c1c7673590f754837d94258c0559984143b\`.
- Evidence record: \`docs/evidence/p1-8/082cc68b14148829c01fc63558f6781fa006756b/P1.8.23.md\`.
- Workflow archive commit: \`50f06a49ea391674b31cc561ade0b00363bd8a89\`.
- Evidence record commit: \`90409fc1e0bb30ad4aceea31c8b58c5eec991f01\`.

## Fault-vector status

All 13 catalogued fault/negative vectors now have executable synthetic test coverage: 13/13 PASS, 0 PARTIAL, 0 MISSING. This includes invalid signature, unknown signing key, revoked signing key, checkpoint boundary, recovery, and Root B duplicate ACK/crash.

Production evidence remains NOT VERIFIED for all 13 vectors. The file-backed SQLite adapter is a synthetic reference model only; no production Root B, key-management, database, feeder, exchange, ledger, strategy, or runtime integration has been performed.

## Operating boundaries

- \`AI_EXECUTION_ENABLED=false\`; no live orders.
- Do not modify T0/T1, VPS, DB, Feeder, production runtime, exchange, ledger, strategy, or risk engine without separate explicit approval.
- No PR or merge was created.
- Continue to use GitHub Actions for validation and retain evidence on the existing branch.
- Any future production integration or change to assurance claims requires separate explicit approval.
