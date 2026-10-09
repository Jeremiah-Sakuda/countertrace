# Devpost submission: Countertrace

## Project name

Countertrace

## Elevator pitch (200 characters max)

Nemotron writes hardware checks. Countertrace checks the checks against a golden design and mutants, then freezes them for bug hunting and repair. Every verdict comes with inspectable evidence.

## Track

Coding and Agentic Engineering

## Built with

NVIDIA Nemotron, Nebius Token Factory, Python, React, TypeScript, Verilator, Yosys, SymbiYosys, ABC, Yices, Docker, Vercel.

## Links

- Recorded application: https://countertrace.vercel.app
- Code: https://github.com/Jeremiah-Sakuda/countertrace
- Video: [YouTube URL — owner records and publishes]

## Inspiration

An AI-generated hardware test can look convincing while checking the wrong behavior, never reaching its trigger, or missing the bug. Before an agent uses generated checks to approve its own repair, someone needs to check the checks.

Countertrace makes that boundary visible. A trusted golden reference supplies a way to challenge a model's properties, and deliberately altered designs reveal what they miss. Developers can inspect the exact feedback and evidence; instructors can use the same failures as debugging exercises.

## What it does

Choose a small synchronous module and read its specification and ports. Nemotron writes structured formal properties without seeing the golden source. Trusted code compiles the properties and runs a gate: prove them on the golden at multiple parameter settings, reach every trigger within a bounded horizon, and test them against generated mutants classified by formal equivalence. Failed properties and surviving-mutant traces go back to the model for up to four rounds.

The interface retains every round, exact properties, feedback, model usage, and mutation denominators. At least 90% of analyzable non-equivalent mutants must be killed, with no unresolved or invalid evidence. Mutation testing currently uses the first parameter setting. A missing result or contradictory verdict prevents promotion.

For the supported FIFO, promoted properties then check a bundled candidate. A reported failure must replay on both the golden and candidate against an independent reference queue before it counts as a confirmed defect. Nemotron can propose repairs, but the properties and existing core checks remain frozen. Evidence bundles replay deterministic verification without calling the model.

The teaching labs remain available: learners predict outcomes of real recorded repairs, build input sequences, and inspect what weak testbenches miss. Instructors and FPGA mentors get activities and learner-owned notes.

## How I built it

React and TypeScript provide the catalog and evidence inspector. A Python control service calls NVIDIA Nemotron through Nebius Token Factory. The model emits structured data, never executable tool directives or assumptions. A trusted compiler owns the environment and exact property inventory.

Verilator, Yosys, SymbiYosys, ABC, and Yices run inside a pinned Docker verifier with no network, no model credentials, and a read-only root. The control service validates worker completion, per-process return codes, artifacts, and hashes. A repair is a separately admitted and verified child run; it cannot change the contract or promoted checks to manufacture success.

## NVIDIA Nemotron and Nebius

Nemotron 3 Ultra writes properties, receives bounded gate feedback, explains counterexamples, and proposes exact-match RTL repairs. Nemotron 3 Super handles brief interpretation. Every live inference request goes through Nebius Token Factory, with required token caps, schema checks, usage records, bounded retries, and a spending reservation. CPU verification currently runs in local Docker, not Nebius Serverless Jobs.

## Evidence and limits

Seven module definitions have golden references and hand-written gate regression properties. Those reference-property results test the verifier; they are not seven model successes. Actual check-writing runs on development modules retain failures and successful rounds. The frozen held-out model evaluation remains pending; no general model success rate is claimed. The full downstream adapter currently supports the synchronous FIFO, 8-bit words, depths 2 and 4.

The earlier frozen FIFO evaluations measured diagnosis and repair under hand-written checks: eval-v1 found 8/8 seeded faults with 0/4 control false alarms and repaired 7/8; eval-v2 found 8/8 with 0/4 false alarms and repaired 8/8. These do not measure the new property generator. Cases were prepared with a coding assistant; eval-v1 includes an independently authored MIT-licensed FIFO. Reports preserve all outcomes and limitations in evaluation/results.

The hosted Vercel application is recorded playback. Live generation and verification run in the configured local build. Project-funded live judge access through December 15 and the owner's final video remain pending. No learner gains, classroom adoption, industrial sign-off, or first-of-kind research claim is made.

## Challenges and lessons

The hardest boundary is evidence integrity. Missing equivalence results must block promotion rather than shrink the denominator. A bounded failure to reach a trigger is not proof that it is impossible. Formal pre-edge samples must be aligned with simulation before a counterexample can support a design-defect claim. Finally, a model's checks and its patch must be evaluated by something it cannot change.

## What's next

Freeze and run the held-out property-generation evaluation with three attempts per module; extend downstream replay beyond the FIFO only with negative controls; provide project-funded live judge access; and observe instructor use without treating simulated reviews as adoption evidence.

## Testing and feedback

See docs/submission/TESTING.md and docs/submission/FEEDBACK.md in the public repository. Recorded playback requires no login or paid key.

## Created during the submission period

Countertrace is a new implementation started October 1, 2026. No historical AKILI code was reused. Third-party fixtures and tools retain their attribution and licenses.
