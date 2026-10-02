# Recorded runs

Curated, completed runs copied here with `countertrace record <run-id>`. The interface labels them as recorded runs and shows their original date, image, tool versions, and timings. They are real evidence from the owner's machine, not live results, and they are read-only. Re-record after changing the harness, stimulus, or model configuration.

Keep the current three curated runs (about 7.6 MiB) in Git so a checkout contains inspectable evidence without another download. Treat this as a small release fixture set: replace deliberately after review, and do not commit every experiment. Growing evaluation archives and repeated recordings belong in release assets or object storage, with a manifest of hashes and retrieval instructions. Git history retains old copies, so frequent replacement also grows the repository.

Before replacing the showcase, run `countertrace model-check --run-id <local-run-id>` and complete the usefulness review in [MODEL_GATE.md](../docs/MODEL_GATE.md). Recording copies the explanation attached to the local run. A model-unavailable response is not an explanation; keep the current recording until there is a reviewed result. Keep private runs and held-out labels out of this directory.
