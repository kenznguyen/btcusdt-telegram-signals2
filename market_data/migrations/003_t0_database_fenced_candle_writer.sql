-- All canonical PostgreSQL candle writes must pass through this function.
-- The migration owner owns the SECURITY DEFINER function; runtime roles receive
-- EXECUTE explicitly during role provisioning, never through PUBLIC.
CREATE OR REPLACE FUNCTION market_data.write_canonical_candle(
    p_lease_name TEXT,
    p_owner_id TEXT,
    p_generation BIGINT,
    p_exchange TEXT,
    p_market_type TEXT,
    p_symbol TEXT,
    p_timeframe TEXT,
    p_open_time_ms BIGINT,
    p_open NUMERIC,
    p_high NUMERIC,
    p_low NUMERIC,
    p_close NUMERIC,
    p_volume NUMERIC,
    p_available_at_ms BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, market_data
AS $function$
DECLARE
    current_lease RECORD;
    inserted_open_time BIGINT;
    existing_candle RECORD;
BEGIN
    SELECT owner_id, generation, expires_at
      INTO current_lease
      FROM market_data.feeder_leases
     WHERE lease_name = p_lease_name
     FOR UPDATE;

    IF NOT FOUND
       OR current_lease.owner_id IS DISTINCT FROM p_owner_id
       OR current_lease.generation IS DISTINCT FROM p_generation
       OR current_lease.expires_at <= clock_timestamp() THEN
        RAISE EXCEPTION 'canonical candle write rejected: lease is not current'
            USING ERRCODE = '42501';
    END IF;

    INSERT INTO market_data.candles (
        exchange, market_type, symbol, timeframe, open_time_ms,
        open, high, low, close, volume, available_at_ms
    ) VALUES (
        p_exchange, p_market_type, p_symbol, p_timeframe, p_open_time_ms,
        p_open, p_high, p_low, p_close, p_volume, p_available_at_ms
    )
    ON CONFLICT (exchange, market_type, symbol, timeframe, open_time_ms)
    DO NOTHING
    RETURNING open_time_ms INTO inserted_open_time;

    IF FOUND THEN
        PERFORM 1
          FROM market_data.feeder_leases
         WHERE lease_name = p_lease_name
           AND owner_id = p_owner_id
           AND generation = p_generation
           AND expires_at > clock_timestamp();
        IF NOT FOUND THEN
            RAISE EXCEPTION 'canonical candle write rejected: lease expired before commit'
                USING ERRCODE = '42501';
        END IF;
        RETURN TRUE;
    END IF;

    SELECT open, high, low, close, volume
      INTO existing_candle
      FROM market_data.candles
     WHERE exchange = p_exchange
       AND market_type = p_market_type
       AND symbol = p_symbol
       AND timeframe = p_timeframe
       AND open_time_ms = p_open_time_ms;

    IF NOT FOUND
       OR ROW(existing_candle.open, existing_candle.high, existing_candle.low,
              existing_candle.close, existing_candle.volume)
          IS DISTINCT FROM
          ROW(p_open, p_high, p_low, p_close, p_volume) THEN
        RAISE EXCEPTION 'conflicting closed candle; canonical history was not overwritten'
            USING ERRCODE = 'P0001';
    END IF;

    PERFORM 1
      FROM market_data.feeder_leases
     WHERE lease_name = p_lease_name
       AND owner_id = p_owner_id
       AND generation = p_generation
       AND expires_at > clock_timestamp();
    IF NOT FOUND THEN
        RAISE EXCEPTION 'canonical candle write rejected: lease expired before commit'
            USING ERRCODE = '42501';
    END IF;

    RETURN FALSE;
END;
$function$;

REVOKE ALL ON FUNCTION market_data.write_canonical_candle(
    TEXT, TEXT, BIGINT, TEXT, TEXT, TEXT, TEXT, BIGINT,
    NUMERIC, NUMERIC, NUMERIC, NUMERIC, NUMERIC, BIGINT
) FROM PUBLIC;

-- Stable NOLOGIN capability role: provisioned Feeder login roles must be
-- members of this role and must not receive direct candle-table write grants.
DO $role$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 't0_feeder_writer') THEN
        CREATE ROLE t0_feeder_writer NOLOGIN;
    END IF;
END;
$role$;

REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON market_data.candles FROM t0_feeder_writer;
GRANT EXECUTE ON FUNCTION market_data.write_canonical_candle(
    TEXT, TEXT, BIGINT, TEXT, TEXT, TEXT, TEXT, BIGINT,
    NUMERIC, NUMERIC, NUMERIC, NUMERIC, NUMERIC, BIGINT
) TO t0_feeder_writer;
