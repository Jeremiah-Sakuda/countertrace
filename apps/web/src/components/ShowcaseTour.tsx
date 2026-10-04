import { ArrowRight, History } from "lucide-react";
import { api } from "../api/client";
import type { Profile, RecordedRunSummary, Run } from "../api/types";
import { allResolvedWithoutFinding, countStatus, diffChanges, findingSignal, passedAttempt, primaryFinding, probableOrigin, SHOWCASE_RUN_ID, signalValue } from "../lib/evidence";
import { formatDate } from "../lib/format";
import { useAsync, type AsyncState } from "../lib/hooks";
import { href } from "../lib/route";

/** "nvidia/Nemotron-3-Ultra-550b-a55b" -> "Nemotron 3 Ultra". */
export function shortModelName(id: string | null | undefined): string {
  if (!id) return "Nemotron";
  const tokens = (id.split("/").pop() ?? id).split("-");
  const kept: string[] = [];
  for (const t of tokens) {
    if (/^a?\d+(\.\d+)?b$/i.test(t)) break;
    kept.push(t.charAt(0).toUpperCase() + t.slice(1));
  }
  return kept.join(" ") || id;
}

/** "wire do_write = wr_en && !full;" -> { target: "do_write", expr: "wr_en && !full" } */
function changedExpression(line: string | undefined): { target: string | null; expr: string } | null {
  if (!line) return null;
  const m = /(?:assign|wire|reg)?\s*(?:\[[^\]]*\]\s*)?(\w+)\s*<?=\s*(.+?);?\s*$/.exec(line);
  return m ? { target: m[1] ?? null, expr: (m[2] ?? line).trim() } : { target: null, expr: line };
}

interface TourData {
  run: Run;
  candidate: Run | null;
}

async function loadTour(): Promise<TourData | null> {
  let id = SHOWCASE_RUN_ID;
  let run: Run;
  try {
    run = await api.run(id);
  } catch {
    // Fall back to the first recorded counterexample when this build ships a different showcase.
    const recorded: RecordedRunSummary[] = await api.recorded();
    const pick = recorded.find((r) => r.kind === "verification" && r.verdict?.headline === "counterexample");
    if (!pick) return null;
    id = pick.id;
    run = await api.run(id);
  }
  const attempt = passedAttempt(run);
  let candidate: Run | null = null;
  if (attempt?.candidate_run_id) {
    try {
      candidate = await api.run(attempt.candidate_run_id);
    } catch {
      candidate = null;
    }
  }
  return { run, candidate };
}

function TourSteps({ data, profile }: { data: TourData; profile: AsyncState<Profile> }) {
  const { run, candidate } = data;
  const finding = primaryFinding(run);
  const origin = probableOrigin(finding);
  const requirements = profile.status === "ok" ? profile.data.contract.requirements : undefined;
  const explanation = run.explanation?.result ? run.explanation : null;
  const check = explanation?.citation_check;
  const cycles = [...new Set((explanation?.result?.steps ?? []).flatMap((s) => s.cycles))].sort((a, b) => a - b);
  const attempt = passedAttempt(run);
  const change = diffChanges(attempt?.diff);
  const expr = changedExpression(change.added[0]);
  const candidateOk = allResolvedWithoutFinding(candidate);
  const proofs = countStatus(candidate?.verification?.obligations, "proved");
  const total = candidate?.verification?.obligations.length ?? 0;

  return (
    <ol className="tour-steps">
      <li>
        <span className="tour-step-label"><span aria-hidden="true">01</span> It breaks</span>
        {finding ? (
          <>
            <strong className="tour-step-value">
              Cycle {finding.cycle}: expected <span className="mono">{signalValue(finding, "expected")}</span>, observed{" "}
              <span className="mono tour-bad">{signalValue(finding, "observed")}</span>
            </strong>
            <p>
              First <code>{findingSignal(finding)}</code> mismatch in simulation test <code>{finding.test}</code>.
              {origin ? ` The word came from cycle ${origin.cycle}, where the contract ignored a ${(requirements?.[origin.row ?? ""]?.title ?? origin.row ?? "write").toLowerCase()}.` : ""}
            </p>
          </>
        ) : (
          <p>No counterexample is recorded in this run.</p>
        )}
      </li>
      <li>
        <span className="tour-step-label"><span aria-hidden="true">02</span> Nemotron explains why</span>
        {explanation?.result ? (
          <>
            <strong className="tour-step-value">
              {explanation.result.steps.length} cited steps{cycles.length ? `, cycles ${cycles.join(" and ")}` : ""}
            </strong>
            <p>
              {shortModelName(explanation.calls[0]?.model_id)} wrote the explanation. {check ? `${check.valid} citations checked against the recorded trace${check.invalid.length ? `, ${check.invalid.length} flagged` : ", none invalid"}.` : ""}
            </p>
          </>
        ) : (
          <p>No explanation was recorded with this run.</p>
        )}
      </li>
      <li>
        <span className="tour-step-label"><span aria-hidden="true">03</span> The fix is checked, not trusted</span>
        {attempt && expr ? (
          <>
            <strong className="tour-step-value">
              <code className="tour-code">{expr.expr}</code>
            </strong>
            <p>
              {change.added.length === 1 && change.removed.length <= 1 ? "A one-line edit" : `An edit of ${change.added.length} lines`}
              {expr.target ? <> to <code>{expr.target}</code></> : null}.{" "}
              {candidate && candidateOk
                ? `Candidate ${attempt.index} passed all ${total} unchanged obligations, ${proofs} of them unbounded proofs.`
                : "The candidate was checked against the unchanged contract and checks."}
            </p>
          </>
        ) : (
          <p>No repair candidate passed in this recording.</p>
        )}
      </li>
    </ol>
  );
}

/** A compact three-step tour of the recorded showcase. Every number comes from the API. */
export function ShowcaseTour({ profile }: { profile: AsyncState<Profile> }) {
  const tour = useAsync(loadTour, []);
  const target = tour.status === "ok" && tour.data ? tour.data.run.id : SHOWCASE_RUN_ID;
  return (
    <section className="tour" aria-labelledby="tour-title">
      <div className="tour-head">
        <p className="eyebrow">
          <History size={13} aria-hidden="true" /> 60-second tour · a recorded case
        </p>
        <h2 id="tour-title" className="tour-title">
          {tour.status === "ok" && tour.data ? tour.data.run.title : "The recorded showcase"}
        </h2>
      </div>
      {tour.status === "loading" && <p className="muted small" role="status">Loading the recorded showcase…</p>}
      {tour.status === "error" && <p className="muted small">The recorded showcase could not be loaded. You can still browse the runs.</p>}
      {tour.status === "ok" && tour.data && <TourSteps data={tour.data} profile={profile} />}
      {tour.status === "ok" && !tour.data && <p className="muted small">No recorded counterexample ships with this build.</p>}
      <div className="tour-actions">
        <a className="btn btn-primary" href={tour.status === "ok" && !tour.data ? href.runs() : href.run(target)}>
          {tour.status === "ok" && !tour.data ? "Browse the runs" : "Open the showcase run"} <ArrowRight size={16} aria-hidden="true" />
        </a>
        {tour.status === "ok" && tour.data && (
          <span className="muted small">
            Recorded {formatDate(tour.data.run.created_at)} · read-only, no model calls
          </span>
        )}
      </div>
    </section>
  );
}
