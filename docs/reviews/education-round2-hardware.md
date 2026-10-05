# Education panel round 2 — hardware and evidence trust

Independent simulated hackathon review of commit `0fd4317`, October 5, 2026. This is an assistant assessment, not an official judge score, independent human hardware review, or learner study. Earlier panel files and scores were not consulted. The demonstration is assessed from `docs/submission/DEMO_SCRIPT.md` only; no footage quality is claimed. The public deployment was updating, so this review used source and local checks without navigating the shared browser.

## Scores

The four criteria have equal weight.

| Criterion | Score / 10 | Reason |
| --- | ---: | --- |
| Tech Implementation | 8.8 | A genuinely implemented finite RTL experiment library with pinned integrity, raw simulation traces, checked interface/property inventories, independent reference agreement, and explicit separation between observations and model advice. The full archived library is checked, not just the showcase. Remaining coaching citation parsing and imported-note consistency gaps are smaller than a verifier correctness defect but matter to the product's evidence discipline. |
| Design | 8.3 | Prediction, short sequence construction, expected/observed tables, explanation, transfer, and export form a coherent learning task. The correct-control lesson teaches restraint. Hosted replay and authored/model assistance are distinguished. Source review supports the flow; this review did not independently inspect rendering, accessibility, or learners using it. The script has a concrete passing-test-to-boundary-failure story and a clearly labeled repair bridge. |
| Potential Impact | 7.7 | The zero-install bounded lab and facilitator workflow plausibly reduce setup friction for students and FPGA clubs. The scope makes an actionable lesson possible. Actual adoption, instructor effort saved, comprehension, and transfer remain unmeasured; declared development coaching checks cannot answer those questions. This limits confidence in impact without making a small pilot an invented eligibility requirement. |
| Quality of Idea | 8.6 | Asking learners to construct the revealing input and state evidence limits is a strong application of independently checked hardware reasoning. Real rejected/accepted Nemotron repair records give the lesson a credible extension. The combination is distinctive as a teaching product, while its component ideas are established and the narrow fixed-data exercise is not an adaptive hardware tutor benchmark. |

**Equal-weight mean: 8.35 / 10.**

## Evidence inspected and verification performed

Read `AGENTS.md`, the PRD and roadmap, the learning generator, browser library loader/reference/session validation, the learning UI, server coaching implementation and route, Python/web learning tests, the current coaching regression record, and the demo script. No paid inference was requested.

- `make check`: all 97 Python tests passed, workspace checks passed, and `git diff --check` passed.
- `npm --prefix apps/web test`: all three web tests passed.
- The Python library test reparsed each archived raw trace against the independent Python reference, checked archive hashes and source hashes, and compared every stored prefix observation. The web test checked all available browser reference states and a tampered-library rejection.
- The current generator covers 4,096 length-six paths per design and 5,461 prefixes, with reset boundaries and fixed edge-dependent values. It rejects incomplete/failed workers, wrong harness hashes, wrong step sets, incompatible ports/properties, incomplete traces, and nonrepeatable prefixes. It preserves a correct control and witnessed faulty candidates.
- The browser and coaching server both bind the library bytes to a release-pinned SHA-256. This protects release consistency; it is not a proof of authorship or mathematical soundness.
- No fresh RTL execution was performed in this review. Passing parser/reference checks reconfirms artifact consistency; it does not constitute a new hardware proof or a clean-environment replay.

No reproducible false hardware verdict was found in the reviewed learning path. Replay is explicitly finite simulation, null read data remains unchecked, reference queues are not described as sampled DUT memory, and model hints cannot change the authoritative observations.

## Ranked fixes within the current scope

### 1. P2 — Close ordinary-language gaps in coaching edge validation

`src/countertrace/learning.py` extracts only a number immediately following `edge`/`edges`, with an optional ascending-looking range. The enclosing validator checks explicit `cycles`, but misses other numbers in normal edge lists, the synonym `cycle`, and reversed ranges. Its returned `citation_scope` consequently overstates how completely references are checked.

Reproduced locally by mocking only `model.structured` to invoke the real validator, with lesson `overflow`, path `wwwr`, and a normal learner reflection. All three responses were accepted:

```json
{"hint":"Compare edges 1 and 99. What changes?","cycles":[1]}
{"hint":"Inspect cycle 99. What happened?","cycles":[]}
{"hint":"Compare edges 4-1. What changes?","cycles":[]}
```

This does not authorize a false RTL result. It does allow an impossible citation to reach a learner despite the stated reference-check guarantee. Parse lists and supported synonyms, reject reversed ranges, and test these specific cases. Alternatively constrain edge mentions to a single validated display syntax and render them from structured data. Keep semantic correctness explicitly advisory; syntax validation cannot certify a hint's explanation.

### 2. P3 — Keep imported attempt observations distinct from revalidated observations

`apps/web/src/lib/learning.ts:85` checks the shape/range of `firstMismatch` without checking it against the selected recorded sequence. A structurally valid completed overflow session with `path: "wwwr"` and `firstMismatch: null` is accepted and `sessionReport` prints:

> Write → Write → Write → Read; prediction: no-mismatch; no mismatch in this sequence

The actual pinned library records the first mismatch at edge 4. This was reproduced through `validateSession` and `sessionReport` using Vite's source loader. The existing global self-reported-record disclaimer mitigates the issue, and this is not a trusted verifier bypass. Still, the exported experiment line reads like an observed result rather than an unverified imported claim.

For imported records, either compare the lesson/path/first-mismatch tuple against the loaded pinned library and visibly reject or flag disagreement, or mark attempt observations as unverified in the facilitator output. Including the library digest/profile in new practice records would make future release comparisons unambiguous. Do not add signing, accounts, or an assessment-security system for this low-stakes practice feature.

## Limits and next evidence

The declared coaching checks appropriately retain mixed outcomes and identify authored development cases, prompt changes, and targeted follow-ups. The four-case targeted record does not erase earlier weak responses or establish general tutoring reliability. The model's advisory status and semantic warning are appropriate and should remain visible.

The largest remaining impact uncertainty is learner usefulness, not additional FIFO breadth. When participants are available, observe a small facilitated session and record whether learners independently construct a boundary case and justify the transfer answer, including wrong attempts and assistance. That would strengthen the impact assessment without claiming population learning gains. It is not a substitute for closing the small reproducible validation defects above.

The script's edge-four `0x11` versus `0x33` example matches the evidence. Its recorded/live coaching distinction and rejected/accepted repair segment are credible proposed content. Actual recording, pacing, visual legibility, public availability, and submission acceptance remain outside this review's evidence.
