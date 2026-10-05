# Demo video script (target 2:45, limit 3:00)

The owner will record and publish the video. Internal simulated reviewers assessed this script and the supporting artifacts as the intended video content; they did not assess footage, audio, or a finished upload. Keep the public-video requirement separate from that script assessment.

Use the Vercel recorded demo for the evidence walkthrough. Capture the live verification and CLI replay in the local Docker build, clearly labeled **Local live run**. The static Vercel deployment does not execute RTL or call a model. No paid inference is needed while filming: the authentic recorded calls and their metadata demonstrate Nemotron use.

## Before recording

- Run `make serve` locally and warm the verifier with one showcase verification.
- Record at 1440 × 900 or larger, at 100% browser zoom. Keep recorded-run labels visible.
- Open these routes in order (use the local base URL for tab 3):
  1. `#/runs/rec-20261004-003607-ver-4cc749` (showcase)
  2. `#/examples/dev-full-exchange` (contract and recorded interpretation)
  3. `#/examples/showcase-overwrite-when-full` (local setup)
  4. `#/runs/rec-20261004-010137-ver-dd43e0` (two-bug repair)
  5. `#/runs/rec-20261001-193049-aud-7cf847` (audit)
- Export the showcase bundle locally before filming: `countertrace bundle rec-20261004-003607-ver-4cc749`. Keep the printed path ready for replay.
- Use only music and visual assets you have rights to; music is unnecessary.

## Script

### 1. The bug (0:00 to 0:15)

**Screen:** Showcase finding, expected/observed values, probable origin. Scope caption: “Synchronous FIFO · 8-bit words · depths 2 and 4.”

**Narration:** “This four-entry FIFO has a seeded bug. At cycle six, it returns 0x65 instead of 0x21. Countertrace traces the corruption to a write while full.”

### 2. The contract and Nemotron 3 Super (0:15 to 0:38)

**Screen:** Tab 2. Open “Read the complete contract” for the full/empty simultaneous-operation rows, then “Decisions by topic” in the recorded interpretation to show `simultaneous_full`. Briefly show the recorded model identity. Cut to tab 3 and accept its contract.

**Narration:** “First, choose the exact behavior to check. Nemotron 3 Super compares a plain-English brief with that contract. Here, the brief requests a write alongside a read while full. Super flags the conflict; it cannot quietly change the rules.”

### 3. A live run and the failing cycle (0:38 to 1:05)

**Screen:** Caption “Local live run · warm Docker verifier.” Click **Run verification**. Show the real stages, then cut the wait with an “Elapsed wait shortened” caption. Show the cycle-6 simulation finding. Show formal replay separately, labeled “Separate solver-generated sequence: full_flag at cycle 5.”

**Narration:** “The design runs through isolated simulation and formal checks, with separate reference monitors. The cycle table shows the accepted inputs and expected output. A solver-generated failing sequence also reproduces in simulation. These are scoped results for this contract and configuration.”

### 4. Explanation and repair with Nemotron 3 Ultra (1:05 to 1:40)

**Screen:** Return to the recorded showcase. Use the Explanation shortcut; click cycle 5, then “Back to explanation step 1.” Use **Repair & export** to show the one-line diff and candidate comparison. Cut to tab 4's two-attempt timeline. Keep the counterexample at cycle 4 readable. Avoid opening secondary metadata during the timeline.

**Narration:** “Nemotron 3 Ultra explains the failure and proposes a one-line patch. Citation checks validate references, not the reasoning itself. The patch passes all ten unchanged obligations, including three proofs. In this two-bug case, the first patch still fails. Its new counterexample goes back to Nemotron, and the second candidate passes. The model never approves its own fix.”

### 5. Auditing a named check set (1:40 to 2:00)

**Screen:** Tab 5. Show “3 of 6 real bugs slip past this check set,” try the exercise, and reveal the missing requirements. Keep the equivalent-mutant count visible. Caption: “Named supplemental set · not imported student testbenches.”

**Narration:** “The audit exposes gaps in a named learner-style check set. This deliberately weak set misses three of six valid seeded bugs. Each survivor points to a requirement the set never exercises, such as writing while full.”

### 6. Evidence anyone can rerun (2:00 to 2:15)

**Screen:** Local terminal, caption “Local deterministic replay.” Run `countertrace replay <exported bundle path>` and show the actual `"matches": true`. Shorten the wait only with a visible caption; do not paste a fabricated result.

**Narration:** “An evidence bundle preserves inputs, traces, logs, and hashes. With Docker and the matching verifier, replay reruns the deterministic checks without a model call.”

### 7. Results and model roles (2:15 to 2:45)

**Screen:** Results for eval-v1/eval-v2: diagnosis 8/8 and 8/8; false alarms 0/4 and 0/4; repair 7/8 and 8/8. Caption throughout: “One run per suite · assistant-authored cases and labels · no external review or learner study.” Then show Super → interpretation; Ultra → explanation/repair; Token Factory → model inference; isolated CPU containers → verification. End on the repository and demo links.

**Narration:** “Each frozen evaluation used eight faults and four controls. Diagnosis found all faults without false alarms; repairs passed in seven of eight and then eight of eight cases. These are small, single-run engineering results. All model calls use Nebius Token Factory. Nemotron proposes patches; unchanged independent checks decide whether they count.”

## After recording

- Rehearse with the actual clicks and pauses; word count alone cannot establish runtime. Keep the final video under three minutes and captions readable.
- Keep recorded evidence and local live execution labeled. Do not suggest the Vercel recorded demo runs the verifier.
- Upload to YouTube as Public and fill the video URL in the submission. Suggested title: “Countertrace: FIFO debugging and repair with NVIDIA Nemotron.”
