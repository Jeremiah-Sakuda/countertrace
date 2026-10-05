# Testing instructions (Devpost field)

The recorded Vercel demo is deployed. **Before submitting:** add the project-funded route for live model calls; the local API-key option is for developers and does not fulfill free live judge access by itself. Do not describe the Vercel route as live execution.

---

## Hosted recorded demo (no setup or account)

Open https://countertrace.vercel.app. The “Recorded demo” notice describes what is available. No API key or login is needed.

1. **Open the showcase run.** “Queue that overwrites when full” shows cycle 6: expected 0x21, got 0x65; probable origin is the ignored write at cycle 5. Follow a cycle citation in the recorded Nemotron explanation, then inspect the one-line repair and the candidate's ten unchanged obligations, including three proofs.
2. **Runs → “Two bugs: reads while empty, and empty ignores the wrap bit.”** The timeline preserves candidate 1's rejection at cycle 4, its counterexample feedback, and candidate 2's acceptance.
3. **Contract setup.** Inspect the source and contract for any bundled example. The showcase and “Accepts a write when full and reading” include actual recorded Super interpretations; the latter flags a contract conflict. “Set up this example” links keep the selected example when navigating from a recording.
4. **Check-quality audit → Open the recorded audit.** Try the missing-requirement exercise, then compare with the faults that escaped the deliberately weak named check set. This does not ingest a user's testbench.
5. **Repair & export → Download evidence bundle.** Verification recordings export ZIPs with inputs, logs, traces, and a manifest of hashes. Replay them locally using the instructions below.

The Vercel deployment is read-only. Live verification, interpretation, explanation, repair, and new audits are disabled there. The recorded model calls are real past Token Factory executions, with their original metadata preserved.

## Local working test build

Needs Python 3.11 or newer, Git, Docker with BuildKit, and Node 20.19+ or 22.12+. On macOS, use Docker Desktop or colima with your home directory shared, and clone under your home directory. On Windows, use WSL2.

```sh
git clone https://github.com/Jeremiah-Sakuda/countertrace
cd countertrace
make setup
make image      # about 700 MB download; pinned checksum
make web
make serve      # http://127.0.0.1:8765
```

The local build includes the same recorded journey plus live deterministic verification, new audits, and bundle replay without a model key. Accept a bundled example's contract and press **Run verification**. Warm runs took 3–11 seconds per example on the development laptop and up to about 25 seconds with concurrent work; this is not a hosted latency promise. One run executes at a time.

For developers, live Nemotron actions require a Token Factory API key in the local `.env`; never place that key in browser code or a public submission. Endpoint, model IDs, token caps, and estimated prices are supplied in `.env.example`. Judge-specific project-funded live access instructions are pending; judges should not be asked to buy credits or provide a paid key.

```sh
source .venv/bin/activate
countertrace verify --example showcase-overwrite-when-full
countertrace audit --check-set weak-learner-v1
countertrace bundle rec-20261004-003607-ver-4cc749
countertrace replay <path-to-downloaded-or-exported-bundle.zip>
make check
make test-integration
```

Use the commit recorded in the bundle manifest and the matching pinned verifier when replaying. The command reports whether deterministic outcomes match; it does not regenerate model text.

## Repository guide

- `README.md`: setup and model roles.
- `evaluation/results/`: both frozen evaluations and the explicitly exploratory reduced-feedback comparison.
- `recorded/`: published evidence behind the demo.
- `verifier/harness/`: trusted simulation driver and formal monitor.
- `docs/DEPLOYMENT.md`: exact deployment capabilities and unauthenticated access checks.
