import { ArrowLeft, Ban, CircleHelp, History, LoaderCircle, ScanSearch, Server } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { api, ApiError } from "../../api/client";
import type { Finding, Profile, Run, Status } from "../../api/types";
import { Callout, Disclosure, ErrorNotice, Loading, Section } from "../../components/common";
import type { FocusRequest } from "../../components/CycleTable";
import type { RunContextInfo } from "../../components/Header";
import { Badge, ObligationBadge, VerdictBadge } from "../../components/StatusBadge";
import { countStatus, findingSignal, primaryFinding, probableOrigin, signalValue } from "../../lib/evidence";
import { elapsedSeconds, formatDateTime, formatDuration, METHOD_LABELS, STAGE_LABELS } from "../../lib/format";
import { useAsync, useDocumentTitle, useNow, usePolling, type AsyncState } from "../../lib/hooks";
import { href } from "../../lib/route";
import { AuditResult } from "../AuditView";
import { CandidatePanel, RepairPayoff } from "./CandidatePanel";
import { EvidencePanel } from "./EvidencePanel";
import { ExplanationPanel } from "./ExplanationPanel";
import { FindingPanel, FormalFindingPanel } from "./FindingPanel";
import { ObligationsPanel } from "./ObligationsPanel";
import { RepairPanel } from "./RepairPanel";
import { StagesPanel } from "./StagesPanel";

export function isActive(run: Run): boolean {
  return run.state === "queued" || run.state === "running" || run.repair?.status === "running";
}

/**
 * A short cause for the unresolved count, read from the obligations themselves: only when the run has a counterexample and every
 * unresolved obligation records that the solver stopped at another property's counterexample.
 */
function unresolvedReason(run: Run): string | null {
  const v = run.verification;
  if (!v || v.findings.length === 0) return null;
  const open = v.obligations.filter((o) => o.status === "unresolved");
  if (open.length === 0) return null;
  return open.every((o) => /stopped at another property'?s counterexample/i.test(o.detail ?? "")) ? "solver stopped at the first counterexample" : null;
}

/**
 * A neutral note after the title and finding: how many obligations stayed open, and why when the run records it.
 * Unresolved obligations establish nothing either way; they are not a second failure.
 */
function UnresolvedNote({ run }: { run: Run }) {
  if (run.kind !== "verification" || run.state !== "complete") return null;
  const count = run.verdict?.unresolved ?? run.verification?.unresolved_count ?? 0;
  if (!count) return null;
  const reason = unresolvedReason(run);
  return (
    <p className="unresolved-note">
      <CircleHelp size={16} aria-hidden="true" />
      <span>
        <strong>
          {count} obligation{count === 1 ? "" : "s"} left unresolved
        </strong>
        {reason ? `: the ${reason}, so ${count === 1 ? "it was" : "they were"} not established either way.` : ": not established either way."}{" "}
        Open, not a second failure. <span className="muted">An obligation is one check by one method.</span>
      </span>
    </p>
  );
}

/** The payoff of a complete run without a finding: proofs, counterexamples, and, for a repair candidate, whether the frozen hashes match. */
function PassingFocus({ run }: { run: Run }) {
  const obligations = run.verification?.obligations ?? [];
  const findings = run.verification?.findings.length ?? 0;
  const proved = countStatus(obligations, "proved");
  const unresolved = run.verdict?.unresolved ?? run.verification?.unresolved_count ?? 0;
  const parentId = run.parent_id ?? null;
  const parent = useAsync(() => (parentId ? api.run(parentId) : Promise.resolve(null)), [parentId]);
  const attempt = parent.status === "ok" ? parent.data?.repair?.attempts.find((a) => a.candidate_run_id === run.id) : undefined;
  const frozen = attempt?.frozen_match;
  const parts = [`${proved} proved`, `${findings} counterexample${findings === 1 ? "" : "s"}`];
  if (parentId && frozen === true) parts.push("frozen hashes match");
  else if (parentId && frozen === false) parts.push("frozen hashes differ");
  else if (!parentId) parts.push(`${unresolved} unresolved`);
  return (
    <>
      <span className="eyebrow">{parentId ? "Repair candidate result" : "Result at a glance"}</span>
      <div className="case-focus-number">{proved}<span>proved</span></div>
      <p className="case-payoff">{parts.join(" · ")}</p>
      <p className="case-focus-source">of {obligations.length} obligations · DEPTH {run.depth ?? "—"} · WIDTH 8</p>
    </>
  );
}

function announcement(run: Run): string {
  const stages = run.verification?.stages ?? run.audit?.stages ?? [];
  const runningStages = stages.filter((s) => s.status === "running").map((s) => STAGE_LABELS[s.id] ?? s.id);
  if (run.state === "queued") return "Run queued.";
  if (run.state === "running") return `Run in progress${runningStages.length ? `: ${runningStages.join(", ")}` : ""}.`;
  if (run.state === "cancelled") return "Run cancelled.";
  if (run.state === "failed") return `Run failed${run.error ? `: ${run.error}` : ""}.`;
  const headline = run.verdict?.headline;
  if (headline === "counterexample") return "Run complete: counterexample found.";
  if (headline === "no_counterexample") return "Run complete: no counterexample found by these methods.";
  if (headline) return `Run complete: ${headline.replace(/_/g, " ")}.`;
  return "Run complete.";
}

function RunHeader({ run, now, onCancel, cancelling, cancelError }: { run: Run; now: number; onCancel: () => void; cancelling: boolean; cancelError: unknown }) {
  const active = run.state === "queued" || run.state === "running";
  const total = elapsedSeconds(run.started_at ?? run.created_at, run.finished_at, now);
  const t = run.verification?.timings;
  const finding = primaryFinding(run);
  const origin = probableOrigin(finding);
  const obligations = run.verification?.obligations ?? [];
  const signal = finding ? findingSignal(finding) : "dout";
  const audit = run.kind === "audit" && run.state === "complete" ? run.audit?.summary : undefined;
  const passing = run.kind === "verification" && !finding && run.state === "complete" && run.verdict?.headline === "no_counterexample";
  return (
    <div className="run-header">
      <div className="case-masthead">
        <a href={href.runs()} className="inline-link"><ArrowLeft size={14} aria-hidden="true" /> Evidence library</a>
        <span>{run.kind === "audit" ? "Check-quality audit" : "Verification notebook"}</span>
      </div>
      <div className="case-hero">
        <div className="case-title">
          <p className="eyebrow">{run.recorded ? "From the recorded collection" : "Run on this server"}</p>
          <h1>{run.title}</h1>
          <div className="run-badges">
            <Badge tone="neutral" icon={run.recorded ? History : Server}>{run.recorded ? "Recorded run" : "Run on this server"}</Badge>
            {run.kind === "verification" && <VerdictBadge headline={active ? "pending" : run.verdict?.headline ?? (run.state === "failed" ? "tool_error" : "unresolved")} />}
          </div>
          <p className="case-caption">
            {audit
              ? "Seeded faults the mandatory core confirms as real bugs, scored against one named supplemental check set."
              : finding
                ? "A requirement failed. Trace the sequence, inspect the cause, and follow the repair evidence."
                : run.parent_id
                  ? "A repair candidate, re-run against its parent's frozen contract and checks."
                  : "Every result has a method, a set of assumptions, and evidence you can inspect."}
          </p>
          {run.kind === "verification" && <RepairPayoff run={run} />}
        </div>
        {audit && (
          <aside className="case-focus case-focus-failure" aria-label="Audit result at a glance">
            <span className="eyebrow">Audit result · valid seeded faults</span>
            <div className="case-focus-number">{audit.supplemental_survived}<span>of {audit.valid_faults} valid faults</span></div>
            <p className="audit-headline">
              {audit.supplemental_survived} of {audit.valid_faults} real bugs slip past this check set
            </p>
            <p className="case-focus-source">{audit.supplemental_killed} caught · {audit.equivalent} equivalent, {audit.unresolved} unresolved, {audit.invalid} invalid excluded</p>
          </aside>
        )}
        {passing && <aside className="case-focus case-focus-pass" aria-label="Run at a glance"><PassingFocus run={run} /></aside>}
        {run.kind === "verification" && !passing && <aside className={`case-focus ${finding ? "case-focus-failure" : ""}`} aria-label="Run at a glance">
          <span className="eyebrow">{finding ? (finding.source === "simulation" ? `First mismatch in simulation test ${finding.test}` : "Shortest formal counterexample") : active ? "In progress" : "Check obligations"}</span>
          <div className="case-focus-number">{finding ? String(finding.cycle).padStart(2, "0") : active ? "…" : obligations.length}<span>{finding ? "cycle" : active ? "running" : "checks"}</span></div>
          {finding ? <div className="case-signal">
            <span><small>Expected {signal}</small><strong>{signalValue(finding, "expected")}</strong></span>
            <span aria-hidden="true" className="case-signal-arrow">→</span>
            <span><small>Observed</small><strong>{signalValue(finding, "observed")}</strong></span>
          </div> : <p className="small">{active && total !== null ? `Elapsed ${formatDuration(total)}. ` : ""}Results below keep simulation, bounded checks, and proof distinct.</p>}
          {origin && <p className="case-origin small">Probable origin: <strong>cycle {origin.cycle}</strong>, derived from the trace</p>}
          <p className="case-focus-source">{finding ? `${finding.source} / ${finding.test}` : `DEPTH ${run.depth ?? "—"} · WIDTH 8`}</p>
        </aside>}
      </div>
      <UnresolvedNote run={run} />
      {!!run.evidence_corrections?.length && <p className="callout-inline">Simulation summaries were corrected from the preserved traces. Original execution timings and model responses are retained; details are in run provenance.</p>}
      <div className="case-facts">
        <span><small>Configuration</small><strong>{run.depth ? `Depth ${run.depth} · 8-bit` : "Supplemental-check audit"}</strong></span>
        <span><small>{run.recorded ? "Recorded" : "Created"}</small><strong>{formatDateTime(run.created_at)}</strong></span>
        {active ? (
          <span><small>Elapsed</small><strong aria-live="off">{total === null ? "—" : formatDuration(total)}</strong></span>
        ) : (
          <span><small>{t?.first_finding_s != null ? "First finding" : "Elapsed verification"}</small><strong>{t?.first_finding_s != null ? formatDuration(t.first_finding_s) : total === null ? "—" : formatDuration(total)}</strong></span>
        )}
        <span><small>Run state</small><strong>{run.state}</strong></span>
      </div>
      <Disclosure summary="Run provenance & original timings" className="case-provenance">
        <p className="mono small wrap-anywhere">{run.id}</p>
        {run.recorded_note && <p className="small muted">{run.recorded_note}</p>}
        <p className="run-timing small">{run.started_at ? `Started ${formatDateTime(run.started_at)}` : "Not started"}{run.finished_at ? ` · finished ${formatDateTime(run.finished_at)}` : ""}{total !== null ? ` · ${active ? "elapsed" : "took"} ${formatDuration(total)}` : ""}{run.image ? ` · verifier ${run.image.tag}` : ""}</p>
      </Disclosure>
      {active && !run.recorded && <button type="button" className="btn btn-danger btn-sm" onClick={onCancel} disabled={cancelling} aria-busy={cancelling}>{cancelling ? <LoaderCircle className="spin" size={14} aria-hidden="true" /> : <Ban size={14} aria-hidden="true" />} Cancel run</button>}
      {run.state === "cancelled" && <Callout kind="warn" title="Run cancelled"><p>A cancelled run establishes nothing. Unfinished obligations remain unresolved.</p></Callout>}
      {run.state === "failed" && <Callout kind="error" title="Run failed" role="alert"><p>{run.error || "The run ended with an error. No result is claimed."}</p></Callout>}
      {cancelError ? <ErrorNotice error={cancelError} title="Cancel request failed" /> : null}
    </div>
  );
}

function NoCounterexample({ run }: { run: Run }) {
  const obligations = run.verification?.obligations ?? [];
  const methods = ["simulation", "bmc", "prove", "cover"] as const;
  const unresolved = run.verdict?.unresolved ?? run.verification?.unresolved_count ?? 0;
  return (
    <Section id="run-finding" title="No counterexample found by these methods" eyebrow="Result" className="no-cex">
      <p className="prose">
        None of the methods below produced a failing trace. That is not a statement that the design is correct: each method establishes
        only what its label says, for DEPTH {run.depth ?? "?"} and the listed assumptions.
      </p>
      <ul className="method-summary">
        {methods.map((m) => {
          const items = obligations.filter((o) => o.method === m);
          if (items.length === 0) return null;
          const statuses = [...new Set(items.map((o) => o.status))];
          return (
            <li key={m}>
              <span className="method-name">{METHOD_LABELS[m]}</span>
              <span className="method-statuses">
                {statuses.map((s) => {
                  const sample = items.find((o) => o.status === s);
                  const count = items.filter((o) => o.status === s).length;
                  return (
                    <span key={s} className="method-status">
                      <ObligationBadge status={s} label={sample?.label} />
                      <span className="muted small">
                        {count} of {items.length}
                      </span>
                    </span>
                  );
                })}
              </span>
            </li>
          );
        })}
      </ul>
      <p className={unresolved ? "warn-text" : "muted"}>
        {unresolved ? `${unresolved} obligation${unresolved === 1 ? " remains" : "s remain"} unresolved; see below.` : "No obligations are unresolved."}
      </p>
    </Section>
  );
}

function VerificationBody({
  run,
  profile,
  status,
  now,
  refresh,
}: {
  run: Run;
  profile: AsyncState<Profile>;
  status: AsyncState<Status>;
  now: number;
  refresh: () => void;
}) {
  const v = run.verification;
  const [focus, setFocus] = useState<FocusRequest | null>(null);
  const onCite = useCallback(
    (cycle: number, origin?: { element: HTMLElement; label: string }) =>
      setFocus((f) => ({ cycle, nonce: (f?.nonce ?? 0) + 1, returnTo: origin?.element ?? null, returnLabel: origin?.label })),
    [],
  );
  const requirements = profile.status === "ok" ? profile.data.contract.requirements : undefined;
  const checks = profile.status === "ok" ? profile.data.contract.checks : undefined;
  const findings = v?.findings ?? [];
  const primary: Finding | undefined = useMemo(() => findings.find((f) => f.source === "simulation") ?? findings[0], [findings]);
  const formalOthers = findings.filter((f) => f !== primary && f.source === "formal");
  const others = findings.filter((f) => f !== primary);
  const depth = run.depth ?? 4;
  const active = run.state === "queued" || run.state === "running";
  const sections = [
    ...(run.parent_id ? [{ id: "run-candidate", label: "What the repair changed" }] : []),
    { id: "run-finding", label: primary ? "Finding & trace" : "Result" },
    ...(primary || run.explanation ? [{ id: "run-explanation", label: "Explanation" }] : []),
    { id: "run-repair", label: primary || run.repair || run.state !== "complete" ? "Repair & export" : "Export" },
    { id: "run-obligations", label: "Check results" },
    { id: "run-evidence", label: "Evidence" },
  ];
  const goToSection = (id: string) => {
    const heading = document.getElementById(id);
    if (!heading) return;
    heading.focus({ preventScroll: true });
    heading.scrollIntoView({ block: "start", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  };

  return (
    <div className="stack-lg">
      <nav className="run-sections" aria-label="On this run">
        <span className="run-sections-label">Explore the evidence</span>
        <ul>
          {sections.filter((section) => section.id !== "run-finding" || primary || run.state === "complete").map((section) => (
            <li key={section.id}>
              <button type="button" onClick={() => goToSection(section.id)}>{section.label}<span aria-hidden="true">↘</span></button>
            </li>
          ))}
        </ul>
      </nav>
      {active && (
        <Section title="Stages" eyebrow="Live status">
          <StagesPanel stages={v?.stages ?? []} now={now} />
          {primary && <p className="muted small">The first finding is shown below while later obligations continue.</p>}
        </Section>
      )}

      {run.parent_id && <CandidatePanel run={run} />}

      {primary ? (
        <FindingPanel runId={run.id} finding={primary} traces={v?.traces} requirements={requirements} depth={depth} focusRequest={focus} onCite={onCite} otherFormal={formalOthers} />
      ) : run.state === "complete" && run.verdict?.headline === "no_counterexample" ? (
        <NoCounterexample run={run} />
      ) : run.state === "complete" ? (
        <Section id="run-finding" title={run.verdict?.headline === "tool_error" ? "Tool error: no result established" : "No finding to show"} eyebrow="Result">
          <p className="prose">
            {run.verdict?.headline === "tool_error"
              ? "The tools or artifact integrity checks failed, so nothing was established by the affected methods. A tool error is never treated as a pass. See the integrity notes and logs below."
              : "No counterexample trace was recorded. See the obligations below for what each method established."}
          </p>
        </Section>
      ) : active ? (
        <Section title="Waiting for the first finding" eyebrow="Live">
          <p className="muted">
            <ScanSearch size={16} aria-hidden="true" /> No counterexample yet. Results appear here as soon as a method records one.
          </p>
        </Section>
      ) : null}

      {others.map((f, i) => (
        <FormalFindingPanel key={`${f.test}-${i}`} runId={run.id} finding={f} traces={v?.traces} requirements={requirements} depth={depth} lead={primary} />
      ))}

      {(primary || run.explanation) && <ExplanationPanel run={run} hasFinding={Boolean(primary)} onCite={onCite} onUpdated={refresh} />}
      <RepairPanel run={run} hasFinding={Boolean(primary)} status={status} onUpdated={refresh} />
      <ObligationsPanel runId={run.id} obligations={v?.obligations ?? []} checks={checks} />
      {!active && (
        <Section title="Stages" eyebrow="Completed stages" className="panel-quiet">
          <StagesPanel stages={v?.stages ?? []} now={now} compact />
        </Section>
      )}
      <EvidencePanel run={run} requirements={requirements} />
    </div>
  );
}

export function RunView({
  id,
  profile,
  status,
  onContext,
}: {
  id: string;
  profile: AsyncState<Profile>;
  status: AsyncState<Status>;
  onContext: (info: RunContextInfo | null) => void;
}) {
  const { data: run, error, loading, refresh } = usePolling(() => api.run(id), isActive, [id], 1000);
  const [cancelling, setCancelling] = useState(false);
  const [cancelError, setCancelError] = useState<unknown>(null);
  const now = useNow(Boolean(run && (run.state === "queued" || run.state === "running")));
  useDocumentTitle(run ? run.title : "Run");

  useEffect(() => {
    if (!run) return;
    onContext({
      id: run.id,
      kind: run.kind,
      recorded: run.recorded,
      // While the run is active the count is not final, so show it as pending rather than a misleading zero.
      unresolved: run.state === "queued" || run.state === "running" ? null : run.verdict?.unresolved ?? run.verification?.unresolved_count ?? null,
      state: run.state,
      unresolvedReason: unresolvedReason(run),
    });
  }, [run, onContext]);
  useEffect(() => () => onContext(null), [onContext]);

  const cancel = async () => {
    setCancelling(true);
    setCancelError(null);
    try {
      await api.cancel(id);
      refresh();
    } catch (e) {
      setCancelError(e);
    } finally {
      setCancelling(false);
    }
  };

  if (loading && !run) return <Loading label="Loading run" />;
  if (!run && error instanceof ApiError && error.status === 404)
    return (
      <Callout kind="warn" title="No run with this ID" role="alert">
        <p>
          There is no run <code>{id}</code> on this server or in the recorded collection. Check the link, or open the{" "}
          <a href={href.runs()}>runs list</a>.
        </p>
      </Callout>
    );
  if (!run) return <ErrorNotice error={error} title={`Run ${id} unavailable`} onRetry={refresh} />;

  return (
    <div className="stack-lg run-view">
      <p className="sr-only" role="status" aria-live="polite" aria-atomic="true">
        {announcement(run)}
      </p>
      {error ? <ErrorNotice error={error} title="Lost contact while polling; showing the last received state" onRetry={refresh} /> : null}
      <RunHeader run={run} now={now} onCancel={cancel} cancelling={cancelling} cancelError={cancelError} />
      {run.kind === "audit" ? (
        <AuditResult run={run} profile={profile} now={now} />
      ) : (
        <VerificationBody run={run} profile={profile} status={status} now={now} refresh={refresh} />
      )}
    </div>
  );
}
