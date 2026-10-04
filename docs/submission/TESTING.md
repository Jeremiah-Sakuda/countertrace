# Testing instructions (Devpost field)

Paste the section below into the Devpost testing-instructions field. Replace [hosted URL] once the hosted build is live, or delete option A if it is not.

---

## Option A: hosted demo (no setup)

Include this option only once the hosted build is live. Open [hosted URL]. No account or API key is needed.

1. **Runs → "Queue that overwrites when full"** (recorded). You will see the first failing cycle (cycle 6: expected 0x21, got 0x65), the probable origin (cycle 5, a write while full that the contract ignores), and the cycle table. Click a cycle in Nemotron's explanation to jump to that row. Scroll to Repair to see the one-line fix and the candidate run where all ten checks pass, including three proofs.
2. **Runs → "Two bugs: reads while empty, and empty ignores the wrap bit"** (recorded). The repair timeline shows candidate 1 rejected at cycle 4, that counterexample given back to the model, and candidate 2 accepted.
3. **Contract setup.** Pick an example and read the contract. Two examples carry a recorded Nemotron interpretation you can open without a key: the showcase, and "Accepts a write when full and reading", where a conflict is flagged. Accept the contract and press Run. A live verification took 3 to 11 seconds per example on my laptop and up to about 25 seconds when several runs shared the machine; only one run executes at a time, so you may wait for another visitor's run.
4. **Check-quality audit.** Open the recorded audit, try the "Which requirements is this check set missing?" exercise, then compare with the seeded faults the weak set let through.
5. On any run, **Export → Download evidence bundle** gives a zip with the inputs, logs, traces, and a manifest of hashes.

Live Nemotron buttons (Interpret, Explain, Propose a repair) use the project's own Token Factory key and are rate limited per visitor.

## Option B: local test build

Needs Python 3.11 or newer, Git, Docker with BuildKit (the default), and Node 20.19+ or 22.12+. On macOS, run Docker in a VM that shares your home directory (Docker Desktop or colima), and clone under your home directory. On Windows, use WSL2.

```sh
git clone https://github.com/Jeremiah-Sakuda/countertrace
cd countertrace
make setup      # creates .venv and a local .env
make image      # builds the pinned verifier image (about 700 MB download, checksum-verified)
make web        # builds the interface
make serve      # http://127.0.0.1:8765
```

Then follow steps 1 to 5 above at http://127.0.0.1:8765. Without a key, everything works except the three live Nemotron buttons: recorded runs (with their recorded explanations and repairs), the two recorded interpretations, live verification, the audit, and evidence bundles. To try the live Nemotron buttons, add your own `NEBIUS_API_KEY` to `.env`; the endpoint, model IDs, token caps, and prices are already filled in.

Command line, after `source .venv/bin/activate`:

```sh
countertrace verify --example showcase-overwrite-when-full   # one live verification
countertrace audit --check-set weak-learner-v1               # the check-quality audit
countertrace bundle rec-20261004-003607-ver-4cc749           # export the showcase evidence
countertrace replay <path printed by the previous command>   # rerun its checks, no model call
make test && make test-integration                           # unit tests and Docker tests
```

## Where to look in the repository

- `README.md`: overview, setup, and how Nemotron and Token Factory are used.
- `evaluation/results/`: both frozen evaluations and the repair ablation, with raw JSON.
- `recorded/`: the evidence behind every recorded run in the interface.
- `verifier/harness/`: the trusted simulation driver and formal monitor.
