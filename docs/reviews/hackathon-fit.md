# Hackathon fit review

Date: October 1, 2026. Scope: PRD assessment against the Nebius x NVIDIA Global AI Hackathon. This is a design review, not external technical validation, a working-system review, or a prediction of prize outcomes.

Recommendation: proceed conditionally in Coding and Agentic Engineering. The architecture and evidence discipline fit the event; the principal risks are unproven model/audit value, absent audience evidence, integration time, and an overly slow first experience. The diagnosis release is the credible baseline until repair is demonstrated.

## Findings adopted in PRD v1.1

| Finding | Adopted change |
| --- | --- |
| The promise implied testing a user's existing testbench | Promise defect diagnosis and unchanged-check repair validation; name supplemental checks as the audit subject |
| Core monitors already detect the supported faults | Measure audit usefulness through identifying a missing requirement and transferring that insight to another example |
| Model contribution could appear incidental | Score intent interpretation, evidence-grounded explanation, and repair separately from deterministic detection |
| Conflict detection could reward rejecting everything | Include four clear compatible briefs alongside four ambiguous/conflicting briefs |
| Workflow comparisons mix audit and additional feedback | Report total workflow differences; reserve audit-specific repair causality for a controlled experiment |
| A 45-minute resource limit is not a user target | Separate immediate recorded evidence, provisional 120-second live findings, and complete repair timing |
| The solo 100-hour estimate has little reserve | Use an October 4 gate, October 8 initial profile decision, and rebaseline for at least 15 hours of contingency |
| Sampling semantics could diverge between engines | Specify pre-edge/post-edge timing, reset behavior, and depth-2 cycle examples |
| Model output is executable input too | Reapply admission to every patch/check and prohibit verifier or tool-specific behavior changes |
| Impact lacks direct audience evidence | Recruit in week one, observe an early session, use a declared comprehension rubric, and limit study claims |
| The video introduces too much machinery early | Lead with consequence, requirement, and trace; show audit after the core debugging journey |
| Judge access is an operating obligation | Fund access through December 15, require no judge-purchased credits, and rehearse recovery and clean access |

Preserve independent checks, frozen repair comparisons, failure evidence, and exact result scope under all reductions. Do not broaden hardware support or add retrieval only to pursue a bonus award.

## Sources

- [Official rules](https://nebiusglobalaihackathon.devpost.com/rules)
- [Nebius Jobs documentation](https://docs.nebius.com/serverless/jobs/manage)
- [Nebius Nemotron catalog](https://github.com/nebius/token-factory-cookbook/blob/main/models/nemotron/README.md)
- [Yosys language support](https://yosyshq.readthedocs.io/projects/yosys/en/latest/using_yosys/verilog.html)
- [Verilator language support](https://verilator.org/guide/latest/languages.html)
- [Veri-Sure](https://arxiv.org/abs/2601.19747), [open-source RTL repair study](https://arxiv.org/abs/2607.28877), and [MCY](https://yosyshq.readthedocs.io/projects/mcy/en/latest/)

Earlier technical/product/judge reviews referenced during PRD preparation are not represented here as recovered original documents.
