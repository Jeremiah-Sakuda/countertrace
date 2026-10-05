# Education release simulated judging

The owner requested an end-to-end education release followed by repeated fresh judging panels and fixes. These are assistant simulations, not sponsor scores, human validation, or award probabilities.

## Protocol fixed before round 1

Three independently prompted reviewers cover learning/product, hardware/trust, and NVIDIA/Nebius/hackathon fit. Each reviews the current product and returns all four equally weighted official criteria on a 0–10 scale: technological implementation, design, potential impact, and quality of idea. Use the same roles and rubric each round; fresh agents do not see previous scores. Each round's overall is the arithmetic mean of all 12 criterion scores. Reviewers assess the demo script as intended content at the owner's request; completed footage and learner observations are not invented.

After a full panel, implement actionable fixes within the current FIFO education scope and rerun relevant checks before the next panel. Stop after at most five total rounds, or after two consecutive rounds differ by less than 0.2 overall and less than 0.3 on every criterion mean, with no remaining critical finding fixable within the authorized scope. This is an operational stopping rule; subjective score stability is not statistical confidence. Unobserved human adoption or unfinished owner video work is disclosed, not fabricated to raise scores.

## Results

| Round | Technology | Design | Impact | Idea | Overall | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 8.23 | 8.03 | 7.33 | 8.33 | 7.98 | Fix actionable findings and rerun. |
| 2 | 8.63 | 8.23 | 7.73 | 8.57 | 8.29 | Changes exceed stability thresholds; fix and rerun. |
| 3 | 8.63 | 8.37 | 7.73 | 8.67 | 8.35 | Numerically stable; fix a trust-boundary finding before stopping. |
| 4 | 8.73 | 8.57 | 8.13 | 8.77 | 8.55 | Stability thresholds exceeded; fix persistence edge case and run final panel. |

Round 1: [learning](education-round1-learning.md), [hardware](education-round1-hardware.md), [sponsor](education-round1-sponsor.md). Individual means were 8.325, 7.875, and 7.750. Their differences are subjective judgment, not statistical uncertainty bounds.

Implemented after round 1: release-pinned replay digest (browser and coaching service); invalid/inconsistent practice rejection; restore/replay past experiments; count recorded model assistance; preserve context-bound live coaching transcripts and ignore responses invalidated by edits/reset; align actual Devpost/testing fields with education; link completed labs directly to real rejected/accepted Nemotron repairs. Added declared development coaching checks across all three lessons and retained unsuccessful outcomes. No external learner evidence was manufactured.

Fresh rounds do not receive earlier scores. All individual reports remain here for audit.

## Round 2 follow-up

Reviews: [learning](education-round2-learning.md), [hardware](education-round2-hardware.md), [sponsor](education-round2-sponsor.md). Individual means: 8.475, 8.350, 8.050. Overall changed by 0.3083; technology and impact each changed by 0.4, so this round does not meet the stopping threshold.

Implemented numeric edge/cycle list and range validation (including reversed and excessively large ranges), a shared 2 MB import limit with bounded record fields and a large Unicode export round trip, a completion snapshot binding selected evidence and pre-transfer assistance, imported mismatch validation against the pinned library, and precise authored-candidate wording in the script. Later exploration remains available and is distinguished from assistance at transfer submission.

The full final-prompt coaching matrix plus three fresh development paths ran, preserving all fifteen responses. The previously indirect exchange policy overclaim was corrected in this response. One fresh exchange response still contradicts the evidence, the overflow blanket claim is not directly challenged, and several hints reveal much of the diagnosis. These remaining model-quality limits are disclosed rather than relabeled as passing checks. Live coaching remains advisory/local; hosted authored hints remain the dependable baseline. Project-funded live judge access and funding/credit expiry require a deployment arrangement beyond the existing static Vercel release; no new spend ceiling or VM is assumed authorized. Owner video and human evidence remain external delivery dependencies.

## Round 3 follow-up

Reviews: [learning](education-round3-learning.md), [hardware](education-round3-hardware.md), [sponsor](education-round3-sponsor.md). Individual means: 8.400, 8.450, 8.200. Overall changed by 0.0583 and every criterion mean by less than 0.3. Although numerical stability is met, the hardware reviewer reproduced a parser trust-boundary defect: preserved solver PASS artifacts could override contradictory worker failure metadata. This merits repair and one final fresh assessment before applying the no-critical-finding stopping condition, even though the reviewer classified its likelihood as P2.

The verifier now requires successful enclosing execution, rejects incomplete/failed elaboration and duplicate step identifiers, and only accepts formal PASS from a successfully completed step. Legitimate SBY FAIL exit code 2 still yields a counterexample. Replay also checks execution and integrity before reporting reproduction. Negative controls use the preserved PASS artifacts and individually altered completion fields; no published proof has been shown false. An audit found all sixteen preserved formal PASS step records, including nested candidates, consistent with successful execution; all root verification batches had clean completion metadata.

Facilitator tables and Markdown notes now retain the selected answer text, keyboard focus moves to the opened bench, and RELEASE_DECISION distinguishes the owner-selected education product from the separate workbench profile gate. Funding/access and human-evidence dependencies remain disclosed.

## Round 4 follow-up

Reviews: [learning](education-round4-learning.md), [hardware](education-round4-hardware.md), [sponsor](education-round4-sponsor.md). Individual means: 8.450, 8.500, 8.700. Overall change is exactly 0.20 and impact mean change is 0.40, exceeding the strict stopping thresholds. Hardware review found no further reproducible trust defect. Its sandboxed Docker invocation skipped; the root's prior Docker-enabled run actually executed all eight tests successfully, as STATUS records.

One learning reviewer reproduced a saved-record mismatch: the backend allowed repeated legal cycle indices, while the browser rejected more than six indices. The backend now returns unique sorted references; the browser also normalizes older duplicated legal references so existing reflections and attempts survive reload. Both server acceptance and legacy JSON restoration have focused regression coverage. Round 5 is the final panel allowed by the owner's cap.
