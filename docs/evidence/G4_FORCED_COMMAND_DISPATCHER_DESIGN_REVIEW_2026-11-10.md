# G4 Forced-Command Dispatcher — Design Review

- Date: 2026-11-10
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Repository baseline: `d0209b29b5d77f927c2d1bc74034167576a562d9`
- Operation class: REPOSITORY-ONLY DESIGN REVIEW
- Result: **DESIGN DEFINED / IMPLEMENTATION BLOCKED**
- No VPS/SSH connection, secret access, workflow dispatch, source-code modification, runtime operation, or database access occurred.

## 1. Decision

A single root-owned forced-command dispatcher is the only acceptable target architecture for extending the current fixed SSH preflight. It must preserve the existing no-command behavior and expose only exact, versioned, read-only selectors.

**Do not implement or install it yet.** The effective authorized_keys forced-command entry, installed script path, root-owned update mechanism, and secure API-token source are not established. The deployment inventory also does not establish a production Flask health listener.

This review authorizes documentation/design only. It does not authorize editing `authorized_keys`, changing SSH restrictions, installing files, invoking new remote commands, or accessing the VPS.

## 2. Existing facts

| Item | Repository evidence | Status |
|---|---|---|
| Existing preflight | `ops/ssh/t0-readonly-preflight.sh`, blob `39de5aa7602cdf7dc301ff6bc65a68fad417ea84` | Fixed read-only snapshot; no subcommand dispatcher |
| SSH workflow | `.github/workflows/t0-manual-validation.yml`, blob `b776c2ddf33874dce0dfe7c6ed71562b30d5df62` | Connects without a remote command; no installer/SCP/rsync |
| SQLite probe | `ci/t0_runtime_acceptance.py`, blob `479cf707feb931e6f46f3261f5a2824afa11e2c2` | Disposable-CI tested; not installed on VPS |
| Probe tests | `ci/test_t0_runtime_acceptance.py`, blob `72b429683e3ce5b21f7514a0bf5d0c819e9982e3` | Contract tests; no host proof |
| Candle API topology | `127.0.0.1:8788`, `market_data.api:application` | Documented intent; host state NOT VERIFIED |
| Flask health app | `app.py` | Production launcher/provider/listener NOT VERIFIED |
| Bearer token | No approved remote probe source identified | NOT VERIFIED |
| Installed root-owned dispatcher/update path | Not established by repository evidence | BLOCKED |

The last known SSH preflight run `42814402445` is a historical point-in-time snapshot, not proof of current host configuration.

## 3. Target command contract

The forced-command entry must invoke one fixed dispatcher binary/script. The dispatcher must inspect the raw `SSH_ORIGINAL_COMMAND` value and compare it by exact string equality against a small hard-coded allowlist.

| SSH original command | Required behavior |
|---|---|
| Empty or unset | Run the existing preflight unchanged (backward compatibility) |
| `t0-runtime-snapshot-v1` | Run the fixed read-only SQLite snapshot probe |
| `t0-candle-api-v1` | Reserved; reject/NOT AVAILABLE until a secure token source is proven |
| `t0-feeder-health-v1` | Reserved; reject/NOT AVAILABLE until a deployed listener and provider binding are proven |
| Any other string, suffix, prefix, whitespace variant, or argument | Reject; nonzero exit; no fallback shell |

The dispatcher must not normalize arbitrary input into an accepted selector. In particular, it must not use `eval`, `bash -c`, `sh -c`, `$@`, arbitrary path arguments, user-provided SQL, or command interpolation.

The command string is a selector, not a parameter channel. No user-supplied path, port, URL, token, database name, or option is accepted.

## 4. Execution boundary

If the prerequisites are later met and the owner separately approves implementation:

1. Keep one root-owned dispatcher and root-owned probe code outside the ubuntu-writable checkout. Do not execute mutable code directly from `/home/ubuntu/t0/app`.
2. Pin the interpreter and probe entrypoint to fixed absolute paths. Do not search PATH for executable code.
3. Verify ownership, permissions, and integrity of dispatcher and probe files before dispatch. A failed check must fail closed.
4. Preserve the current forced-command key restriction and host-key pinning. No general shell, PTY, port forwarding, agent forwarding, SCP, or SFTP capability is added.
5. Do not alter the current empty-command preflight output contract.
6. Emit a versioned, bounded, sanitized result with selector, probe version, observed timestamp, deployed source/script SHA where verifiable, and explicit PASS/FAIL/NOT_VERIFIED state.
7. Do not print environment variables, raw lease owner, tokens, secret values/paths, database contents, or unrestricted process command lines.
8. Use fixed output limits and bounded execution time. A probe timeout or malformed output is NOT_VERIFIED, never PASS.

If root-owned code integrity cannot be verified, do not execute the probe.

## 5. Probe-specific requirements

### SQLite snapshot selector

- Require the canonical database to exist; never create it.
- Open only with SQLite URI `mode=ro`; enforce `PRAGMA query_only=ON`.
- Permit only the already-reviewed fixed SELECT/PRAGMA operations.
- Read integrity, canonical lease owner/generation/expiry and M15/H1 watermarks.
- Return only a truncated owner fingerprint, never the raw owner.
- No schema creation, writes, acquire/heartbeat/release, vacuum, checkpoint, migration, restore, or file modification.
- Missing/expired/invalid lease, missing DB, invalid schema, integrity failure, or stale data must fail closed.

### Candle API selector

- Use only the documented loopback Candle API `127.0.0.1:8788`; do not infer other ports.
- Token may be read only from a separately approved, permission-verified secret provider. Never pass it as an argument, URL parameter, environment dump, output field, log field, or artifact.
- If no secure source is proven, do not make the authenticated request; report NOT_VERIFIED.
- Keep GET-only, loopback validation, no redirects/proxies, bounded timeout/body, Bearer header only, and existing response contract validation.

### Feeder health selector

- Do not assume the Flask health application is deployed or bound to port 8788.
- Require independent evidence of its launcher, provider registration, and exact loopback listener.
- Until then, do not make an HTTP request and report NOT_VERIFIED.

## 6. Installation and update prerequisites

All items below are hard gates, not implementation details to guess:

- [ ] Owner-supplied or separately authorized read-only evidence of the exact effective `authorized_keys` forced-command entry (redacted; preserve the command path and options).
- [ ] Exact installed dispatcher path, owner, group, mode, parent-directory permissions, and integrity verification method.
- [ ] Proven root-owned update/install mechanism. No SCP/rsync, generic SSH shell, or ad hoc sudo command.
- [ ] Exact deployed application checkout SHA and confirmation whether it is writable by the SSH login user.
- [ ] Root-owned probe installation location and pinned interpreter/runtime.
- [ ] Secure API token provider, access policy, rotation behavior, and proof the token cannot leak into process arguments/logs/artifacts.
- [ ] Evidence whether Flask health app is deployed; if yes, exact launcher, provider binding, and loopback listener.
- [ ] Contract tests for exact allowlist matching, command injection variants, backward compatibility, file-integrity failure, timeout, output redaction, and no-write guarantees.
- [ ] Independent review of the proposed deployment diff and explicit owner approval for installation/invocation.

A missing item blocks deployment. Do not weaken the gates to make the workflow green.

## 7. GitHub Actions plan — future, not implemented

After the design prerequisites and separate approval:

- Add static contract tests for selector allowlisting and preservation of the existing preflight.
- Add a disposable-runner integration test using temporary files and SQLite fixtures only.
- Keep pull-request/push contract jobs credential-free, with `contents: read` and `persist-credentials: false`.
- Keep any remote SSH invocation manual-dispatch only and separate from CI-only contract tests.
- Bind the remote job to an exact source SHA; record workflow run, job conclusions, sanitized output, artifact ID/digest/expiry.
- Do not expose SSH secrets to contract jobs. Do not add a remote installer job until its installation mechanism is separately approved.

## 8. Status and next step

| Gate | Status |
|---|---|
| Existing G4a/G4b disposable CI contracts | PASS |
| Dispatcher target contract | DESIGN REVIEW COMPLETE |
| Exact installed forced-command path | NOT VERIFIED |
| Root-owned update mechanism | BLOCKED |
| Secure API token source | NOT VERIFIED |
| Flask health deployment/listener | NOT VERIFIED |
| Dispatcher implementation | NOT STARTED |
| VPS installation or invocation | NOT AUTHORIZED |
| G4 live VPS runtime | NOT VERIFIED |

**Next step:** obtain the bounded owner-supplied deployment evidence described in `docs/evidence/T0_OWNER_READONLY_DEPLOYMENT_EVIDENCE_PROTOCOL_2026-11-10.md`, specifically the effective forced-command entry and root-owned update path, with secrets redacted. This documentary evidence step does not require probe installation or a new remote command. Then reassess whether a secure implementation path exists.

No T0 canonical SQLite mutation, Feeder/API restart, T1 activation, PostgreSQL work, data deletion, or trading action is included in this design.
