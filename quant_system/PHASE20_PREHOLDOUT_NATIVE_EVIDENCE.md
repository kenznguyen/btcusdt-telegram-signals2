# Phase 20 — register real Phase19 native inference evidence before OOS

## Exact observed Codemagic evidence (31 Oct 2026, history only)

The user-supplied `btcusdt-telegram-signals2_1_artifacts (7).zip` was
read directly; it contains the genuine Phase19
`phase19-native-forecast-reconciliation.json`.

- Original ZIP SHA256:
  `fb33f1490cd3c995fa2d325561138d1d7a4e32f1be4e63dee28d7f1fc457b2ce`.
- Original Phase19 report SHA256:
  `f5fe8a4dcd5780088069373472dad2f3f87ecec6a7c21e0ff3897373bb5bd415`.
- Original last-fold native PREDICT: **480 rows, 471 accepted, 9 rejected**.
- Witness timestamps: **2026-10-25 22:00 UTC** through
  **2026-10-30 21:45 UTC**, exactly contiguous M15 and wholly before OOS.
- Native matrix X, do_predict and frozen forecasts reconciled: TRUE.
  `errors=[]`. 13 Codemagic preflight and 20 CPU-runtime regressions passed.
- Frozen model bytes:
  `sha256:918dc4737ee432df8f7f9d2c3e561ac3983aaf56d8791a731a55624ab836b81f`.
- Original native event ledger:
  `sha256:382546af84244b97fc553eddc5ad02e3da7383e8384dd6e93196cf7f7f38edf7`.
- Original native forecast trace:
  `sha256:973dd79862ce17c3b20791f849c627261e94cef896bd9b83b7068ec003019f52`.

## This phase records historical SHA evidence, not OOS claims

The Git-stored registration record
`research_seals/phase20-native-predict-preholdout.json`
locks the observed ZIP, report, model, trace, historical timestamps and
source/approval Git SHAs. `quant_system/phase20_preholdout_attestation.py`
checks the original **report bytes**, then all 480 row identities/flags,
counts, native evidence provenance and false OOS/live certification flags.
It does not unpickle a model, access an exchange or access OOS.

Running the Phase20 gate against the uploaded original report in the
authoring environment returned:
`native_historical_evidence_locked=true`, `errors=[]`.
The ten negative/positive regressions also passed locally.
These local checks **do not substitute for the next Codemagic build**.

## Codemagic repeatability / reproducibility check

Manual workflow:
`dual-strategy-phase20-preholdout-native-evidence-gate`

Branch:
`feature/dual-strategy-phase20-preholdout-native-evidence-seal-20261031`

Codemagic recreates the actual Phase19 frozen-native report from the
original **Phase14 PREDICT archive**, requires its original SHA seal and
preholdout approval, and then requires the complete regenerated
`phase19-native-forecast-reconciliation.json` bytes to have exactly the
registered SHA. Any difference fails closed; not even a numerically similar
report can silently replace the original. It exports:

`artifacts/phase19/report/phase20-preholdout-native-evidence-gate.json`

The required result is:
`native_historical_evidence_locked=true`, `errors=[]`.
If different runtime byte serialization results in SHA drift, **investigate**
that drift; do not override the original witnessed SHA or model to force
a pass. No 360d/independent OOS claims should be made on this basis.

The original prospective **untouched** OOS runs from
**2026-11-04T00:00:00Z** to **2026-12-04T00:00:00Z**; do not run it before
completion, retrain on it or tune parameters using its results.

No modification to CORE RSI/ADX/Smart DCA, AI LONG/SHORT independent
signals, Shared Risk, Freqtrade position logic, funding assumptions,
Android APK/keystore, or model bytes/protocol is made here.
Both AI promotion and live orders remain disabled.
