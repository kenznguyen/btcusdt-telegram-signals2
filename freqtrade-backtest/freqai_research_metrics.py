"""Independent LightGBM walk-forward validation on OKX 15m + CLOSED H1.

This is a diagnostic baseline run separately from FreqAI's internal model.
Never call these estimates FreqAI's own backtest predictions or live profit.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def build_samples(m15, h1):
    base = m15[["date", "open", "high", "low", "close", "volume"]].copy()
    hour = h1[["date", "close", "volume"]].copy()
    base["date"] = pd.to_datetime(base["date"], utc=True)
    hour["date"] = pd.to_datetime(hour["date"], utc=True)
    if not base["date"].is_monotonic_increasing or not hour["date"].is_monotonic_increasing:
        raise ValueError("Candle timestamps must be sorted")
    if base["date"].duplicated().any() or hour["date"].duplicated().any():
        raise ValueError("Duplicate candles")
    # A candle timestamp is its OPEN. An H1 feature becomes known only at close.
    hour["h1_available"] = hour["date"] + pd.Timedelta(hours=1)
    hour = hour.rename(columns={"close": "h1_close", "volume": "h1_volume"})
    base["available"] = base["date"] + pd.Timedelta(minutes=15)
    base = pd.merge_asof(base, hour[["h1_available", "h1_close", "h1_volume"]],
                         left_on="available", right_on="h1_available",
                         direction="backward", allow_exact_matches=True)
    close = base["close"]
    change = close.diff()
    up = change.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
    down = (-change.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
    base["rsi14"] = 100 - 100 / (1 + up / down.replace(0, np.nan))
    hlc3 = (base["high"] + base["low"] + close) / 3
    flow = hlc3 * base["volume"]
    positive = flow.where(hlc3.diff() > 0, 0.0).rolling(14).sum()
    negative = flow.where(hlc3.diff() < 0, 0.0).rolling(14).sum()
    base["mfi14"] = 100 - 100 / (1 + positive / negative.replace(0, np.nan))
    ma = close.rolling(20).mean()
    std = close.rolling(20).std(ddof=0)
    base["percent_b"] = (close - (ma - 2*std)) / (4*std.replace(0, np.nan))
    base["bb_width"] = 4 * std / ma
    base["return1"] = close.pct_change(1)
    base["return4"] = close.pct_change(4)
    base["volatility20"] = base["return1"].rolling(20).std()
    base["volume_ratio"] = base["volume"] / base["volume"].rolling(20).mean()
    base["h1_distance"] = close / base["h1_close"] - 1
    # Target is known 4 candles later, at end of the fourth future candle.
    base["target"] = close.shift(-4) / close - 1
    base["label_available"] = base["available"] + pd.Timedelta(hours=1)
    features = ["rsi14", "mfi14", "percent_b", "bb_width",
                "return1", "return4", "volatility20", "volume_ratio",
                "h1_distance"]
    base = base.replace([np.inf, -np.inf], np.nan)
    return base, features


def run_walkforward(m15, h1, start, end, train_days=45, step_days=15):
    from lightgbm import LGBMRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    df, features = build_samples(m15, h1)
    start, end = pd.Timestamp(start).tz_convert("UTC"), pd.Timestamp(end).tz_convert("UTC")
    windows, predictions = [], []
    cursor = start
    while cursor < end:
        stop = min(cursor + pd.Timedelta(days=step_days), end)
        # Training data must have its future LABEL known before the
        # validation window starts (purging all 4-bar overlap).
        train = df.loc[
            (df["available"] >= cursor - pd.Timedelta(days=train_days)) &
            (df["label_available"] <= cursor) &
            df["target"].notna() &
            df[features].notna().all(axis=1)
        ]
        test = df.loc[
            (df["available"] >= cursor) & (df["available"] < stop) &
            (df["label_available"] <= end) &
            df["target"].notna() &
            df[features].notna().all(axis=1)
        ]
        if len(train) < 1000 or len(test) < 100:
            raise ValueError(f"Insufficient train/test at {cursor.isoformat()}: {len(train)}/{len(test)}")
        model = LGBMRegressor(n_estimators=100, learning_rate=.05,
                             num_leaves=15, verbosity=-1, random_state=42,
                             n_jobs=2)
        model.fit(train[features], train["target"])
        y = test["target"].to_numpy()
        yhat = model.predict(test[features])
        mae = float(mean_absolute_error(y, yhat))
        rmse = float(np.sqrt(mean_squared_error(y, yhat)))
        baseline = float(mean_absolute_error(y, np.zeros_like(y)))
        windows.append({
            "start_utc": cursor.isoformat(), "end_exclusive_utc": stop.isoformat(),
            "train_rows": int(len(train)), "test_rows": int(len(test)),
            "train_last_label_available": train["label_available"].max().isoformat(),
            "mae": mae, "rmse": rmse, "zero_return_baseline_mae": baseline,
            "direction_accuracy": float(np.mean((yhat > 0) == (y > 0))),
            "beats_zero_baseline": bool(mae < baseline)
        })
        for time, target, pred in zip(test["available"], y, yhat):
            predictions.append({"available_utc": time.isoformat(),
                                "actual_forward_return": float(target),
                                "predicted_forward_return": float(pred),
                                "window_start_utc": cursor.isoformat()})
        cursor = stop
    if not predictions:
        raise ValueError("No out-of-sample predictions")
    true = np.array([p["actual_forward_return"] for p in predictions])
    pred = np.array([p["predicted_forward_return"] for p in predictions])
    return {
        "engine": "independent LightGBM walk-forward diagnostics; not FreqAI internal predictions",
        "target": "four M15 closed-candle forward return (60 minutes)",
        "timeframe": "15m", "informative_timeframe": "1h closed only",
        "no_live_orders": True, "strategy_parameters_unchanged": True,
        "not_profitability_evidence": True,
        "train_days": train_days, "step_days": step_days,
        "oos_rows": len(predictions),
        "oos_mae": float(np.mean(np.abs(true - pred))),
        "zero_return_mae": float(np.mean(np.abs(true))),
        "oos_direction_accuracy": float(np.mean((true > 0) == (pred > 0))),
        "windows": windows,
        "predictions": predictions,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--datadir", required=True, type=Path)
    parser.add_argument("--timerange-start", required=True)
    parser.add_argument("--timerange-end", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    files = {}
    for tf in ("15m", "1h"):
        paths = list(args.datadir.rglob(f"BTC_USDT_USDT-{tf}-futures.feather"))
        if len(paths) != 1:
            raise ValueError(f"Missing/ambiguous {tf} OHLCV")
        files[tf] = pd.read_feather(paths[0])
    result = run_walkforward(files["15m"], files["1h"],
                             pd.Timestamp(args.timerange_start, tz="UTC"),
                             pd.Timestamp(args.timerange_end, tz="UTC"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({k: v for k, v in result.items() if k != "predictions"},
                                      indent=2) + "\n", encoding="utf-8")
    predictions = args.output.with_name("freqai-research-predictions.csv")
    pd.DataFrame(result["predictions"]).to_csv(predictions, index=False)
    print("Out-of-sample MAE:", result["oos_mae"],
          "zero-return baseline:", result["zero_return_mae"],
          "windows:", len(result["windows"]))


if __name__ == "__main__":
    main()
