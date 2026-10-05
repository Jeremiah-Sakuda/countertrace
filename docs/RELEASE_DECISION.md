# Release decision record

**Current commitment: diagnosis (unchanged until the owner decides). Evidence now supports primary.** On October 4 the frozen eval-v1 suite met every measured primary target: repair 7/8 within three candidates (bar 5/8), diagnosis 8/8 across four classes, 0/4 false alarms, interpretation 4/4 and 4/4 ([report](../evaluation/results/eval-v1/REPORT.md)). Caveats: one run, assistant-authored cases and labels, assistant review only, and no learner evidence yet.

**Recommendation (assistant, for the owner to accept or reject), revised October 4:** retain diagnosis plus repair in the hackathon demonstration. Two frozen evaluations met the engineering repair target (7/8 and 8/8 within three candidates), and the submission materials present those observed results with their limitations. External label review and learner sessions are not hackathon entry requirements and are not blockers for implementing fixes or deploying the recorded demonstration. They remain unperformed; do not claim the PRD's learning targets, independent validation, or complete primary-release acceptance have been achieved. This recommendation does not silently waive those internal targets.

Previous summary: An authenticated Ultra explanation and one real unchanged-check showcase repair ran October 3. The explanation was reviewed by Codex, not an independent human. A development success does not satisfy the frozen repair evaluation. This record implements the existing PRD gates; it does not change them.

| Decision | Date | Required evidence | Current result |
| --- | --- | --- | --- |
| Model feasibility | October 4 | Useful authenticated Nemotron explanation of a replayed failure | Met October 3 on development evidence; Codex source/trace review, independent human validation pending |
| Initial profile | October 8 | Complete diagnosis journey, first real unchanged-check repair, measured verification batch, early feedback | Journey, real repairs (7/8 frozen, 5/5 development with edits), and warm batches measured; early feedback pending |
| Final profile | October 14 | Evidence supports the primary repair target and unchanged-check trust rules; otherwise diagnosis | Pending |

The primary repair target is at least 5 of 8 faulty cases repaired within three candidate attempts, with all-case and attempted-repair denominators. A showcase success is insufficient. Freeze cases and evaluation configuration before the evidence used to make this decision; if that evidence is unavailable by October 14, choose diagnosis. Later evaluations must remain separate from development tuning.

Both profiles still require the PRD's diagnosis, explanation, audit, reproducibility, and user-study evidence. External FIFO acquisition is not independent validation. Either profile is blocked by persistent false acceptance or an untrustworthy oracle. Declare proof versus bounded-only scope separately, using actual named obligations and assumptions.

## Fill when deciding

- Decision date and owner: pending.
- Profile (primary / diagnosis): pending final decision; diagnosis is the delivery baseline.
- Evidence manifest: [freeze](../evaluation/freeze-2026-10-04.json), [cases](../evaluation/cases-frozen-eval-v1.json), [results](../evaluation/results/eval-v1/results.json).
- Repair successes / all 8 cases / attempted cases: 7 / 8 / 8 (eval-v1, full-file format); 8 / 8 / 8 (eval-v2, edit format). Single runs, with assistant-authored cases and review.
- Scope of formal claims: named proofs exist on development, evaluation controls, and accepted repair configurations under their recorded assumptions. External review remains absent.
- Submission work remaining (owner unless noted): final release declaration; free access to the advertised live model features and availability through December 15; owner recording/publication of the video. The Vercel recorded demo and the local Docker test build are distinct routes; publishing recordings does not complete live access. Clean-environment replays and the frozen evaluations are done (eval-v1, eval-v2).
- Optional evidence strengthening for the hackathon: outside review of labels and learner sessions. Their absence must remain disclosed. The PRD's separate internal study targets remain unmet, not waived by this submission checklist.

If diagnosis is selected, remove repair controls from the judged journey and repair promises from the README, submission, and video; retain developer experiments clearly labeled. Use a second held-out counterexample and replay for the replacement video segment. Update [STATUS.md](STATUS.md), [DEMO.md](DEMO.md), and the [roadmap](ROADMAP.md) with the actual decision. No release decision or future reminder is scheduled by this document.
