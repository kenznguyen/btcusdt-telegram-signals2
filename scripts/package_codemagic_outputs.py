"""Package only selected research/backtest outputs for GitHub Release storage.

Never include environment variables, API keys, raw config files or full OHLCV.
"""
import argparse
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

def create_bundle(kind, root, output):
    if kind not in ("freqtrade", "freqai"):
        raise ValueError("Unsupported bundle kind")
    root = Path(root).resolve()
    result_dir = root / ("freqtrade-futures-results" if kind == "freqtrade" else "freqai-research-results")
    if not result_dir.is_dir():
        raise FileNotFoundError(result_dir)
    if kind == "freqtrade":
        required = ["run-manifest.json", "equity-5m-summary.json", "fill-reconciliation.csv"]
        optional = ["history-coverage.json", "liquidation-funding-input-audit.json",
                    "funding-timeline-estimate.json", "walkforward-windows.json"]
        result_folder = root / "freqtrade-futures-data" / "backtest_results"
        zips = sorted(result_folder.glob("backtest-result-*.zip"))
        if not zips:
            raise FileNotFoundError("Missing actual Freqtrade backtest ZIP")
        files = [result_dir / name for name in required] + [zips[-1]]
    else:
        required = ["run-manifest.json", "freqai-research-report.json",
                    "freqai-research-predictions.csv"]
        optional = ["window.json", "freqai-backtest.log"]
        files = [result_dir / name for name in required]
    files += [result_dir / name for name in optional if (result_dir / name).is_file()]
    for path in files:
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(f"Missing required output: {path}")
        if not path.resolve().is_relative_to(root):
            raise ValueError("Output must be within build directory")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=6) as dest:
        for path in files:
            dest.write(path, path.relative_to(root).as_posix())
    if output.stat().st_size <= 0:
        raise ValueError("Empty release bundle")
    return len(files)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--kind", required=True, choices=["freqtrade", "freqai"])
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    print("Packaged", create_bundle(a.kind, a.root, a.output), "audited outputs into", a.output)

if __name__ == "__main__":
    main()
