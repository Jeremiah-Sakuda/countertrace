# Trusted verifier

Reserved for the independent simulation scoreboard, formal monitors, result parser, and pinned worker environment. None is implemented yet.

The first milestone selects and pins Verilator, Yosys, SymbiYosys, and a solver in a Linux image, then demonstrates a known-good control and a witnessed defect. Record image digest and tool versions instead of treating a floating image tag as reproducible.

Use the [PRD sampling convention](../docs/PRD.md) and shared timing fixtures. Assertions and accepted transactions must follow reference occupancy, not DUT flags. Generated checks are supplemental and cannot replace the core.

Do not execute user or model-generated HDL until the admission and isolation boundaries are implemented. Workers receive no model credentials and cannot edit the trusted harness or contact the network.
