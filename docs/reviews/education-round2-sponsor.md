# Independent simulated sponsor panel — education round 2

Reviewed October 5, 2026, at commit `0fd4317a51b790b5eed4aece4a3b352b2762e198`. This is an assistant's simulated review, not actual NVIDIA, Nebius, or hackathon judging. No earlier panel files or scores were consulted. The current publishing source is the review target; no shared browser navigation, new inference call, or deployment check was performed. The demo is assessed as the intended story in `docs/submission/DEMO_SCRIPT.md`, not as unseen footage.

## Scores

The four official criteria receive equal weight. These are subjective 0–10 assessments, not predicted official scores or a win probability. The [official rules](https://nebiusglobalaihackathon.devpost.com/rules) were checked for criteria, required integration, and judge access.

| Criterion | Score | Reason |
| --- | ---: | --- |
| Technological Implementation | 8.4 | An unusually substantial independent-verification foundation supports the educational interface. Finite replay is actual isolated RTL execution with pinned integrity and browser/reference agreement, not invented animation. Live coaching selects evidence on the server and uses the existing guarded Nemotron client; actual Token Factory request records substantiate integration. Repairs face unchanged independent checks. Deductions reflect mixed semantic coaching results, only targeted regression evidence for the latest prompt, and the uncompleted funded live judge route. |
| Design | 8.1 | Prediction, a learner-built sequence, explicit observed/expected values, explanation, transfer, export, and facilitator import form a coherent activity. Assistance is preserved and recorded coaching is plainly distinguished from a response to typed text. The two-boundary contrast gives the proposed video a clear demonstration. The split between hosted replay and locally configured coaching imposes friction at the sponsor-facing moment. This score assesses implemented interaction and script; it does not certify rendered accessibility or footage quality. |
| Potential Impact | 7.3 | Digital-design instructors and FPGA club mentors are a specific audience, with a reusable lesson and concrete learner output. A browser-only lab addresses setup friction, and the correct-control lesson teaches restraint about passing tests. The demonstrated benefit is access to a usable practice activity; instructor demand, reuse, learner improvement, and time savings remain hypotheses. A small target audience is acceptable, but impact beyond that audience has not been demonstrated. |
| Quality of the Idea | 8.4 | Teaching students to construct counterexamples and challenge an AI repair is a thoughtful application of model-assisted hardware tooling. Keeping the model advisory while simulation/formal artifacts decide results expresses real domain understanding. The correct-control exercise and attention to evidence scope are especially strong. The repair algorithm itself is established territory, and the adaptive coach's advantage over good authored hints remains unshown. |

**Total: 32.2/40; equally weighted mean: 8.05/10.**

## NVIDIA and Nebius fit

The integration is substantive. The local application makes runtime calls to Token Factory for Nemotron interpretation, explanation, repair, and coaching; the retained coaching records include endpoint, model, request identifiers, tokens, and latency. The rules accept runtime inference API use, so running deterministic verification on CPU and not using Serverless Jobs is not a shortcoming in eligibility. Coding and Agentic Engineering is credible because the project includes an actual propose–execute–check repair loop, even though the education journey is the public front door. This is an assessment of apparent fit, not an eligibility ruling. [Official project requirements](https://nebiusglobalaihackathon.devpost.com/rules).

The strongest sponsor story is not simply that Nemotron can generate a hint. It is that a student can inspect an actual failed model repair, see the counterexample, and understand why a later proposal earned acceptance under unchanged checks. The planned final workbench segment demonstrates that role. The submission appropriately avoids claiming that the hosted authored hints are model output, that Ultra is proven superior to Super, or that the exploratory reduced-feedback result establishes causality.

## Remaining concrete actions

1. **P1 — Complete free live judge access before submission.** `docs/submission/TESTING.md` explicitly marks project-funded access as pending. The current hosted replay is useful and free, but a judge wanting to exercise advertised live coaching or repair still needs local service configuration and a developer key. Supply and verify a funded route or test-build access path, document it, and maintain it through judging. This is a deployment/submission task, not a reason to replace the existing evidence library. The rules require free project access through the judging period; this review does not assume a public unlimited inference endpoint is necessary. [Official testing requirements](https://nebiusglobalaihackathon.devpost.com/rules).
2. **P2 — Make the coach explicitly address the remaining specification overclaim.** In `learning-coaching-check-2026-10-05-v3.json`, exchange/overclaim says any FIFO accepting a full exchange is universally incorrect. The response restates this contract and asks about occupancy, but does not plainly correct the universal statement. A useful response should distinguish this chosen policy from another valid FIFO policy, then ask the next question. The current system prompt already requests explicit challenge, so an additional prompt sentence alone is not evidence that the issue is resolved. Preserve this failing behavior and review its response directly.
3. **P2 — Close the latest-configuration validation gap before promoting coaching reliability.** The first two declared development checks each cover twelve authored cases but expose semantic errors. The latest check covers only four known weak cases after prompt changes. It supports the narrow statement that those four responses improved, not an all-lesson coaching success rate. Run the existing full matrix under a fixed final configuration when budget is authorized, preserve failures, and separately add a few fresh sequences/reflections before claiming broad adaptation. No paid calls were made for this review. Current materials disclose this limitation, so this is a reliability improvement rather than a correction to fabricated results.
4. **P3 — Tighten the opening sentence of the script.** “This authored exercise shows how a convincing hardware fix can still lose your data” suggests that the first candidate is a repair; it is an authored faulty fixture. Say “a plausible FIFO implementation” in that first shot and reserve the actual failed-fix claim for the later recorded Nemotron repair. The source and provenance labels are already honest; this makes the narration equally precise.

## Evidence that should not be overstated

The latest four coaching responses contain no obvious factual contradiction on inspection, but the cases and reviews are development artifacts produced with an assistant. They are neither independent tutoring evaluation nor learner results. Earlier failures are retained, including agreement with an incorrect cause, confusion about the contract's scope, and imprecise wrap/edge claims. Structural validation and legal edge references do not certify semantics.

The workbench evaluations are useful engineering evidence: eval-v2 reports 8/8 detected faults, 0/4 control false alarms, and 8/8 repaired cases under the frozen checks, with 3/4 conflicting briefs detected. Their assistant-authored cases, single-run design, correction history, and explanation weaknesses remain material limits. Those figures cannot support learning-gain, adoption, or classroom-readiness claims.

## External limitations and delivery dependencies

No learner study, independent educator assessment, or observed instructor reuse exists. These are external evidence gaps; more UI polish or assistant scoring cannot replace them. A small consenting pilot is the next meaningful impact test, without making it a prerequisite for recognizing the implemented lab.

The owner still needs to record and publish the video and insert its URL. The intended 2:45 story is coherent, demonstrates an ordinary passing test before a revealing boundary test, identifies recorded/live context, and ends with an actual rejected/accepted model repair. Recording availability and unseen editing quality have not been used to lower these scores. Final publication must preserve the labels and correction warning described by the script.

## Sources reviewed

- `README.md`; `docs/submission/DEVPOST.md`, `TESTING.md`, `DEMO_SCRIPT.md`; `docs/TEACHING.md`.
- `src/countertrace/learning.py`; learning API routing; `apps/web/src/lib/learning.ts`; `apps/web/src/views/LearnView.tsx`.
- All three `docs/evidence/learning-coaching-check-2026-10-05*.json` development records, with their protocols, outputs, source snapshots, and assistant-review qualifications.
- `evaluation/results/eval-v2/REPORT.md` and `evaluation/results/eval-v2-ablation/REPORT.md`.
- [Official hackathon rules](https://nebiusglobalaihackathon.devpost.com/rules), accessed October 5, 2026.

Only this review file was authored. No product behavior was changed; no live model or verifier execution was requested for the assessment.
