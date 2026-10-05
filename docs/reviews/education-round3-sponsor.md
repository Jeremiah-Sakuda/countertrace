# Independent simulated panel — education round 3, sponsor/impact lens

Reviewed October 5, 2026 at source `6100514022ed8e8afc88f281e652195d7208bd16`. This is an assistant simulation, not NVIDIA/Nebius judging, human research, or a prize prediction. No previous panel reports or scores were read. Reviewed the current learning source, replay/coaching artifacts, README, PRD, roadmap, submission material, and engineering evaluation report. The shared browser was not navigated; design assessment is of implementation and intended flow, not a fresh visual inspection. No paid calls were made. The demo script is assessed as intended content, without deducting for unavailable footage.

The [official rules](https://nebiusglobalaihackathon.devpost.com/rules), checked during this review, give the following four criteria equal weight. Token Factory runtime inference qualifies as platform use; additional Nebius compute is not mandatory. Coding and Agentic Engineering is a credible fit for an executable RTL learning tool backed by constrained, independently checked model repairs.

| Criterion | Score / 10 | Assessment |
| --- | ---: | --- |
| Technological Implementation | 8.4 | Real NVIDIA inference, preserved unsuccessful outputs, frozen repair comparisons, two engineering evaluations, and a hash-bound library of executed RTL make this substantially more than an AI wrapper. Coaching is a bounded advisory feature with explicit semantic limits. Free access to the advertised live model functions remains an unfinished release dependency. |
| Design | 8.3 | Predict → compose → inspect → explain → transfer → export is a coherent small product. A facilitator can share a lesson and review local practice records without accounts or infrastructure. Recorded execution, authored hints, model output, and accepted repairs are distinguished. Source review cannot establish visual polish or observed ease of use. |
| Potential Impact | 7.5 | Instructors and FPGA mentors are a specific audience, and installation-free experiments plus reusable lesson keys directly address a plausible preparation and evidence-reasoning problem. No learner or facilitator has demonstrated usefulness, demand, or repeat adoption. Engineering success does not fill that evidence gap. |
| Quality of the Idea | 8.6 | Constructing a counterexample and then challenging an actual rejected/accepted AI repair is an effective, non-obvious educational use of the verifier/model combination. Fixed acceptance semantics and a correct-control lesson show domain understanding. The contribution is the teaching workflow and evidence discipline, not a novel repair algorithm. |

**Equal-weight result: 8.20/10 (32.8/40).**

## Sponsor fit and intended video

The model contribution is genuine and legible: Super interprets briefs; Ultra explains, proposes edits, and coaches reasoning; independent tools decide verification outcomes. Keeping CPU verification outside Nebius Jobs is defensible and does not reduce eligibility merely because another sponsor service exists. The preserved coaching failures and the v4 development check support a candid account of model limitations rather than a synthetic tutoring benchmark.

The 2:45 script tells a coherent story: ordinary passing test, revealing boundary sequence, context-labelled Nemotron response, transfer/export, facilitator reuse, then a real failed and accepted repair. The 25-second repair segment is important because it demonstrates sponsor-powered code work beyond a scripted lesson. Keep the recorded/live labels and unchanged-check evidence visible as written. No additional model family, upload path, infrastructure service, or course catalog is needed.

## Remaining actionable items

1. **P1 — Release/access dependency, not a newly discovered software defect: finish free access to the advertised live model capability.** Reproduction: follow `docs/submission/TESTING.md` from the no-account hosted route to live coaching; the hosted application makes no live call, and the documented local path requires the developer's Token Factory configuration. The document explicitly leaves project-funded judge instructions pending. Narrow completion: supply and test one project-funded route or functioning test-build arrangement for the existing model capability, document exact instructions, and verify its availability plan through December 15. The rules allow a test build; they do not require converting the Vercel frontend into a live verifier host. Do not portray the current static route as a failed application or erase the already demonstrated integration.

2. **P2 — Documentation consistency: the release decision still describes the former primary product choice.** Reproduction: compare PRD v1.2's owner-selected education direction and the education-led submission with the opening of `docs/RELEASE_DECISION.md` (“Current commitment: diagnosis”) and its primary/diagnosis-only decision fields. A reviewer cannot immediately tell whether the selected education product and its optional workbench extension are the declared release. Narrow fix: add the existing October 5 education decision and explicitly identify the legacy diagnosis/repair gate as the maintained workbench profile; preserve pending learner outcomes and access obligations. This does not require declaring an unmet milestone complete.

No further confirmed software defect was found in this sponsor-focused review. The latest fifteen-case coaching record includes a factual contradiction on an exchange example despite valid references. The current advisory label, authored fallback, preserved failure, and absence of a tutoring-success claim are proportionate; perfect LLM semantics is not a release requirement. It should remain visible in limitations and must not be converted into a broad effectiveness claim.

## External evidence, separate from fixes

The highest-value impact evidence is one facilitator trying the existing lesson and a few learners attempting the transfer question, recording failed attempts and assistance. This requires real participants and is not a software defect, a reason to add more features, or an official entry prerequisite. Until available, retain the current explicit absence of adoption, measured learning gains, and preparation-time savings. Simulated panels cannot raise that evidence level.

Review validation: source/artifact inspection and `make check` passed (98 Python tests, workspace checks, CLI smoke check, whitespace check). No new HDL execution or model call; these checks do not establish hardware proof or learner outcomes.
