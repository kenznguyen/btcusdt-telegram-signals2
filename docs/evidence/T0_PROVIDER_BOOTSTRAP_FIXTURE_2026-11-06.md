# T0 Restricted Provider Bootstrap Fixture — 2026-11-06

## Scope

Add an integration acceptance case for a managed-provider-style bootstrap login that is explicitly **not SUPERUSER**, but has `CREATEROLE` and `CREATEDB`. The fixture provisions the temporary migration identity and its memberships, creates a disposable database owned by `t0_db_owner`, pre-enables TimescaleDB as the provider-controlled extension step, and then runs the existing immutable migrations using the restricted `t0_migrator_login`.

This is an isolated CI test only. It does not connect to an external provider or create any paid resource.

## Source

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Source commit: `66194a83d421050514f1d401ceff4bfd425dce81`
- Test file: `market_data/test_postgres_role_privileges.py`
- Test blob: `ffa5d9102b15aad7792a07d9f73eb07bfeac8f2d`
- Added test: `test_non_superuser_bootstrap_prepares_restricted_migrator_roles`

## Acceptance intent

1. Bootstrap login is confirmed `rolsuper=false`, `rolcreaterole=true`, `rolcreatedb=true`.
2. Bootstrap creates the temporary `t0_db_owner`, `t0_migrator`, and `t0_migrator_login` roles.
3. `t0_migrator` receives only the required database/function-owner memberships; ephemeral login is only a member of `t0_migrator`.
4. Database ownership is assigned to `t0_db_owner`.
5. Migrations execute through the restricted login and transfer schema/table/function ownership to the intended non-login roles.
6. Test teardown drops the disposable database and revokes/drops temporary role memberships.

## Explicit limitations

- The existing CI TimescaleDB service has already applied the baseline migrations, so the capability/SECURITY DEFINER owner roles `t0_candle_writer_owner` and `t0_lease_manager_owner` exist at cluster scope before this new test runs. This fixture verifies a non-superuser bootstrap for the migration identity and database ownership, **not** a pristine-cluster creation of every T0 role.
- TimescaleDB extension enablement is performed by the service admin before restricted migrations. Provider-specific permission to enable the extension remains unverified.
- The fixture does not model DigitalOcean/Tiger Cloud role semantics exactly and does not establish provider compatibility.
- No code change to migration behavior is included.

## Verification

- Test execution on the new exact source commit: **NOT VERIFIED** (no CI status check is currently attached to this commit).
- Test result: **NOT RUN / NOT VERIFIED**.
- Existing PostgreSQL/TimescaleDB evidence from earlier source SHAs is historical only and is not promoted to this commit.
- No provider endpoint, VPS, production database, credential, canonical T0 database, Feeder activation, exchange connection, or market-data synchronization was created or used.

## Next step

Run the new focused integration test and full `market_data` suite on this exact source SHA using the existing GitHub Actions TimescaleDB service. If the restricted bootstrap test fails, preserve the failure output and adjust only the fixture or documented provider preconditions—do not weaken T0 role guards or grant SUPERUSER to the migration login.
