# T0 A2.2 Stage I — Independent Read-only Review of F-01/F-02 Repair

Date: 2026-11-18
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/core-operational-proof-20261112
Reviewed source HEAD: 6d1350471f4422b0d6f142baa28ed6fa04e77892
Governing A2.2 source blob: d9f93bf390d107381b7135c3073aeca0d14894d4
Scope: static review of the repaired fixture builder, verdict derivation and tests against A2.2 §§15–18. No files were modified during review.

## Executive disposition

**REQUEST CHANGES — Stage I contract-conformance remains BLOCKED / NOT VERIFIED.**

The earlier F-01 and F-02 repairs are real but narrow:
- F-01: declared mutation paths now resolve to existing leaves and the builder prevents accidental structural expansion.
- F-02: fixture verdict routing now derives facts from fixture content rather than catalog `fact_key` metadata.

However, the current fixtures and tests still do not implement several normative A2.2 §15–18 semantics. The 40/40 package test result proves internal consistency of the current harness, not conformance of all 27 cases to the governing contract.

## Findings

### R1 — BLOCKER: NV-03 does not perform the contract-defined mutation

- Contract: A2.2 §18.2, line 584: keep the A1 historical object unchanged and select the A2.2 V2 profile in the verifier request.
- Implementation: `verdicts.py:90` mutates `verification_request.subject_fixture` from `A2_2_CURRENT` to `A1_HISTORICAL`; it does not change the selected profile.
- Routing: `verdicts.py:331-335` emits `PROFILE_VERSION_MISMATCH` solely when that string marker is present. The `historical_fixture` object in B0 is not read by `derive_stage1_facts`.
- Consequence: the expected verdict can be produced without testing an unchanged historical A1 object's profile binding. The fixture encodes a label-trigger, not the §18.2 scenario.
- Required remedy: represent the historical A1 object's actual profile ID/version in the fixture, leave that object unchanged, mutate only the verifier request's selected profile to V2, and derive the mismatch from those actual fields. Add a regression that changes the label alone and proves it cannot trigger the contract verdict.

### R2 — BLOCKER: profile field names and B0-PF do not match A2.2

- Contract: §15.1–15.2 specifies `signature_profile_id` and `signature_profile_version`; §18.1 line 576 defines B0-PF using statement `signature_profile_id` set to the LEGACY value while all other locations remain V2.
- Implementation: B0 and B0-PF use `profile_id` / `profile_version` at `verdicts.py:154-171` and `180-197`; B0-PF's legacy field is `statement.profile_id` at line 182. The derivation at lines 311-329 reads those aliases.
- Consequence: the fixture schema is not the normative schema, so it can pass while the actual required field is missing or wrong.
- Additional gap: §15.2 requires binding across descriptor, statement, detached envelope, Trust Policy profile authorization, Trust Policy signed statement/digest binding, bootstrap record/authorization when applicable, and verifier request/local allowed-profile configuration. Current `validate_profile_bindings` checks only five simplified maps (descriptor, statement, envelope, policy, request), and the B0 fixture does not represent all required locations.
- Required remedy: use the exact contract field names and model each applicable binding location explicitly. Add missing-field and mismatched-location tests, including Trust Policy signed binding and bootstrap binding when applicable.

### R3 — BLOCKER: the evaluator accepts zero mutations

- Implementation: `verdicts.py:405-410` rejects structural changes and `len(changed) > 1`, but does not reject `len(changed) == 0`.
- Contract: §18.4 item 2 requires exactly one semantic mutation.
- Consequence: `evaluate_fixture_content(baseline, baseline, state)` is allowed to continue to verdict routing and may return an ordinary BLOCKED result rather than INVALID. The generic evaluator does not enforce the single-mutation invariant.
- Required remedy: require exactly one changed semantic leaf; add a no-mutation regression that expects a fixture-integrity INVALID result and unchanged state.

### R4 — BLOCKER: B0/B-A and per-case evidence are incomplete against §§18.1 and 18.4

- Contract: §18.1 lines 566-574 requires a mutually consistent descriptor and canonical Evidence Object (bytes, ID, type, schema, digest, byte length), Signature Statement and detached envelope, test signer, Trust Policy authorization for signer role/namespace/audience, verifier request, separate A1 historical fixture, bootstrap configuration and a complete S0 snapshot.
- Implementation: `verdicts.py:151-176` provides abbreviated dictionaries and an `accepted_state: "S0"` label. It has no canonical Evidence Object bytes/ID/type/schema/digest/length, no detached signature/enclosing digest material, no signer identity/role authorization, and no complete Trust Policy signed binding. The supplied `StageStateSnapshot` is constructed by the test separately rather than being captured from a complete fixture state.
- Contract: §18.4 items 1 and 3-7 require schema version, per-dimension results, one aggregate result/reason, S0/S1, and explicit forbidden-transition assertions.
- Implementation: `FixtureSpec` stores one `dimension_result` string, not the required per-dimension outcomes; no schema-version field exists. Tests at `test_verdicts.py:30-44` check the aggregate verdict/reason and equality of the small in-memory snapshot, but do not record each dimension or assert the full forbidden-transition set.
- Required remedy: either implement the complete synthetic fixture/evidence shape within the approved mock-only boundary, or explicitly mark the unavailable cryptographic/digest dimensions NOT VERIFIED and narrow the Stage I acceptance claim. Do not describe these 27 records as complete §18 fixtures until the missing contract fields and assertions are represented.

### R5 — REQUIRED: tests do not guard against the semantic errors above

- `test_each_fixture_produces_exact_expected_verdict_and_reason` compares the evaluator result to expected values carried by the same fixture catalog; this is useful for deterministic mapping but does not independently validate that each mutation matches its normative §18 row.
- Existing semantic regression `test_fixture_verdict_is_derived_from_mutated_content_not_catalog_fact_key` covers only NV-01 purpose mutation.
- Add contract-row-specific tests for NV-03, NV-04, all required profile field names/binding locations, zero mutation, and per-dimension/state evidence. Expected scenarios should be derived from the A2.2 row semantics, not only copied from `_FIXTURE_ROWS`.

## Positive observations

- F-01 path existence and structural single-leaf mutation checks are materially improved.
- Compound mutations are rejected.
- Mutable catalog mutation values are defensively copied.
- Bootstrap first-match table ordering at §17 is represented in `_BOOTSTRAP_RULES`; the existing unit tests cover two precedence examples. Static review found the row order aligned with §17 priorities 1–18.
- The mock verifier is clearly labelled non-cryptographic and does not claim `VALID_SIGNATURE`. This boundary must remain explicit.
- Path A/B are not enabled by the B0 baseline; no positive bootstrap acceptance path was added.

## Verification boundary

- Review type: read-only static review of exact GitHub blobs.
- Reviewed source HEAD: `6d1350471f4422b0d6f142baa28ed6fa04e77892`.
- `verdicts.py` blob: `f38cecb9eb72638f62661999dd6924cdce5bfe4d`.
- `test_verdicts.py` blob: `a28d957fc4522cf56805f0435c04a4b98b812268`.
- A2.2 spec blob: `d9f93bf390d107381b7135c3073aeca0d14894d4`.
- No tests were run during this read-only review. The previously recorded isolated run (17 focused / 40 package tests PASS) remains valid for its exact source SHA, but does not override the semantic findings above.
- No source, test, README, workflow, runtime, T0, VPS, credential, exchange or trading state changed during this review.

## Disposition and next step

- F-01: PASS for existing-path/one-leaf builder mechanics only.
- F-02: PASS for removal of catalog fact-key routing only.
- A2.2 NV-03/NV-04 semantic conformance: BLOCKED.
- A2.2 §15 profile field/binding conformance: BLOCKED.
- A2.2 §18 complete fixture/per-dimension/state assertions: NOT VERIFIED / BLOCKED.
- Overall Stage I contract conformance: **REQUEST CHANGES / NOT READY**.
- F-03 README digest-helper inconsistency remains separately unresolved.
- Workflow dispatch, Stages II–V, merge, deployment and trading remain NOT AUTHORIZED.

Next permitted increment: owner-approved, narrowly scoped repair of the contract-specific fixture semantics and missing tests in the existing Stage I package only. Do not dispatch workflow/CI or broaden into production cryptography, real keys, bootstrap, durable state, T0, VPS or runtime.
