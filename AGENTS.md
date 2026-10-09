# Working on Countertrace

Read `docs/PRD.md` and `docs/ROADMAP.md` before changing product behavior. Keep the public README accurate about what has actually run.

## Scope

- Build from scratch. Historical AKILI code is not a dependency.
- The FIFO workbench keeps its specified profile: 8-bit words, depths 2 and 4.
- Model-written checks are the lead direction (PRD 1.4, October 9). New module families enter only through the catalog: reviewed specification, hand-written golden reference, and seeded bugs. Do not add an orchestration framework.
- The public MVP uses bundled examples. User testbench ingestion and public arbitrary uploads are deferred.

## Trust boundaries

- The model proposes interpretation, explanation, DUT patches, or properties; it never authorizes a verification result. Model-written properties count only after the golden gate, and a design defect found by them counts only after golden replay confirms it.
- Model-written properties are structured data compiled by trusted code. The model never supplies assumptions, covers, tool directives, or scripts, and never sees the golden source.
- Preserve independent reference monitors. Freeze the contract, assumptions, checks, parameters, and tool configuration during a repair comparison.
- Revalidate all model-generated HDL and supplemental checks before execution. Execute RTL only in the isolated verifier, with no model credentials or child network access.
- Parse authoritative tool artifacts and expected property counts. Timeouts, errors, missing evidence, unsupported inputs, and cancelled runs cannot become proof or success.
- Never publish proprietary RTL, secrets, private runs, or unfrozen held-out labels. `.env` and generated artifacts are ignored.

## Development

- Run `make check` for every change and `make test-integration` (Docker) for verifier changes. Record anything newly observed in `docs/STATUS.md`.
- Keep development, showcase, and held-out evaluation data separate. Moving a holdout case into prompt development must be recorded.
- Update the PRD and status documentation when scope changes. Keep the Page and repository PRD aligned when editing the requirements; see `docs/DEVELOPMENT.md`.
- Do not claim a hardware proof, model benchmark, user result, or completed milestone from a scaffold check.
