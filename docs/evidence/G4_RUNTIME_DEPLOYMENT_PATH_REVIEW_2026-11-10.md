# G4 Runtime Deployment Path Review — Read-Only Probe Delivery

- Date: 2026-11-10
- Repository: kenznguyen/btcusdt-telegram-signals2
- Branch: feature/t0-centralized-data-feeder-p1-20261101
- Review baseline: a6d939252f1651c4f8f5478bf49581824cc67cc9
- Operation class: READ-ONLY REPOSITORY / WORKFLOW REVIEW
- Scope: determine whether the approved G4 read-only probes have a safe existing installation and invocation path to the VPS.
- No SSH/VPS connection, credential/secret read, workflow dispatch, service operation, file installation, database access, or runtime change occurred.

## 1. Decision

**BLOCKED — no verified deployment path for the new G4 probes.**

G4a/G4b CI contracts pass, but they run only on disposable GitHub-hosted runners. The current SSH workflow can invoke the already-installed fixed forced command; it does not deploy or update that command. The current forced-command script does not dispatch allowlisted subcommands. The repository does not establish the effective installed root-owned script path or a controlled update mechanism.

Do not use SCP, generic SSH shell, authorized_keys edits, sudo install, or an improvised remote command to work around this gap.

## 2. Evidence

| Evidence | Exact blob / SHA | Finding |
|---|---|---|
| ops/ssh/t0-readonly-preflight.sh | 39de5aa7602cdf7dc301ff6bc65a68fad417ea84 | Fixed read-only snapshot: host/user, checkout SHA, Feeder PIDs, port 8788 listener scope, SQLite integrity. It does not inspect lease owner/generation/expiry, candle watermarks, authenticated Candle API responses, or detailed Flask health. It does not parse SSH_ORIGINAL_COMMAND or dispatch subcommands. |
| .github/workflows/t0-manual-validation.yml | b776c2ddf33874dce0dfe7c6ed71562b30d5df62 | The SSH step connects to $SCW_SSH_USER@$SCW_SSH_HOST without a remote command; the installed forced command runs. No SCP/rsync, script-install, deployment, root command, or service mutation step exists. |
| docs/evidence/T0_DEPLOYMENT_CONFIGURATION_HEALTH_LAUNCH_INVENTORY_2026-11-10.md | 852998a95f347d58657237ba8a88a208bba54c3c | Repository inventory found no production Feeder/API systemd units or versioned deployment manifest. It found no established production launch target/provider registration for Flask app.py. This is repository evidence, not proof of host absence. |
| docs/evidence/T0_OWNER_READONLY_DEPLOYMENT_EVIDENCE_PROTOCOL_2026-11-10.md | 56ae166ae90770a775220f71dacfe2498080839f | Defines a bounded owner-supplied deployment evidence protocol; it does not grant agent SSH or installation authority. |
| G4a/G4b workflow run | 42824628084, source a6d939252f1651c4f8f5478bf49581824cc67cc9 | G4 CI PASS on disposable runner only; SSH and manual VPS acceptance jobs were skipped. |

## 3. Missing operational facts

1. Exact effective forced-command entry and installed root-owned script path on the VPS.
2. Who/what currently owns the script update path and how its integrity/permissions are verified.
3. Whether a dedicated Flask Feeder health process exists on the VPS. The repository has no established production launcher/provider registration; do not guess its port.
4. A secure source for the Candle API Bearer token usable by the read-only probe. The current SSH workflow passes host, port, username, private key, known-hosts and key passphrase; it does not pass MARKET_DATA_TOKEN. Never place the token in a command argument, URL, shell history, log, or artifact.
5. Whether the deployed checkout contains the G4 probe code. The last known preflight remote SHA is historical and does not establish current VPS checkout contents.

## 4. Safe target design (not implemented or installed)

If separately approved, retain a single root-owned forced-command dispatcher and the existing pinned-key/host-key controls. The dispatcher should:

- Preserve the current empty-command behavior as the existing read-only preflight.
- Read only exact SSH_ORIGINAL_COMMAND selector strings from a small hard-coded allowlist, e.g. t0-runtime-snapshot-v1; reject every other command and every argument.
- Never invoke bash -c, eval, arbitrary paths, user-supplied SQL, or a general shell.
- Run fixed, root-owned, integrity-checked read-only probe code with fixed DB/API paths.
- Open SQLite with URI mode=ro, enforce PRAGMA query_only=ON, and issue only SELECT/PRAGMA reads. Never acquire, heartbeat, release, migrate, vacuum, checkpoint, or create schema.
- Use an approved secret source for the Bearer token without echoing or serializing it. If no safe token source is established, report authenticated API verification as NOT VERIFIED.
- Treat detailed Flask health as NOT VERIFIED until a deployed listener and provider registration are proven.
- Emit a versioned, sanitized machine-readable result and exact deployed source/script SHA; never emit raw owner IDs, tokens, environment contents, or secret paths.
- Keep all actions read-only: no restart, install, file write, data mutation, T1 activation, or trading order.

This is a target design only. It is not permission to edit authorized_keys, install a dispatcher, change SSH restrictions, or run a new remote command.

## 5. Current status

| Gate | Status |
|---|---|
| G1/G2/G3 isolated CI | PASS |
| G4a SQLite probe contracts | PASS |
| G4b HTTP probe contracts | PASS |
| Existing SSH preflight snapshot | Historical PASS at run 42814402445 only |
| G4 live VPS runtime | NOT VERIFIED |
| Detailed Flask health listener | NOT VERIFIED |
| Secure API token source for probe | NOT VERIFIED |
| Probe installation/update path | BLOCKED |
| Generic SSH shell / SCP / authorized_keys changes | NOT AUTHORIZED |

## 6. Next step

Continue repository-only review and preserve the current forced-command boundary. Before any VPS installation or invocation, obtain separate explicit approval for an exact installation mechanism and prove the root-owned update path and secure token source. Do not convert G4 CI PASS into VPS runtime PASS.
