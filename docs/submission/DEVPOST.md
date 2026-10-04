# Devpost submission: Countertrace

Paste each section into the matching Devpost field. Items in [brackets] still need a value before submitting.

## Project name

Countertrace

## Elevator pitch (200 characters max)

A coding agent for hardware learners: it finds the exact cycle a FIFO breaks, explains why with Nemotron, and only accepts a fix that passes checks the model cannot change.

## Track

Coding and Agentic Engineering

## Links

- Video: [YouTube URL]
- Hosted demo: [hosted URL, or "Test build: see testing instructions"]
- Code: https://github.com/Jeremiah-Sakuda/countertrace

## Built with

python, typescript, react, vite, docker, verilator, yosys, symbiyosys, abc, yices, nebius-token-factory, nvidia-nemotron, nemotron-3-ultra, nemotron-3-super, github-actions

---

## Inspiration

A FIFO is the first queue most hardware students write, and it usually passes their own tests. The bugs show up at the edges: a write when the queue is full, a read and a write in the same cycle, a reset in the middle of traffic. Their testbenches rarely drive those cases, and when a waveform finally shows a wrong value, it does not say which rule was broken or which earlier cycle caused it.

AI coding assistants add a second problem. Ask one to fix the RTL and it will rewrite the code and tell you it works. Nothing independent checks that claim. I wanted a tool where the model does the reading, explaining, and patching, but a fixed set of checks decides whether anything is actually fixed.

## What it does

Countertrace takes a small synchronous FIFO (8-bit words, depth 2 or 4) and walks it through five steps.

1. **Contract.** It shows the exact behavior the FIFO will be held to, cycle by cycle, including simultaneous reads and writes, full and empty boundaries, and reset. If you describe your intent in plain English, Nemotron 3 Super compares it with the contract and flags conflicts, such as "accept the write when full if a read frees a slot," instead of quietly changing the rules.
2. **Diagnosis.** The RTL runs in an isolated container with no network: Verilator simulation of 14 to 15 directed and seeded tests, plus SymbiYosys bounded model checking, an unbounded proof, and reachability checks. Two independently written references, a Python model and a formal monitor, judge the results. The first failure appears as a cycle table with the inputs, what the contract accepts, the expected queue, and what the design actually output, followed by a deterministic "probable origin" line. In the showcase: you wrote 0x21 at cycle 1, the design wrote 0x65 over it at cycle 5 while full, and the read at cycle 6 returned 0x65.
3. **Explanation.** Nemotron 3 Ultra explains the recorded failure for a student. Every cycle, signal, and line of RTL it cites is checked against the trace and the source, and bad citations are flagged in the interface. The explanation never changes the verdict.
4. **Repair agent.** Nemotron 3 Ultra proposes a patch as a short list of exact edits. Countertrace re-checks the patch for forbidden constructs, runs it as a new verification against the same frozen contract, harness, stimulus, and limits (all compared by hash), and accepts it only if every check passes, including the unbounded proofs. If a candidate fails, its own counterexample goes back to the model for the next attempt, up to three attempts. In one recorded case with two bugs, the first patch fixed one, failed the checks at cycle 4, and the second patch fixed both.
5. **Check-quality audit.** It seeds known bugs into a correct FIFO and scores a named set of learner-style checks against them. A deliberately weak set misses 3 of 6 real bugs, and each miss points to the requirement those checks never exercise.

Every run exports an evidence bundle with hashes, and `countertrace replay` reruns the deterministic checks with no model call. Results keep their method in the wording: "Simulation passed for these runs," "No counterexample within 23 cycles," "Property proved under these assumptions." There is no overall "verified" badge.

## How I built it

- **Control service:** Python, standard library only. It owns run state, the queue, model calls, and every command line.
- **Verifier:** a Docker image pinned by digest, with OSS CAD Suite 2026-09-30 pinned by SHA-256 (Verilator 5.053, Yosys 0.69, SymbiYosys, ABC, Yices). RTL runs with no network, a read-only root, dropped capabilities, and no credentials. The worker only records raw artifacts; the host parses them.
- **Trusted checks:** a hand-written SystemVerilog monitor with three assertions and twelve reachability covers, and a separate Python reference queue. Both follow one cycle convention, and formal counterexamples are replayed in simulation to confirm the two engines agree.
- **Admission gate:** a single ordered lexical pass rejects anything that could tamper with the checks: assertions or assumptions in the design, system tasks, delays, extra event controls, hidden ports, hierarchical references, and more. Every model patch goes through the same gate.
- **Interface:** React and TypeScript. It shows the cycle table, citations you can click to jump to a cycle, the repair timeline, a candidate diff with before-and-after checks, and the audit exercise.
- **Testing:** 73 unit tests and negative controls, 7 Docker integration tests, and a CI job that rebuilds the image on fresh runners and replays three recorded evidence bundles.

### How Nemotron and Token Factory are used

All model calls are runtime calls to the Nebius Token Factory OpenAI-compatible API.

| Task | Model | Notes |
| --- | --- | --- |
| Brief interpretation, check-set proposals | Nemotron 3 Super, reasoning off | 1.7 to 3.7 s per brief |
| Failure explanation | Nemotron 3 Ultra | about 6 s for the showcase, 18 checked citations |
| Repair proposals | Nemotron 3 Ultra | up to three attempts, counterexample fed back |

I routed the interactive calls to Super after measuring it: on the same briefs it matched Ultra's answers and ran in a few seconds, where Ultra with reasoning on took up to 72 seconds. When a reply runs out of output tokens, Countertrace retries with `chat_template_kwargs: {"enable_thinking": false}`, which turns off Nemotron 3 reasoning on Token Factory. Every response is schema-checked, token caps are required, and each call reserves its worst-case cost against a spending threshold before it runs.

### Results

I froze the model configuration and prompts first, committed a hash of the test cases, and then ran each evaluation once.

| | eval-v1 | eval-v2 |
| --- | --- | --- |
| Bugs found | 8 of 8 | 8 of 8 |
| False alarms on 4 correct designs | 0 | 0 |
| Repairs that passed the unchanged checks | 7 of 8 | 8 of 8 |
| Conflicting briefs flagged | 4 of 4 | 3 of 4 |
| Compatible briefs accepted | 4 of 4 | 4 of 4 |

eval-v1 included an MIT-licensed FIFO by another author that I never used while writing prompts. eval-v2 used fresh cases, including multi-line bugs and designs with two bugs. A follow-up comparison on eval-v2 found that Nemotron 3 Super repaired 8 of 8 as well and Nano repaired 6 of 8. Each evaluation cost under half a dollar at list prices.

These are single runs on cases and labels I wrote with my coding assistant; no outside reviewer or user study was involved.

## Challenges I ran into

- **Making simulation and formal checking agree on what a cycle means.** The solver checks outputs one step after each edge, while simulation samples after the edge settles. I wrote the convention down, built both references to it, and replay every formal counterexample in simulation to catch disagreements.
- **Keeping the model from moving the goalposts.** A patch could add its own assumptions, hide a port, or write into the files the checker reads. The admission gate, a property inventory parsed from the elaborated netlist, and hash-frozen check sets close those paths. A code review found a bypass using nested comment markers; I fixed it and added regression tests.
- **Reasoning tokens eating the JSON budget.** Nemotron 3 Ultra sometimes spent its whole output budget reasoning and never produced the answer. Switching repairs to short exact edits, and retrying with reasoning off, made every such failure recoverable in the second evaluation.
- **Admitting someone else's FIFO without editing it.** The independent design used an active-low reset and different port names. I added a validated port mapping that generates a fixed wrapper instead of touching the design.

## Accomplishments that I'm proud of

- Unbounded proofs, in addition to tests, for every correct design in both evaluations, and every repair accepted only after those proofs pass on the same frozen checks.
- A repair loop that uses its own failures: the recorded two-bug case shows a rejected candidate, the counterexample it produced, and the accepted fix that followed.
- Evidence anyone can rerun: hashed bundles that replay on a clean machine with no API key.
- An interface that leads with the failing cycle and the expected and observed values, so a student can see the bug before reading any formal terminology.

## What I learned

- Smaller Nemotron tiers were good enough for more of this work than I expected. Super matched Ultra on interpretation, in a fraction of the time, and also repaired all eight eval-v2 cases, using fewer output tokens than Ultra (its repair requests were not faster).
- The deterministic evidence matters as much as the model output. The "probable origin" line comes from the trace, not the model, and it is often the most useful sentence on the page.
- Citation checks catch references to cycles and signals that do not exist, but they cannot tell whether the reasoning is right. Two eval-v2 explanations had a partly wrong or incomplete root cause, so the interface treats explanations as help, not as proof.

## What's next for Countertrace

- A hosted classroom version where students paste their own FIFO, with a port mapping for their naming.
- Selectable contract policies, such as first-word fall-through and exchange-when-full, so more correct student designs are supported instead of flagged.
- A second module family after the FIFO, such as a simple UART or arbiter, reusing the same frozen-check repair loop.
- Using Nebius Serverless Jobs for batch audits and evaluations.

## Testing instructions

[Use the text in TESTING.md.]

## Feedback on Nebius Token Factory, Nebius AI Cloud, and NVIDIA tools

[Use the text in FEEDBACK.md.]

## Was this project created during the submission period?

Yes. Countertrace is a new implementation started on October 1, 2026, within the submission period. No earlier code was reused. One third-party file is included for evaluation: an unmodified MIT-licensed FIFO by William Mar, attributed in the repository.
