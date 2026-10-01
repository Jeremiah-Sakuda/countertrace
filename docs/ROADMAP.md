# Build milestones

All implementation milestones below are pending. Dates are in 2026. The [PRD](PRD.md) defines acceptance targets and fallback behavior; this file is the working checklist.

## October 1 to 4 — feasibility

- [x] Create a fresh public repository and workspace scaffold.
- [x] Fold the hackathon review into PRD v1.1.
- [ ] Confirm a useful authenticated NVIDIA Nemotron response through Nebius Token Factory; preserve model ID, sanitized request metadata, usage, and timing.
- [ ] Select and pin the verifier image, toolchain, and supported syntax.
- [ ] Turn the PRD sampling examples into timing fixtures used by both verification flows.
- [ ] Distinguish a known-good FIFO from a witnessed faulty design with independent checks.
- [ ] Replay the failure and confirm pre-edge/post-edge cycle alignment.
- [ ] Recruit an experienced technical reviewer and at least three target users.
- [ ] Rebaseline the 100-hour plan with at least 15 hours of contingency.

**Gate:** an end-to-end witnessed failure plus a useful real model response. If absent by October 4, stop interface expansion and work on the contract and verifier. The scaffold diagnostic does not satisfy this gate.

## October 5 to 8 — first complete diagnosis

- [ ] Contract review, a compact trace, grounded explanation, and a readable report form a usable journey.
- [ ] Demonstrate one nontrivial proof, or explicitly select bounded-only scope.
- [ ] Attempt one unchanged-contract repair and measure a CPU verification batch.
- [ ] Measure first useful finding separately from total runtime, with cold/warm conditions stated.
- [ ] Observe an early learner session and obtain technical feedback where available.
- [ ] Make the initial release-profile decision; diagnosis remains the commitment until repair is earned.

## October 9 to 14 — trustworthy release scope

- [ ] Add immutable comparison inputs, complete regression reruns, and re-admission of generated candidates.
- [ ] Add compact mutation canaries, evidence export, cancellation, and honest error states.
- [ ] Test negative controls and worker isolation.
- [ ] Finalize primary versus diagnosis and proof versus bounded-only profiles by October 14.

## October 15 to 25 — evaluation and usability

- [ ] Freeze evaluation fixtures, baseline, prompts/model choice, budgets, and scoring rubric.
- [ ] Run the declared engineering and learning comparisons; preserve all outcomes and denominators.
- [ ] Run the three-person study, including the separate audit transfer question.
- [ ] Reproduce three evidence bundles twice in a clean environment.
- [ ] Simplify confusing evidence and stabilize deployment; no new module family.

## October 26 to 30 — submission

- [ ] Record the 2:45 demonstration using actual results and the selected release profile.
- [ ] Finish setup instructions, provenance, sponsor feedback, and public project description.
- [ ] Test the judge route free of charge without the owner's login or a judge-supplied paid API key.
- [ ] Verify funding, credit expiry, release preservation, and recovery steps through December 15.
- [ ] Rehearse the submission on October 29 and submit before October 30 at 1:00 p.m. EDT.

## October 31 to December 15 — judging availability

- [ ] Maintain funded access and retained judging fixtures.
- [ ] Preserve the tested release; do not assume submission materials can change after the deadline.
