# Fixtures

No RTL designs or measured verification results are included at initialization.

Keep development, showcase, and final evaluation sources separate. Each fixture must record authorship/source, license, supported profile, parameters, expected behavior, and whether the expected defect was independently witnessed. Parameter variants of one source do not count as independent implementations.

- `development/`: prompt and toolchain iteration; no holdout claims.
- `showcase/`: the explicitly curated public demonstration.
- `timing/`: specified cycle expectations shared by simulation and formal replay tests.

Final held-out sources and labels belong in ignored `evaluation/holdout/` until evaluation is frozen and publication is appropriate. See the [evaluation protocol](../evaluation/README.md).
