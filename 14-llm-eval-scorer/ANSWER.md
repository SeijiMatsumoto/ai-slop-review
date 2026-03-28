# 14 — LLM Eval Scorer (Python)

**Categories:** Logic errors (float comparison, boolean logic), Silent failures

1. **`passed = overall == pass_threshold`** — Line 88 uses `==` to compare a float with the threshold. Should be `>=`. A score of 0.71 would fail because `0.71 == 0.7` is `False`. This means essentially nothing ever passes unless the score is exactly 0.7.
2. **Bare `except: pass` in `llm_judge`** — Lines 42-43 silently swallow all errors (network failures, JSON parse errors, API errors) and return all zeros. Failed judgments look like terrible scores rather than errors.
3. **Division by zero if `cases` is empty** — `run_eval_suite` divides by `len(results)` on lines 100-103 with no empty-list guard.
4. **`compare_models` ignores the original `actual_output`** — It re-generates outputs for each model but uses the same `expected_output` from the input cases. The original `actual_output` field is discarded, which may not be the intended behavior.
5. **No batching or rate limiting in `compare_models`** — Sequentially generates responses for every case x every model with no parallelism, rate limiting, or progress indication. Can easily hit API rate limits.
6. **LLM judge prompt is injectable** — `case.input` and `case.actual_output` are interpolated directly into the judge prompt. Adversarial inputs could manipulate the judge's scoring.
