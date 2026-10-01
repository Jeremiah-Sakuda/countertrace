# Timing fixtures

The [PRD](../../docs/PRD.md) specifies a seven-edge depth-2 sequence covering reset, simultaneous requests at empty/intermediate/full occupancy, recurrent reset, and an ignored empty read. Convert those specified expectations into shared fixtures when implementing the monitors. Add wraparound cases and an explicit raw-solver-step to application-cycle mapping.

These are contract examples, not observed hardware results. Both engines must agree on accepted operations and on when registered output is compared.
