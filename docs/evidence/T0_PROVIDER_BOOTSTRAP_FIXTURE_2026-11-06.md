# T0 Fresh-Cluster Restricted Provider Bootstrap — 2026-11-06

## Scope

Replace the first bootstrap probe after source review found it was unsuitable for the shared TimescaleDB integration cluster: it attempted to create fixed cluster-wide T0 roles after the baseline migrations had already created some of them.

The replacement is a dedicated, fresh TimescaleDB service job. A temporary bootstrap login has `CREATEROLE` and `CREATEDB`, but is asserted to have `rolsuper=false`. It provisions the complete reserved T0 role set, creates an isolated database, revokes its temporary role memberships, and then applies the existing migrations using only `t0_migrator_login`.

## Source

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Test: `market_data/test_postgres_provider_bootstrap.py`
- Current source commit: `7d194d29ae011330b22f74d65401e68654b995f3`\n- Test blob: `6e2f59b4b8725f15156e98e8f7360c9639be7986`
- Workflow: `.github/workflows/t0-single-writer-gateway-red.yml`
- Workflow blob: `47e8312469db0772eba52053005324314fe0baf6`
- Removed the invalid shared-cluster probe from `market_data/test_postgres_role_privileges.py`; current blob: `f26f8ec7a782fd1ca0d339a1d8eb5ef613cda13f`
- Relevant commits:
  - New isolated test: `edc3d653c0929768dead89301622dc0e14ab75b6`
  - Removed shared-cluster test: `34efd769266472826b36bc13d9ab4a4b10eae4c2`
  - Dedicated CI job: `b2394dc97e80d7f87b5ff2e1f2138a310d02b256`
  - Additional ownership assertions: `3eb21368eaa4b0d46d69a1ba1a97ae5f80e226d3`, `7e6ec2dab44c954bc48ded7eda14b93a1c1c7b13`\n- Safe partial-setup teardown: `b85b6cc5f99511b11aa2eacbabeb20a87595d78e`\n- Teardown now drops only roles recorded as created by this test, preventing cleanup from touching pre-existing roles when the pristine-cluster assertion fails: `7d194d29ae011330b22f74d65401e68654b995f3`

## Acceptance checks

1. The test requires a fresh disposable PostgreSQL cluster and fails if any reserved T0 role already exists.
2. Bootstrap role is confirmed non-superuser with CREATEROLE and CREATEDB.
3. Bootstrap creates `t0_db_owner`, `t0_migrator`, `t0_migrator_login`, both Feeder capability roles and both SECURITY DEFINER owner roles.
4. `t0_migrator` receives the required memberships; the ephemeral login receives only `t0_migrator`.
5. Bootstrap's temporary memberships are revoked before migration safety checks run.
6. TimescaleDB is pre-enabled as a separate provider/service-admin operation.
7. Migrations execute through the restricted login and assert schema, table, and SECURITY DEFINER function ownership.
8. The test asserts restricted role attributes and absence of unexpected owner-role memberships.
9. Teardown drops the disposable database, then the bootstrap identity first (removing any partially-created ADMIN memberships), then all reserved roles.

## PostgreSQL 16 role semantics\n\nPostgreSQL 16 documents that a non-superuser CREATEROLE identity receives ADMIN OPTION membership on roles it creates, with SET and INHERIT disabled by default. The fixture revokes those temporary memberships before the migration guard runs. This is a PostgreSQL 16 baseline fact, not proof that every managed provider exposes identical privileges. See [PostgreSQL 16 role attributes](https://www.postgresql.org/docs/16/role-attributes.html).\n\n## CI isolation

A new independent job, `restricted-provider-bootstrap-integration`, starts its own `timescale/timescaledb:2.17.2-pg16` service. It does not share the already-migrated database used by other integration jobs. The job checks loopback host, port, database/user identity, disposable flag, and empty trading/Paper environment variables before running the focused test.

## Verification

- Exact-source test execution: **NOT VERIFIED**; no direct-push workflow run result has been retrieved yet.
- Test result: **NOT RUN / NOT VERIFIED**.
- Workflow syntax/runtime: **NOT VERIFIED** until GitHub Actions reports the job outcome.
- No provider endpoint, VPS, production database, external credential, canonical T0 database, Feeder activation, exchange connection, or market-data synchronization was created or used.
- This fixture proves only the PostgreSQL 16 / TimescaleDB 2.17.2 CI service path if it passes. It does not certify DigitalOcean/Tiger Cloud role behavior, provider extension permissions, TLS CA/SAN, PITR, restore, RPO/RTO or failover fencing.

## Next step

Retrieve the direct-push GitHub Actions run for the exact branch tip. Confirm the new job checked out that exact SHA and inspect its logs/artifact. If it fails, preserve the failure and adjust the bootstrap/test assumptions without weakening T0 role guards or granting SUPERUSER to the migration login.
