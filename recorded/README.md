# Recorded runs

Curated, completed runs copied here with `countertrace record <run-id>`. The interface labels them as recorded runs and shows their original date, image, tool versions, and timings. They are real evidence from the owner's machine, not live results, and they are read-only. Re-record after changing the harness, stimulus, or model configuration.

Keep the current curated runs (showcase fault and its repaired candidate, a correct control, the audit, and the eval-v2 F1, F2, and F6 repair cases with every candidate, about 26 MiB in total) in Git so a checkout contains inspectable evidence without another download. Treat this as a small release fixture set: replace deliberately after review, and do not commit every experiment. Growing evaluation archives and repeated recordings belong in release assets or object storage, with a manifest of hashes and retrieval instructions. Git history retains old copies, so frequent replacement also grows the repository.

The October 3 refresh contains a reviewed Ultra explanation and one successful real repair. Failed explanation checks and request metadata are preserved in [the development evidence record](../docs/evidence/model-gate-2026-10-03.json), not represented as a benchmark.

Before replacing the showcase, run `countertrace model-check --run-id <local-run-id>` and complete the usefulness review in [MODEL_GATE.md](../docs/MODEL_GATE.md). Recording copies the explanation attached to the local run. A model-unavailable response is not an explanation; keep the current recording until there is a reviewed result. Parent/candidate links use recording IDs; record each intended public relative explicitly. Recording never auto-publishes a private related run. Keep private runs and held-out labels out of this directory.

Raw files under each recording’s `batches/` preserve tool output byte for byte. Git attributes disable newline conversion and whitespace linting only for these generated artifacts; source and documentation checks remain enabled.

## Corrected derived summaries

On October 4, `scripts/refresh_recorded_evidence.py --apply` reparsed the existing raw simulation traces and their stimulus and verified they exactly reproduced the stored normalized rows. It corrected the showcase, two-bug parent, and rejected first candidate: some properties failed after a test's first finding and were previously omitted from their failure summaries. Overall failure and repair decisions are unchanged; accepted candidates had no mismatching rows and needed no correction.

Each changed `run.json` retains the original values, original record hash and Git revision, method, and raw-input hashes in `evidence_corrections`. This history is also exported in evidence bundles. Model responses retain their original text and timing and carry an evidence warning where their input summaries were corrected. No new inference was performed. The script is idempotent for this correction and is a dry run unless `--apply` is supplied. These derived corrections must not be presented as new benchmark executions.
