// Types for the Countertrace control-service API. Source of truth: docs/API.md.
// Fields the backend may omit are optional; unknown extras are tolerated.

export type Iso = string;

// ---- Status ----------------------------------------------------------------
export interface Spend {
  calls: number;
  prompt_tokens: number;
  completion_tokens: number;
  estimated_cost_usd: number | null;
  cost_status: string;
  spend_limit_usd: number | null;
}

export interface Status {
  version: string;
  verifier: {
    docker: boolean;
    docker_detail: string | null;
    image_tag: string | null;
    image_built: boolean;
    network: string;
    resources: Record<string, string>;
    limits: Record<string, number>;
  };
  model: {
    configured: boolean;
    reason: string | null;
    model_id: string | null;
    repair_model_id: string | null;
    /** Faster model used for brief interpretation and check-set proposals. */
    fast_model_id?: string | null;
    endpoint_host: string | null;
    input_token_limit: number | null;
    output_token_limit: number | null;
    spend: Spend;
  };
  uploads_enabled: boolean;
  data_notice: string;
}

// ---- Contract and profile --------------------------------------------------
export interface PortSpec {
  direction: "input" | "output" | string;
  width: number | string;
}

export interface Requirement {
  title: string;
  text: string;
}

export interface Contract {
  profile: string;
  version: string;
  parameters: { DEPTH: number; WIDTH: number } & Record<string, number>;
  ports: Record<string, PortSpec>;
  requirements: Record<string, Requirement>;
  checks: Record<string, string>;
  assumptions: string[];
  sampling: string;
}

export interface TimingEdge {
  cycle: number;
  pre: string[] | null;
  rst: number;
  wr_en: number;
  rd_en: number;
  din: string;
  row: string;
  accepted: string;
  post: string[];
  dout: string | null;
  empty: number;
  full: number;
  wraps?: string[];
}

export interface TimingExample {
  id: string;
  source: string;
  parameters: Record<string, number>;
  symbols: Record<string, number>;
  edges: TimingEdge[];
}

export interface Profile {
  supported_depths: number[];
  contract: Contract;
  timing_example: TimingExample;
}

// ---- Examples ----------------------------------------------------------------
export interface Fault {
  id: string;
  summary: string;
  category: string;
  class: string;
  intended_consequence: string;
}

export interface Example {
  id: string;
  split: "showcase" | "development";
  title: string;
  depth: number;
  brief: string;
  expected: "correct" | "faulty";
  base: string;
  fault: Fault | null;
}

export interface ExampleDetail extends Example {
  source: string;
  contract: Contract;
  contract_hash: string;
}

// ---- Check sets and recorded runs -----------------------------------------
export interface CheckSetCheck {
  id: string;
  check: string;
  rows: string[] | null;
  requirement: string;
  text: string;
}

export interface CheckSet {
  id: string;
  label: string;
  origin: string;
  description: string;
  /** false marks a model-proposed candidate that no person has reviewed. */
  reviewed?: boolean;
  /** Frozen-suite tests the set observes; null means all tests. */
  tests?: string[] | null;
  checks: CheckSetCheck[];
}

export type VerdictHeadline =
  | "pending"
  | "counterexample"
  | "no_counterexample"
  | "unresolved"
  | "tool_error"
  | "unsupported";

export interface Verdict {
  headline: VerdictHeadline;
  counts: Partial<Record<ObligationStatus, number>>;
  unresolved: number;
}

export interface RecordedRunSummary {
  id: string;
  kind: RunKind;
  title: string;
  example_id: string | null;
  created_at: Iso;
  finished_at: Iso | null;
  recorded: true;
  verdict: Verdict | null;
  recorded_note?: string;
}

// ---- Runs ----------------------------------------------------------------------
export type RunKind = "verification" | "audit";
export type RunState = "queued" | "running" | "complete" | "cancelled" | "failed";

export interface RunSummary {
  id: string;
  kind: RunKind;
  example_id: string | null;
  title: string;
  state: RunState;
  created_at: Iso;
  parent_id: string | null;
  recorded: boolean;
  verdict: Verdict | null;
  /** bundled_example | model_repair | evaluation | local_file | … (absent on older servers and audits). */
  origin?: string | null;
  depth?: number | null;
}

export type StageId = "validating" | "simulating" | "checking_properties" | "replaying" | string;
export type StageStatus = "pending" | "running" | "done" | "error" | "skipped" | "cancelled";

export interface Stage {
  id: StageId;
  status: StageStatus;
  started_at?: Iso;
  finished_at?: Iso;
  detail?: string;
}

export interface AdmissionDiagnostic {
  code: string;
  message: string;
  line: number | null;
  alternative: string | null;
}

export interface Admission {
  accepted: boolean;
  module: string | null;
  parameters: string[];
  ports: Record<string, { direction: string; range: string | null }>;
  diagnostics: AdmissionDiagnostic[];
}

export type ObligationStatus =
  | "simulation_passed"
  | "bounded_pass"
  | "proved"
  | "counterexample"
  | "unresolved"
  | "tool_error"
  | "not_checked"
  | "unsupported";

export type ObligationMethod = "simulation" | "bmc" | "prove" | "cover" | "admission";

export interface Obligation {
  id: string;
  check: string;
  method: ObligationMethod;
  status: ObligationStatus;
  label: string;
  detail: string | null;
  depth?: number;
  step?: number;
  cycles?: number;
  tests?: string[];
  log?: string | null;
}

export interface Flags {
  dout: number | null;
  empty: boolean;
  full: boolean;
}

export interface RelatedEvent {
  cycle: number;
  kind: string;
  text: string;
  row?: string;
}

export type ReplayStatus = "reproduced" | "not_reproduced" | "mismatch" | "error" | "not_attempted";

export interface Replay {
  status: ReplayStatus;
  task: string | null;
  solver_step: number | null;
  application_cycle: number | null;
  detail: string | null;
}

export interface Finding {
  test: string;
  source: "simulation" | "formal";
  cycle: number;
  check: string;
  checks_failed: string[];
  check_text: string;
  requirement_id: string;
  requirement_title: string;
  requirement_text: string;
  expected: Flags;
  observed: Flags;
  related_events: RelatedEvent[];
  note: string;
  window: { start: number; end: number };
  trace: string;
  vcd: string | null;
  replay?: Replay;
}

export interface CycleRow {
  cycle: number;
  rst: number;
  wr_en: number;
  rd_en: number;
  din: number;
  row: string;
  pre_queue: number[] | null;
  post_queue: number[];
  accepted: { reset: boolean; read: boolean; write: boolean };
  expected: { dout: number | null; empty: boolean; full: boolean };
  observed: { dout: number | null; empty: boolean; full: boolean };
  dout_checked: boolean;
  mismatches: string[];
  wraps: string[];
}

export interface BatchStep {
  id: string;
  argv: string[];
  timeout_s: number;
  returncode: number | null;
  timed_out: boolean;
  duration_s: number | null;
  log?: string | null;
  log_truncated?: boolean;
}

export interface Batch {
  argv?: string[];
  container_returncode?: number | null;
  wall_s?: number | null;
  cancelled?: boolean;
  timed_out?: boolean;
  image?: RunImage;
  resources?: Record<string, string>;
  network?: string;
  out_dir?: string;
  tool_versions?: Record<string, string>;
  steps?: BatchStep[];
}

export interface Frozen {
  contract: string;
  harness: Record<string, string>;
  verifier_digest: string;
  stimulus_version: string;
  stimulus: Record<string, string>;
  limits: Record<string, number>;
  formal_tasks: string[];
  expected_properties: Record<string, number>;
}

export interface Verification {
  design_id: string;
  source_hash: string;
  contract_hash: string;
  frozen?: Frozen;
  stages: Stage[];
  admission?: Admission;
  obligations: Obligation[];
  findings: Finding[];
  coverage?: Record<string, number>;
  formal_covers?: Record<string, { reached: boolean; step: number | null }>;
  traces?: Record<string, CycleRow[]>;
  replay?: Replay;
  timings?: { first_finding_s?: number | null; total_s?: number | null };
  integrity?: string[];
  integrity_checked?: string[];
  unresolved_count?: number;
  batches?: Record<string, Batch>;
}

export interface RunImage {
  tag: string;
  image_id: string;
  verifier_digest: string;
}

// ---- Model results --------------------------------------------------------------
export type ModelStatus =
  | "ok"
  | "ok_with_invalid_citations"
  | "schema_error"
  | "unavailable"
  | "input_too_large"
  | "error"
  | "not_applicable";

export interface ModelCall {
  task: string;
  model_id: string | null;
  endpoint_host: string | null;
  latency_ms: number | null;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  attempts: number | null;
  status: string;
  schema_error?: string | null;
}

export interface ModelResult<R> {
  status: ModelStatus;
  detail?: string | null;
  result: R | null;
  calls: ModelCall[];
}

export type DecisionStatus = "matches" | "conflict" | "unspecified" | "unsupported";

export interface Decision {
  topic: string;
  contract: string;
  brief_says: string;
  status: DecisionStatus;
  note: string;
}

export interface InterpretationResult {
  summary: string;
  decisions: Decision[];
  backend_filled?: unknown;
}

export interface Interpretation extends ModelResult<InterpretationResult> {
  blocking?: string[];
  needs_decision?: string[];
}

export interface ExplanationStep {
  text: string;
  cycles: number[];
  signals: string[];
}

export interface ExplanationResult {
  summary: string;
  steps: ExplanationStep[];
  likely_cause: { text: string; lines: number[] };
  next_action: string;
  limits: string;
}

export interface CitationCheck {
  valid: number;
  invalid: { step: number | null; kind: string; value: unknown }[];
  uncited_steps: number;
  allowed_cycles: [number, number] | null;
}

export interface Explanation extends ModelResult<ExplanationResult> {
  citation_check?: CitationCheck;
  finding?: Partial<Finding> | null;
}

// ---- Repair ---------------------------------------------------------------------
export type RepairStatus = "running" | "passed" | "exhausted" | "unavailable" | "error";
export type AttemptStatus =
  | "model_error"
  | "admission_rejected"
  | "interface_changed"
  | "verifying"
  | "passed_unchanged_checks"
  | "failed_checks"
  | "error";

export interface RepairAttempt {
  index: number;
  origin: "model" | "user";
  status: AttemptStatus;
  rationale?: string | null;
  diff?: string | null;
  diagnostics?: unknown;
  candidate_run_id?: string | null;
  frozen_match?: boolean | null;
  summary: string;
  calls?: ModelCall[];
}

export interface Repair {
  status: RepairStatus;
  detail?: string | null;
  max_attempts: number;
  parent_frozen?: unknown;
  started_at?: Iso;
  finished_at?: Iso | null;
  attempts: RepairAttempt[];
}

// ---- Audit ----------------------------------------------------------------------
export type MutantClassification = "valid_fault" | "equivalent" | "unresolved" | "invalid" | "baseline_clean" | (string & {});

export interface Mutant {
  fault_id: string;
  summary: string;
  category: string;
  class: string;
  core: {
    status: "killed" | "survived" | "error";
    checks: string[];
    first: { test: string; cycle: number; check: string; requirement_id?: string } | null;
    errors?: string[];
  };
  formal: {
    status: "counterexample" | "proved_equivalent" | "bounded_no_difference" | "unresolved" | "error" | "not_run";
  };
  classification: MutantClassification;
  supplemental: {
    status: "killed" | "survived" | "not_applicable";
    by: string[];
    first_cycle: number | null;
  };
  missing_requirements: string[];
  target_requirement?: string | null;
  note?: string | null;
}

export interface Audit {
  check_set: CheckSet;
  library_version: string;
  base: string;
  depth: number;
  stages: Stage[];
  mutants: Mutant[];
  summary: {
    mutants: number;
    valid_faults: number;
    supplemental_killed: number;
    supplemental_survived: number;
    equivalent: number;
    unresolved: number;
    invalid: number;
    note?: string;
  };
  contract_hash?: string;
  stimulus?: string[];
  tool_versions?: Record<string, string>;
  baseline?: string;
  requirements: Record<string, AuditRequirement>;
  set_tests?: string[] | null;
  set_rows_exercised?: string[] | null;
}

export interface AuditRequirement {
  title: string;
  covered_by_set: boolean;
  exercised_by_set?: boolean;
  checks?: string[];
  surviving_faults: string[];
}

// ---- Full run --------------------------------------------------------------------
export interface Run {
  id: string;
  kind: RunKind;
  title: string;
  example_id: string | null;
  origin?: string;
  parent_id: string | null;
  depth?: number;
  state: RunState;
  created_at: Iso;
  started_at?: Iso | null;
  finished_at?: Iso | null;
  recorded: boolean;
  recorded_note?: string;
  error?: string | null;
  image?: RunImage;
  verdict?: Verdict | null;
  verification?: Verification;
  audit?: Audit;
  explanation?: Explanation;
  repair?: Repair;
}

export interface CheckSetProposal extends ModelResult<unknown> {
  check_set?: CheckSet;
}

export interface RepairStartResponse {
  started: boolean;
  repair: Repair | null;
}
