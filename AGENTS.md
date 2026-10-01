# Working on Countertrace

Read `docs/PRD.md` and `docs/ROADMAP.md` before changing product behavior. Keep the public README accurate about what has actually run.

## Scope

- Build from scratch. Historical AKILI code is not a dependency.
- Start with the specified synchronous FIFO profile: 8-bit words, depths 2 and 4.
- Diagnosis is the delivery baseline; repair is earned scope. Do not add a module family or orchestration framework before the feasibility gate.
- The public MVP uses bundled examples. User testbench ingestion and public arbitrary uploads are deferred.

## Trust boundaries

- The model proposes interpretation, explanation, or DUT patches; it never authorizes a verification result.
- Preserve independent reference monitors. Freeze the contract, assumptions, checks, parameters, and tool configuration during a repair comparison.
- Revalidate all model-generated HDL and supplemental checks before execution. Execute RTL only in the isolated verifier, with no model credentials or child network access.
- Parse authoritative tool artifacts and expected property counts. Timeouts, errors, missing evidence, unsupported inputs, and cancelled runs cannot become proof or success.
- Never publish proprietary RTL, secrets, private runs, or unfrozen held-out labels. `.env` and generated artifacts are ignored.

## Development

- Run `make check` for every change and `make test-integration` (Docker) for verifier changes. Record anything newly observed in `docs/STATUS.md`.
- Keep development, showcase, and held-out evaluation data separate. Moving a holdout case into prompt development must be recorded.
- Update the PRD and status documentation when scope changes. Keep the Page and repository PRD aligned when editing the requirements; see `docs/DEVELOPMENT.md`.
- Do not claim a hardware proof, model benchmark, user result, or completed milestone from a scaffold check.
