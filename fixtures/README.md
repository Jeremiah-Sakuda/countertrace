# Fixtures

All fixtures were authored for Countertrace (MIT). Nothing here is held out, and both known-good implementations share an author, so they do not count as independent implementations for the PRD's evaluation.

- `rtl/fifo_count.v` and `rtl/fifo_wrapbit.v`: known-good FIFOs in two styles (occupancy counter; wrap-bit pointers).
- `faults.json`: the versioned fault library. Each fault is an exact-match edit to a known-good source with the contract condition it targets (`class`), a category, and its intended consequence. `audit_library` lists the mutants used by the audit, including one intended-equivalent mutant.
- `examples.json`: bundled public examples with split (`showcase` or `development`), depth, brief, and the author's intent. Intent is not a result; only a run establishes what was witnessed.
- `check_sets/`: named supplemental check sets built only from reviewed templates (`empty_flag`, `full_flag`, `read_data` over chosen contract rows) and the frozen-suite tests they observe. `weak-learner-v1` is deliberately weak for the demonstration.
- `timing/`: specified cycle expectations (PRD depth-2 sequence; depth-4 wraparound) shared by the reference model tests and the simulation suite.

Final held-out sources and labels belong in ignored `evaluation/holdout/` until evaluation is frozen. See the [evaluation protocol](../evaluation/README.md).
