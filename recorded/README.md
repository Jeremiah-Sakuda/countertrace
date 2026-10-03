# Recorded runs

Curated, completed runs copied here with `countertrace record <run-id>`. The interface labels them as recorded runs and shows their original date, image, tool versions, and timings. They are real evidence from the owner's machine, not live results, and they are read-only. Re-record after changing the harness, stimulus, or model configuration.

Keep the current four curated runs (about 9 MiB: showcase fault, its repaired candidate, control, and audit) in Git so a checkout contains inspectable evidence without another download. Treat this as a small release fixture set: replace deliberately after review, and do not commit every experiment. Growing evaluation archives and repeated recordings belong in release assets or object storage, with a manifest of hashes and retrieval instructions. Git history retains old copies, so frequent replacement also grows the repository.

The October 3 refresh contains a reviewed Ultra explanation and one successful real repair. Failed explanation checks and request metadata are preserved in [the development evidence record](../docs/evidence/model-gate-2026-10-03.json), not represented as a benchmark.

Before replacing the showcase, run `countertrace model-check --run-id <local-run-id>` and complete the usefulness review in [MODEL_GATE.md](../docs/MODEL_GATE.md). Recording copies the explanation attached to the local run. A model-unavailable response is not an explanation; keep the current recording until there is a reviewed result. Parent/candidate links use recording IDs; record each intended public relative explicitly. Recording never auto-publishes a private related run. Keep private runs and held-out labels out of this directory.
