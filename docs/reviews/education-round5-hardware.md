# Education round 5 — hardware and trust review

Independent simulated hackathon assessment of commit `2ce3f15f463eb618386edd3b99eb7fd5ca4e9594`, October 5, 2026. This is an assistant review, not sponsor judging, independent human validation, or a learner study. Earlier panel files and scores were not consulted. The video is judged from `docs/submission/DEMO_SCRIPT.md` as intended content; footage quality is unknown. Source, recorded artifacts, and local tests were reviewed; no deployment, paid inference, or shared-browser navigation was performed.

| Equally weighted criterion | Score / 10 | Reason |
| --- | ---: | --- |
| Technological Implementation | 8.9 | Substantial working verifier and repair system supports the education layer. Executed RTL evidence, independent reference checks, pinned replay integrity, candidate re-admission, frozen comparisons, and explicit error states are unusually strong for a small educational demo. Advisory coaching still has documented factual errors; the engineering evaluations remain small and assistant-authored. |
| Design | 8.5 | Prediction, learner-built sequence, expected/observed comparison, explanation, transfer, and facilitator export form a coherent activity. The correct-control lesson teaches restraint. Evidence provenance and recorded/live distinctions are visible in source, and the script shows a convincing ordinary-test/boundary-test contrast. This score assesses interaction structure and intended story, not freshly observed visual usability or footage. |
| Potential Impact | 7.8 | A reusable, browser-accessible lesson can remove simulator setup from a mentor's session and make boundary reasoning tangible. Facilitator keys and voluntary records support a credible adoption route. No observed learner transfer, instructor reuse, preparation-time saving, or retention evidence supports a stronger impact claim yet. |
| Quality of Idea | 8.8 | Asking learners to construct a counterexample and defend the scope of evidence is a strong use of this machinery. The bridge to a real rejected and accepted Nemotron repair gives the lesson a useful engineering consequence. The distinction is the integrated learning experience and evidence discipline; formal checking and RTL repair themselves have precedents. |

**Equal-weight mean: 8.50/10.**

## Verified strengths

- `make check` passed all **101 Python tests**, workspace checks, and diff validation. `npm --prefix apps/web test` passed **3/3**. These are software checks, not newly executed hardware proofs.
- The archive test re-parses actual raw traces and checks every supported prefix against the independent reference: three candidates, 4,096 six-edge paths each, 5,461 prefix nodes per candidate. The browser test independently agrees with those records and rejects mismatching evidence. I did not rerun Docker simulation in this review.
- The script's overflow example is supported: `wwwr` expects `0x11` and observes `0x33` at edge 4. The exchange candidate disagrees on the full flag after `wwb`; the control agrees. Null read values remain unchecked when no read was accepted.
- The formal monitor accepts transactions from reference occupancy, checks post-edge flags and accepted read data, assumes reset only initially, and includes recurring-reset/boundary reachability. The worker disables networking, uses a read-only root, drops capabilities, and receives no model credentials.
- The shown repair is genuine recorded evidence: `rec-20261004-010137-ver-dd43e0` rejects candidate 1 on a cycle-4 `empty_flag` counterexample and accepts candidate 2 with all ten unchanged obligations resolved, including three property proofs. Both comparisons record matching frozen checks. These are scoped property results, not whole-device assurance.

## Remaining findings and limits

**No new reproducible in-scope hardware-verdict or replay-integrity defect was found.** There is no new P0/P1/P2 implementation fix requested by this review. Further module families, uploads, orchestration, or perfect model semantics are not prerequisites for this release.

One known limitation remains material to scoring: the preserved fifteen-case coaching development check includes an exchange hint that says the candidate rejects a write it actually accepts (`bwwbr`, edge 4). This is inspectable evidence of advisory-response weakness, not a new verdict flaw or a guarantee that another call reproduces the text. The current interface discloses semantic uncertainty and keeps the deterministic evidence and authored guidance available. The narrow recording action is to select and inspect an actual useful response, retain its recorded/live label, and avoid presenting structural validation as tutoring accuracy. No additional paid rerun is required by this review.

Actual learner usefulness, facilitator reuse, funded live judge access, sustained availability, and owner-recorded/published footage are external validation or release dependencies. They should remain explicitly open; neither this panel nor passing software tests supplies those outcomes. The hosted recorded labs already serve the bounded education journey without learner credentials. The script's intended content is strong and honestly scoped, with the real repair segment preserving the project's NVIDIA/Nebius contribution.
