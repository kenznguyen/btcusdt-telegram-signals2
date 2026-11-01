"""Dedicated SQLite store for OKX BTC-USDT-SWAP shadow candles."""
import hashlib
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from market_data.okx_swap import OkxSwapCandle, EXCHANGE, INTERVAL_MS, MARKET_TYPE, MAX_CANDLES, SYMBOL

def _path(value, label):
    if value is None or not str(value).strip() or str(value) == ":memory:":
        raise ValueError(f"{label} must be a dedicated on-disk SQLite path")
    return Path(value).expanduser().resolve()

class OkxSwapSQLiteStore:
    def __init__(self, db_path, *, canonical_db_path=None):
        self.path=_path(db_path,"OKX shadow database")
        canonical=canonical_db_path or os.environ.get("MARKET_DATA_DB")
        if not canonical: raise ValueError("Binance canonical database path is required for isolation")
        canonical_path=_path(canonical,"Binance canonical database")
        same=self.path==canonical_path
        if not same and self.path.exists() and canonical_path.exists(): same=os.path.samefile(self.path,canonical_path)
        if same: raise ValueError("OKX shadow database must be separate from Binance canonical storage")
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with closing(sqlite3.connect(self.path,timeout=5)) as db, db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS okx_swap_candles (
                exchange TEXT NOT NULL CHECK(exchange='okx'),
                market_type TEXT NOT NULL CHECK(market_type='LINEAR_PERPETUAL'),
                inst_type TEXT NOT NULL CHECK(inst_type='SWAP'),
                symbol TEXT NOT NULL CHECK(symbol='BTC-USDT-SWAP'),
                timeframe TEXT NOT NULL CHECK(timeframe IN ('15m','1h')),
                open_time_ms INTEGER NOT NULL,
                open TEXT NOT NULL, high TEXT NOT NULL, low TEXT NOT NULL, close TEXT NOT NULL,
                volume_btc TEXT NOT NULL, turnover_usdt TEXT NOT NULL, available_at_ms INTEGER NOT NULL,
                PRIMARY KEY(exchange,market_type,inst_type,symbol,timeframe,open_time_ms)
            )""")

    def insert(self,candles):
        batch=list(candles)
        if any(not isinstance(x,OkxSwapCandle) for x in batch):
            raise ValueError("Only validated OkxSwapCandle values can be stored")
        count=0
        with closing(sqlite3.connect(self.path,timeout=5)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            for x in batch:
                key=("okx","LINEAR_PERPETUAL","SWAP",SYMBOL,x.timeframe,x.open_time_ms)
                values=(x.open,x.high,x.low,x.close,x.volume_btc,x.turnover_usdt)
                old=db.execute("""SELECT open,high,low,close,volume_btc,turnover_usdt FROM okx_swap_candles
                    WHERE exchange=? AND market_type=? AND inst_type=? AND symbol=? AND timeframe=? AND open_time_ms=?""",key).fetchone()
                if old is not None:
                    if old != values: raise ValueError("Conflicting OKX candle; existing history is immutable")
                    continue
                db.execute("INSERT INTO okx_swap_candles VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",key+values+(x.available_at_ms,))
                count+=1
        return count

    def read_window(self,timeframe,start_ms,end_ms):
        interval=INTERVAL_MS.get(timeframe)
        if interval is None or type(start_ms) is not int or type(end_ms) is not int:
            raise ValueError("Invalid OKX read window")
        if start_ms%interval or end_ms%interval or not 0<end_ms-start_ms<=MAX_CANDLES*interval:
            raise ValueError("OKX read window must be aligned and bounded")
        with closing(sqlite3.connect(self.path.as_uri()+"?mode=ro",uri=True)) as db:
            db.row_factory=sqlite3.Row
            rows=db.execute("""SELECT * FROM okx_swap_candles WHERE exchange=? AND market_type=? AND inst_type=?
                AND symbol=? AND timeframe=? AND open_time_ms>=? AND open_time_ms<? ORDER BY open_time_ms""",
                ("okx","LINEAR_PERPETUAL","SWAP",SYMBOL,timeframe,start_ms,end_ms)).fetchall()
        candles=[{
            "exchange":r["exchange"],"marketType":r["market_type"],"instType":r["inst_type"],"symbol":r["symbol"],
            "timeframe":r["timeframe"],"openTimeMs":r["open_time_ms"],"closeTimeMs":r["open_time_ms"]+interval,
            "open":r["open"],"high":r["high"],"low":r["low"],"close":r["close"],
            "volumeBtc":r["volume_btc"],"turnoverUsdt":r["turnover_usdt"],"isClosed":True,
            "availableAtMs":r["available_at_ms"],"availabilityKind":"FIRST_OBSERVED",
            "source":"okx.api.v5.market.candles",
        } for r in rows]
        gaps=[]; cursor=start_ms
        for item in candles:
            if item["openTimeMs"]>cursor: gaps.append({"startMs":cursor,"endMs":item["openTimeMs"]})
            cursor=item["closeTimeMs"]
        if cursor<end_ms: gaps.append({"startMs":cursor,"endMs":end_ms})
        result={"exchange":"okx","marketType":"LINEAR_PERPETUAL","instType":"SWAP","symbol":SYMBOL,
                "timeframe":timeframe,"startMs":start_ms,"endMs":end_ms,"candles":candles}
        digest=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
        result["datasetVersion"]="sha256:"+digest
        result["coverage"]={"expected":(end_ms-start_ms)//interval,"returned":len(candles),"complete":not gaps,"gaps":gaps}
        return result
