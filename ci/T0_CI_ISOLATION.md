# T0 CI database isolation contract

## SQLite audit and test processes

CI must set `T0_TEST_MODE=1`, `T0_TEST_ROOT`, and `T0_TEST_DB`.
The root must already exist. The selected database path must resolve inside
that root and match `T0_TEST_DB` exactly. When any of
`MARKET_DATA_DB`, `T0_FEEDER_LEASE_DB`, `PAPER_DB`, or
`PAPER_TRADING_DB` is set, it must resolve to the same disposable database.
The guard runs before SQLite is opened by the CI-only read-only audit modules.

GitHub Actions creates the root below `RUNNER_TEMP` and exports its paths
through `GITHUB_ENV`. Tests that create their own fixtures pass an explicit
temporary root and exact DB path. Production Feeder/storage modules do not
import the CI guard and are not forced into a disposable root.

## PostgreSQL / TimescaleDB integration gate

The optional manual TimescaleDB gate requires two GitHub Actions secrets:

- `MARKET_DATA_TEST_DATABASE_URL`: the dedicated disposable test DSN.
- `MARKET_DATA_TEST_DATABASE_URL_SHA256`: SHA-256 of the exact DSN string
  after trimming surrounding whitespace.

The second secret is an explicit endpoint allowlist. A missing or mismatched
fingerprint stops the shell script before importing the PostgreSQL driver or
opening a connection. Changing the hostname, database name, credentials, or
query parameters changes the fingerprint and fails closed.

To calculate the fingerprint without displaying the DSN, place the DSN in an
environment variable locally and run:

```bash
python -c 'import hashlib,os; print(hashlib.sha256(os.environ["MARKET_DATA_TEST_DATABASE_URL"].strip().encode()).hexdigest())'
```

Store only the resulting 64-character hexadecimal digest as
`MARKET_DATA_TEST_DATABASE_URL_SHA256`.

## Evidence and limitations

The automated workflow runs on GitHub-hosted runners, checks out the exact
triggering SHA, creates an ephemeral disposable root, runs guard and regression
tests, compiles the changed CI modules, and uploads the run log and source SHA.

This contract does not claim that GitHub-hosted runner network egress is
blocked. The PostgreSQL fingerprint proves the integration DSN matches the
explicitly allowlisted value; it does not independently prove that the remote
database is disposable. The owner must only allowlist a dedicated test
database. Path resolution and symlink checks reduce path escape risk but do
not eliminate all filesystem TOCTOU races or provide an OS-level sandbox.
Production canonical DB activation and Feeder runtime certification remain
separate gates.
