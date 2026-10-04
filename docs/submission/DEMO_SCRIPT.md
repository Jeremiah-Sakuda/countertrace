# Demo video script (target 2:45, limit 3:00)

Seven segments. Narration totals about 330 words, roughly 2:15 of speech, which leaves time for pauses and for viewers to read the screen. Everything on screen except the live run is a recorded run, so no live model call is needed during recording. Record at 1440 × 900 or larger, with browser zoom at 100%.

## Before recording

- `make serve`, then open http://127.0.0.1:8765 (or the hosted URL) in a clean browser window with no other tabs or bookmarks visible.
- Open these tabs in order:
  1. `#/runs/rec-20261004-003607-ver-4cc749` (showcase)
  2. `#/examples/dev-full-exchange` (contract setup with a recorded interpretation)
  3. `#/` (setup, for the live run)
  4. `#/runs/rec-20261004-010137-ver-dd43e0` (two-bug repair)
  5. `#/runs/rec-20261001-193049-aud-7cf847` (audit)
- Have a terminal ready with `.venv` activated, in the repository folder, with the bundle already exported: `countertrace bundle rec-20261004-003607-ver-4cc749`.
- Do one practice live run of `showcase-overwrite-when-full` so the verifier image is warm.
- No background music, or only music you have rights to. No third-party logos beyond the sponsor names in narration.

## Script

### 1. The bug (0:00 to 0:15)

**Screen:** Tab 1, showcase run hero. Hover over "Expected 0x21 → Observed 0x65", then the "Probable origin: cycle 5" line.

**Narration:** "This queue passes its author's tests. This copy has a seeded bug, and Countertrace pins it down: the byte written at cycle one is gone, and the read at cycle six returns a different byte."

### 2. The contract and Nemotron 3 Super (0:15 to 0:38)

**Screen:** Tab 2. Scroll slowly past the contract rows (simultaneous read and write, write while full). Open the recorded interpretation and point at the blocking conflict on "simultaneous_full". Then go to Tab 3, pick the showcase example, and click Accept contract.

**Narration:** "Before anything runs, you see the exact behavior the checks enforce, cycle by cycle. Nemotron 3 Super reads the designer's plain-English brief and flags where it conflicts with the contract. Here it caught a request to accept writes when the queue is full. It flags the conflict instead of changing the rules."

### 3. A live run and the failing cycle (0:38 to 1:05)

**Screen:** Press Run. Show the stages for two or three seconds, then cut (put a small "sped up" caption on the cut). Land on the finding: the cycle table with cycle 6 highlighted and the reference queue. Then open the formal panel and show "Reproduced in simulation."

**Narration:** "The design runs in an isolated container: Verilator simulation, then bounded and unbounded formal checks with SymbiYosys, judged by two independent references. About ten seconds later, the cycle table shows exactly where it breaks. At cycle five the design writes while full, which the contract says to ignore. The formal counterexample replays in simulation, so both engines agree."

### 4. Explanation and repair with Nemotron 3 Ultra (1:05 to 1:40)

**Screen:** Tab 1. Scroll to the explanation. Click the "cycle 5" citation and let it jump to the row. Scroll to Repair: the one-line diff `wr_en && !full`. Click through to the candidate and show "3 proved · 0 counterexamples · frozen hashes match." Then Tab 4: show the repair timeline with "candidate 1 rejected", "counterexample fed back: empty_flag at cycle 4", and "candidate 2 passed".

**Narration:** "Nemotron 3 Ultra explains the failure for a student, and every cycle and signal it cites is checked against the trace. Then it proposes a patch: one line. Countertrace reruns the identical checks, compared by hash, and accepts the fix only because the proofs pass. When a patch fails, its own counterexample goes back to the model. In this design with two bugs, the first patch still failed at cycle four, and the second passed every check."

### 5. Auditing the learner's checks (1:40 to 2:00)

**Screen:** Tab 5. Show the headline "3 of 6 real bugs slip past this check set." Tick an answer in the exercise and reveal the missing requirements.

**Narration:** "Countertrace can also grade a student's checks instead of their design. A deliberately weak, learner-style check set misses three of six seeded bugs, and each miss points to the requirement it never drives, like a write while full."

### 6. Evidence anyone can rerun (2:00 to 2:15)

**Screen:** Terminal. Run `countertrace replay <bundle path>` and show `"matches": true`.

**Narration:** "Every run exports a hashed evidence bundle. Replay reruns the deterministic checks with no model call, on any machine."

### 7. Results and how the models are used (2:15 to 2:45)

**Screen:** A simple slide with the results table from the Devpost write-up: eval-v1 and eval-v2 side by side (8 of 8 bugs found, 0 false alarms, repairs 7 of 8 and 8 of 8). Then the model routing table. End on the repository URL.

**Narration:** "In two frozen evaluations, Countertrace found every seeded bug with no false alarms, and Nemotron's repairs passed the unchanged checks in seven of eight and then eight of eight cases. Every model call goes through Nebius Token Factory, while verification runs in CPU containers: Super with reasoning off for fast calls, Ultra for explanations and repairs. Nemotron proposes every fix, and checks it cannot change decide whether it counts."

## After recording

- Keep it under 3:00; trim pauses rather than speeding up narration.
- Add captions for the sped-up wait in segment 3 and label recorded runs as "recorded" where they first appear.
- Upload to YouTube as Public (the rules require a publicly visible video), title "Countertrace: a FIFO bug-finding and repair agent on NVIDIA Nemotron", and paste the link into Devpost.
