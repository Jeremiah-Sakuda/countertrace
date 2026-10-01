# Architecture boundaries

This describes the intended system. Only the local package and environment diagnostic exist at repository initialization.

| Component | Responsibility | Boundary |
| --- | --- | --- |
| TypeScript interface in `apps/web` | Contract review, findings, repair/export | Presents recorded evidence and honest run states |
| Python control service in `src/countertrace` | Run state, inference, immutable inputs, queue, artifact ownership | Holds model credentials and owns allowed commands |
| Nemotron on Token Factory | Intent interpretation, grounded explanation, optional source patch | Cannot accept repairs or alter the trusted verifier |
| Isolated CPU worker in `verifier` | Simulation, formal tasks, replay, authoritative result artifacts | No model secrets; no child network access; bounded resources |
| Independent monitors | Reference occupancy, flags, transaction accounting, data order | Authored separately from DUT repair; frozen for comparison |
| Artifact storage | Inputs, versions, commands, traces, logs, diffs, result manifest | Private inputs stay private; deterministic replay requires no new model call |

Use a single bounded control loop. Avoid multiple orchestration frameworks. Start with a pinned local Linux worker; measure Nebius Serverless Jobs access and latency before choosing the deployment runner. Runtime Token Factory calls remain required for the planned sponsor integration route.

## First slice

1. Accept a bundled FIFO and an explicit versioned contract.
2. Run admission and independent verification.
3. Preserve a failure artifact and normalize the cycle table.
4. Ask Nemotron to explain the recorded failure using signal/cycle references.
5. Display the finding and unresolved obligations, then export replay inputs.

Repair follows this slice. Re-admit each candidate, preserve every attempt, and rerun the unchanged checks. A change to the contract, assumptions, parameters, or checkers starts a new baseline.

## Result integrity

Simulation passed, no counterexample within a horizon, and unbounded property proof are different claims. Unknown, timeout, unsupported, cancelled, tool error, and missing evidence must remain explicit. A model answer, zero exit code, cloud-job completion, or absence of assertions is not a hardware proof.

The supplemental-check audit is a separate educational surface. Its mutation score never becomes overall design confidence, and it does not replace the core monitor. User testbench ingestion is outside the MVP.
