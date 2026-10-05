# Repair feedback treatments

The historical [eval-v2 reduced-feedback run](results/eval-v2-ablation/REPORT.md) is exploratory: it retained failure summaries and incorrectly attributed old evidence to newer RTL. Keep its raw outputs unchanged. It is not a clean feedback-off control and cannot establish that feedback caused a repair.

## Corrected implementation

Both modes begin with the same original RTL, fixed contract, and original witnessed failure. Both retain the model's own patch history and use the same independent acceptance checker.

- Default `COUNTERTRACE_REPAIR_FEEDBACK=on`: when a candidate has a new counterexample, the next proposal receives that candidate's RTL and its own trace. When a candidate has no usable counterexample, its RTL advances but the retained trace is labeled as coming from an earlier version. Errors never become new trace evidence.
- `COUNTERTRACE_REPAIR_FEEDBACK=off`: later attempts receive only rejection feedback, their own edit history, and the explicitly labeled original finding/trace. They do not receive new failure checks, cycles, diagnostics, or trace rows. “Off” means no new diagnostic feedback, not no initial problem statement.

Unit regressions check both modes and stale provenance after errors. The full Docker repair regression exercises admission rejection, failed checks with refreshed feedback, and a passing candidate. These tests establish loop behavior with simulated model proposals, not a model success rate. No corrected-treatment benchmark has run.

## Before a new comparison

Freeze and externally anchor the exact code commit, prompts, model IDs, reasoning mode, budgets, verifier, suite, and scoring before executing a new experiment. Keep initial evidence and hidden acceptance checks identical between modes. Preserve rejection-only feedback as the declared control and distinguish source/provenance updates from actual new diagnostic content.

Use at least three runs per condition on the same cases, alternate condition order, and report every candidate, failure, unknown, token count, and runtime. Repeats measure variability; they do not add independent designs. Reusing the now-inspected eval-v2 cases is a regression experiment, not a fresh held-out evaluation. Use fresh frozen cases before making a new held-out claim. Publish new results separately and avoid causal claims from isolated case outcomes.
