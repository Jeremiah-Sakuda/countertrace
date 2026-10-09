# Testing instructions (Devpost field)

Open https://countertrace.vercel.app without signing in. The public site provides recorded model repairs and independently executed verification evidence. No account or API key is needed for playback. Live execution is available in the configured local build described below.

---

## Start with model-written checks

1. Open **Checks**. Read the catalog and choose the synchronous FIFO specification.
2. Open its actual recorded run. Inspect every model round, properties, exact gate feedback, parameter settings, mutation denominators, and model-call provenance.
3. Follow its linked FIFO bug-hunt evidence when present. A confirmed defect requires the golden replay to pass and the candidate to violate the independent reference on the same input sequence.
4. Follow the repair link and inspect every attempted diff and unchanged-check comparison. Missing or unresolved evidence cannot appear as acceptance.
5. Download the checks or verification bundle and replay it from the matching checkout. The new checks bundle reruns deterministic gates, not inference.

Live start buttons are disabled on Vercel. In the configured local build, choose **Write checks**, then start a FIFO hunt from a promoted run. Other catalog modules currently support the gate only. Do not use held-out modules for exploratory prompt development before freezing the evaluation protocol.

## Optional repair learning lab

1. Open **Labs** and choose the repair lab. Case 01 is selected; the other three cases are in the row above it. Inspect the depth-4 contract and the actual Nemotron diff.
2. Choose a prediction and write a reason. Open **Test it yourself first**, add Write four times, and see the candidate report empty at edge 4 while the reference queue is full. Then reveal the recorded checks, which show the same kind of counterexample.
3. Investigate the revised proposal and commit another prediction. Its ten obligations pass under unchanged comparison inputs: three simulation obligations, three bounded checks, three proved properties, and one cover group containing twelve covers.
4. Follow **Inspect this run’s trace & methods** for raw evidence and scope. Return to the lab, explain your decision, answer the depth-8 transfer question, and download Markdown notes.
5. Try case 02 (a fix that breaks working code: a single Read exposes it) or case 03 (three rounds on one flag).
6. Open **Practice bench → Will your testbench catch it?** Load a typical first testbench, predict, and run: it catches 3 of 6 seeded bugs, and each miss names the situation its tests never produced. Select only **simultaneous** with all three signals: 6 of 6 in 15 edges.
7. Open **Teach** for the discussion plan. The separate practice-bench exercises below provide sequence construction and JSON session import.

This is recorded playback, not a new model response or solver run. Test answers you enter are demonstration practice data, not participant observations.

## Hosted learning lab (no setup or account)

Open https://countertrace.vercel.app. All browser experiments replay actual recorded RTL execution. No API key or login is needed.

1. **Labs → Practice bench → The disappearing word.** Commit a prediction. Add Write → Read, choose “No mismatch,” and run. Clear the sequence, add Write → Write → Write → Read, predict a mismatch, and run. Edge 4 should show expected 0x11 versus observed 0x33. The expected reference queue ignores the third write while full.
2. **Explain and transfer.** Write an explanation. Open an authored hint or the explicitly recorded Nemotron example if desired; assistance is counted. The recorded response answers its displayed example text, not your newly typed text. Answer the depth-4 simultaneous-operation question and download notes or session JSON. Free text is ungraded.
3. **Facilitator desk.** Open lesson notes/answer keys. Optionally import the JSON you just exported; it stays in the browser. Counts describe practice records, not unique participants or learning gains.
4. **Other labs.** The simultaneous-operation candidate fails Write → Write → Read + write at edge 3. The correct-control lesson permits no-mismatch conclusions; Write → Read repeated three times returns no mismatch under this finite test.
5. **Real model repair extension.** Follow the completed lab's link to the recorded two-bug run. Inspect candidate 1's rejection and candidate 2's acceptance under unchanged checks. The learner fixtures and these actual model proposals are explicitly distinguished.
6. **Evidence.** The lab downloads its raw trace/source/stimulus archive and hash manifest. Runs in the workbench separately export replayable verification bundles. The library is finite simulation; workbench formal results retain their named methods and scope.

The hosted site does not call a model or execute RTL live. Vercel rejects API writes. Authored hints and recorded coaching remain usable without paid access. The local build below supplies live coaching, interpretation, verification, explanation, repair, and audits when configured.

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

The local build includes the same learning lab and recorded workbench plus live deterministic verification, new audits, and bundle replay without a model key. Accept a bundled example's contract and press **Run verification**. Warm runs took 3–11 seconds per example on the development laptop and up to about 25 seconds with concurrent work; this is not a hosted latency promise. One run executes at a time.

After a local experiment and reflection, **Ask Nemotron about my reasoning** sends those inputs to the configured service. The hint is advisory and retains its experiment context.

For developers, live Nemotron actions require a Token Factory API key in the local `.env`; never place that key in browser code or a public submission. Endpoint, model IDs, token caps, and estimated prices are supplied in `.env.example`. Judge-specific project-funded live access instructions are pending; judges should not be asked to buy credits or provide a paid key.

```sh
source .venv/bin/activate
countertrace write-checks --module sync_fifo --rounds 4
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
