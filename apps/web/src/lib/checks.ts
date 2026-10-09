import type { CheckGate, ChecksResult, Run } from "../api/types";

/** Presentation integrity guard: absent or inconsistent evidence never displays promotion. */
export function promotedRound(checks: ChecksResult | undefined) {
  if (checks?.status !== "promoted" || !Number.isInteger(checks.promoted_round)) return null;
  const round = checks.rounds.find(r => r.index === checks.promoted_round);
  const g = round?.gate;
  if (!round?.properties?.properties.length || !g?.passed || g.stage !== "mutants") return null;
  const counts = [g.total, g.killed, g.equivalent, g.invalid, g.unresolved, g.nonequivalent];
  if (!counts.every(n => Number.isInteger(n) && n! >= 0) || !g.nonequivalent || g.unresolved !== 0 || g.invalid !== 0) return null;
  const survivors = g.survived?.length;
  if (survivors === undefined || g.killed! + survivors !== g.nonequivalent ||
    g.nonequivalent + g.equivalent! + g.invalid! !== g.total || g.killed! / g.nonequivalent < 0.9) return null;
  return round;
}

export function checkOutcome(run: Pick<Run, "state" | "checks">): string {
  if (run.state === "running" || run.state === "queued") return "Writing and checking";
  if (run.state === "failed") return "Run failed — no promotion";
  if (run.state === "cancelled") return "Cancelled — no promotion";
  if (promotedRound(run.checks)) return "Checks promoted";
  if (run.checks?.status === "promoted") return "Promotion evidence incomplete";
  return "Checks not promoted";
}

export function gateStages(gate: CheckGate | undefined): { label: string; result: string }[] {
  const order = ["format", "compile", "integrity", "golden", "vacuity", "mutants"];
  const position = gate ? order.indexOf(gate.stage) : -1;
  const result = (at: number, failure: string) => position < 0 ? "Not established" : position > at ? "Passed" : position === at ? failure : "Not reached";
  return [
    {label:"Trusted compilation", result: result(1, "Rejected")},
    {label:"Golden proof", result: result(3, gate?.status === "FAIL" ? "Counterexample" : "Not proved")},
    {label:"Trigger reachability", result: position > 4 ? "Reached within the configured horizon" : position === 4 ? "Not reached within the configured horizon" : "Not established"},
    {label:"Mutation challenge", result: gate?.stage === "mutants" ? (gate.passed ? "Threshold met" : "Not passed") : "Not reached"},
  ];
}
