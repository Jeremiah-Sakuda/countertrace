# Devpost submission: Countertrace

Paste each section into the matching Devpost field. Replace the video placeholder once the video is published.

## Project name

Countertrace

## Elevator pitch (200 characters max)

A hardware debugging lab where learners challenge real Nemotron repairs: predict, inspect counterexamples, and defend the fix. Independent checks decide, and instructors get a ready-made lesson.

## Track

Coding and Agentic Engineering

## Built with

NVIDIA Nemotron, Nebius Token Factory, Python, React, TypeScript, Verilator, Yosys, SymbiYosys, ABC, Yices, Docker, Vercel.

## Links

- Learning lab: https://countertrace.vercel.app
- Facilitator desk: https://countertrace.vercel.app/#/teach
- Code: https://github.com/Jeremiah-Sakuda/countertrace
- Video: [YouTube URL]

## Inspiration

Hardware students learn to trust a passing testbench too early. A FIFO passes their tests, then fails on the cases they never drove: a write when the queue is full, a read and a write in the same cycle, a reset in the middle of traffic. AI coding assistants make this worse in a new way. Ask one to fix the RTL and it returns a plausible patch and says it works.

Digital-design instructors and FPGA club mentors already teach "a passing test is not a proof," but they rarely have a ready exercise that shows it on a real circuit with a real AI fix. I built Countertrace to be that exercise: the model proposes, the learner investigates, and checks the model cannot change decide.

## What it does

1. **Pick a case.** The repair lab is a casebook of four real Nemotron 3 Ultra repairs of seeded FIFO bugs from the evaluation: a patch that misses a second bug, a patch that fixes the reported bug but breaks code that was working, three rounds on one flag, and a one-line fix that was right the first time.
2. **Predict, then probe.** For each proposed patch, commit an expected result and a reason. Then build your own input sequence and replay what that candidate actually did on it. Every sequence of up to six actions was run on every candidate in the isolated verifier.
3. **Challenge.** Reveal the recorded checks. A rejected patch shows its counterexample with expected and observed values; an accepted one passes the same frozen checks, with simulation, bounded checking, unbounded proofs, and reachability reported separately.
4. **Explain and transfer.** Say which evidence supports the decision, answer whether the result still holds for an eight-slot queue, and download field notes.
5. **Test your own testbench.** In the testbench lab, choose which test sequences a testbench runs and which signals it checks, predict how many of six seeded bugs it catches, and see each miss explained as a situation the tests never produced or a signal they never checked. A typical first testbench catches 3 of 6; one well-chosen directed test catches all six. Results come from the raw traces of a recorded audit.
6. **Teach.** Instructors share any case with a discussion plan. Three practice labs, built on hand-written FIFO designs, let learners construct input sequences for overflow, simultaneous operations, and the limits of a passing test. The facilitator desk gives instructors a session plan and answer keys, and imports the practice records learners choose to share; repair-lab notes download as Markdown for discussion.

Behind the lab is a full verification workbench. It runs any bundled FIFO in an isolated container, shows the first failing cycle with expected and observed values, asks Nemotron to explain the failure with checked citations, and runs the repair agent: Nemotron proposes an edit, Countertrace verifies it against the unchanged checks, and a failed candidate's own counterexample goes back to the model for the next attempt.

## How I built it

- **Learning interface:** React and TypeScript, with committed predictions, an action builder, expected and observed values, hints, transfer questions, and a local facilitator review. The practice library replays 4,096 executed six-edge input sequences per design, and the repair probe library does the same for each of the eight Nemotron candidates at depth 4. Both are pinned by SHA-256 (finite simulation, not a proof).
- **Verifier:** Verilator, Yosys, SymbiYosys, ABC, and Yices in a Docker image built from a digest-pinned base, run with no network. A hand-written formal monitor and a separate Python reference queue own every check.
- **Admission and integrity:** RTL that could tamper with the checks is rejected before it runs, and the elaborated netlist is checked for the expected ports, free inputs, and exactly the monitor's properties. Every model patch goes through the same gate.
- **Repair judging:** a candidate counts only if a separate run with hash-identical contract, harness, stimulus, limits, and formal tasks passes every obligation. Exported evidence bundles replay without a model call.

## NVIDIA Nemotron and Nebius Token Factory

Every live model call goes to the Nebius Token Factory API from the control service.

| Task | Model | Role |
| --- | --- | --- |
| Repair proposals | Nemotron 3 Ultra | Proposes exact-match RTL edits; unchanged checks accept or reject each one, up to three attempts with counterexample feedback. |
| Failure explanation | Nemotron 3 Ultra | Explains the failing cycles; every cited cycle, signal, and line is checked against the trace. |
| Learning coaching | Nemotron 3 Ultra | Responds to a learner's explanation using the recorded evidence; advisory only. |
| Brief interpretation | Nemotron 3 Super, reasoning off | Compares a plain-English design brief with the fixed contract and flags conflicts in 1.7 to 3.7 s. |

When a reply runs out of output tokens, Countertrace retries with `enable_thinking: false`. Every call has required token caps, a schema check, a usage record, and a cost reservation against a spending limit. In a repair comparison on eight cases, Nemotron 3 Super repaired 8 of 8 and Nano 6 of 8.

## Results

I froze the model configuration and prompts, recorded a hash of the test cases, and ran each evaluation once.

| | eval-v1 | eval-v2 |
| --- | --- | --- |
| Bugs found | 8 of 8 | 8 of 8 |
| False alarms on 4 correct designs | 0 | 0 |
| Repairs that passed the unchanged checks | 7 of 8 | 8 of 8 |
| Conflicting briefs flagged | 4 of 4 | 3 of 4 |
| Compatible briefs accepted | 4 of 4 | 4 of 4 |

eval-v1 includes an MIT-licensed FIFO by another author. eval-v2 adds multi-line and two-bug cases; in eval-v2, 6 of 8 explanations cited only valid cycles, signals, and lines. Some derived simulation summaries in the recorded evidence were corrected from the preserved traces; the original model text and the correction record remain visible. Full reports: https://github.com/Jeremiah-Sakuda/countertrace/tree/main/evaluation/results

**Limits.** One synchronous FIFO profile (8-bit, depth 2 and 4). The hosted lab replays recorded evidence; live verification and Nemotron calls run in the local build. Evaluation cases were prepared with my coding assistant, and these numbers measure the tool's diagnosis and repair, not learning; learning outcomes have not been measured yet.

## Challenges and lessons

- **Making simulation and formal checking agree on what a cycle means.** I wrote down one sampling convention, built both references to it, and replay every formal counterexample in simulation.
- **Keeping the model from moving the goalposts.** A patch could add assumptions, hide ports, or drive its own inputs. Admission, netlist checks, and hash-frozen check sets close those paths.
- **Reasoning tokens eating the answer.** Nemotron 3 Ultra sometimes spent its whole budget reasoning. Short exact-edit patches and a reasoning-off retry recovered every such case in eval-v2.
- **Coaching that sounds right but is not.** A model can repeat a learner's mistaken cause while citing a real edge, so citation checks are not enough. Coaching stays advisory and never changes a result.

## What's next

Classroom sessions with instructors, project-funded live model access on the hosted site, more repair cases, and a second module family such as a UART or an arbiter.

## Testing instructions

See https://github.com/Jeremiah-Sakuda/countertrace/blob/main/docs/submission/TESTING.md. The hosted lab needs no account or API key.

## Feedback

See https://github.com/Jeremiah-Sakuda/countertrace/blob/main/docs/submission/FEEDBACK.md.

## Created during the submission period

Countertrace is a new implementation started October 1, 2026. No earlier code was reused. The independently authored evaluation FIFO keeps its MIT attribution, and third-party tools keep their licenses.
