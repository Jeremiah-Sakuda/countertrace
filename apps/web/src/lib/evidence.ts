// Deterministic readings of recorded run data. Nothing here comes from a model; every value is read from the run JSON.
import type { Finding, Obligation, RelatedEvent, RepairAttempt, Run } from "../api/types";
import { bit, hex } from "./format";

/** The recorded showcase case used by the setup tour. Its numbers are always read from the API, never hardcoded. */
export const SHOWCASE_RUN_ID = "rec-20261004-003607-ver-4cc749";

/** The lead finding: the first simulation mismatch when there is one, otherwise the first finding. */
export function primaryFinding(run: Run | null | undefined): Finding | undefined {
  const findings = run?.verification?.findings ?? [];
  return findings.find((f) => f.source === "simulation") ?? findings[0];
}

export type Signal = "dout" | "empty" | "full";

export function findingSignal(finding: Finding): Signal {
  return finding.check === "empty_flag" ? "empty" : finding.check === "full_flag" ? "full" : "dout";
}

export function signalValue(finding: Finding, which: "expected" | "observed"): string {
  const signal = findingSignal(finding);
  const value = finding[which];
  return signal === "dout" ? hex(value.dout) : bit(value[signal]);
}

/**
 * A word the DUT later returned was offered at an earlier edge where the contract ignored it.
 * The backend emits this as an `observed_word_offered` related event; it is derived from the trace and the contract only.
 */
export function probableOrigin(finding: Finding | undefined): RelatedEvent | null {
  if (!finding) return null;
  return (
    finding.related_events.find((e) => e.kind === "observed_word_offered" && /contract ignored it/i.test(e.text) && e.cycle < finding.cycle) ?? null
  );
}

export function passedAttempt(run: Run | null | undefined): RepairAttempt | undefined {
  return run?.repair?.attempts.find((a) => a.status === "passed_unchanged_checks" && a.candidate_run_id && a.frozen_match !== false);
}

/** The changed lines of a unified diff (without file headers). */
export function diffChanges(diff: string | null | undefined): { added: string[]; removed: string[] } {
  const added: string[] = [];
  const removed: string[] = [];
  for (const line of (diff ?? "").split("\n")) {
    if (line.startsWith("+++") || line.startsWith("---")) continue;
    if (line.startsWith("+")) added.push(line.slice(1).trim());
    else if (line.startsWith("-")) removed.push(line.slice(1).trim());
  }
  return { added, removed };
}

export function countStatus(obligations: Obligation[] | undefined, status: Obligation["status"]): number {
  return (obligations ?? []).filter((o) => o.status === status).length;
}

/** True when every obligation has a non-failing, resolved result (the backend's candidate-pass rule, read back). */
export function allResolvedWithoutFinding(run: Run | null | undefined): boolean {
  const v = run?.verification;
  if (!v || v.obligations.length === 0) return false;
  if (v.findings.length > 0) return false;
  return v.obligations.every((o) => ["proved", "bounded_pass", "simulation_passed"].includes(o.status));
}

export const ORIGIN_LABELS: Record<string, string> = {
  bundled_example: "Bundled example",
  model_repair: "Repair candidate",
  evaluation: "Evaluation suite",
  local_file: "Local file",
  user_upload: "Uploaded RTL",
  user_edit: "Your edit",
};

export function originLabel(origin: string | null | undefined): string | null {
  if (!origin) return null;
  return ORIGIN_LABELS[origin] ?? origin.replace(/_/g, " ");
}
