# T0 PostgreSQL 16 Role Provisioning — Provider Capability Decision

**Status:** DESIGN REVIEW ONLY — no provider selected, no provider capability certified, no implementation approved.

## 1. Decision context

The disposable CI reproduction on PostgreSQL 16.6 (timescale/timescaledb:2.17.2-pg16) confirmed that a non-superuser with CREATEROLE receives an automatic membership in every role it creates. The membership is recorded with the bootstrap superuser as grantor and ADMIN OPTION=true, INHERIT=false, SET=false. The creator cannot revoke that automatic membership. A superuser can remove it.

The current T0 migration guard intentionally rejects:
- Any member of t0_migrator other than t0_migrator_login.
- Any member of t0_db_owner, t0_candle_writer_owner, or t0_lease_manager_owner other than the intended t0_migrator role.

Therefore, the existing bootstrap pattern — one persistent non-superuser CREATEROLE login creates all reserved roles and then tries REVOKE ... FROM CURRENT_USER — is incompatible with the PostgreSQL 16 membership graph. The guard is not the defect demonstrated by this reproduction.

## 2. Candidate paths

### Option A — Provider-authorized control-plane role provisioning

Have the database provider's documented control-plane/bootstrap mechanism create the reserved roles and membership graph, rather than having a persistent application-facing CREATEROLE login create them.

**Required proof before acceptance**
- Provider documentation explicitly authorizes the operation for this database tier/plan.
- The provider operation creates the required roles without leaving an unintended login/bootstrap member in reserved roles.
- Catalog inspection proves exact role attributes and membership graph, including grantor, admin_option, inherit_option, and set_option.
- The application migrator remains a restricted LOGIN member only of t0_migrator; runtime roles remain NOLOGIN and isolated.
- A disposable provider cluster can execute migrations through the restricted migrator and pass the full T0 role, writer, lease, restart, and readiness tests.

**Benefits:** preserves the existing strict migration guard and least-privilege separation.

**Costs/risks:** provider-specific; may require a support ticket, control-plane permission, or a provider tier that exposes the operation. Do not assume this capability exists.

### Option B — Provider-authorized privileged cleanup of automatic memberships

Use a provider-documented superuser-equivalent operation to remove the automatic bootstrap-superuser-granted membership rows after role creation.

**Required proof before acceptance**
- Provider documentation identifies the exact principal/operation and confirms it may revoke the PostgreSQL 16 automatic membership despite its bootstrap-superuser grantor.
- On a disposable cluster matching the actual provider and tier, create uniquely named roles through the intended bootstrap identity.
- Capture the complete membership rows before cleanup.
- Execute the provider-authorized cleanup, then prove the exact automatic rows are gone and no unintended memberships remain.
- Prove the operation is available to the deployment process without giving the application migrator or feeder runtime role elevated privileges.
- Re-run all least-privilege and T0 integration tests.

**Benefits:** can preserve the current schema/migration guard and existing role graph.

**Costs/risks:** many managed services do not expose PostgreSQL superuser. A normal CREATEROLE or provider-admin role must not be assumed to be equivalent. The local CI superuser result is not proof that a managed provider permits this.

### Option C — Declare the provider/bootstrap path unsupported and fail closed

If neither A nor B is supported by the selected provider, do not provision this T0 PostgreSQL role model on that provider. Keep the strict guard and disable PostgreSQL-backed readiness for that provider until a supported provisioning path is established. Continue using the approved SQLite T0 mode or another separately reviewed provider path; do not silently downgrade role isolation.

**Benefits:** preserves data integrity and the current security boundary.

**Costs/risks:** limits provider portability and may defer PostgreSQL deployment.

## 3. Rejected shortcuts

The following are not accepted as fixes:
- Removing or weakening _assert_writer_roles_safe just to make CI green.
- Allowing bootstrap logins to remain members of t0_migrator or SECURITY DEFINER owner roles without a separate threat model and explicit approval.
- Treating INHERIT=false and SET=false as sufficient: the automatic membership still has ADMIN OPTION=true, allowing the member to grant membership to others.
- Assuming createrole_self_grant removes the automatic bootstrap-superuser grant. It does not remove the membership demonstrated in the reproduction.
- Using superuser credentials for application migrations or runtime Feeder access.
- Relying on the creator's REVOKE ... FROM CURRENT_USER; PostgreSQL 16.6 reproduction proves that it leaves the automatic membership intact.
- Dropping a bootstrap login as a cleanup shortcut unless the actual provider exposes and documents an authorized role-drop path and the full ownership/dependency graph is reconciled.

## 4. Provider qualification gate

No provider should be marked supported until all checks below pass on a disposable instance of the exact provider, tier, and PostgreSQL major version:

1. Record provider, plan/tier, region, PostgreSQL version, extension versions, and documented administrative role capabilities.
2. Record session_user, current_user, role flags, and all relevant pg_auth_members rows before and after each role creation, grant, revoke, and cleanup.
3. Prove the provider-supported way to create or remove the automatic membership.
4. Prove final role flags and membership graph against the T0 migration guard's exact requirements.
5. Run restricted migrations as t0_migrator_login; verify schema/table/function ownership.
6. Run role-privilege, writer gateway, lease fencing, Feeder lifecycle/restart, Health/Readiness, and complete market_data regression tests.
7. Preserve logs, artifact digest, exact source SHA, provider/tier identity, and the test instance's destruction evidence.

A failure at any gate means UNSUPPORTED/BLOCKED, not a reason to weaken the guard.

## 5. Recommendation

**Default to Option C (fail closed) until a concrete provider and its documented capabilities are selected and qualified.** Evaluate Option A first because it can preserve the strict role model without granting the application migrator elevated powers. Evaluate Option B only if the provider explicitly documents a privileged cleanup operation and the disposable-provider proof succeeds.

The existing disposable GitHub Actions reproduction validates PostgreSQL 16.6 semantics only. It does not qualify Timescale Cloud or any other managed provider. No production provider capability has been verified.

## 6. Authorization boundary

This document authorizes no source/test changes, role-policy changes, provider provisioning, database creation, migration, Feeder activation, data sync, backtest, merge, deployment, or live execution.

A separate explicit user approval is required before implementing a selected path. Any implementation must remain isolated, preserve the migration guard, start with focused RED tests, and pass the full T0 acceptance suite on the exact source SHA. ai_execution_enabled=false remains unchanged.
