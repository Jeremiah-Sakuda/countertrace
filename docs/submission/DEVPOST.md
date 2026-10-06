# Devpost submission Countertrace

Paste each section into the matching field. The YouTube URL remains owner-supplied; no video has been published by this workflow.

## Project name

Countertrace

## Elevator pitch (200 characters max)

A hardware debugging lab where learners challenge real Nemotron repairs: predict, inspect counterexamples, and defend the fix. Independent checks decide; instructors reuse the lesson.

## Track

Coding and Agentic Engineering

## Built with

NVIDIA Nemotron, Nebius Token Factory, Python, React, TypeScript, Verilator, Yosys, SymbiYosys, ABC, Yices, Docker, Vercel.

## Links

- Learning lab: https://countertrace.vercel.app
- Facilitator desk: https://countertrace.vercel.app/#/teach
- Code: https://github.com/Jeremiah-Sakuda/countertrace
- Video: [YouTube URL — owner to record and publish]

## Inspiration

A passing test can give a hardware learner confidence without revealing which boundary cases were missed. A plausible AI repair adds another claim to evaluate. We wanted a small lab where students construct a revealing sequence themselves, see actual circuit outputs, and explain what those observations establish.

Our initial audience is digital-design instructors and FPGA club mentors working with students who already understand clocks, reset, and basic RTL. The need and educational benefit remain hypotheses; no classroom study or adoption is claimed.

## What it does

1. **Inspect.** Read the fixed four-slot FIFO contract and an actual Nemotron RTL patch.
2. **Predict.** Commit an expected result and rationale before revealing the recorded checks.
3. **Challenge.** The first patch still produces a counterexample. Inspect the expected and observed empty flag at edge 4, then investigate the revised proposal. The final candidate passed the same frozen checks; simulation, bounded results, property proofs, and covers stay distinct.
4. **Explain and transfer.** State which evidence supports the decision, answer whether the result applies to eight slots, and download field notes. Free text is ungraded; practice is not measured learning gain.
5. **Teach.** Share the repair link and discussion plan. Three smaller authored practice exercises let learners build short sequences on overflow, simultaneous operations, and evidence limits. Instructors can review voluntarily shared notes and locally import practice-bench JSON.

The repair patches are actual NVIDIA Nemotron responses through Nebius Token Factory. The hosted experience reveals their recorded tool evidence; it performs no live RTL execution or inference. Live repair, interpretation, verification, explanation, coaching, and auditing remain available in the configured local workbench.

The three depth-2 practice candidates are authored exercises, not model outputs. Their library contains 4,096 executed six-edge paths per candidate and checked repeatable shorter prefixes. This is finite simulation with fixed 8-bit values, not an unbounded proof.

## How I built it

- **Learning interface:** React and TypeScript; committed predictions, action builder, actual expected/observed values, authored hints, saved practice, transfer questions, and local facilitator review. A release-pinned SHA-256 binds replay to the checked evidence bytes.
- **Evidence library:** the pinned, network-isolated Docker verifier ran all permitted sequences for three candidates. Independent Python scoring checked complete traces and prefix repeatability. Tests reparse every archived observation and compare all browser reference states with those results.
- **Verification workbench:** Verilator plus Yosys/SymbiYosys, ABC and Yices. A separate formal monitor and Python queue own the checks. Admission rejects unsupported or checker-tampering RTL; every model patch is re-admitted and compared under frozen inputs. Exported workbench bundles replay without a model call.
- **Coaching service:** Python routes through the existing token/spend limits and visitor quotas. The server chooses the evidence; client-supplied verification claims are ignored. Cited edges and structured output are validated, but semantic accuracy is not guaranteed.

## NVIDIA Nemotron and Nebius Token Factory

All live model calls use the Nebius Token Factory API from the control service. Hosted authored hints are not model output.

| Task | Model configuration | Role |
| --- | --- | --- |
| Learning coaching | Nemotron 3 Ultra | Responds to an explanation using recorded evidence, source, and authored facilitator focus; advisory only. |
| Brief interpretation | Nemotron 3 Super | Compares natural-language intent with the fixed contract and flags conflicts. |
| Failure explanation | Nemotron 3 Ultra | Explains recorded failing cycles with checked references. |
| Repair proposals | Nemotron 3 Ultra | Proposes constrained edits; independent unchanged checks accept or reject each candidate. |

The initial coaching development record preserves two unhelpful Super responses and a useful revised Ultra response. Both prompt and model changed, so this is not a tier comparison. Four further development checks contain 12, 12, 4 targeted, and 15 cases, with prompt/source changes between versions. The final 15-case check still contains a factual contradiction in an exchange response and insufficient challenge of an overflow overclaim. All outcomes are preserved; adaptation or tutoring efficacy is not established. Neither exercise is a learner study or proof of improvement over authored hints.

Model requests have required token caps, bounded retries, usage records, and estimated cost reservations. Provider billing controls remain separate. Verification runs on CPU in the isolated Docker worker; Nebius Serverless Jobs are not used.

## Results and limits

The education interaction and finite replay evidence work. Learning gains, instructor adoption, preparation-time savings, and demand remain unmeasured. Practice records are self-reported and are not authenticated assessments.

The underlying workbench has two separately frozen single-run engineering evaluations:

| Outcome | eval-v1 | eval-v2 |
| --- | --- | --- |
| Bugs detected | 8/8 | 8/8 |
| False alarms on four controls | 0/4 | 0/4 |
| Repairs passing unchanged checks | 7/8 | 8/8 |
| Conflicting briefs flagged | 4/4 | 3/4 |
| Compatible briefs accepted | 4/4 | 4/4 |

The first suite includes an independently authored MIT FIFO held out of prompt development. The second suite’s additional FIFO was written by the coding assistant shortly before freezing and held out of prompt development; it is not independent-author evidence. Cases and labels were prepared by the coding assistant. These are engineering outcomes, not educational outcomes. See the full evaluation reports and their limitations, including corrected derived summaries in some recorded evidence. Original model text and correction provenance remain visible.

## Challenges and lessons

A model can repeat a learner's mistaken cause even when its cited edge exists. We retained those unsuccessful coaching calls, added candidate source and facilitator guidance, and tested the revised configuration. Reference validity alone never certifies reasoning.

Recorded execution makes the classroom exercise immediate, but its scope must stay visible. We preserve raw RTL/stimulus/traces, check library integrity before replay, and distinguish a passing sequence from a universal proof. The correct-control lesson makes that distinction part of the activity.

## Next steps

Observe instructor and learner use, record exact answers and assistance, and improve confusing interactions. Complete project-funded access for advertised live model capabilities and preserve judge availability through December 15. The owner will record and publish the script-based demo. Public arbitrary uploads, additional module families, and LMS integration remain deferred.

## Testing instructions

Use [TESTING.md](TESTING.md). The hosted lesson needs no account or API key. Live local inference requires configuration; a judge should not be asked to purchase credits.

## Feedback

See [FEEDBACK.md](FEEDBACK.md) for sponsor-tool observations and reproducible issues.

## Created during the submission period

Countertrace is a new implementation started October 1, 2026. No historical AKILI code was reused. The independently authored evaluation FIFO retains its MIT attribution. Third-party tools and dependencies retain their licenses.
