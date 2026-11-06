# T0 staging provider research — preliminary shortlist

**Research date:** 2026-11-06  
**Status:** RESEARCH ONLY — no provider, region, plan, budget, or topology approved. No account/resource provisioning authorized.

## 1. Non-negotiable system constraints

- PC remains development/research environment.
- VPS remains intended continuous runtime for T0 Feeder and monitoring.
- T0 canonical market-data database remains independent from Paper DB and SWG-F.
- One canonical writer only, protected by database lease/generation fencing. PC must not write while VPS owns the canonical writer.
- Staging must pass before canonical database provisioning or real market-data ingestion.
- Binance USD-M BTCUSDT perpetual remains the provisional canonical source; no exchange order permissions or trading credentials.
- `ai_execution_enabled=false`; paper-only boundary.
- GitHub stores source/docs/evidence; GitHub Actions is default CI. Codemagic only if GitHub Actions is unavailable or materially constrained.

## 2. Preliminary candidate topologies

These are candidates for a later decision, not recommendations or approvals.

### Candidate A — Hetzner Cloud Singapore, self-managed PostgreSQL + TimescaleDB on VPS

**Evidence found**
- Hetzner currently lists Singapore as an available Cloud location. Cloud products there include shared AMD and dedicated AMD instances.
- Hetzner describes hourly billing with a monthly cap and included outbound traffic varying by plan.
- Its June 15, 2026 price adjustment lists Singapore CCX13 at **$63.49/month excluding IPv4**. The Hetzner Singapore product page identifies CCX13 as 2 cores, 8 GB RAM, 80 GB storage.
- Dedicated CCX vCPUs are exclusive; Hetzner describes these as intended for predictable continuous CPU performance.

**Advantages**
- Full control over PostgreSQL/TimescaleDB version, extension build, roles, SECURITY DEFINER ownership, OS hardening, filesystem, WAL archiving, and service lifecycle.
- Can reproduce the current disposable CI engine family (TimescaleDB 2.17.2 / PostgreSQL 16) more directly than a managed service, subject to package/image availability.
- Feeder and database can be placed in one private host/network boundary for a small isolated staging environment.

**Risks / unresolved**
- A single VPS is one failure domain; it does not by itself meet backup isolation or high availability requirements.
- Operator owns PostgreSQL upgrades, patching, TLS CA configuration, WAL/PITR, backup encryption, restore drills, monitoring, and old-primary fencing.
- CCX13 published price is a relatively high indicative cost and excludes IPv4; actual checkout price, taxes, storage, backup destination, and network costs must be verified.
- Smaller shared instances must not be assumed suitable for a PostgreSQL + Feeder acceptance workload without measured RAM, disk I/O, WAL, and recovery headroom.

**Staging gate**
- Require an off-host backup destination and successful restore to a separate host before this topology can pass Gate F.
- Require measured disk I/O, fsync/commit latency, sustained ingestion, recovery, and resource headroom under representative synthetic load.

Official sources:
- https://www.hetzner.com/cloud-singapore/
- https://docs.hetzner.com/cloud/general/locations/
- https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/
- https://docs.hetzner.com/cloud/servers/faq/

### Candidate B — DigitalOcean Managed PostgreSQL Singapore + separate Feeder VPS

**Evidence found**
- DigitalOcean lists Managed PostgreSQL availability in Singapore region `SGP1`.
- Its Standard Edition supported-extension table lists `timescaledb` for PostgreSQL 16 and 17 (also lists it in other supported Standard major versions). Extension availability must be confirmed on the exact created cluster using `pg_available_extensions` and `CREATE EXTENSION`.
- DigitalOcean documentation says managed PostgreSQL has daily full backups and WAL retained for point-in-time recovery within the previous seven days.
- Published starting prices: single-node cluster starts at **$15/month** for 1 GiB RAM; HA starts at **$30/month per node**, with at least one matching standby, so the documented minimum primary + standby baseline is $60/month before any additional services/taxes.
- A single-node cluster is not highly available. HA requires the additional standby node.

**Advantages**
- Managed database reduces operator responsibility for base infrastructure, routine database service operations, and backup mechanics.
- Singapore region is listed for Managed PostgreSQL.
- Seven-day PITR history is aligned with the proposed minimum retention target, subject to actual plan behavior and restore verification.
- Separate database service and Feeder VPS reduce the chance that one host failure destroys both runtime and database.

**Risks / unresolved**
- Public extension documentation proves the extension name is on the supported list, not that the exact TimescaleDB version matches CI's 2.17.2. Verify exact `pg_extension.extversion` on a disposable cluster before selecting.
- The provider-managed role model, database ownership, SECURITY DEFINER function ownership, role memberships, grant restrictions, and lease table/API privileges may differ from vanilla PostgreSQL. Existing least-privilege tests must run using actual provider-created Feeder, Reader, migrator, and function-owner identities.
- Seven-day PITR retention does not prove RPO <=5 minutes, RTO <=60 minutes, successful isolated restore, or fencing of an old primary/Feeder after failover.
- Managed HA is not a substitute for application-level lease generation fencing.
- Current public pricing is a starting price only; exact region, node class, standby, storage, backup, egress, and tax costs must be recalculated at selection time.

**Staging gate**
- Test exact PG16 or PG17 + TimescaleDB extension version against current migrations 002–004 and the role privilege suite.
- Execute provider-specific TLS positive/negative tests, role/function-owner tests, credential rotation, point-in-time restore, measured RPO/RTO, and failover/old-primary fencing.
- Do not use a cluster plan that cannot satisfy the tested role and extension contract.

Official sources:
- https://docs.digitalocean.com/platform/regional-availability/
- https://docs.digitalocean.com/products/databases/postgresql/details/availability/
- https://docs.digitalocean.com/products/databases/postgresql/details/supported-extensions/
- https://docs.digitalocean.com/products/databases/postgresql/details/features/
- https://docs.digitalocean.com/products/databases/postgresql/details/pricing/
- https://docs.digitalocean.com/products/databases/postgresql/how-to/create/

## 3. Comparison against T0 acceptance requirements

| Requirement | Hetzner self-managed | DigitalOcean Managed PostgreSQL |
|---|---|---|
| Singapore location | Cloud Singapore listed | Managed PostgreSQL SGP1 listed |
| TimescaleDB extension | Operator installs exact build | Listed for Standard PG16/17; exact version must be checked |
| PostgreSQL superuser/role control | Full OS/DB control | Provider-managed role restrictions must be tested |
| TLS hostname verification | Operator configures and proves it | Provider CA/hostname contract must be proved |
| Seven-day PITR | Operator must implement | Provider documents 7-day PITR window |
| Restore isolation | Operator must build separate target | Must verify provider supports separate restore target |
| RPO <=5m / RTO <=60m | Not proven; timed drills required | Not proven; timed drills required |
| Old-primary fencing | Operator must implement | Must be tested with app lease generation after failover |
| Ops burden | High | Lower database operations burden |
| Cost | CCX13 listed $63.49/mo excluding IPv4; backups extra | $15/mo single-node 1GiB; HA baseline $60/mo before extras |
| Status | Candidate only | Candidate only |

## 4. Current technical interpretation

1. **Do not choose solely by monthly VM/database sticker price.** A provider that cannot satisfy the database role contract, exact TimescaleDB extension version, isolated restore, and old-primary fencing is disqualified.
2. **Do not treat seven-day PITR as RPO/RTO proof.** Those are separate measured outcomes.
3. **Do not treat managed HA as writer fencing.** After failover, the application must still ensure the old Feeder cannot write and the replacement generation advances.
4. **Do not combine staging and production evidence.** Staging uses synthetic candles and non-production credentials only.
5. **Do not place the only backup on the same VPS or storage failure domain as the primary database.**
6. Existing CI runs used disposable TimescaleDB 2.17.2 / PostgreSQL 16. Provider acceptance must pin and record the exact actual engine and extension versions; a generic claim of TimescaleDB support is insufficient.

## 5. Decision still required from the operator

No value is inferred or preselected.

- Provider/topology: Candidate A, Candidate B, or another provider.
- Region: Singapore is the researched Asia candidate, not an approved location.
- Monthly maximum budget: not supplied.
- Staging maximum one-time/temporary spend: not supplied.
- Production monthly ceiling: not supplied.
- Acceptable responsibility split: self-managed DB operations versus managed database.
- Required recovery topology: single primary with tested restore/fencing versus provider HA plus application fencing.

Until these decisions are explicitly approved:
- No account creation, VPS/database order, trial activation, DNS, network rule, credential, TLS certificate, or secret is created.
- No staging database is provisioned.
- No canonical database, production Feeder, Binance connection, or real market-data sync is activated.

## 6. Research limitations

- Prices and availability can change and are not checkout quotes.
- Provider feature pages do not replace a live staging acceptance test.
- No latency, IOPS, TLS handshake, role privilege, backup restore, RPO, RTO, or failover experiment has been run against either provider.
- No vendor SLA or marketing statement is treated as evidence that T0 meets its operational targets.
