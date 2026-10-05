# Education release simulated judging

The owner requested an end-to-end education release followed by repeated fresh judging panels and fixes. These are assistant simulations, not sponsor scores, human validation, or award probabilities.

## Protocol fixed before round 1

Three independently prompted reviewers cover learning/product, hardware/trust, and NVIDIA/Nebius/hackathon fit. Each reviews the current product and returns all four equally weighted official criteria on a 0–10 scale: technological implementation, design, potential impact, and quality of idea. Use the same roles and rubric each round; fresh agents do not see previous scores. Each round's overall is the arithmetic mean of all 12 criterion scores. Reviewers assess the demo script as intended content at the owner's request; completed footage and learner observations are not invented.

After a full panel, implement actionable fixes within the current FIFO education scope and rerun relevant checks before the next panel. Stop after at most five total rounds, or after two consecutive rounds differ by less than 0.2 overall and less than 0.3 on every criterion mean, with no remaining critical finding fixable within the authorized scope. This is an operational stopping rule; subjective score stability is not statistical confidence. Unobserved human adoption or unfinished owner video work is disclosed, not fabricated to raise scores.

## Results

| Round | Technology | Design | Impact | Idea | Overall | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 8.23 | 8.03 | 7.33 | 8.33 | 7.98 | Fix actionable findings and rerun. |

Round 1: [learning](education-round1-learning.md), [hardware](education-round1-hardware.md), [sponsor](education-round1-sponsor.md). Individual means were 8.325, 7.875, and 7.750. Their differences are subjective judgment, not statistical uncertainty bounds.

Implemented after round 1: release-pinned replay digest (browser and coaching service); invalid/inconsistent practice rejection; restore/replay past experiments; count recorded model assistance; preserve context-bound live coaching transcripts and ignore responses invalidated by edits/reset; align actual Devpost/testing fields with education; link completed labs directly to real rejected/accepted Nemotron repairs. Added declared development coaching checks across all three lessons and retained unsuccessful outcomes. No external learner evidence was manufactured.

Fresh rounds do not receive earlier scores. All individual reports remain here for audit.
