# Build milestones

Dates are in 2026. A checked item has evidence in [STATUS.md](STATUS.md); development-fixture results are not evaluation results. The [PRD](PRD.md) defines acceptance targets and fallback behavior; this file is the working checklist.

## October 1 to 4 — feasibility

- [x] Create a fresh public repository and workspace scaffold.
- [x] Fold the hackathon review into PRD v1.1.
- [x] Confirm a useful authenticated NVIDIA Nemotron response through Nebius Token Factory; preserve model ID, sanitized request metadata, usage, and timing.
- [x] Select and pin the verifier image, toolchain, and supported syntax. (Debian digest, OSS CAD Suite 2026-09-30 SHA-256, admission subset.)
- [x] Turn the PRD sampling examples into timing fixtures used by both verification flows. (Depth-2 PRD sequence and depth-4 wraparound; the depth-2 sequence is also a simulation test.)
- [x] Distinguish a known-good FIFO from a witnessed faulty design with independent checks. (Development fixtures only.)
- [x] Replay the failure and confirm pre-edge/post-edge cycle alignment.
- [ ] Recruit an experienced technical reviewer and at least three target users.
- [ ] Rebaseline the 100-hour plan with at least 15 hours of contingency.

**Gate:** an end-to-end witnessed failure plus a useful real model response. *Met on development evidence October 3: the failure, replay, and useful authenticated Ultra explanation exist. Source/trace review was by Codex; independent human validation is pending.* If absent by October 4, stop interface expansion and work on the contract and verifier. The scaffold diagnostic does not satisfy this gate.

## October 5 to 8 — first complete diagnosis

- [ ] Contract review, a compact trace, grounded explanation, and a readable report form a usable journey.
- [x] Demonstrate one nontrivial proof, or explicitly select bounded-only scope. (abc pdr proves the flag and data-ordering properties for depth 2 and 4 controls; reachability covers reached. Expert review pending.)
- [x] Attempt one unchanged-contract repair and measure a CPU verification batch. (October 3: one real candidate passed all ten unchanged obligations; 8.92-second warm candidate verification.)
- [x] Measure first useful finding separately from total runtime, with cold/warm conditions stated. (Warm local Docker: first finding 3.3–12 s, total 3.3–22 s across bundled examples; hosted/cold not measured.)
- [ ] Observe an early learner session and obtain technical feedback where available.
- [ ] Make the initial release-profile decision; diagnosis remains the commitment until repair is earned.

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

- [ ] Record the 2:45 demonstration using actual results and the selected release profile.
- [ ] Finish setup instructions, provenance, sponsor feedback, and public project description. (Drafted in [SUBMISSION.md](SUBMISSION.md); hosted URL and video pending.)
- [ ] Test the judge route free of charge without the owner's login or a judge-supplied paid API key.
- [ ] Verify funding, credit expiry, release preservation, and recovery steps through December 15.
- [ ] Rehearse the submission on October 29 and submit before October 30 at 1:00 p.m. EDT.

## October 31 to December 15 — judging availability

- [ ] Maintain funded access and retained judging fixtures.
- [ ] Preserve the tested release; do not assume submission materials can change after the deadline.
