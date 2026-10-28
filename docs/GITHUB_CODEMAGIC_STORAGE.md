# BTCUSDT Chart Pro: GitHub storage + Codemagic execution

## Architecture

- **GitHub repository:** source code, `codemagic.yaml`, test suites, and documentation.
- **Codemagic:** compile Android Debug APK, execute historical Freqtrade Futures backtests and train/run FreqAI research. **No GitHub Actions or real orders**.
- **GitHub Releases:** immutable-ish prerelease per Codemagic build ID holding selected binary outputs. Separate `chart-pro/android/<build>`, `chart-pro/freqtrade/<build>`, and `chart-pro/freqai/<build>` tags. Release assets carry a SHA256 checksum in `release-metadata/github-release-status.json`.
- **Codemagic Artifacts:** still keeps full build outputs. GitHub publication is additional and is skipped when the token is absent.

## One-time setup (Android phone)

1. Open GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate token.
2. Restrict repository access to `kenznguyen/btcusdt-telegram-signals2`; grant **Contents: Read and write**. Use minimal expiration. Copy the token to a safe password manager, never to a GitHub file or a chat.
3. In [Codemagic applications](https://codemagic.io/apps), open the existing app's **Environment variables**, create variable group **`github_release`** and secret variable **`GH_RELEASE_TOKEN`** with that token. Mark it Secret. All three publishing workflows import that variable group in `codemagic.yaml`.
4. On Codemagic, ensure the GitHub webhook is connected/updated. Then pushes to `integration/android-freqtrade-analytics-20261025` trigger `android_chart_pro_qa` (Android source/workflow/script changes). Other expensive workflows are **manual**.
5. Start `freqtrade_chart_pro_analytics` or `freqai_lightgbm_research` manually when historical analysis/retraining is wanted.
6. Open [GitHub Releases](https://github.com/kenznguyen/btcusdt-telegram-signals2/releases) to find the prereleases and download their artifacts. On your Android device, install the **Debug** APK side by side with the existing Release app; in Chart Pro Analytics, import the Freqtrade results ZIP or FreqAI research JSON.

## Workflows

| Codemagic workflow | Execution | GitHub Release content |
| --- | --- | --- |
| `android_chart_pro_qa` | push to integration branch / manually | `app-debug.apk`, distinct application ID, no release keystore |
| `freqtrade_chart_pro_analytics` | manually, 90/180/360-day choice | `freqtrade-backtest-<build>.zip`: actual Freqtrade ZIP + selected risk/equity reports |
| `freqai_lightgbm_research` | manually, 90/180/360-day choice | `freqai-research-<build>.zip`: research manifest, validation report, predictions, log |

**Notes:** The GitHub Releases storage path is implemented by our own authenticated post-build uploader, not Codemagic's built-in GitHub publisher (which is tag-triggered only). The script reads `GH_RELEASE_TOKEN` from the build environment, never prints it, and fails if a selected file is missing or an upload is unsuccessful. Build artifacts remain available in Codemagic if the token is not configured. The release manifest includes the exact source commit and SHA256/size of each upload.

The backtesting and research results are **historical simulations**, not a promise of profits. Freqtrade and Android Kotlin parity remain unverified; FreqAI does not place trades or change StrategyEngine parameters.

## Retention and failure rules

- Do not commit APKs, backtest datasets, trained models, market history or sensitive secrets to `main`.
- Every published release is tied to its source commit and unique Codemagic build ID. Re-running the same build ID will be rejected if its Release tag already exists, rather than silently overwriting existing evidence.
- GitHub Release uploads are limited here to 250 MB per file; oversized reports stay within Codemagic Artifacts until appropriately split.
- A failure in the optional publishing step after enabling the token **must not be confused with successful publication**. Check `release-metadata/github-release-status.json` or the final GitHub Release URL.
- The Strict Kotlin ↔ Freqtrade parity workflow remains independent and fail-closed; publishing a Freqtrade historical report does not certify parity.
