# Education round 5 — independent learning/product review

Reviewed commit `2ce3f15f463eb618386edd3b99eb7fd5ca4e9594` on October 5, 2026. This is a simulated hackathon review, not sponsor judging or human learner evidence. No earlier panel scorecards were consulted. Read-only source/artifact review; no shared-browser navigation, new model calls, deployment, or product edits. The video is assessed as the intended content in `docs/submission/DEMO_SCRIPT.md`, not unavailable footage.

| Equally weighted criterion | Score / 10 | Assessment |
| --- | ---: | --- |
| Technological Implementation | 9.0 | Learner-built sequences resolve to actual archived isolated-Verilator observations, with a pinned library and independent reference agreement. Real Nemotron repair remains inspectable in the workbench, including a rejected candidate and unchanged-check acceptance. Advisory coaching is useful additional functionality with explicitly mixed development evidence; it does not determine verification or grades. |
| Design | 8.8 | Clear prediction → experiment → explanation → transfer progression, bounded choices, answer preservation, context-bound coaching, completion assistance snapshot, and local facilitator import/export. Source review shows labeled controls, focus transfer, and scoped result wording. This review did not independently recheck visual rendering or screen-reader behavior. |
| Potential Impact | 8.5 | A concrete reusable activity for instructors and FPGA mentors, with low-friction recorded access and inspectable learner reasoning. The benefit is plausible and demonstrable as a workflow; reuse, preparation-time savings, and improved transfer remain unmeasured. |
| Quality of Idea | 9.0 | Choosing a revealing counterexample, distinguishing contract policy from universal correctness, and challenging a real AI repair form a coherent teaching proposition. The limited action library is sufficient for the stated lesson; adding module families or arbitrary uploads would not improve this assessment. |

**Equal-weight mean: 8.825/10 (88.25/100).** Strong submission story with no blocking education-flow defect found in this review.

Evidence examined: PRD/roadmap; teaching guide and demo script; `LearnView.tsx`, `learning.ts`, server coaching; archived learning library and its raw-trace validation; recorded coaching development evidence; eval-v2 repair report and recorded-run documentation. Fresh checks: `make check` passed 101 Python tests plus workspace checks; `npm --prefix apps/web test` passed 3/3. The learning checks hash-validate the archive, compare every raw trace to the independent reference, and check all browser prefixes. These are software/evidence checks, not fresh RTL execution or new model/learner results. UI/UX Pro Max guidance was used for the interaction-source review.

## Remaining reproducible in-scope defect

- **P3 — retained history is presented as total experiment count.** `LearnView.tsx` appends with `session.attempts.slice(-199)`, while the notebook and transfer snapshot use `attempts.length` as the experiment count. Repeating the same valid sequence 201 times leaves 200 records, drops attempt 1, and records 200 experiments at submission. Reproduced the exact append operation in Node: 201 runs → displayed count 200, first retained run 2. This is unlikely in one short lesson and does not change RTL outcomes, first answers, or assistance counts. Narrow fix: identify the history as the latest 200 experiments and disclose truncation; retain a separate total only if a total is needed. No broader analytics system is necessary.

## Dependencies and limits, not new product defects

- Actual facilitator reuse and learner transfer need willing participants. A simulated panel cannot supply this evidence; no adoption or learning gains are claimed.
- Public recorded access supports the core lesson without paid learner credentials. Free live model access and availability/funding through judging are separate release dependencies, not grounds to describe the hosted lesson as nonfunctional.
- Coaching checks contain semantic failures despite valid structure/citations. The visible advisory limitation, authored fallback, and independent answers make that a disclosed model-quality limit. This review does not require perfect model semantics or another paid prompt-tuning loop.
- The 2:45 script shows an ordinary passing test, a learner-built boundary failure, actual recorded/live-labeled coaching, transfer/export, facilitator review, and genuine rejected/accepted repairs. That is a strong intended demonstration. Actual footage, editing, publication, and delivery quality remain unassessed.

Recommendation: retain the current narrow education scope. The small history-label correction can be handled as polish; the most useful next evidence is actual learner/facilitator observation when available, not additional feature breadth.
