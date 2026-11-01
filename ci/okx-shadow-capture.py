"""Manual OKX BTC-USDT-SWAP shadow snapshot; isolated from Binance canonical data."""
import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT=Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path: sys.path.insert(0,str(REPO_ROOT))

from market_data.okx_swap import OkxSwapAdapter, INTERVAL_MS
from market_data.okx_swap_store import OkxSwapSQLiteStore

root=Path(os.environ.get("CM_BUILD_DIR",".")).resolve()
artifact_dir=root/"okx-shadow-artifacts"; artifact_dir.mkdir(exist_ok=True)
db_path=artifact_dir/"okx-shadow.sqlite3"
canonical_path=Path(os.environ.get("MARKET_DATA_DB",str(root/"market_data.sqlite3"))).expanduser().resolve()
canonical_path.parent.mkdir(parents=True,exist_ok=True)
if not canonical_path.exists(): canonical_path.touch()
store=OkxSwapSQLiteStore(db_path,canonical_db_path=canonical_path)
adapter=OkxSwapAdapter()
now=time.time_ns()//1_000_000
report={"source":"okx.api.v5","instType":"SWAP","symbol":"BTC-USDT-SWAP","marketType":"LINEAR_PERPETUAL","datasets":{}}
for timeframe,interval in INTERVAL_MS.items():
    end=(now//interval)*interval; start=end-24*60*60*1000
    candles=adapter.fetch_closed_window(timeframe,start,end,now_ms=now)
    inserted=store.insert(candles); dataset=store.read_window(timeframe,start,end)
    report["datasets"][timeframe]={"inserted":inserted,"coverage":dataset["coverage"],"datasetVersion":dataset["datasetVersion"]}
    if not candles: raise SystemExit(f"No confirmed closed OKX candles returned for {timeframe}")
with (artifact_dir/"okx-shadow-report.json").open("w",encoding="utf-8") as stream:
    json.dump(report,stream,sort_keys=True,indent=2); stream.write("\n")
print(json.dumps(report,sort_keys=True))
