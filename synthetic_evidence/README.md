# Synthetic Evidence Fixture Generator (P1.8)

Standalone, standard-library-only generator for deterministic **synthetic** paper-evidence fixtures. It has no account database, exchange, network, cloud-provider, credential, or runtime integration.

## Local use

\`\`\`bash
python -m unittest synthetic_evidence.test_generator -v
python -m py_compile synthetic_evidence/*.py
python -m synthetic_evidence \\
  --seed 0000000000000000000000000000000000000000000000000000000000000000 \\
  --namespace 2e4e8f6e-9a3c-5d72-9b4a-8a4f6b2d1c30 \\
  --base-time-utc 2026-11-07T00:00:00.000Z \\
  --events 1000 \\
  --source-sha <full-git-commit-sha> \\
  --out ./synthetic-evidence-output
\`\`\`

The output directory must not already exist. It contains a run descriptor, event JSONL, immutable local segment files, pre-upload manifest JSONL, measurement summary, separate negative fault vectors and SHA-256 file manifest. Re-running with the same descriptor and source/build identity into a different empty directory must produce byte-identical output files.

## Contract and limitations

- HMAC-SHA-256 PRF framing and UUIDv5 identities follow the P1.7 deterministic profile. The seed is synthetic/public reproducibility material, not a credential.
- Canonical JSON implements the project's strict RFC 8785-compatible subset: UTF-8, UTF-16 property ordering, duplicate-key rejection on parse, safe integers only, and no floating-point values. Full RFC 8785 conformance and independent cross-language vectors remain NOT VERIFIED.
- Event and manifest hashes are generated. Event signatures and signed storage receipts are intentionally absent; local manifests are explicitly unsigned. No private key is created or persisted.
- Scenario templates are deterministic and stream-specific. Event-class target weights are reported separately from actual scenario-driven counts.
- Local replay is labeled \`LOCAL_REPLAY_SIMULATION\`; it does not prove Root B process/admin/provider independence or provider durability.
- No benchmark result is a production workload estimate. Provider tests, storage qualification, persistent capture, and runtime integration are out of scope.
