# Timing fixtures

Specified expectations from the [PRD](../../docs/PRD.md) sampling convention, not observed hardware results.

- `depth2_prd_sequence.json`: the PRD's seven-edge depth-2 sequence (reset, simultaneous requests at empty, intermediate, and full occupancy, recurrent reset, and an ignored empty read). The `wraps` field is derived and is not part of the PRD table.
- `depth4_wraparound.json`: pointer wraparound for depth 4, including an ignored write while full and a simultaneous read and write while full.

`tests/test_contract.py` checks the reference model against both. The depth-2 sequence is also driven through the simulation harness as the `prd_sequence` test. The solver-step to application-cycle mapping is tested against a real solver counterexample in `tests/test_evidence.py`.
