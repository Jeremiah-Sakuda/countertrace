# Evaluation protocol

No evaluation cases have been admitted or frozen, and no participants or outcomes are established yet. One external FIFO candidate is quarantined locally; see [independent fixture review](INDEPENDENT_FIXTURE.md). Follow the [PRD](../docs/PRD.md); this checklist prevents accidental claims from scaffold or showcase data. Recruitment drafts, session instructions, and scoring are in [STUDY.md](STUDY.md).

## Freeze before measuring

- Declare primary versus diagnosis release and proof versus bounded-only scope.
- Prepare eight faulty cases and four correct controls across at least two independently authored implementations; hold at least one implementation out of prompt development.
- Record provenance and ground truth, including reviewer participation or its absence.
- Freeze model, prompts, core checks, supplemental checks, attempt/token/time budgets, and final evaluator.
- Keep hidden regressions and labels in ignored `holdout/`; do not expose them to the repair feedback loop.

## Separate questions

1. **Engineering:** compare the full repair workflow with the matched tool-feedback baseline. Report all cases and attempts. Additional checks and feedback prevent attributing a difference solely to the audit.
2. **Interpretation:** use four ambiguous/conflicting briefs and four clear compatible briefs. Report missed conflicts and false blocking conflicts separately.
3. **Explanation:** use the same deterministic checks and trace, with audit presentation fixed. Score the violated requirement, first failing transaction, expected/observed behavior, and limits of a pass as incorrect/partial/correct. Record assistance.
4. **Audit learning:** ask the learner to identify a missing requirement and recognize the omission in a different example. Do not turn the mutation score into design confidence.

In the diagnosis release, omit the repair comparison. One run per configuration is the required pilot; repeats are stretch work and do not increase the independent-design count. Three user sessions provide observations, not population estimates.

Publish all outcomes, unresolved cases, tool errors, mutation categories, cost availability, first-finding time, total run time, and queue time. Report both all-case and attempted-repair denominators. After evaluation, release authorized fixtures, protocol, and raw outcomes with any holdout contamination disclosed.
