# G0.35 — G0.34 Measurement Evidence Integrity Correction

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Baseline HEAD: `807381f03e25fc5a816d0d847f2458a240d411fd`  
Baseline handoff blob: `cc625179dc34e49455711c13124b143e3a410ce4`  
Scope: documentation-only evidence correction; no re-execution  
Disposition: **G0.34 MEASUREMENT EVIDENCE NOT VERIFIED — D05 oracle/input separation violated in the recorded generator; execution terminated before final output/acceptance assertions. G0.33-A consumed; no rerun authorized.**

## 1. Purpose

This report corrects the assurance status of G0.34 after reviewing its recorded measurement procedure against the owner-ratified D05 contract and the actual execution cell.

The G0.34 report and its historical commit are preserved unchanged. This correction does not delete or rewrite historical evidence and does not create a replacement measurement.

## 2. Findings

### F-01 — Oracle metadata was included in parser-input bytes

The recorded generator's base fixture object included an `expected` member and serialized the entire object into the measured JSON payload. The measurement traversal therefore measured bytes and structural nodes for the oracle field as part of the input.

This conflicts with G0.31 D05, which requires `expected` test-oracle metadata to be kept outside parser-under-test input. The G0.34 report states that the oracle field was not present in well-formed parser-input payloads; that statement is contradicted by the recorded generator.

Impact:
- D05 input/oracle separation was not satisfied.
- Corpus digest, payload sizes and structural maxima do not represent a compliant S1 parser-input corpus.
- Any candidate ceilings derived from these measurements cannot be ratified on this evidence.

### F-02 — Execution stopped at a failing namespace assertion

After generating the corpus and performing two measurement passes, the execution cell evaluated a namespace assertion comparing a byte-string slice to a text string. That assertion raised `AssertionError`.

The cell therefore terminated before emitting its final aggregate summary object. Although intermediate metric values had been calculated in memory, the final acceptance/summary output was not produced. The reported run cannot be treated as a fully completed, independently inspectable measurement record.

Impact:
- The claimed G0.34 end-to-end execution/acceptance PASS is not substantiated by the captured execution result.
- The recorded aggregate table and corpus digest are not accepted as ratified evidence for D11.
- Repeatability assertions executed before the failing assertion, but the run's overall completion remains failed.

### F-03 — Measurement scope does not establish operational resource safety

Even if the structural measurements were otherwise valid, G0.34 did not profile CPU, peak memory, allocation amplification, throughput or adversarial parser behavior. It cannot establish production resource ceilings or parser safety.

## 3. Authorization and non-reexecution rule

G0.33-A authorized exactly one in-memory corpus generation and measurement run. That execution attempt has occurred and is considered consumed.

This correction does not authorize:
- a second corpus generation or measurement run;
- repair-and-rerun of the failed cell;
- persistent fixture creation;
- parser or test implementation/execution;
- CI changes or workflow dispatch;
- CPU/RAM benchmarking or adversarial performance testing;
- numeric D11 ratification;
- cryptographic/verifier work or runtime access.

A further measurement requires a new, separately scoped owner decision. It must not be inferred from G0.33-A.

## 4. Corrected status

| Item | Corrected status |
|---|---|
| G0.33-A authorization | APPROVED; one attempt consumed |
| Corpus generation attempt | EXECUTED; D05 separation violation |
| Two measurement passes | Intermediate computations occurred; overall run failed before final output |
| G0.34 aggregate metrics | NOT VERIFIED for policy use |
| Corpus digest | NOT VERIFIED for policy use |
| D05 oracle/input separation | FAIL |
| D11 numeric ceilings | OPEN / NOT RATIFIED |
| Parser implementation | NOT AUTHORIZED |
| Test module / test execution | NOT AUTHORIZED |
| CI | NOT AUTHORIZED |
| Additional measurement | REQUIRES NEW OWNER APPROVAL |

## 5. Required next gate

Do not ratify any numeric ceiling from G0.34.

The next valid step is a documentation-only design proposal for a corrected measurement authorization, explicitly separating parser-input bytes from oracle metadata, defining the completion assertions before execution, and specifying what evidence must be captured before the one permitted run is considered complete. Any new run must be separately approved.

No source code, tests, fixture files, workflows, dependencies, credentials, keys, runtime, database, network, VPS, market data, model, ledger or lifecycle state was changed. No external service was accessed for this correction. T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.

**G0.35 verdict: EVIDENCE CORRECTION PASS — G0.34 assurance downgraded to NOT VERIFIED; no numeric ceiling ratified; no re-execution authorized.**
