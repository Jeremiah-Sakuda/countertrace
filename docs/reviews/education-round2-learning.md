# Education release: fresh simulated panel, round 2 — learning and usability

Reviewed commit `0fd4317a51b790b5eed4aece4a3b352b2762e198` on October 5, 2026. This is a fresh assistant simulation, not actual sponsor judging, educator validation, or a learner study. No previous panel score files were read. Source and preserved execution evidence were sufficient for this review; the shared browser was not navigated. The owner identifies this exact commit as the release being published to `countertrace.vercel.app`; this review does not independently attest deployment completion.

## Equally weighted scores

| Official criterion | Score / 10 | Assessment |
| --- | ---: | --- |
| Technological Implementation | 8.7 | A substantive implemented system: isolated RTL evidence, an integrity-pinned finite learning library, exhaustive browser/reference agreement checks, bounded advisory coaching, and separate genuine Nemotron repair records. The evidence is stronger than a UI mockup or model narrative. Coaching semantics remain fallible, and imported practice has a size-contract defect. |
| Design | 8.3 | A coherent prediction → experiment → explanation → transfer journey; progressive disclosure, readable choices, authored hint ladder, explicit scope, local persistence, and an instructor route. Exports preserve useful attempts and coaching context. Completion does not preserve the timing/context of assistance and subsequent work, reducing the precision of facilitator interpretation. This is source-based interaction assessment, not a fresh visual or screen-reader certification. |
| Potential Impact | 8.2 | A credible, specific problem for instructors and FPGA club mentors: students with basic RTL knowledge need practice choosing revealing boundary inputs and separating a passing test from proof. A browser-accessible exercise, reusable facilitation plan, and voluntary record review address that problem directly. No adoption, learning gains, or preparation-time savings are demonstrated or assumed. |
| Quality of Idea | 8.7 | Constructing counterexamples and then challenging an AI repair is a strong, understandable educational application of verification. A correct control and explicit evidence limits improve the idea beyond simply finding planted bugs. This is an effective combination of established techniques, not a first-of-kind research claim. |
| **Equal-weight mean** | **8.475** | **33.9 / 40** |

The demo script has a clear intended story: an ordinary sequence passes, an overflow sequence exposes a lost word, a preserved or live Nemotron response supports discussion, a transfer question changes the context, and a rejected real repair demonstrates the independent checker's role. Its 2:45 plan contains an appropriate audience and concrete problem. Footage quality and actual delivery remain unassessed; their absence is not substituted with a fabricated video score or treated as a product defect.

## Remaining concrete issues and bounded fixes

### P2 — A supported local session can export a file that the facilitator refuses to import

`apps/web/src/lib/learning.ts:78–83` permits 100 coaching entries, each retaining up to 2,000 characters of learner text and 1,600 characters of response. `apps/web/src/views/LearnView.tsx:117` exports the full session, while line 130 rejects any imported file above 128,000 bytes.

Reproduced directly through the actual Vite-loaded module: a session with one valid overflow experiment, a 2,000-character reflection, and 60 successful short coaching responses passes `validateSession`; its normally formatted JSON export is **140,249 bytes**. That file is rejected by the facilitator's size gate. This is a long-practice/local-coaching edge case rather than a blocker for the short hosted demonstration, but it breaks the stated export/import round trip for valid product output.

Fix: define one shared bounded serialization/import policy that accommodates every valid export, or prevent growth before a session becomes unshareable and explain the limit. Preserve the existing local-only handling and bounded imports. Verify a near-limit product-generated record round-trips.

### P2 — Completion records do not distinguish assistance before the transfer answer from later exploration

`LearnView.tsx:114` freezes the transfer answer and completion timestamp; the hint buttons, recorded coaching example, experiment builder, and history remain usable (`:95–107`, `:112`, `:116`). `Session` has only total hint counts and no authored-hint/view timestamps or completion snapshot (`learning.ts:64–69`). The facilitator reports whether a record "used hints" (`LearnView.tsx:131`).

Reproduction from the source's deterministic handlers: complete the overflow lab without assistance, then open the recorded coaching example or reveal an authored hint. The completed transfer remains unchanged while `hints` becomes 1. The exported record cannot distinguish this from assistance used before answering. Similarly, later experiments can become the restored latest evidence while the completed explanation remains locked and has no saved sequence association. These are still honestly labeled self-reported records, but a facilitator cannot reliably use them to distinguish unassisted transfer or determine the evidence shown when the learner completed the activity.

Fix: preserve a small completion snapshot containing the selected experiment and assistance counters; alternatively timestamp assistance and bind the submitted reflection to a path. Keep later experimentation available and label it as subsequent practice. This is a narrow record-model fix, not a request for accounts, grading, or an analytics platform.

### P3 — Sharpen the script's transition from authored exercise to actual AI repair

The opening calls the candidate an "authored exercise" while also saying a "convincing hardware fix" can lose data. The later repair section clearly concerns actual Nemotron output, and the UI already discloses fixture origin. To remove the remaining ambiguity in the spoken story, call the opening object an authored candidate or faulty implementation, then explicitly introduce the later run as an actual model-proposed repair. This is a wording improvement, not a false-origin finding against the implementation.

## Evidence and verification

Read `AGENTS.md`, the education requirements in `docs/PRD.md`, `docs/ROADMAP.md`, `docs/TEACHING.md`, current `docs/submission/DEMO_SCRIPT.md`, `LearnView.tsx`, `learning.ts`, routing, the learning tests, integrity manifest, current targeted coaching evidence, and engineering evaluation reports. The current targeted coaching record honestly labels itself as development regression and includes actual responses; it does not establish general tutoring quality. The engineering reports preserve attempted denominators and limitations, including corrections to derived summaries and the exploratory ablation's confound.

Ran the three web tests successfully, including all recorded browser queue states against independent executed evidence, tamper rejection, selected revealing/no-mismatch sequences, and record validation. Ran `make check`: 97 Python tests passed, with workspace checks and CLI validation. These are software/regression checks, not new RTL executions or learner outcomes. No verifier or product code changed; Docker integration was not rerun for this review-only file.

No new module family, public uploads, full LMS, invented study, or broad product rewrite is needed to improve this demonstration. The remaining external evidence limits are actual learner/facilitator use, independent technical review, and the owner's finished recording. Those limits should stay visible; they are not concrete software defects to simulate away.
