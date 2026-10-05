# Education round 4 — independent simulated hardware/trust review

Reviewed commit `794b8d556a5bacc14aa26c773319b6f4dc2207a9` on October 5, 2026. This is an assistant's simulated hackathon assessment, not sponsor judging or human technical validation. Earlier panel reports and scores were not consulted. The video is assessed from `docs/submission/DEMO_SCRIPT.md` as intended content; footage quality is not scored as observed.

| Equally weighted criterion | Score / 10 | Basis |
| --- | ---: | --- |
| Technological Implementation | 8.8 | Strong separation of model advice from verification authority. All available lesson paths have archived simulator evidence, browser/reference agreement and pinned integrity checks. The local workbench retains re-admission, isolated execution, property inventory checks and frozen repair comparisons. Real failed and accepted model candidates are preserved. Independent human review and a fresh Docker execution in this review remain absent. |
| Design | 8.5 | Prediction, learner-built experiment, expected/observed comparison, explanation and transfer form a coherent short lab. The reference queue is explicitly distinguished from sampled DUT state. Authored hints, recorded coaching, local live coaching and formal evidence have different labels. Facilitator keys and voluntary local imports make the result usable beyond an individual demonstration. This score reflects source and flow inspection, not fresh visual or screen-reader testing. |
| Potential Impact | 8.0 | Browser access without learner credentials, bounded experiments and portable practice records fit instructors and FPGA mentors. The product can teach causal debugging and limits of evidence with little learner setup. Usefulness, facilitator preparation cost, transfer and repeat adoption remain hypotheses; no observed learner or instructor outcomes justify a higher impact score yet. |
| Quality of Idea | 8.7 | A focused educational use of executable counterexamples, connected to genuine independently checked repair, is convincing. The learner must choose an experiment and explain its scope. Novelty lies in this useful combination and teaching workflow, not a new verification or repair algorithm. The deliberately small FIFO scope helps the idea stay inspectable. |

**Equal-weight mean: 8.50 / 10.**

## Evidence inspected and fresh checks

- Read AGENTS, PRD and roadmap; inspected teaching guidance, README, demo script, current learning flow, library builder, coaching boundary, independent formal monitor, verifier integrity handling and repair gate.
- `make check`: **100 tests passed**, workspace checks and diff check passed. The learning test verifies archived file hashes and every stored observation against the raw traces and Python reference.
- `npm --prefix apps/web test`: **3 tests passed**, including every browser path/reference comparison and fail-closed evidence handling. TypeScript and production build passed.
- `make test-integration`: **all 8 tests skipped** because the Docker daemon was unavailable. This is not a successful fresh RTL run. Archived executions and reported historical integration results remain distinct from this review's checks.
- The demo's `rec-20261004-010137-ver-dd43e0` record contains a first candidate rejected on `empty_flag` at cycle 4, then a second accepted with ten resolved unchanged obligations, including three proofs. Both comparisons record matching frozen checks. This supports the intended rejected/accepted repair story.
- The script's ordinary `wr` path and failing `wwwr` path match the tested library: the latter first diverges at edge 4, expected `0x11`, observed `0x33`. The script discloses recorded replay and does not turn the bounded learning library into a proof claim.

## Remaining actionable in-scope defects

**None reproduced in the reviewed hardware/trust path.** No P0–P2 finding or narrow product fix is supported by this review. Citation validity is appropriately described as weaker than semantic correctness; the existing advisory warnings and published imperfect model outcomes should remain visible. Broader HDL support, arbitrary uploads, a different FIFO policy or perfect model explanations are not requirements for this education release.

## Dependencies and limits, separate from defects

- Observe consenting learners and a facilitator when available; record attempts, assistance, exact transfer answers and willingness to reuse. These are external impact evidence dependencies, not a reason to expand the product or claim results now.
- Preserve free recorded judge access and verify funded/configured access for any live local demonstration promised during judging. Deployment and funding continuity were not tested here.
- Record the proposed 2:45 video with its replay/coaching labels and corrected-summary warning intact. The planned story is strong; actual recording and publishing remain owner tasks.
- A fresh Docker run and independent human review would strengthen confidence. The current review establishes source/artifact consistency and passing software checks, not new hardware proof or educational efficacy.
