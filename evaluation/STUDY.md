# Reviewer and learner pilot

Status: recruitment and sessions have **not** happened. The owner has not supplied contacts or a community/channel. The drafts below are ready to personalize and send once recipients are identified. No outreach is implied by this document.

## Recruitment drafts

Technical reviewer (one experienced RTL/formal-verification practitioner):

> I'm building Countertrace for the Nebius x NVIDIA hackathon: a small synchronous-FIFO debugging workbench with independent simulation/formal checks and model explanations. Could you spend 45–60 minutes reviewing its reset/boundary contract, trace sampling, proof assumptions, and mutation labels? I also need help admitting an independently authored FIFO without using it for prompt development. I'd like initial feedback by October 8. I'll credit you only with your permission, and record unresolved concerns rather than treating review as certification.

Learners (at least three advanced digital-design students or junior FPGA developers who know clocks, reset, and basic RTL):

> Could you try a FIFO debugging tool in a 30-minute session? You'll inspect a real failing trace, explain what happened, and export its evidence. We're testing whether the interface and explanations help, not testing you. No proprietary code or paid account is needed. I'd like one early session by October 8 and the final pilot during October 21–25. Participation is voluntary; you can stop at any point. I'd take anonymous notes, with recording only if you agree separately.

Recruit three distinct learners; seek five only if time permits. Do not count the builder or reviewer as a learner unless they independently meet the audience criteria, and disclose overlapping roles. A returning early participant has prior exposure; report that separately or recruit a replacement for the final comparison. No incentives or endorsements have been promised.

Store contact details, availability, consent, and notes in ignored `evaluation/study-private/`. Use participant IDs L1–L3 in reports. Publish aggregates and authorized anonymized excerpts only. Keep contact information and recordings out of Git.

## Technical review checklist

Give the reviewer the frozen contract, reference monitors, normalized trace, tool versions, assumptions, and result-label rules. Ask for concrete errors or ambiguity in reset priority, simultaneous operations at full/empty, pre-edge acceptance versus post-edge observation, unbounded proofs and cover reachability, and mutant ground truth. Keep issues and their disposition. Review the [independent candidate](INDEPENDENT_FIXTURE.md) separately from prompt development; record incompatible candidates as such.

## Session preparation

Complete the authenticated [model gate](../docs/MODEL_GATE.md) before comparing explanations. Freeze two matched fault examples (A and B), their traces/checks, explanation versions, and rubric before sessions. For each example, the condition with explanation adds only the model explanation to the same deterministic evidence; keep the audit presentation fixed. Neither case should be the held-out engineering implementation used to tune the system afterward.

Use a predeclared small-sample order: L1 sees A without explanation then B with; L2 sees A with then B without; L3 sees B without then A with. This partially balances case and order; three people cannot fully counterbalance or establish a causal population effect. Do not show a participant the same case twice. Preserve all observations, including failures and assistance. Choose a third matched example for the audit transfer question and do not reveal its missing requirement before scoring.

## Thirty-minute session

| Minutes | Activity |
| --- | --- |
| 0–3 | Explain the purpose, voluntary participation, anonymous notes, and separate recording choice. Record prior RTL/formal experience and previous exposure to Countertrace. |
| 3–12 | First assigned example: inspect contract/finding, explain the failure aloud, state result limits, export evidence. Start the task timer after instructions. |
| 12–21 | Second assigned example in the other explanation condition. Ask the same neutral questions. |
| 21–27 | Show the weak supplemental-check audit, ask which requirement is missing, then ask the participant to recognize that omission in the different transfer example. |
| 27–30 | Ask what was confusing, what next action they would take, and whether/how they would use this tool. Collect qualitative feedback without leading toward adoption. |

Neutral questions: "Which requirement failed?", "Which transaction first shows it?", "What did you expect and what happened?", "What can you conclude from this passing result?" Let the participant work before helping. Record the timestamp, exact assistance, and resulting completion; stop a stuck task at its allocated time and preserve it as incomplete.

## Scoring sheet (copy per participant and case)

| Field | Value to record |
| --- | --- |
| Participant, case, condition, order, tool/model version | Blank until observed |
| Contract/finding/explanation inspected; bundle exported | Completed / incomplete, with assistance |
| Task elapsed time | Seconds; include time spent stuck |
| Violated requirement | 0 incorrect / 1 partial / 2 correct |
| First failing transaction | 0 / 1 / 2, against the predeclared answer |
| Expected versus observed behavior | 0 / 1 / 2 |
| Limits of a pass | 0 / 1 / 2; must distinguish simulation, bounded checking, and proof scope |
| Missing requirement after audit | Incorrect / partial / correct; record assistance |
| Same omission in transfer example | Incorrect / partial / correct; record assistance |
| Misunderstandings and quotations | Anonymous notes; quote publicly only with permission |

The PRD pilot targets at least 2 of 3 completing the principal journey and correctly distinguishing simulation from proof, and at least 2 of 3 identifying and transferring the audit omission. Report every participant and all four comprehension scores; a total score must not conceal an incorrect conclusion about proof. Report counts and individual observations, not significance, general demand, or population-level productivity gains. No scores are populated yet.
