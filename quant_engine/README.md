# Dual-Strategy Foundation (Phase 1)

This package is a pure-Python, paper-only signal routing foundation. It is NOT a Freqtrade adapter, a trained FreqAI model, or a live trading system.

- CORE rules remain in existing Kotlin/adapter code unchanged. CORE candidates will be wired only after parity checks.
- AI_NATIVE candidates are independent but disabled for paper execution by default (`allow_ai_native=False`).
- Agreement creates one CONFIRMED candidate; disagreement blocks new entry.
- One BTCUSDT position at a time in this initial routing policy.
- Existing position exits and emergency protection must be handled outside this ENTRY-only router.
- No live execution, no network access, no credentials.

Run focused tests from repository root:

```bash
python -m unittest discover -s quant_engine/tests -v
```

Next: add versioned candle/signal schemas, Kotlin↔Python parity fixtures, Freqtrade callbacks/state store, FreqAI trained models and Codemagic test job. Do not enable AI executions without walk-forward and runtime verification.
