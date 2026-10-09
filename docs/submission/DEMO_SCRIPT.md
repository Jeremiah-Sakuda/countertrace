# Countertrace check-writing demo script

Target length: 2:45. This is the intended script, not recorded footage. The owner records and publishes separately. Internal panels may score the story from this script; actual video quality remains unknown.

| Time | Screen and action | Spoken point |
| --- | --- | --- |
| 0:00–0:15 | Checks home; open the new recorded FIFO revision | “AI can write a convincing check that is wrong—or catches nothing. Countertrace asks Nemotron to write hardware checks, then checks the checks.” |
| 0:15–0:35 | Corrected FIFO specification and ports | “The model gets the specification and ports, never the golden source. This is recorded execution; the configured local build runs it live.” |
| 0:35–1:05 | Expand the first FIFO property, exact counterexample feedback, and fourth-round correction | “The gate rejected three proposals, including a repeated timing error. The fourth corrected the check and passed. The same properties also caught the non-equivalent mutants at the second depth.” Keep the rejected round visible. This is an observed revision, not a controlled estimate of feedback benefit. |
| 1:05–1:20 | Home evaluation table, with link to all attempts | “We froze the implementation before three runs each on four held-out modules. Twelve attempts promoted. Eight worked from the first raw response; two needed format retries and two needed property revisions.” Show the small-suite and assistant-authored-golden limits. |
| 1:20–2:05 | Continue with this same FIFO check set into its golden-confirmed bug hunt and repair | “Now put these checks to work. They expose a seeded overflow bug. The same inputs pass the golden and fail the candidate. Nemotron proposes a patch, then faces the same frozen properties and independent core checks.” Read the actual repair verdict and obligation count; keep the check-set identity visible. |
| 2:05–2:30 | Download the four-round evidence bundle; show deterministic replay; briefly open Labs | “The rejected and accepted rounds replay without another model call. Instructors can also use the repairs and traces as debugging lessons.” |
| 2:30–2:45 | Return to scope and sponsor roles | “NVIDIA Nemotron through Nebius Token Factory writes and revises checks. Independent tools decide. This small catalog result depends on the golden references; it is not production sign-off or a general reliability score.” |

Use the linked run IDs and exact outcomes in docs/STATUS.md. The primary FIFO check run is `rec-20261009-154341-che-06ba10`, with three rejected rounds and promotion in the fourth. Its linked hunt and repair are `rec-20261009-154734-ver-dfae43` and `rec-20261009-154833-ver-5bb770`. The separate debouncer recording `rec-20261009-153159-che-312266` also preserves a rejection and second-round correction. All twelve attempts, including the UART revision and both schema retries, are in evaluation/results/checks-v1. Do not edit waits or failures into a fictional success. Keep recorded labels and parameter scope visible. Mutation testing in the frozen evaluation uses the primary setting; golden proof and trigger reachability use both settings. The separate FIFO depth-transfer audit must be described as such.

Vercel is recorded-only; the funded live judging route remains pending. No participant testimonial or classroom result is needed for this engineering demonstration.
