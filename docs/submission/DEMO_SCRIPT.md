# Countertrace check-writing demo script

Target length: 2:45. This is the intended script, not recorded footage. The owner records and publishes separately. Internal panels may score the story from this script; actual video quality remains unknown.

| Time | Screen and action | Spoken point |
| --- | --- | --- |
| 0:00–0:15 | Checks home and module catalog | “AI can write a convincing check that is wrong—or catches nothing. Countertrace asks Nemotron to write hardware checks, then checks the checks.” |
| 0:15–0:35 | FIFO specification and ports; open the actual recorded check-writing run | “The model gets the specification and ports, never the golden source. Everything shown here is recorded execution; the configured local build runs it live.” |
| 0:35–1:10 | Expand actual rounds, generated properties, gate results, and any feedback | “Trusted tools prove the properties on a golden implementation at multiple settings, reach their triggers, and test them against mutants. These are the actual failed and successful rounds.” Read the visible counts, including equivalents and unresolved cases; do not substitute a planned score. |
| 1:10–1:35 | Follow the recorded FIFO hunt; show promoted-property failure and golden replay | “A check failure alone is not enough. The same inputs pass the golden reference and expose a mismatch in the candidate. That is our confirmed defect.” Show this only if the recorded confirmation is confirmed. |
| 1:35–2:05 | Follow linked repair; show diff and complete unchanged obligations | “Nemotron proposes the fix. The properties, golden, and independent core checks cannot move. Each candidate gets a new verification run.” Show actual acceptance or rejection, preserving failed attempts. |
| 2:05–2:25 | Download evidence; show deterministic replay result; briefly open Labs | “The evidence is portable. Replaying it needs Docker, not inference. Instructors can also turn these failures into a debugging lesson.” |
| 2:25–2:45 | Return to Checks and scope | “Seven catalog modules, a FIFO end-to-end path, NVIDIA Nemotron through Nebius Token Factory. Development results are recorded; held-out property-generation evaluation is still pending.” |

Before recording, use the linked run IDs and outcomes in docs/STATUS.md. Show the actual status if generation or repair fails; do not edit waits or failures into a fictional success. Keep recorded labels and parameter scope visible. Mutation testing uses the first declared setting; the promotion target is at least 90% of analyzable non-equivalent mutants with no unresolved or invalid cases.

Vercel is recorded-only; the funded live judging route remains pending. No participant testimonial or classroom result is needed for this engineering demonstration.
