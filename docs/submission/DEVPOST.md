# Devpost submission Countertrace

Paste each section into the matching field. The YouTube URL remains owner-supplied; no video has been published by this workflow.

## Project name

Countertrace

## Elevator pitch (200 characters max)

An interactive hardware debugging lab: predict, build a counterexample, and justify a fix. Nemotron coaches your reasoning; independent verification checks the evidence.

## Track

Coding and Agentic Engineering

## Links

- Learning lab: https://countertrace.vercel.app
- Facilitator desk: https://countertrace.vercel.app/#/teach
- Code: https://github.com/Jeremiah-Sakuda/countertrace
- Video: [YouTube URL — owner to record and publish]

## Inspiration

A passing test can give a hardware learner confidence without revealing which boundary cases were missed. A plausible AI repair adds another claim to evaluate. We wanted a small lab where students construct a revealing sequence themselves, see actual circuit outputs, and explain what those observations establish.

Our initial audience is digital-design instructors and FPGA club mentors working with students who already understand clocks, reset, and basic RTL. The need and educational benefit remain hypotheses; no classroom study or adoption is claimed.

## What it does

1. **Predict.** Read a fixed two-slot FIFO contract and commit an answer before seeing the result.
2. **Investigate.** Build up to six edges using write, read, simultaneous read/write, and reset. Compare actual recorded RTL outputs with an independently computed reference queue. An ordinary write/read sequence passes; an overflow sequence returns 0x33 where 0x11 was expected.
3. **Explain.** Write the governing rule and evidence in your own words. Authored hints work on the hosted site. In the configured local build, Nemotron responds to the learner explanation using server-selected observations, candidate RTL, and an authored facilitator focus. AI feedback is advisory; free text is ungraded.
4. **Transfer.** Answer a related boundary or evidence-scope question. Preserve the initial answer, experiment predictions, assistance, and first transfer answer in a downloadable practice record. Completion is not mastery or a measured learning gain.
5. **Teach.** A facilitator shares lesson links, opens answer keys, and reviews voluntarily shared anonymous session JSON locally in the browser. Nothing is uploaded during import.

Three lessons cover overflow, simultaneous operations, and evidence limits with a correct control. Every permitted action sequence was actually run in the isolated verifier: 4,096 six-edge paths per candidate, plus all shorter prefixes. This is finite simulation with fixed data values, depth 2 and width 8. Hosted playback is clearly labeled; it performs no live RTL execution or model call. Learner candidates are authored exercises, not claimed AI outputs.

After the lab, learners can inspect a separate recorded Nemotron repair that initially failed and later passed the same frozen checks. The underlying workbench supports diagnosis, explanation, up to three repair candidates, supplemental-check auditing, and hashed evidence export. The model cannot alter the contract, checker, or acceptance decision. Simulation, bounded checks, property proofs, unresolved results, and errors remain distinct.

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

The initial coaching development record preserves two unhelpful Super responses and a useful revised Ultra response. Both prompt and model changed, so this is not a tier comparison. A separate declared development check uses the fixed coaching configuration across all three lessons; its results and assistant review are in the repository. Neither exercise is a learner study or proof of improvement over authored hints.

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

The first suite includes an independently authored MIT FIFO held out of prompt development; cases and labels were prepared by the coding assistant. These are engineering outcomes, not educational outcomes. See the full evaluation reports and their limitations, including corrected derived summaries in some recorded evidence. Original model text and correction provenance remain visible.

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
