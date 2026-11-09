# P1 — GitHub Actions Authenticated SSH Preflight

Date: 2026-11-09 UTC  
Status: IMPLEMENTED IN REPOSITORY — REMOTE PREFLIGHT NOT RUN  
Scope: authenticated, read-only inspection of the existing Scaleway VPS

## 1. Owner authorization and limits

The owner approved P1 with the following bounded scope:

- establish an authenticated SSH path from GitHub Actions to the Scaleway VPS;
- verify SSH host identity using a pinned Ed25519 host key;
- run only a root-owned, forced, read-only remote preflight command;
- inspect host/user, source checkout SHA, Feeder process presence, TCP listener state for port 8788, and read-only SQLite integrity;
- retain sanitized evidence and an explicit PASS/PARTIAL/BLOCKED verdict.

This gate does not authorize service start/stop/restart, deployment, source update, database mutation, permission broadening, firewall changes, T1/T2 activation, API requests, live trading, or any destructive operation. The existing paper-only and no-live-order constraints remain.

## 2. Implementation

- Existing workflow extended: `.github/workflows/t0-manual-validation.yml`.
- New manual gate: `scaleway-ssh-preflight`.
- Protected GitHub Environment: `scaleway-preflight`.
- Contract test: `ci/test_t0_ssh_preflight_contract.py`.
- Forced remote command: `ops/ssh/t0-readonly-preflight.sh`.

The workflow has two jobs:

1. `ssh-preflight-contract` checks shell syntax and the security contract without accessing the VPS.
2. `ssh-preflight` runs only after the contract job passes and the GitHub Environment approval is satisfied.

The SSH client supplies no remote command. The server-side authorized key must force exactly `/usr/local/sbin/t0-readonly-preflight`. Thus workflow inputs cannot select arbitrary remote commands.

## 3. Required one-time operator setup

Do not paste private keys, host private keys, or credentials into ChatGPT, commits, workflow files, or artifacts.

1. On a trusted operator workstation, generate a dedicated Ed25519 key pair for this workflow. Keep the private key local until it is entered directly into the GitHub Environment secret.
2. Create a dedicated non-root VPS account (suggested name: `t0-preflight`). Do not grant sudo or interactive administration rights.
3. Install `ops/ssh/t0-readonly-preflight.sh` on the VPS as `/usr/local/sbin/t0-readonly-preflight`, owned by root and not writable by the preflight account. Verify its SHA against the repository blob before installation.
4. Add the dedicated public key to that account's `authorized_keys` with a forced command and restrictions, for example:

   ```text
   restrict,command="/usr/local/sbin/t0-readonly-preflight" ssh-ed25519 AAAA... github-actions-t0-preflight
   ```

   Do not reuse an administrator key. Do not permit PTY, agent forwarding, X11 forwarding, TCP forwarding, or arbitrary commands.
5. Ensure the account can only read the specific source metadata and SQLite files needed by the script. Do not use broad recursive chmod/chown. If narrow ACLs are required, review and apply them as a separate operator action; SQLite WAL/SHM sidecars may also need read access. If access is unavailable, the preflight must report failure rather than broaden permissions.
6. Verify the VPS Ed25519 host-key fingerprint through the Scaleway console or another independent trusted channel. Construct a `known_hosts` entry from that verified host key; do not use runtime `ssh-keyscan` trust-on-first-use.
7. In GitHub repository Settings → Environments, create `scaleway-preflight`. Configure required reviewer approval and prevent self-review where the available settings allow it.
8. Add these Environment secrets to `scaleway-preflight`:
   - `SCW_SSH_HOST`: VPS hostname or public IP;
   - `SCW_SSH_PORT`: SSH port (normally 22);
   - `SCW_SSH_USER`: dedicated non-root account;
   - `SCW_SSH_PRIVATE_KEY`: dedicated Ed25519 private key;
   - `SCW_SSH_KNOWN_HOSTS`: exact host-key line, including the port-qualified host form when using a non-default port.

The repository is public. The SSH private key and all connection values must remain Environment secrets; never put them in repository variables, files, artifacts, issue comments, or logs.

## 4. Remote command contract

The remote script is intentionally fixed-path and argument-free. It reports only:

- sanitized hostname and SSH account;
- Git source SHA from `/home/ubuntu/t0/app`;
- PIDs matching the known T0 Feeder module names (no full command lines);
- listener endpoints for TCP port 8788, classifying loopback-only, absent, or non-loopback;
- SQLite `PRAGMA integrity_check` using a read-only URI and `PRAGMA query_only=ON`.

It does not print environment variables, process command lines, tokens, database contents, logs, credentials, or private paths beyond the fixed database target. It does not invoke systemctl, kill processes, write to the database, or modify files.

The account must be constrained by the forced command. The workflow alone is not a substitute for server-side SSH restrictions.

## 5. Verdict semantics

- **PASS**: SSH transport and forced command work; source SHA is verified; SQLite integrity is `ok`; Feeder is present; port 8788 is listening only on loopback.
- **PARTIAL**: transport and core read-only evidence work, but Feeder or the API listener is absent. This is diagnostic evidence, not deployment approval.
- **BLOCKED**: missing/invalid secrets, host-key mismatch, SSH failure, missing source SHA, unreadable/integrity-failing database, malformed forced-command output, or a non-loopback 8788 listener.

A successful GitHub job is not automatically a PASS verdict; inspect `preflight-verdict.txt` and the remote evidence artifact.

## 6. Evidence and current status

- Contract and shell syntax checks are part of the manual gate.
- The remote job is protected by the `scaleway-preflight` Environment.
- Evidence artifact name: `p1-scaleway-ssh-preflight-<run_id>`.
- No SSH key or secret has been generated, received, or stored by ChatGPT.
- No remote command has been run from this session.
- No VPS account, authorized key, file permission, firewall, Feeder, DB, API, or T2 runtime has been changed by this implementation.

Current verdict: **IMPLEMENTATION RECORDED — NOT VERIFIED**. Contract tests and the GitHub Actions workflow have not yet been run. Remote authentication and VPS inspection remain **NOT VERIFIED** until the operator completes the one-time setup and dispatches the gate.

## 7. Next step and prohibited expansion

Next: complete the one-time account/key/host-key/Environment setup, then manually dispatch `T0 Manual Validation → scaleway-ssh-preflight` on the approved feature branch.

After the run, record the exact workflow run ID, source SHA, artifact ID, and PASS/PARTIAL/BLOCKED result in this record and the project handoff.

Even after PASS, this gate does not authorize API deployment, Feeder restart, T2 one-shot read, T1 activation, or any unrelated runtime change. Those remain separate rollout gates under the previously approved T0→T2 sequence.
