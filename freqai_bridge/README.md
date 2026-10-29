# FreqAI prediction-only bridge — tầng 2

This bridge consumes **actual FreqAI predictions**, verifies their input OHLCV
against the canonical store and emits a bounded JSON artifact for the paper
pipeline. Missing model output, outlier flags, provenance, data or an exact
candle match produces an unavailable artifact/`WAIT`; it does not invent an AI
prediction or fall back to a technical rule labeled as AI.

## Run with the real framework

The integration targets **Freqtrade/FreqAI 2026.9**. Install that official release
with its FreqAI/LightGBM dependencies in a separate environment, or use the
corresponding official FreqAI image. No model files or exchange credentials are
bundled here. From the repository root, put this checkout on `PYTHONPATH`:

```bash
PYTHONPATH="$PWD" freqtrade list-strategies \
  --strategy-path freqai_bridge --config freqai_bridge/config.research.json

PYTHONPATH="$PWD" freqtrade download-data \
  --config freqai_bridge/config.research.json --timeframes 15m --days 45

PYTHONPATH="$PWD" freqtrade backtesting \
  --config freqai_bridge/config.research.json \
  --strategy-path freqai_bridge --strategy ChartProFreqaiResearch \
  --freqaimodel LightGBMRegressor --timerange 20260901-20261001
```

Choose a historical range whose training prehistory is actually downloaded; the
dates above are command examples, not a statement that a dataset/model exists.
Backtesting exercises model research and emits **no native trades** because all
entry/exit flags are zero and `confirm_trade_entry()` always returns false.
Zero trades therefore cannot be used as a strategy profitability result.

For prediction collection after research and data/provenance preparation:

```bash
PYTHONPATH="$PWD" freqtrade trade \
  --config freqai_bridge/config.research.json \
  --strategy-path freqai_bridge --strategy ChartProFreqaiResearch \
  --freqaimodel LightGBMRegressor
```

The supplied config enforces `dry_run: true`; the strategy rejects other modes
and other pairs. No Freqtrade order signals are enabled. FreqAI features use
only present/past rows; the learning target is the four-candle future return.
The model invokes `self.freqai.start()` only in `populate_indicators()` following
the official interface. The framework manages training; HTTP paper-evaluation
requests never start training.

## Canonical data and provenance hand-off

Run canonical CCXT collection before the prediction process. The strategy reads
the shared SQLite database at `freqai_bridge.canonical_db_path`, by default
`.data/market-data.sqlite3`. The inference window defaults to **two closed M15
bars**, matching the common API. Its range is:

```text
[floor(now / 900000) * 900000 - 2 * 900000,
 floor(now / 900000) * 900000)
```

The query deliberately uses `as_of_ms=None` so its content hash does not change
on every retry. All candle `availableAtMs` values are still required to be no
later than the decision clock. To inspect/save the same context manually:

```bash
python3 -m freqai_bridge.context \
  --db .data/market-data.sqlite3 --output .data/canonical-window.json --bars 2
```

Prediction publication requires `.data/freqai-provenance.json` from the actual
training process. It must contain:

| Field | Meaning |
| --- | --- |
| `freqaiIdentifier` | Exact identifier of the loaded FreqAI model family |
| `modelVersion` | Actual immutable model version/fingerprint, not a generated clock value |
| `strategyVersion` | Strategy/feature version used to generate the model |
| `trainingDatasetVersion` | `sha256:` plus 64 lowercase hex characters of the actual training dataset manifest |
| `trainedThroughMs` | Last data/label availability used during training, UTC ms |
| `trainingCompletedAtMs` | Actual completion time of that training job, UTC ms |

The provenance must not be fabricated from `now` or inferred from a directory
name. In particular `trainedThroughMs` must include future-label horizons;
using the last feature-row time instead can conceal leakage. This bridge checks
the declared bounds but does not certify a training job's truthfulness or
automatically extract provenance from an arbitrary saved model. Producing that
sidecar is a required training-job hand-off. Without it the system stays `WAIT`.

Training provenance is static across inference candles. The artifact's
`datasetVersion` is independently derived from the current canonical query,
after matching every input-window OHLCV/date against the real FreqAI dataframe.
If an optional provenance `datasetVersion` is supplied, it must also match.
The training hash remains separately recorded as `trainingDatasetVersion`.

Outputs are written atomically to `freqai_bridge.output_path`, default
`.data/freqai-prediction.json`. Configure `FREQAI_REPORT_PATH` in the common API
to this file. All paths are operator configuration, not browser-supplied URLs.
Use the same mounted database and checkout when the producer runs in a separate
container. Keep trained model files private; this bridge never unpickles or
loads a downloaded model.

## Decision behavior

`pipeline.decision.evaluate()` requires complete canonical data, fresh gap-free
**observed** trades, a trustworthy FreqAI flag (`do_predict == 1`), matching
model/candle/dataset provenance and a fresh Hummingbot snapshot. A forecast
beyond the configured return threshold must agree with net taker flow. All
errors return a reasoned `WAIT` and no intent.

The resulting intent is `PAPER` only and targets a bounded signed position.
Source timestamps determine its 30-second prediction lifetime, so repeating an
evaluation cannot extend it. The ID includes the target, source provenance and
limit price; a re-priced limit is a distinct intent and the ledger must prevent
competing pending orders. The Hummingbot time is snapshot retrieval time, not
proof of an exchange sequence or achievable queue position.

## Verification

```bash
python3 -m unittest pipeline.test_decision freqai_bridge.test_exporter -v
python3 -m freqai_bridge.context --help
```

The tests use real SQLite, real pandas dataframes and actual JSON publication.
They do not train a model, install Freqtrade, prove forecast quality or verify a
live run. A real framework strategy-load smoke test and a research training run
remain separate checks; no profitability or execution parity is claimed.

Official source checked at the pinned release:
[FreqAI example strategy](https://github.com/freqtrade/freqtrade/blob/2026.9/freqtrade/templates/FreqaiExampleStrategy.py),
[configuration](https://github.com/freqtrade/freqtrade/blob/2026.9/docs/freqai-configuration.md),
[running FreqAI](https://github.com/freqtrade/freqtrade/blob/2026.9/docs/freqai-running.md),
[release 2026.9](https://github.com/freqtrade/freqtrade/releases/tag/2026.9).
