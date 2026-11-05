-- Lease state transitions are a database capability, not arbitrary Feeder table DML.
-- The Feeder login may read the lease row for fenced writes, but all mutation
-- must pass through these SECURITY DEFINER functions.
DO $role$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 't0_feeder_lease_manager') THEN
        CREATE ROLE t0_feeder_lease_manager NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 't0_lease_manager_owner') THEN
        CREATE ROLE t0_lease_manager_owner NOLOGIN;
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_roles
         WHERE rolname IN ('t0_feeder_lease_manager', 't0_lease_manager_owner', 't0_migrator')
           AND (rolsuper OR rolcanlogin OR rolcreatedb OR rolcreaterole
                OR rolreplication OR rolbypassrls)
    ) THEN
        RAISE EXCEPTION 'T0 lease capability roles must remain restricted NOLOGIN roles'
            USING ERRCODE = '42501';
    END IF;

    IF EXISTS (
        SELECT 1
          FROM pg_auth_members membership
          JOIN pg_roles member_role ON member_role.oid = membership.member
         WHERE member_role.rolname IN ('t0_feeder_lease_manager', 't0_lease_manager_owner')
    ) THEN
        RAISE EXCEPTION 'T0 lease capability roles must not inherit privileges from other roles'
            USING ERRCODE = '42501';
    END IF;

    IF EXISTS (
        SELECT 1
          FROM pg_auth_members membership
          JOIN pg_roles granted_role ON granted_role.oid = membership.roleid
          JOIN pg_roles member_role ON member_role.oid = membership.member
         WHERE granted_role.rolname = 't0_migrator'
           AND member_role.rolname <> 't0_migrator_login'
    ) THEN
        RAISE EXCEPTION 't0_migrator may only be granted to the ephemeral t0_migrator_login role'
            USING ERRCODE = '42501';
    END IF;

    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 't0_migrator')
       AND (
           NOT EXISTS (
               SELECT 1 FROM pg_roles
                WHERE rolname = 't0_migrator_login'
                  AND rolcanlogin
                  AND NOT rolsuper
                  AND NOT rolcreatedb
                  AND NOT rolcreaterole
                  AND NOT rolreplication
                  AND NOT rolbypassrls
           )
           OR EXISTS (
               SELECT 1
                 FROM pg_auth_members membership
                 JOIN pg_roles granted_role ON granted_role.oid = membership.roleid
                 JOIN pg_roles member_role ON member_role.oid = membership.member
                WHERE granted_role.rolname = 't0_migrator_login'
           )
           OR (
               SELECT count(*)
                 FROM pg_auth_members membership
                 JOIN pg_roles granted_role ON granted_role.oid = membership.roleid
                 JOIN pg_roles member_role ON member_role.oid = membership.member
                WHERE member_role.rolname = 't0_migrator_login'
                  AND granted_role.rolname = 't0_migrator'
           ) <> 1
           OR EXISTS (
               SELECT 1
                 FROM pg_auth_members membership
                 JOIN pg_roles granted_role ON granted_role.oid = membership.roleid
                 JOIN pg_roles member_role ON member_role.oid = membership.member
                WHERE member_role.rolname = 't0_migrator_login'
                  AND (granted_role.rolname <> 't0_migrator' OR membership.admin_option)
           )
           OR EXISTS (
               SELECT 1
                 FROM pg_auth_members membership
                 JOIN pg_roles granted_role ON granted_role.oid = membership.roleid
                 JOIN pg_roles member_role ON member_role.oid = membership.member
                WHERE member_role.rolname = 't0_migrator_login'
                  AND granted_role.rolname <> 't0_migrator'
           )
       ) THEN
        RAISE EXCEPTION 't0_migrator_login must be an isolated restricted LOGIN member only of t0_migrator'
            USING ERRCODE = '42501';
    END IF;

    IF EXISTS (
        SELECT 1
          FROM pg_auth_members membership
          JOIN pg_roles granted_role ON granted_role.oid = membership.roleid
          JOIN pg_roles member_role ON member_role.oid = membership.member
         WHERE granted_role.rolname = 't0_lease_manager_owner'
           AND member_role.rolname <> 't0_migrator'
    ) THEN
        RAISE EXCEPTION 'T0 SECURITY DEFINER owner role must not be granted to runtime or login roles'
            USING ERRCODE = '42501';
    END IF;
END;
$role$;

CREATE OR REPLACE FUNCTION market_data.acquire_feeder_lease(
    p_lease_name TEXT,
    p_owner_id TEXT,
    p_ttl_seconds INTEGER
)
RETURNS TABLE(generation BIGINT, expires_at TIMESTAMPTZ)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, market_data
AS $function$
DECLARE
    v_owner_id TEXT;
    v_generation BIGINT;
    v_expires_at TIMESTAMPTZ;
    v_active BOOLEAN;
BEGIN
    IF p_lease_name IS DISTINCT FROM 'binance-btcusdt-canonical' THEN
        RAISE EXCEPTION 'invalid canonical feeder lease identity'
            USING ERRCODE = '42501';
    END IF;
    IF p_lease_name IS NULL OR length(btrim(p_lease_name)) = 0
       OR p_owner_id IS NULL OR length(btrim(p_owner_id)) = 0
       OR p_ttl_seconds IS NULL OR p_ttl_seconds <= 0 THEN
        RAISE EXCEPTION 'invalid feeder lease request'
            USING ERRCODE = '22023';
    END IF;

    INSERT INTO market_data.feeder_leases
        (lease_name, owner_id, generation, expires_at)
    VALUES
        (p_lease_name, NULL, 0, '1970-01-01 00:00:00+00'::timestamptz)
    ON CONFLICT (lease_name) DO NOTHING;

    SELECT lease.owner_id, lease.generation, lease.expires_at
      INTO v_owner_id, v_generation, v_expires_at
      FROM market_data.feeder_leases AS lease
     WHERE lease.lease_name = p_lease_name
     FOR UPDATE;

    SELECT v_expires_at > clock_timestamp() INTO v_active;
    IF v_active THEN
        IF v_owner_id = p_owner_id THEN
            RETURN QUERY SELECT v_generation, v_expires_at;
        END IF;
        RETURN;
    END IF;

    UPDATE market_data.feeder_leases AS lease
       SET owner_id = p_owner_id,
           generation = lease.generation + 1,
           expires_at = clock_timestamp() + (p_ttl_seconds * interval '1 second'),
           updated_at = clock_timestamp()
     WHERE lease.lease_name = p_lease_name
     RETURNING lease.generation, lease.expires_at
      INTO v_generation, v_expires_at;

    RETURN QUERY SELECT v_generation, v_expires_at;
END;
$function$;

CREATE OR REPLACE FUNCTION market_data.heartbeat_feeder_lease(
    p_lease_name TEXT,
    p_owner_id TEXT,
    p_generation BIGINT,
    p_ttl_seconds INTEGER
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, market_data
AS $function$
DECLARE
    v_updated BOOLEAN;
BEGIN
    IF p_lease_name IS DISTINCT FROM 'binance-btcusdt-canonical' THEN
        RAISE EXCEPTION 'invalid canonical feeder lease identity'
            USING ERRCODE = '42501';
    END IF;
    IF p_lease_name IS NULL OR length(btrim(p_lease_name)) = 0
       OR p_owner_id IS NULL OR length(btrim(p_owner_id)) = 0
       OR p_generation IS NULL OR p_generation < 1
       OR p_ttl_seconds IS NULL OR p_ttl_seconds <= 0 THEN
        RAISE EXCEPTION 'invalid feeder lease heartbeat'
            USING ERRCODE = '22023';
    END IF;

    UPDATE market_data.feeder_leases AS lease
       SET expires_at = clock_timestamp() + (p_ttl_seconds * interval '1 second'),
           updated_at = clock_timestamp()
     WHERE lease.lease_name = p_lease_name
       AND lease.owner_id = p_owner_id
       AND lease.generation = p_generation
       AND lease.expires_at > clock_timestamp()
     RETURNING TRUE INTO v_updated;

    RETURN COALESCE(v_updated, FALSE);
END;
$function$;

CREATE OR REPLACE FUNCTION market_data.is_current_feeder_lease(
    p_lease_name TEXT,
    p_owner_id TEXT,
    p_generation BIGINT
)
RETURNS BOOLEAN
LANGUAGE SQL
SECURITY DEFINER
SET search_path = pg_catalog, market_data
AS $function$
    SELECT CASE
      WHEN p_lease_name IS DISTINCT FROM 'binance-btcusdt-canonical' THEN FALSE
      ELSE EXISTS (
        SELECT 1
          FROM market_data.feeder_leases AS lease
         WHERE lease.lease_name = p_lease_name
           AND lease.owner_id = p_owner_id
           AND lease.generation = p_generation
           AND lease.expires_at > clock_timestamp()
      )
    END;
$function$;

CREATE OR REPLACE FUNCTION market_data.release_feeder_lease(
    p_lease_name TEXT,
    p_owner_id TEXT,
    p_generation BIGINT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, market_data
AS $function$
DECLARE
    v_updated BOOLEAN;
BEGIN
    IF p_lease_name IS DISTINCT FROM 'binance-btcusdt-canonical' THEN
        RAISE EXCEPTION 'invalid canonical feeder lease identity'
            USING ERRCODE = '42501';
    END IF;
    IF p_lease_name IS NULL OR length(btrim(p_lease_name)) = 0
       OR p_owner_id IS NULL OR length(btrim(p_owner_id)) = 0
       OR p_generation IS NULL OR p_generation < 1 THEN
        RAISE EXCEPTION 'invalid feeder lease release'
            USING ERRCODE = '22023';
    END IF;

    UPDATE market_data.feeder_leases AS lease
       SET owner_id = NULL,
           expires_at = '1970-01-01 00:00:00+00'::timestamptz,
           updated_at = clock_timestamp()
     WHERE lease.lease_name = p_lease_name
       AND lease.owner_id = p_owner_id
       AND lease.generation = p_generation
     RETURNING TRUE INTO v_updated;

    RETURN COALESCE(v_updated, FALSE);
END;
$function$;

REVOKE ALL ON FUNCTION market_data.acquire_feeder_lease(TEXT, TEXT, INTEGER) FROM PUBLIC;
REVOKE ALL ON FUNCTION market_data.heartbeat_feeder_lease(TEXT, TEXT, BIGINT, INTEGER) FROM PUBLIC;
REVOKE ALL ON FUNCTION market_data.release_feeder_lease(TEXT, TEXT, BIGINT) FROM PUBLIC;
REVOKE ALL ON FUNCTION market_data.is_current_feeder_lease(TEXT, TEXT, BIGINT) FROM PUBLIC;

GRANT USAGE ON SCHEMA market_data TO t0_lease_manager_owner;
GRANT SELECT, INSERT, UPDATE ON market_data.feeder_leases TO t0_lease_manager_owner;
GRANT CREATE ON SCHEMA market_data TO t0_lease_manager_owner;

ALTER FUNCTION market_data.acquire_feeder_lease(TEXT, TEXT, INTEGER)
    OWNER TO t0_lease_manager_owner;
ALTER FUNCTION market_data.heartbeat_feeder_lease(TEXT, TEXT, BIGINT, INTEGER)
    OWNER TO t0_lease_manager_owner;
ALTER FUNCTION market_data.release_feeder_lease(TEXT, TEXT, BIGINT)
    OWNER TO t0_lease_manager_owner;
ALTER FUNCTION market_data.is_current_feeder_lease(TEXT, TEXT, BIGINT)
    OWNER TO t0_lease_manager_owner;

REVOKE CREATE ON SCHEMA market_data FROM t0_lease_manager_owner;

REVOKE ALL ON market_data.feeder_leases FROM t0_feeder_lease_manager;
REVOKE ALL ON market_data.feeder_leases FROM t0_feeder_writer;
REVOKE ALL ON market_data.candles FROM t0_feeder_lease_manager;
GRANT EXECUTE ON FUNCTION market_data.acquire_feeder_lease(TEXT, TEXT, INTEGER)
    TO t0_feeder_lease_manager;
GRANT EXECUTE ON FUNCTION market_data.heartbeat_feeder_lease(TEXT, TEXT, BIGINT, INTEGER)
    TO t0_feeder_lease_manager;
GRANT EXECUTE ON FUNCTION market_data.release_feeder_lease(TEXT, TEXT, BIGINT)
    TO t0_feeder_lease_manager;
GRANT EXECUTE ON FUNCTION market_data.is_current_feeder_lease(TEXT, TEXT, BIGINT)
    TO t0_feeder_lease_manager;
