# Frozen check-generation evaluation

Completed October 9, 2026: **12/12 attempts promoted** across four held-out catalog modules, three repeats per module. **10/12 passed in their first gate round**; all rounds, including failed proposals, are retained. Two of those first-round successes required the shipped schema-retry mechanism; eight attempts succeeded from the first raw model response. This is a small catalog evaluation, not a general model reliability estimate.

## Protocol and provenance

The public [commitment](../../checks-v1-commitment.json) preceded every attempt. The now-released [original protocol](protocol.json) matches its SHA-256 exactly. Execution used commit `db13724c788535125b0cd1c0e293abd4998bad99`. No prompts, source, module definitions, budgets or gate logic changed during the twelve attempts. Model: NVIDIA Nemotron 3 Ultra through Nebius Token Factory, reasoning enabled, 16,384 input and check-output token caps, four rounds maximum.

The four module specifications and golden implementations were assistant-authored, reserved from model/prompt development, and previously exercised with hand-written reference properties. They are not independently authored or externally reviewed. Three repeats test generation variation; they do not create twelve independent designs. Golden proof and trigger reachability cover both declared settings. The mutation challenge uses the primary setting, 40 requested mutants and seed 1, with at least 90% killed and no invalid/unresolved evidence for promotion.

| Module | Promoted | Rounds by repeat | Killed / non-equivalent by repeat | Equivalent by repeat |
| --- | --- | --- | --- | --- |
| Debouncer | 3/3 | 2, 1, 1 | 27/27, 27/27, 27/27 | 13, 13, 13 |
| Saturating up/down counter | 3/3 | 1, 1, 1 | 35/35, 35/35, 35/35 | 3, 3, 3 |
| Pattern detector | 3/3 | 1, 1, 1 | 23/23, 23/23, 23/23 | 17, 17, 17 |
| UART transmitter (8N1) | 3/3 | 1, 1, 2 | 26/26, 26/26, 26/26 | 14, 14, 14 |

## All attempts

| Module | Repeat | Outcome | Run | Rounds |
| --- | --- | --- | --- | --- |
| debouncer | 1 | promoted | `20261009-153159-che-312266` | 2 |
| sat_counter | 1 | promoted | `20261009-153248-che-0ab3c2` | 1 |
| seq_detector | 1 | promoted | `20261009-153321-che-fc43eb` | 1 |
| uart_tx | 1 | promoted | `20261009-153358-che-8306f2` | 1 |
| debouncer | 2 | promoted | `20261009-153447-che-97b7a9` | 1 |
| sat_counter | 2 | promoted | `20261009-153519-che-ff1856` | 1 |
| seq_detector | 2 | promoted | `20261009-153547-che-2b438d` | 1 |
| uart_tx | 2 | promoted | `20261009-153619-che-5886a8` | 1 |
| debouncer | 3 | promoted | `20261009-153708-che-a5c55a` | 1 |
| sat_counter | 3 | promoted | `20261009-153740-che-f45986` | 1 |
| seq_detector | 3 | promoted | `20261009-153927-che-f60716` | 1 |
| uart_tx | 3 | promoted | `20261009-154029-che-771474` | 2 |

## A real rejected proposal and revision

The first debouncer attempt failed `outputs_match` on the golden at STABLE=3. The gate returned a pre-edge counterexample. The second model proposal changed the shadow counter to reset when the stable threshold is reached; it then passed golden proof, reachability and the mutation challenge. Both proposals, the exact feedback and model-call metadata are in the [raw results](results.json), and this complete run is the representative published recording. This demonstrates an observed revision after feedback, not a causal benefit over a no-feedback baseline.

The third UART attempt also needed two gate rounds: its first set failed `busy_correct` and `tx_correct`, then its revision promoted. Counter attempts 1 and 3 used one schema retry each (invalid helper width and a helper name colliding with an output port). Thus the evaluation contains 14 gate rounds and 16 model calls, rather than twelve error-free generations.

## Usage, timing and limits

16 recorded model calls used 12,583 prompt tokens and 147,353 completion tokens. Estimated inference cost: $0.4546 using the configured $1/$3 per million input/output token rates; account billing is unverified. Local wall time per complete attempt: median 43.0s, range 28.0–107.0s. These are local Docker observations with overlapping UI work and a secondary FIFO audit, not hosted latency promises.

See [machine-readable summary](summary.json) and [all proposals and outcomes](results.json). The raw verifier artifacts remain in the local run store; the representative recorded run includes a portable deterministic evidence bundle. No result establishes all-parameter correctness, arbitrary-design coverage, real-user impact or production hardware sign-off. The subsequent FIFO specification correction is separate development work and does not change this frozen evaluation.
