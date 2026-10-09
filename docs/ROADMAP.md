# Build milestones

Dates are in 2026. A checked item has evidence in [STATUS.md](STATUS.md); development-fixture results are not evaluation results. The [PRD](PRD.md) defines acceptance targets and fallback behavior; this file is the working checklist.

## October 5 education release

The owner selected education as the primary product: predict → investigate → explain → transfer. The verification workbench remains available. PRD v1.3 and the Page are synchronized. The primary activity now centers on challenging actual Nemotron repairs; the three sequence lessons remain the practice bench.

- [x] Three interactive bounded labs, including a correct control; authored hint ladder and per-experiment predictions.
- [x] Record every supported sequence using the isolated verifier; validate archived evidence and browser reference agreement.
- [x] Facilitator desk, answer keys, local session export/import, ungraded explanations, explicit assistance and scope.
- [x] Implement local evidence-grounded Nemotron coaching with existing budgets/rate limits.
- [x] Verify/deploy the completed education release and run up to five fresh simulated panel rounds, fixing actionable feedback until scores stabilize. (Five rounds completed; final averages 8.55 → 8.53 met the declared stability thresholds. All software/documentation fixes applied; [review record](reviews/education-panel.md). These are simulated scores.)
- [ ] Observe actual learner/facilitator use when participants are available. No simulated panel substitutes for learners.

## October 1 to 4 — feasibility

- [x] Create a fresh public repository and workspace scaffold.
- [x] Fold the hackathon review into PRD v1.1.
- [x] Confirm a useful authenticated NVIDIA Nemotron response through Nebius Token Factory; preserve model ID, sanitized request metadata, usage, and timing.
- [x] Select and pin the verifier image, toolchain, and supported syntax. (Debian digest, OSS CAD Suite 2026-09-30 SHA-256, admission subset.)
- [x] Turn the PRD sampling examples into timing fixtures used by both verification flows. (Depth-2 PRD sequence and depth-4 wraparound; the depth-2 sequence is also a simulation test.)
- [x] Distinguish a known-good FIFO from a witnessed faulty design with independent checks. (Development fixtures only.)
- [x] Replay the failure and confirm pre-edge/post-edge cycle alignment.
- [ ] Recruit an experienced technical reviewer and at least three target users. (Evidence strengthening, not an official hackathon requirement or a blocker for deployment; no sessions are claimed.)
- [ ] Rebaseline the 100-hour plan with at least 15 hours of contingency.

**Gate:** an end-to-end witnessed failure plus a useful real model response. *Met on development evidence October 3: the failure, replay, and useful authenticated Ultra explanation exist. Source/trace review was by Codex; independent human validation is pending.* If absent by October 4, stop interface expansion and work on the contract and verifier. The scaffold diagnostic does not satisfy this gate.

## October 5 to 8 — first complete diagnosis

Impact priority selected October 4: help instructors and FPGA club mentors reuse a short debugging lab. The [teaching guide](TEACHING.md) and worksheet are prepared. Next, observe one facilitator and three learners where available; measure transfer answers, assistance, and instructor preparation before expanding scope. This is a proposed pilot, not a completed milestone or additional entry requirement.

- [ ] Contract review, a compact trace, grounded explanation, and a readable report form a usable journey.
- [x] Demonstrate one nontrivial proof, or explicitly select bounded-only scope. (abc pdr proves the flag and data-ordering properties for depth 2 and 4 controls; reachability covers reached. Expert review pending.)
- [x] Attempt one unchanged-contract repair and measure a CPU verification batch. (October 3: one real candidate passed all ten unchanged obligations; 8.92-second warm candidate verification.)
- [x] Measure first useful finding separately from total runtime, with cold/warm conditions stated. (Warm local Docker: first finding 3.3–12 s, total 3.3–22 s across bundled examples; hosted/cold not measured.)
- [ ] Observe an early learner session and obtain technical feedback where available.
- [ ] Make the initial release-profile decision; diagnosis remains the commitment until repair is earned.

## October 8 to 28 — model-written checks (lead direction, PRD 1.4)

- [x] Feasibility spike: structured properties compiled by trusted code, golden proof, trigger reachability, and mutants classified by formal equivalence, in the pinned verifier. Nemotron 3 Ultra promoted on the FIFO in one round and on a round-robin arbiter in two. (October 8, development data; see STATUS.md.)
- [x] Productize the gate with negative controls and a worker job type, including fail-closed per-step and mutation evidence checks (October 9).
- [x] Agent loop as a recorded run type with replayable property evidence (October 9).
- [x] Seven-module gate catalog with golden references, specifications, and hand-written reference properties (October 9). This is not a seven-module model benchmark.
- [ ] Extend golden-confirmed bug hunt and frozen repair beyond the implemented FIFO adapter (October 16 to 19).
- [x] Check-writing interface in recorded mode and configured local live mode (October 9); funded public live runtime remains pending.
- [ ] Frozen held-out evaluation, three runs per module (October 21 to 24).
- [x] Align README, PRD, Devpost draft, and demo script with model-written checks (October 9). Final submission review remains pending.

## October 9 to 14 — trustworthy release scope

- [x] Add immutable comparison inputs, complete regression reruns, and re-admission of generated candidates. (Stubbed negative paths plus one real Ultra candidate on October 3; frozen evaluation pending.)
- [ ] Add compact mutation canaries, evidence export, cancellation, and honest error states. (Implemented locally; awaiting review and learner feedback.)
- [x] Test negative controls and worker isolation. (Altered harness hash, cancellation, unsupported syntax, zero/DUT-owned properties, truncated or tampered traces; network-less, read-only, capability-dropped worker. No external penetration test.)
- [ ] Finalize primary versus diagnosis and proof versus bounded-only profiles by October 14.

## October 15 to 25 — evaluation and usability

- [x] Freeze evaluation fixtures, baseline, prompts/model choice, budgets, and scoring rubric. (October 4: [configuration](../evaluation/freeze-2026-10-04.json) then [cases](../evaluation/cases-frozen-eval-v1.json). Baseline comparison not run; see the eval-v1 report.)
- [ ] Run the declared engineering and learning comparisons; preserve all outcomes and denominators. (Engineering evaluation eval-v1 done October 4, see [report](../evaluation/results/eval-v1/REPORT.md); learning comparisons need participants.)
- [ ] Run the three-person study, including the separate audit transfer question.
- [x] Reproduce three evidence bundles twice in a clean environment. (October 4: two fresh GitHub-hosted x64 runners each built the pinned image and replayed three recorded bundles; all matched. Repeated on every push.)
- [ ] Simplify confusing evidence and stabilize deployment; no new module family.

## October 26 to 30 — submission

- [ ] Record the 2:45 demonstration using actual results and the selected release profile. (Owner will record/post; internal reviewers assessed the revised script as intended content, not finished footage.)
- [ ] Finish setup instructions, provenance, sponsor feedback, and public project description. (Drafted in [SUBMISSION.md](SUBMISSION.md); recorded Vercel URL live, free live inference access and video pending.)
- [ ] Test the judge route free of charge without the owner's login or a judge-supplied paid API key.
- [ ] Verify funding, credit expiry, release preservation, and recovery steps through December 15.
- [ ] Rehearse the submission on October 29 and submit before October 30 at 1:00 p.m. EDT.

## October 31 to December 15 — judging availability

- [ ] Maintain funded access and retained judging fixtures.
- [ ] Preserve the tested release; do not assume submission materials can change after the deadline.
