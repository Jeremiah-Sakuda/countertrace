# Education round 1 — hardware and evidence review

Independent simulated hackathon assessment of commit `cff82df69e58068edd0f507f92b4012158d89953`. Not an official sponsor judgment. No prior panel reports or scores consulted. The proposed demo is assessed from `docs/submission/DEMO_SCRIPT.md`; no footage quality or learner outcomes are inferred.

| Equally weighted criterion | Score / 10 | Reason |
| --- | ---: | --- |
| Technological Implementation | 8.0 | Substantial executed hardware evidence, independent reference checking, correct control, finite-library completeness, and grounded advisory model integration. Runtime artifact integrity and practice-state validation need strengthening. |
| Design | 8.0 | Clear prediction → experiment → explanation → transfer progression, readable expected/observed table, explicit scope, and usable facilitator/export paths. Assistance accounting and persisted experiment context are weaker than the central lesson flow. Visual assessment is from implementation, not a fresh browser usability session. |
| Potential Impact | 7.0 | A concrete, reusable activity for students and instructors, with no paid learner credentials required for replay. Adoption, preparation savings, and learning benefit remain unobserved; this limits evidence of impact rather than constituting a missing-feature defect. |
| Quality of Idea | 8.5 | Constructing revealing inputs and learning to limit claims is a coherent educational use of the verifier. The correct-control exercise and frozen-check repair extension add substance beyond an AI explanation demo. Narrow authored exercises and one useful coaching example limit demonstrated generality. |

**Equal-weight mean: 7.875 / 10.**

## Evidence credited

- `scripts/build_learning_evidence.py:45–104` checks worker completion, harness hashes, expected steps, ports, property inventory, independent normalized traces, repeated prefixes, and expected control/fault behavior before publication. This is considerably stronger than browser-generated DUT animation.
- `tests/test_learning.py:14–34` reparses the actual compressed archive and verifies hashes, library agreement, 28,672 cycles per candidate, and all 5,461 prefixes. The 4,096 six-edge paths per candidate use four actions and fixed offered values. They are executed finite simulation evidence, not proof or arbitrary-input coverage.
- `src/countertrace/learning.py:14–35` selects evidence/source server-side, rejects unsupported sequences, validates cited edge ranges, and keeps output advisory. The model cannot change the deterministic verdict. The two unsuccessful Super responses and revised Ultra response are honestly disclosed in `apps/web/src/views/LearnView.tsx:105`.
- The script's overflow sequence and expected `0x11` versus observed `0x33` are supported by the library. The script distinguishes replay, live/recorded coaching, authored hints, and unmeasured learning outcomes.

## Ranked fixes

1. **P1 — bind runtime replay to the verified library bytes.** `apps/web/src/views/LearnView.tsx:55` checks only the schema; `apps/web/src/lib/learning.ts:18–24` checks reference values and observation types, but has no integrity binding for observed DUT outputs. Reproduced with the actual library: `evidenceRows(library, 'overflow', 'wwwr')` reports edge 4; assigning `library.designs.overflow.nodes.wwwr[3] = 17` makes the same call return no mismatches. Thus an altered observation becomes a displayed passing result rather than an evidence error. The checked-in archive is valid; this finding concerns delivery-time corruption/stale artifact defense, not an observed false result in that archive. Generate a pinned digest with the verified release, validate fetched bytes before results, and validate the fixed metadata. Apply equivalent validation before coaching consumes the file (`src/countertrace/learning.py:19–24`). No cryptographic signing system is necessary.

2. **P2 — record assistance from the preserved coaching example.** `apps/web/src/views/LearnView.tsx:105` opens an actual helpful model response without updating the session; the authored/live paths do update `hints` at lines 67 and 100. Reproduction: run overflow `wr`, open the recorded example, read its boundary guidance, and export JSON. `hints` remains zero, and the facilitator summary at line 122 counts the record as not having used hints. Track first opening as recorded-model assistance and expose the category in exported notes/JSON. This matters to the stated promise to preserve assistance, even though records are correctly labeled self-reported practice.

3. **P2 — reject impossible imported/restored lesson states.** `apps/web/src/lib/learning.ts:63–81` validates individual field shapes but not progression. Reproduced: `validateSession({...newSession('overflow'), transferAnswer: 1, completed: new Date().toISOString()})` succeeds with `transferCorrect: true`, despite no initial prediction, experiment, or reflection. The facilitator counts this as a matching transfer answer (`apps/web/src/views/LearnView.tsx:122`). Require a completed/answered-transfer record to contain the preceding required stages and sensible timestamps. This is consistency validation, not authentication or proof that someone learned.

4. **P3 — restore a usable experiment context with saved practice.** `apps/web/src/views/LearnView.tsx:41,46–49,63,103` restores the session and explanation but initializes the builder/result to empty. After running `wwwr`, entering an explanation, and reloading, stage 3 remains available yet its evidence table disappears and local coaching is disabled until another attempt is added. Restore the last attempt as an explicitly labeled previous experiment, or offer a replay button that does not manufacture a new attempt.

## Verification and limits

`make check` passed: 96 Python tests plus workspace and diff checks. `npm --prefix apps/web test` passed all three web tests, including every browser reference state. Both mutation reproductions above ran through the actual TypeScript module using Vite. No product files were changed, no new model calls were made, and the independent verifier was unchanged; Docker integration was not rerun for this review. Existing archive execution is credited, without claiming fresh hardware execution. No learner study exists, and simulated judging cannot supply one.
