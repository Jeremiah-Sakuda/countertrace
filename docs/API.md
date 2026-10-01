# Control service API

The local control service (`countertrace serve`, default `http://127.0.0.1:8765`) serves JSON under `/api` and the built web interface from `apps/web/dist`. It is standard-library Python. All responses are JSON unless noted. Errors return `{"error": string}` with 400, 403, 404, or 500. 403 covers disabled uploads, a visitor who already has an active run, the hourly model-call cap, and explain/repair/cancel on read-only recorded runs.

Real examples of every run shape are in `.countertrace/runs/*/run.json` after running `countertrace verify` or `countertrace audit`.

## Status and catalog

| Method and path | Returns |
| --- | --- |
| `GET /api/status` | `{version, verifier: {docker, docker_detail, image_tag, image_built, network, resources, limits}, model: {configured, reason, model_id, repair_model_id, endpoint_host, input_token_limit, output_token_limit, spend}, uploads_enabled, data_notice}` |
| `GET /api/profile` | `{supported_depths, contract, timing_example}`. `timing_example` is `fixtures/timing/depth2_prd_sequence.json` (specified expectations, not results). |
| `GET /api/examples` | `[{id, split: "showcase"\|"development", title, depth, brief, expected: "correct"\|"faulty", base, fault: {id, summary, category, class, intended_consequence}\|null}]` |
| `GET /api/examples/{id}` | Example plus `{source, contract, contract_hash}`. `contract` is the versioned document the user accepts: `{profile, version, parameters, ports, requirements: {row_id: {title, text}}, checks: {check_id: text}, assumptions: [string], sampling}`. |
| `GET /api/check-sets` | `[{id, label, origin, description, reviewed, tests: [test]\|null, checks: [{id, check, rows\|null, requirement, text}]}]`. `reviewed: false` marks model-proposed candidates. |
| `GET /api/recorded` | Recorded runs shipped in `recorded/`: `[{id, kind, title, example_id, created_at, finished_at, recorded: true, verdict, recorded_note}]` |

## Runs

| Method and path | Body | Returns |
| --- | --- | --- |
| `POST /api/runs` | `{example_id, accepted_contract_hash}`, or `{source, depth, accepted_contract_hash}` when uploads are enabled | 201 run summary. Starts asynchronously. |
| `GET /api/runs` | | `[{id, kind, example_id, title, state, created_at, parent_id, recorded, verdict}]`, newest first |
| `GET /api/runs/{id}` | | Full run state (below). Works for recorded run ids too. Poll while `state` is `queued` or `running`. |
| `POST /api/runs/{id}/cancel` | | `{cancelled: bool}` |
| `POST /api/runs/{id}/explain` | | Explanation result (below); also stored as `run.explanation`. Synchronous; can take tens of seconds. |
| `POST /api/runs/{id}/repair` | | `{started: bool, repair}`; progress appears in `run.repair` while polling. |
| `POST /api/runs/{id}/candidates` | `{source}` (uploads enabled only) | User-edited candidate checked against the unchanged contract; appears as a repair attempt with `origin: "user"`. |
| `GET /api/runs/{id}/bundle` | | Zip download of the evidence bundle. |
| `GET /api/runs/{id}/files/{path}` | | Raw artifact inside the run directory (logs, VCD, source), as text. |
| `POST /api/interpret` | `{example_id, brief?}` | Interpretation result (below). |
| `POST /api/audits` | `{check_set, depth?}` | 201 audit run summary. |
| `POST /api/check-sets/propose` | `{description, depth?}` | Model result plus `check_set` (saved unreviewed) when `status` is `ok`. Proposals may use only the reviewed templates, contract rows, and frozen-suite tests. |

### Verification run (`kind: "verification"`)

```text
{id, kind, title, example_id, origin, parent_id, depth, state: queued|running|complete|cancelled|failed,
 created_at, started_at, finished_at, recorded, recorded_note?, error?, image: {tag, image_id, verifier_digest},
 verdict: {headline: pending|counterexample|no_counterexample|unresolved|tool_error|unsupported,
           counts: {status: n}, unresolved: n},
 verification: {
   design_id, source_hash, contract_hash,
   frozen: {contract, harness: {file: hash}, verifier_digest, stimulus_version, stimulus: {test: hash}, limits, formal_tasks, expected_properties},
   stages: [{id: validating|simulating|checking_properties|replaying, status: pending|running|done|error|skipped|cancelled, started_at?, finished_at?, detail?}],
   admission: {accepted, module, parameters, ports, diagnostics: [{code, message, line, alternative}]},
   obligations: [{id, check: empty_flag|full_flag|read_data|reachability, method: simulation|bmc|prove|cover|admission,
                  status: simulation_passed|bounded_pass|proved|counterexample|unresolved|tool_error|not_checked|unsupported,
                  label, detail, depth?, step?, cycles?, tests?, log?}],
   findings: [Finding], coverage: {row_or_wrap: count}, formal_covers: {cov_label: {reached, step}},
   traces: {"sim:<test>"|"formal:bmc"|"formal:prove"|"replay": [CycleRow]},
   replay?: {status: reproduced|not_reproduced|mismatch|error|not_attempted, task, solver_step, application_cycle, detail},
   timings: {first_finding_s?, total_s}, integrity: [string], unresolved_count, batches: {...}},
 explanation?: Explanation, repair?: Repair}
```

`Finding`: `{test, source: simulation|formal, cycle, check, checks_failed, check_text, requirement_id, requirement_title, requirement_text, expected: {dout, empty, full}, observed: {dout, empty, full}, related_events: [{cycle, kind, text, row?}], note, window: {start, end}, trace, vcd, replay?}`. The cycle is the **first observed** mismatch; the governing row is the contract condition at that edge.

`CycleRow`: `{cycle, rst, wr_en, rd_en, din, row, pre_queue: [int]|null, post_queue: [int], accepted: {reset, read, write}, expected: {dout|null, empty, full}, observed: {dout, empty, full}, dout_checked, mismatches: [check], wraps: ["read"|"write"]}`. `pre_queue` is null before the first reset.

### Model results

Every model result has `{status, detail?, result, calls: [{task, model_id, endpoint_host, latency_ms, prompt_tokens, completion_tokens, attempts, status, schema_error?}]}`. `status` is one of `ok`, `ok_with_invalid_citations`, `schema_error`, `unavailable`, `input_too_large`, `error`, `not_applicable`. When the model is not configured the status is `unavailable` with a reason; never invent output.

- Interpretation `result`: `{summary, decisions: [{topic, contract, brief_says, status: matches|conflict|unspecified|unsupported, note}], backend_filled}`, plus top-level `blocking: [topic]` and `needs_decision: [topic]`.
- Explanation `result`: `{summary, steps: [{text, cycles, signals}], likely_cause: {text, lines}, next_action, limits}`, plus `citation_check: {valid, invalid: [{step, kind, value}], uncited_steps, allowed_cycles}` and `finding`.

### Repair (`run.repair`)

```text
{status: running|passed|exhausted|unavailable|error, detail?, max_attempts: 3, parent_frozen, started_at, finished_at?,
 attempts: [{index, origin: model|user, status: model_error|admission_rejected|interface_changed|verifying|passed_unchanged_checks|failed_checks|error,
             rationale?, diff?, diagnostics?, candidate_run_id?, frozen_match?, summary, calls?}]}
```

A candidate passes only when its verification has no findings, no tool errors or unresolved obligations, and its frozen check set is identical to the parent's.

### Audit run (`kind: "audit"`)

```text
{..., audit: {check_set: {id, label, origin, description, checks}, library_version, base, depth,
  stages: [...], mutants: [{fault_id, summary, category, class,
    core: {status: killed|survived|error, checks, first: {test, cycle, check}|null},
    formal: {status: counterexample|proved_equivalent|bounded_no_difference|unresolved|error|not_run},
    classification: valid_fault|equivalent|unresolved|invalid,
    supplemental: {status: killed|survived|not_applicable, by: [check id], first_cycle},
    missing_requirements: [requirement id]}],
  summary: {mutants, valid_faults, supplemental_killed, supplemental_survived, equivalent, unresolved, invalid},
  requirements: {requirement_id: {title, covered_by_set, surviving_faults: [fault_id]}}}}
```

The mutation result scores the named supplemental check set only. It is never a design-confidence score, and the mandatory core still decides every mutant's validity.
