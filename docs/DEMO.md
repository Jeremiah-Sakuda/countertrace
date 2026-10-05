> The recording script is now [docs/submission/DEMO_SCRIPT.md](submission/DEMO_SCRIPT.md). This file keeps the original storyboard and its status notes.

# Demonstration storyboard (draft)

A 2:45 plan following the PRD's timing table. Every screen must show actual evidence; label recorded runs and any edited waits. Replace bracketed items only with observed results.

| Time | Screen | Evidence to show | Status today |
| --- | --- | --- | --- |
| 0:00–0:15 | Showcase example card | "This 4-entry queue drops a byte you already stored when a write arrives while it is full." Scope line: one sync FIFO profile, 8-bit, depth 2 or 4. | Available |
| 0:15–0:35 | Contract setup | RTL, the brief, the contract rows; Nemotron's interpretation flags any conflict (for contrast, `dev-full-exchange` has a conflicting brief). | Available: Nemotron 3 Super with reasoning off, 2.3–3.7 s per brief; eval-v1 4/4 and eval-v2 3/4 conflicts detected |
| 0:35–1:05 | Findings | Cycle table: 0x21 accepted at cycle 1, 0x65 offered while full at cycle 5, read at cycle 6 returns 0x65. Formal counterexample at cycle 5 reproduced in simulation. Nemotron's explanation with clickable cycle citations. | Available: October 4 recording, one Ultra request, 18 valid citations, assistant-reviewed; independent human review pending |
| 1:05–1:35 | Repair | Proposed diff, "unchanged contract and checks: hashes match", candidate run with proofs. | Available: October 4 recording, first-candidate one-line edit (`wr_en && !full`), all ten unchanged obligations passed; eval-v1 repaired 7/8 |
| 1:35–2:00 | Audit | `weak-learner-v1` misses 3 of 6 valid faults; ask "which requirement is missing?"; reveal write-while-full and simultaneous-at-boundary rows. The core still witnessed every fault; the equivalent mutant is reported separately. | Available |
| 2:00–2:20 | Obligations and export | Method-specific labels, unresolved count, bundle download, `countertrace replay` matching. | Available |
| 2:20–2:45 | Results and roles | Actual evaluation counts (frozen suite), user observations if obtained, measured Nemotron and Nebius usage. | eval-v1 counts available; learner study not done |

If repair is cut (diagnosis release), replace 1:05–1:35 with a second counterexample and its evidence replay. If only bounded checking is claimed, replace proof wording with the exact depth.

Recording prerequisites: complete the [model gate and showcase refresh](MODEL_GATE.md), record the [release decision](RELEASE_DECISION.md), and replace the results segment with measured evaluation/study outcomes. No final video has been recorded. The October 4 showcase recording (`rec-20261004-003607-ver-4cc749`) contains the assistant-reviewed explanation and links to its one-line repaired candidate (`rec-20261004-003622-ver-d88ef8`); verification, explanation, and repair all ran October 4. Usage is measured, but account billing and credits remain unverified. Prompt iterations and one showcase repair must not be presented as evaluation performance.

## Education release update — October 5

The current narrative and timings are in [the education demo script](submission/DEMO_SCRIPT.md). Start at the learning lab, build an ordinary test and an overflow counterexample, then show explanation, transfer, and facilitator reuse. The earlier workbench shot list remains background. The owner records/uploads; script review is not footage review.
