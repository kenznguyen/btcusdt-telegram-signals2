-- Initial canonical market-data schema for PostgreSQL + TimescaleDB.
-- Apply only to a dedicated target database after reviewing the migration plan.
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE SCHEMA IF NOT EXISTS market_data;

CREATE TABLE IF NOT EXISTS market_data.schema_migrations (
    migration_id TEXT PRIMARY KEY,
    checksum_sha256 TEXT NOT NULL CHECK (checksum_sha256 ~ '^[0-9a-f]{64}$'),
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS market_data.instruments (
    exchange TEXT NOT NULL,
    market_type TEXT NOT NULL,
    symbol TEXT NOT NULL,
    base_asset TEXT NOT NULL,
    quote_asset TEXT NOT NULL,
    settlement_asset TEXT NOT NULL,
    instrument_kind TEXT NOT NULL,
    is_active BOOLEAN NOT NULL,
    PRIMARY KEY (exchange, market_type, symbol)
);

INSERT INTO market_data.instruments (
    exchange, market_type, symbol, base_asset, quote_asset,
    settlement_asset, instrument_kind, is_active
) VALUES (
    'binance', 'USDT_PERPETUAL', 'BTCUSDT', 'BTC', 'USDT',
    'USDT', 'LINEAR_PERPETUAL', TRUE
)
ON CONFLICT (exchange, market_type, symbol) DO NOTHING;

CREATE TABLE IF NOT EXISTS market_data.candles (
    exchange TEXT NOT NULL CHECK (exchange = 'binance'),
    market_type TEXT NOT NULL CHECK (market_type = 'USDT_PERPETUAL'),
    symbol TEXT NOT NULL CHECK (symbol = 'BTCUSDT'),
    timeframe TEXT NOT NULL CHECK (timeframe IN ('15m', '1h')),
    open_time_ms BIGINT NOT NULL CHECK (open_time_ms >= 0),
    open NUMERIC NOT NULL CHECK (
        open > 0 AND open::text NOT IN ('NaN', 'Infinity', '-Infinity')
    ),
    high NUMERIC NOT NULL CHECK (
        high > 0 AND high::text NOT IN ('NaN', 'Infinity', '-Infinity')
    ),
    low NUMERIC NOT NULL CHECK (
        low > 0 AND low::text NOT IN ('NaN', 'Infinity', '-Infinity')
    ),
    close NUMERIC NOT NULL CHECK (
        close > 0 AND close::text NOT IN ('NaN', 'Infinity', '-Infinity')
    ),
    volume NUMERIC NOT NULL CHECK (
        volume >= 0 AND volume::text NOT IN ('NaN', 'Infinity', '-Infinity')
    ),
    available_at_ms BIGINT NOT NULL CHECK (available_at_ms >= 0),
    ingestion_batch_id UUID NULL,
    PRIMARY KEY (exchange, market_type, symbol, timeframe, open_time_ms),
    CHECK (
        open_time_ms <= 9223372036854775807 -
            CASE timeframe WHEN '15m' THEN 900000 ELSE 3600000 END
    ),
    CHECK (
        open_time_ms % CASE timeframe
            WHEN '15m' THEN 900000 ELSE 3600000
        END = 0
    ),
    CHECK (
        available_at_ms::numeric >= open_time_ms::numeric +
            CASE timeframe WHEN '15m' THEN 900000 ELSE 3600000 END
    ),
    CHECK (high >= GREATEST(open, low, close)),
    CHECK (low <= LEAST(open, high, close))
);

SELECT create_hypertable(
    'market_data.candles',
    'open_time_ms',
    chunk_time_interval => 2592000000,
    if_not_exists => TRUE
);
