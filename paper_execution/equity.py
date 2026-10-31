"""Persistent Paper equity history and fail-closed shared risk limits."""
from decimal import Decimal
import hashlib
import json

from pipeline.values import number, stamp

DAY_MS = 86_400_000


def parse_limits(environment):
    names = {
        "maxDrawdownPct": "PAPER_MAX_DRAWDOWN_PCT",
        "maxDailyLossUsdt": "PAPER_MAX_DAILY_LOSS_USDT",
        "maxExposureUsdt": "PAPER_MAX_EXPOSURE_USDT",
    }
    values = {}
    for field, variable in names.items():
        raw = environment.get(variable)
        if raw in (None, ""):
            return None
        value = number(str(raw))
        if value <= 0 or (field == "maxDrawdownPct" and value > 100):
            raise ValueError("Invalid shared risk limit configuration")
        values[field] = value
    return values


def ensure(connection):
    connection.execute("""CREATE TABLE IF NOT EXISTS paper_equity_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_hash TEXT NOT NULL UNIQUE,
        candle_close_ms INTEGER NOT NULL,
        observed_at_ms INTEGER NOT NULL,
        mark_price TEXT NOT NULL,
        position_base TEXT NOT NULL,
        average_entry_price TEXT NOT NULL,
        realized_pnl TEXT NOT NULL,
        fees TEXT NOT NULL,
        unrealized_pnl TEXT NOT NULL,
        equity TEXT NOT NULL,
        high_water_mark TEXT NOT NULL,
        drawdown_usdt TEXT NOT NULL,
        drawdown_pct TEXT NOT NULL,
        exposure_usdt TEXT NOT NULL,
        dataset_version TEXT NOT NULL
    )""")
    connection.execute("CREATE INDEX IF NOT EXISTS paper_equity_time ON paper_equity_history(observed_at_ms,id)")
    connection.execute("""CREATE TABLE IF NOT EXISTS paper_daily_baselines (
        utc_day_ms INTEGER PRIMARY KEY,
        baseline_at_ms INTEGER NOT NULL,
        baseline_equity TEXT NOT NULL,
        baseline_kind TEXT NOT NULL
    )""")


def record(connection, *, initial_capital, position, average, realized, fees,
           mark_price, candle_close_ms, observed_at_ms, dataset_version):
    ensure(connection)
    capital, qty, avg = number(str(initial_capital)), number(str(position), signed=True), number(str(average))
    realized_pnl, fee, mark = number(str(realized), signed=True), number(str(fees)), number(str(mark_price))
    candle_at, observed_at = stamp(candle_close_ms), stamp(observed_at_ms)
    if capital <= 0 or mark <= 0 or candle_at > observed_at or observed_at-candle_at > 30*60_000:
        raise ValueError("Invalid or stale equity mark")
    unrealized = qty * (mark-avg) if qty else Decimal(0)
    equity = capital + realized_pnl - fee + unrealized
    previous_hwm = connection.execute(
        "SELECT high_water_mark FROM paper_equity_history ORDER BY id DESC LIMIT 1"
    ).fetchone()
    hwm = max(Decimal(previous_hwm[0]), equity) if previous_hwm else equity
    drawdown = max(Decimal(0), hwm-equity)
    drawdown_pct = drawdown/hwm*100 if hwm > 0 else Decimal(0)
    exposure = abs(qty)*mark
    day_start = observed_at//DAY_MS*DAY_MS
    baseline = connection.execute(
        "SELECT baseline_equity FROM paper_daily_baselines WHERE utc_day_ms=?", (day_start,)
    ).fetchone()
    if baseline is None:
        connection.execute(
            "INSERT INTO paper_daily_baselines VALUES (?,?,?,?)",
            (day_start, observed_at, str(equity), "FIRST_OBSERVED_UTC_DAY"),
        )
    canonical = {"candleCloseMs":candle_at,"observedAtMs":observed_at,"markPrice":str(mark),
        "positionBase":str(qty),"averageEntryPrice":str(avg),"realizedPnl":str(realized_pnl),
        "fees":str(fee),"unrealizedPnl":str(unrealized),"equity":str(equity),
        "datasetVersion":str(dataset_version)}
    digest = hashlib.sha256(json.dumps(canonical,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    connection.execute("""INSERT OR IGNORE INTO paper_equity_history
        (snapshot_hash,candle_close_ms,observed_at_ms,mark_price,position_base,average_entry_price,
         realized_pnl,fees,unrealized_pnl,equity,high_water_mark,drawdown_usdt,drawdown_pct,
         exposure_usdt,dataset_version) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (digest,candle_at,observed_at,str(mark),str(qty),str(avg),str(realized_pnl),str(fee),
         str(unrealized),str(equity),str(hwm),str(drawdown),str(drawdown_pct),str(exposure),str(dataset_version)))
    return snapshot(connection, observed_at)


def snapshot(connection, now_ms, limit=500):
    ensure(connection)
    now = stamp(now_ms)
    rows = connection.execute("""SELECT id,candle_close_ms,observed_at_ms,mark_price,position_base,
        average_entry_price,realized_pnl,fees,unrealized_pnl,equity,high_water_mark,
        drawdown_usdt,drawdown_pct,exposure_usdt,dataset_version
        FROM paper_equity_history ORDER BY id DESC LIMIT ?""", (limit,)).fetchall()
    if not rows:
        return {"available":False,"reason":"EQUITY_HISTORY_EMPTY","points":[],"maxDrawdownUsdt":None,
                "maxDrawdownPct":None,"dailyPnlUsdt":None,"dailyLossUsdt":None,"exposureUsdt":None}
    points = [{
        "id":r[0],"candleCloseMs":r[1],"observedAtMs":r[2],"markPrice":r[3],"positionBase":r[4],
        "averageEntryPrice":r[5],"realizedPnl":r[6],"fees":r[7],"unrealizedPnl":r[8],"equity":r[9],
        "highWaterMark":r[10],"drawdownUsdt":r[11],"drawdownPct":r[12],"exposureUsdt":r[13],
        "datasetVersion":r[14]} for r in reversed(rows)]
    latest = points[-1]
    maximum = connection.execute("""SELECT MAX(CAST(drawdown_usdt AS REAL)),
        MAX(CAST(drawdown_pct AS REAL)) FROM paper_equity_history""").fetchone()
    day_start = now//DAY_MS*DAY_MS
    baseline = connection.execute(
        "SELECT baseline_at_ms,baseline_equity,baseline_kind FROM paper_daily_baselines WHERE utc_day_ms=?",
        (day_start,)).fetchone()
    daily_pnl = daily_loss = None
    if baseline:
        daily_pnl = Decimal(latest["equity"])-Decimal(baseline[1])
        daily_loss = max(Decimal(0), -daily_pnl)
    return {"available":True,"points":points,"latest":latest,
        "maxDrawdownUsdt":str(maximum[0]) if maximum[0] is not None else "0",
        "maxDrawdownPct":str(maximum[1]) if maximum[1] is not None else "0",
        "dailyBaselineAtMs":baseline[0] if baseline else None,
        "dailyBaselineKind":baseline[2] if baseline else None,
        "dailyPnlUsdt":str(daily_pnl) if daily_pnl is not None else None,
        "dailyLossUsdt":str(daily_loss) if daily_loss is not None else None,
        "exposureUsdt":latest["exposureUsdt"],"updatedAtMs":latest["observedAtMs"]}


def block_reason(connection, *, target_position, limit_price, limits, require_limits=True, now_ms=None):
    if limits is None:
        return ("RISK_LIMITS_UNCONFIGURED" if require_limits else None), None
    if now_ms is None:
        return ("RISK_CLOCK_UNAVAILABLE" if require_limits else None), None
    state = snapshot(connection, now_ms, limit=1)
    if not state["available"]:
        return ("RISK_EQUITY_UNAVAILABLE" if require_limits else None), None
    latest = state["latest"]
    drawdown = Decimal(latest["drawdownPct"])
    daily_loss = state["dailyLossUsdt"]
    if daily_loss is None:
        return ("RISK_DAILY_BASELINE_UNAVAILABLE" if require_limits else None), None
    if drawdown >= limits["maxDrawdownPct"]:
        return "MAX_DRAWDOWN_LIMIT", "MAX_DRAWDOWN_LIMIT"
    if Decimal(daily_loss) >= limits["maxDailyLossUsdt"]:
        return "DAILY_LOSS_LIMIT", "DAILY_LOSS_LIMIT"
    projected_exposure = abs(number(str(target_position), signed=True))*number(str(limit_price))
    if projected_exposure > limits["maxExposureUsdt"]:
        return "MAX_EXPOSURE_LIMIT", None
    return None, None
