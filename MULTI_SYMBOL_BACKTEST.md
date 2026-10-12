# Multi-symbol historical backtest

This workflow is intentionally separate from the live signal scanner and the Telegram command workflow.

## Run it

1. Open the repository on branch `feature/multi-symbol-backtest`.
2. Open **Actions → Multi-Symbol Backtest → Run workflow**.
3. Keep the default values to screen eight perpetual pairs over 360 days, or choose a smaller symbol list first.
4. Download the `multi-symbol-backtest-<run-id>` artifact after the workflow finishes. The summary is `multi_backtest_summary.json`; per-symbol reports and CSVs are in their own subfolders.

Supported symbols: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT, ADAUSDT, LINKUSDT.

## Isolation and safety

- Each symbol runs sequentially in its own Python subprocess with independent starting capital.
- Results are stored under `multi_backtest_results/<SYMBOL>/`; the summary is stored at `multi_backtest_results/multi_backtest_summary.json`.
- The runner does not import the live scanner to run it, does not read or write `state.json`, and does not send Telegram messages.
- The workflow is manual-only and has its own workflow file. It does not change the schedule in `signal-scan.yml`.
- This is historical simulation only; it does not submit exchange orders.
- A failed symbol is marked failed in the summary; successful symbols are still retained. Review API/data errors before comparing performance.

Defaults: 360 days, 100 USDT starting capital per symbol, initial margin 50% of current simulated balance, DCA margin 100% of initial order margin. The existing entry, DCA, TP, and SL rules are reused; only the instrument is parameterized.
