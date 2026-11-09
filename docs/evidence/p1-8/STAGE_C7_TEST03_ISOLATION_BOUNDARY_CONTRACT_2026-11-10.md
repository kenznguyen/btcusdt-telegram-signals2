# Stage C.7 — TEST-03 Isolation Boundary Contract

Date: 2026-11-10  
Repository: kenznguyen/btcusdt-telegram-signals2  
Branch: feature/t0-centralized-data-feeder-p1-20261101  
Work type: documentation-only isolation contract  
Predecessors: Stage C.4 prerequisite closure plan; Stage C.5 TEST-01 runner contract; Stage C.6 TEST-02 synthetic adapter contract  
Scope: TEST-03 only; no implementation, provisioning or execution

## 1. Purpose and authority boundary

Define the minimum security boundaries and evidence required before a future synthetic lifecycle harness can execute. The contract covers process identity, host/container boundary, filesystem, mounts, network, credentials, environment/configuration, synthetic storage, GitHub Actions runner exposure, and independent observation.

This is a design contract, not proof that any current runner or environment is isolated. Stage C approval authorizes this bounded documentary work only. It does not authorize code changes, container/workflow/runner changes, test execution, compile, dry-run, fault injection, GitHub Actions dispatch, secret or permission access, VPS/runtime/database/provider/network probes, provisioning, or data mutation.

TEST-08 remains a separate exact-scope authorization gate. TEST-03 closure would not itself grant execution authority.

Option C remains active: no deletion, archive, cleanup, expiry, compaction, vacuum, backup/replica removal, export mutation or irreversible transition. T0 canonical data and recovery copies, CORE_LEDGER, AI_LEDGER, required T3 reconstruction/audit evidence, governance history, and unknown/unclassified objects remain protected.

## 2. Security objectives and threat model

The future harness must demonstrate all of the following:

1. The executor can access only resources created for one explicitly identified synthetic run.
2. Production credentials and ambient identities are absent, not merely unused.
3. Production paths, databases, sockets, mounts, network routes and provider endpoints are inaccessible.
4. A malformed manifest, adapter, URI, path, environment variable or runtime configuration cannot cause fallback to a real backend.
5. An attempted escape is denied and recorded; uncertainty causes BLOCKED before test execution.
6. The executor cannot modify the independent oracle, its expected-state source or protected evidence.
7. The runner cannot invoke cleanup or destructive operations. TEST-07 remains a separate capability and authorization gate.
8. Isolation evidence is tied to the exact source, runner image/toolchain, workflow, configuration, namespace and run being claimed.

Threats include accidental configuration fallback, malicious or malformed fixtures, path traversal, symlink and mount escape, namespace collision, DNS/IP redirection, metadata-service access, inherited credentials, privileged containers, host socket exposure, shared writable workspaces, cross-job persistence, cache/artifact leakage, workflow token overreach, compromised dependencies, stale runner state and incomplete teardown inventory.

The contract does not claim to defeat a compromised host kernel, GitHub control plane, hypervisor, cloud provider or hardware root of trust. Such trust assumptions must be declared in any future assurance claim.

## 3. Isolation architecture and trust zones

A future design must explicitly separate these zones:

| Zone | Role | Permitted access | Forbidden access |
|---|---|---|---|
| Control/manifest zone | Supplies frozen run manifest and approved configuration | Read-only manifest and pinned toolchain identity | Secrets, production config, mutable policy source |
| Executor zone | Runs selected synthetic test cases | Synthetic adapter APIs for its one namespace | Host paths, production networks, credentials, oracle writes |
| Synthetic resource zone | Holds per-run synthetic objects and metadata | Exact namespace-scoped adapter operations | Cross-run and production resources |
| Oracle zone | Independently observes and evaluates expected/actual state | Read-only observation of declared synthetic evidence | Executor write access or shared mutable state |
| Evidence zone | Stores immutable run outputs and audit evidence | Append-only, run-scoped evidence submission | Rewrite/delete, arbitrary destination or recipient |
| Host/runner zone | Provides execution substrate | Minimum runtime services needed to execute | Executor access to host control sockets, privileged APIs or unrelated workspaces |

The zones may be logical or physical in a future implementation, but their boundaries must be evidenced rather than inferred from naming or configuration alone. Executor and oracle must not share a mutable principal, writable volume, process namespace or control channel that allows the executor to alter oracle expectations or results.

## 4. Process, identity and privilege boundary

Minimum contract:

- Run the executor as a dedicated non-root, non-administrator identity with a unique run-scoped identity.
- No privilege escalation, setuid/setcap helpers, host PID namespace, host IPC namespace, host network namespace, privileged container mode or equivalent elevated capability.
- Drop all unnecessary Linux capabilities; deny raw sockets, mount, ptrace, namespace creation, device access and host administration interfaces unless a separately justified requirement is frozen and approved.
- Apply resource limits for CPU, memory, process count, file descriptors and execution duration; limit exhaustion must terminate the run as BLOCKED/FAIL, never bypass isolation.
- No Docker/container runtime socket, Kubernetes service-account token, host agent socket, SSH agent socket, cloud metadata proxy or credential helper is mounted or forwarded.
- Executor process tree and descendants remain within the same run boundary; subprocesses inherit no broader identity or capability.
- Oracle runs under a separate principal/process boundary and has no executor-writable state.
- Record effective UID/GID or platform principal, groups, capabilities, namespaces, security profile and process ancestry as evidence. Do not record secret values.

A container boundary alone is not proof of isolation. If the threat model requires resistance to hostile code, a separately isolated VM or equivalent boundary may be required; the chosen boundary and residual host trust assumptions must be explicit.

## 5. Filesystem, mount and path boundary

The executor filesystem must be constructed from an explicit allowlist:

- Read-only runtime image and pinned dependencies.
- One dedicated, run-specific synthetic workspace.
- Explicit temporary directory within that workspace, with bounded size and lifetime.
- Explicit evidence output channel with append-only semantics or a narrowly scoped write API.
- No host root, home directory, repository secrets directory, Docker socket, cloud credential directory, SSH material, production configuration, database file, WAL/SHM file, backup directory, replica mount, shared cache or unrelated workspace.

Required controls and evidence:

1. Mount namespace is private; no host mount propagation.
2. No writable host bind mounts or device mounts.
3. Synthetic workspace root is canonicalized and bound to the immutable namespace identity.
4. Reject absolute paths outside the root, parent traversal, alternate separators, encoded traversal, NUL bytes, hard-link escape, symlinks, magic links, mount points and path aliases.
5. Use descriptor-relative safe file operations and no-follow semantics in any future implementation; string-prefix checks are insufficient.
6. Resolve and validate each path at use time to prevent time-of-check/time-of-use substitution.
7. Enforce file type, ownership, permissions, size and inode/link-count constraints as applicable.
8. Reject special files, sockets, FIFOs, block/character devices and unexpected hard links.
9. No cleanup, unlink, truncate, overwrite or recursive deletion capability is exposed to the executor. Temporary-file handling must be narrowly specified and must not be conflated with lifecycle cleanup.
10. Capture pre-run and post-run mount tables, filesystem roots, workspace inventory and protected-root reachability evidence from an observer outside executor control.

A path that is absent from a listing is not proof that it is inaccessible. Negative proof must combine namespace/mount configuration, effective permissions and an independent attempted-access or reachability observation in a synthetic test environment.

## 6. Network and name-resolution boundary

Initial TEST-03 profile is **DENY_ALL outbound and inbound network access** for the executor, including loopback access to unrelated host services.

The future implementation must establish:

- No host networking, port publishing, forwarded ports, proxy variables, service-mesh sidecar or shared network namespace.
- No route to public internet, private/VPC networks, VPS, T0/T1/T2/T3/T4 services, databases, object stores, exchange endpoints, metadata services, DNS resolvers or external recipients.
- No DNS resolution or alternate name-resolution channel. A hostname allowlist is not sufficient for the initial deny-all profile.
- No Unix-domain sockets or named pipes that bridge to host or production services.
- No inherited HTTP_PROXY, HTTPS_PROXY, ALL_PROXY, NO_PROXY, custom resolver, SSH tunnel, VPN or port-forward configuration.
- Network policy is enforced outside the executor's mutable trust boundary and is observed independently.
- Capture effective routes, interfaces, firewall/network policy, namespace membership and denied connection evidence without contacting any production endpoint.
- If the isolation proof itself requires an external control plane, that control-plane access must be performed by a separate trusted controller, not granted to the executor.

Any future network exception requires a new, explicit, destination- and protocol-specific scope, a reason, a control owner, an independently verifiable enforcement point and separate owner approval. No exception is implied by this contract.

## 7. Credentials, secrets and ambient identity

The executor receives no:

- GitHub Actions secrets or environment secrets;
- exchange/API keys, VPS/SSH credentials or database passwords;
- cloud access keys, workload identity tokens, OIDC tokens or metadata credentials;
- signing keys, TSA credentials, registry tokens or external recipient credentials;
- inherited developer credentials, .netrc, credential helpers, SSH keys, agent sockets or browser/session state.

Requirements:

- Do not inject secrets and then rely on code not to read them. Their absence must be established from workflow/job configuration and the actual process environment/credential mounts.
- Disable OIDC token issuance and permission to request identity tokens for the executor job.
- Use a minimal, explicit workflow token permission set; no write permissions unless a future separately approved evidence-upload mechanism proves they are necessary. Any such mechanism should be isolated from test execution.
- Separate evidence publication from the executor; do not expose a repository write token to untrusted test code.
- Sanitize environment variables and configuration inputs against credential-bearing values and backend overrides.
- Record a redacted inventory of environment variable names, mounted credential locations and effective identity sources; never log secret values or token contents.
- Missing or ambiguous credential evidence means BLOCKED.

## 8. Configuration, dependency and supply-chain boundary

- The run manifest is the only source of test selection and adapter allowlist; no implicit discovery from host environment or user home.
- Pin source commit, runner image digest, dependency lock digest, adapter versions, fixture digest and configuration digest.
- Reject mutable tags, floating dependency versions, unpinned downloads and runtime package installation.
- No package manager or build step may fetch from the network during execution.
- No startup scripts, repository hooks, user profile scripts or ambient shell initialization are executed unless explicitly included in the frozen and reviewed runner definition.
- No production config file, .env, secret store mount or inherited process environment is loaded.
- Configuration schema is strict: unknown keys, production-like URI/path, credential field, alternate backend, network exception or unrecognized capability causes rejection before test discovery.
- Dependency provenance and any required image signature verification are evidence inputs; this contract does not choose a registry or trust root.

## 9. Synthetic storage and namespace containment

- Every resource is bound to one immutable run_id and namespace_id, as specified in Stage C.6.
- The namespace is created by a trusted controller before executor start and cannot be chosen or widened by test code.
- Adapter calls require exact namespace identity and explicit operation capability.
- Storage is isolated per run; no shared mutable object store, database, cache, filesystem path or reusable namespace.
- No backend discovery, fallback, production URI resolution, account/project inheritance or default credential chain.
- Resource limits and quotas are bounded and frozen before execution.
- Cross-run access is denied even if a caller guesses another run's object identifier.
- Namespace ownership and expiry metadata may be recorded, but no expiry/deletion/cleanup action is authorized by this contract.
- Synthetic labels or prefixes are supplemental identifiers, not the isolation boundary.

## 10. GitHub Actions and CI runner boundary

No workflow is selected or dispatched by this document. If a future implementation uses GitHub Actions, it must separately establish:

- Dedicated, ephemeral, isolated runner execution; no persistent self-hosted runner with residual workspaces or credentials.
- No privileged reusable workflow, untrusted pull-request code with write token, or shared runner state across jobs.
- Minimal permissions at workflow and job level; effective token permissions and OIDC availability must be independently verified, not inferred solely from YAML.
- No secrets in lifecycle test jobs; no environment approval bypass.
- No access to deployment environments, repository administration, package publishing, release signing or unrelated artifacts.
- No cache restore/save across trust boundaries; no artifact containing secrets, private paths or unintended fixture data.
- Artifact destination and upload principal are isolated from executor; evidence publication must not grant source or repository mutation authority to test code.
- Workflow definition, reusable workflow references, actions and runner image are pinned and included in provenance.
- Runner lifecycle, workspace disposal and residual-state checks are independently evidenced. This is not permission to delete repositories, artifacts or external resources.

The existing repository workflow inventory and permission state are not revalidated by this contract. LDA-08 remains HOLD / NOT VERIFIED until effective permissions and runner boundaries are established through an authorized read-only evidence path.

## 11. Oracle and observer separation

TEST-04 remains a separate prerequisite, but TEST-03 must reserve and protect its boundary:

- Oracle expectations are loaded from a frozen, immutable source outside executor write access.
- Oracle identity, process and storage are separate from the executor's mutable trust boundary.
- Executor cannot signal PASS directly, edit expected results, replace oracle binaries, change verification policy or suppress failed observations.
- Oracle observes actual synthetic object bytes, metadata revisions, lineage, audit sequence and protected-root invariance through read-only interfaces.
- Evidence collection is performed by a trusted observer/controller and is not dependent solely on executor self-report.
- If oracle independence cannot be proven, all affected outcomes are BLOCKED or INDETERMINATE.

This section does not close TEST-04 or establish an independent oracle implementation.

## 12. Required isolation evidence package

Before any future execution proposal, a frozen isolation evidence package must include:

| Evidence ID | Required evidence | Acceptance condition |
|---|---|---|
| ISO-01 | Exact source commit, workflow/job definition, runner image and toolchain digests | All identities immutable and cross-bound to the run manifest |
| ISO-02 | Effective process principal, groups, capabilities and namespace membership | Dedicated non-privileged identity; no host namespace or privilege escalation |
| ISO-03 | Mount table, filesystem roots, writable paths and workspace inventory | Only explicit synthetic roots writable; no host/production mounts |
| ISO-04 | Path traversal, symlink, hard-link, mount and special-file negative evidence | All escape attempts denied; no protected path reached |
| ISO-05 | Network interfaces, routes, policy and independent deny observations | No executor network route; outbound/inbound DENY_ALL |
| ISO-06 | Environment and credential-source inventory (redacted) | No secrets, ambient identity or credential mounts present |
| ISO-07 | Effective workflow token/OIDC permissions and runner lifecycle | No OIDC/secrets; least privilege; ephemeral isolated runner |
| ISO-08 | Adapter/namespace allowlist and storage identity | Exact run binding; no fallback or cross-run access |
| ISO-09 | Oracle principal/process/storage separation | Executor cannot alter or suppress oracle state/evidence |
| ISO-10 | Pre/post protected-root reachability and integrity observations | No route/mount/credential to protected roots; observer independent |
| ISO-11 | Dependency/image/configuration provenance | Frozen and verifiable identities; no runtime downloads |
| ISO-12 | Abort-path and evidence-preservation design | Failure stops execution and preserves evidence without cleanup side effects |

A configuration declaration alone is insufficient. Evidence must establish effective runtime state and independent observation. A synthetic PASS does not prove production isolation or environment equivalence.

## 13. Mandatory stop conditions

The future controller must refuse to start the executor, or mark the run BLOCKED/INDETERMINATE, if any of the following occurs:

- privileged/root execution or unapproved Linux capability;
- host PID/network/IPC namespace, host socket, device or mount exposure;
- writable path outside the exact synthetic workspace;
- unresolved symlink, hard-link, path traversal, mount alias or special file;
- any network route, DNS resolver, proxy or socket path not explicitly covered by the deny-all proof;
- secret, token, ambient identity or credential source detected or cannot be ruled out;
- unknown environment variable, backend, adapter, workflow permission or dependency;
- mutable image/dependency/action reference or digest mismatch;
- namespace collision, cross-run reference or fallback path;
- oracle shares executor's mutable state or trust boundary;
- incomplete pre-run/post-run evidence or inability to independently observe effective controls;
- protected-root reachability or integrity cannot be established;
- runner persistence/residual state is unresolved;
- any requirement depends on cleanup or deletion not separately authorized;
- TEST-08 exact execution authorization is absent.

On stop, preserve diagnostic and audit evidence through the approved evidence channel. Do not attempt cleanup, deletion or compensating mutation.

## 14. TEST-03 acceptance assertions for a future isolated implementation

| ID | Assertion | Minimum evidence |
|---|---|---|
| ISO-T01 | Executor runs non-root with no privilege escalation | Effective principal/capability snapshot |
| ISO-T02 | Host namespaces, sockets and devices are unavailable | Namespace/mount/device inventory and denied access |
| ISO-T03 | Only synthetic workspace is writable | Mount/permission inventory and independent write-denial probes |
| ISO-T04 | Traversal, symlink, hard-link and mount escape are denied | Negative fixture traces and unchanged protected-root observations |
| ISO-T05 | Network is DENY_ALL, including loopback and metadata routes | External policy snapshot and denied synthetic connection attempts |
| ISO-T06 | DNS, proxy, tunnel and socket bypasses are unavailable | Resolver/routes/environment/socket inventory |
| ISO-T07 | No secrets or ambient identity are present | Redacted env, mount and identity-source inventory |
| ISO-T08 | OIDC and secret injection are disabled for executor | Effective job/token configuration and runtime observation |
| ISO-T09 | Unknown config/backend/adapter fails before resource access | Invalid-manifest trace and no-open evidence |
| ISO-T10 | Namespace is unique, run-bound and cross-run isolated | Two synthetic namespace fixture identities and denied cross-access |
| ISO-T11 | Oracle cannot be modified by executor | Separate principal/storage proof and negative write attempt |
| ISO-T12 | Runner is ephemeral and leaves no reusable state | Runner lifecycle and residual-state evidence |
| ISO-T13 | Dependencies/configuration are pinned and no runtime fetch occurs | Digests, lock/config inventory and network-deny evidence |
| ISO-T14 | Protected roots are inaccessible and unchanged | Independent reachability and integrity observations |
| ISO-T15 | Abort preserves evidence and performs no cleanup | Fault/abort trace and evidence completeness record |

These are proposed TEST-03 assertions, not executed tests, not coverage credit for any lifecycle vector, and not evidence that the current repository or GitHub runner satisfies them.

## 15. Dependency and closure conditions

TEST-03 may be considered closed only when:

1. A concrete isolation architecture and threat model are frozen.
2. Executor/oracle/controller/evidence principals and trust boundaries are explicitly defined.
3. Effective process, filesystem, mount, network, credential and workflow controls are proven.
4. Negative escape attempts are executed only in an explicitly authorized synthetic environment and independently observed.
5. No secret or ambient identity is available to the executor.
6. TEST-02 adapters are bound to the isolated namespace with no fallback.
7. TEST-04 oracle separation is independently proven before oracle-backed PASS claims.
8. TEST-06 provenance binds exact isolation configuration and run evidence.
9. TEST-07 remains separately designed; no cleanup capability is introduced by TEST-03.
10. TEST-08 exact-scope owner authorization is obtained before any test execution.

This document alone does not close TEST-03, prove current runner security, or authorize implementation, provisioning or execution.

## 16. Current disposition

| Item | Status |
|---|---|
| TEST-01 | CONTRACT DOCUMENTED / IMPLEMENTATION NOT ESTABLISHED |
| TEST-02 | CONTRACT DOCUMENTED / IMPLEMENTATION NOT ESTABLISHED |
| TEST-03 | CONTRACT DOCUMENTED / EFFECTIVE ISOLATION NOT VERIFIED |
| TEST-04 | OPEN / NOT ESTABLISHED |
| TEST-05 | OPEN / NOT ESTABLISHED |
| TEST-06 | PARTIAL / NOT ESTABLISHED |
| TEST-07 | OPEN / NOT ESTABLISHED |
| TEST-08 | NOT GRANTED — separate exact-scope authorization required |
| LDA-07 | NOT RUN; 87/87 lifecycle vectors remain NOT RUN |
| LDA-06 | PARTIAL / NOT VERIFIED |
| LDA-08 | HOLD / NOT VERIFIED |

No tests, compile, dry-run, fault injection, provisioning or Actions dispatch were performed. No secrets, permissions, runtime, VPS, database, provider, recipient, backup or replica were accessed. No source, workflow, runner, permission, runtime or data changes were made. No destructive operation was performed.

**STAGE C.7 DOCUMENTARY CONTRACT COMPLETE — TEST-03 NOT CLOSED — EFFECTIVE ISOLATION NOT VERIFIED — NO IMPLEMENTATION OR EXECUTION AUTHORITY.**
