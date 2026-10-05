import { ArrowRight, ClipboardCheck, History, Server } from "lucide-react";
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { api } from "../api/client";
import type { RecordedRunSummary, Run, RunSummary, Status, Verdict } from "../api/types";
import { Disclosure, ErrorNotice, Loading, Section, TableScroll } from "../components/common";
import { Badge, VerdictBadge } from "../components/StatusBadge";
import { isRecordedDemo, LOCAL_BUILD_URL } from "../components/DeploymentNotice";
import { formatDateTime } from "../lib/format";
import { findingSignal, originLabel, passedAttempt, primaryFinding, signalValue } from "../lib/evidence";
import { useAsync, useDocumentTitle, type AsyncState } from "../lib/hooks";
import { href } from "../lib/route";

function Outcome({ kind, state, verdict }: { kind: string; state: string; verdict: Verdict | null | undefined }) {
  if (kind === "audit")
    return (
      <Badge tone="neutral" icon={ClipboardCheck}>
        Check-set audit · {state}
      </Badge>
    );
  if (state === "queued" || state === "running") return <VerdictBadge headline="pending" />;
  if (!verdict) return <span className="muted">{state}</span>;
  return (
    <span className="outcome">
      <VerdictBadge headline={verdict.headline} />
      {verdict.unresolved > 0 && <span className="muted small"> · {verdict.unresolved} unresolved</span>}
      {state !== "complete" && <span className="muted small"> · {state}</span>}
    </span>
  );
}

function caseDescription(run: RecordedRunSummary, detail: Run | null): string {
  if (run.kind === "audit") return "See which seeded faults a supplemental check set misses. The mandatory core checks stay independent.";
  if (detail?.parent_id) return "A model-proposed repair, re-run against the parent's frozen contract and checks. Compare its results with the failing run.";
  if (run.verdict?.headline === "counterexample") return "Follow the failing sequence from its first mismatch to the evidence behind it.";
  if (run.verdict?.headline === "no_counterexample") return "Inspect the individual simulation, bounded-check, and proof results, with their assumptions and limits.";
  return "Read the preserved checks, trace artifacts, and unresolved questions for this run.";
}

/** Two facts per card, read from the recorded run. The strongest available evidence leads. */
function CardFacts({ run, detail }: { run: RecordedRunSummary; detail: Run | null }) {
  const facts: { label: string; value: ReactNode; note: string; small?: boolean }[] = [];
  if (run.kind === "audit") {
    const s = detail?.audit?.summary;
    if (s) {
      facts.push({ label: "Real bugs missed", value: `${s.supplemental_survived} of ${s.valid_faults}`, note: "valid seeded faults survived the set" });
      facts.push({ label: "Caught", value: s.supplemental_killed, note: "valid faults killed by the set" });
    }
  } else if (run.verdict?.headline === "counterexample") {
    const finding = primaryFinding(detail);
    const attempt = passedAttempt(detail);
    if (finding) facts.push({ label: "First mismatch", value: `Cycle ${finding.cycle}`, note: `${findingSignal(finding)} ${signalValue(finding, "expected")} expected, ${signalValue(finding, "observed")} observed` });
    const extras = [detail?.explanation?.result ? "Explanation" : null, attempt ? "accepted repair" : detail?.repair ? "repair attempted" : null].filter(Boolean);
    if (extras.length) {
      const text = extras.join(" · ");
      facts.push({ label: "Recorded with", small: true, value: text.charAt(0).toUpperCase() + text.slice(1), note: attempt ? `candidate ${attempt.index} passed the unchanged checks` : "model output, checked separately" });
    } else facts.push({ label: "Unresolved", value: run.verdict.unresolved, note: "obligations" });
  } else if (run.verdict) {
    facts.push({ label: "Properties proved", value: run.verdict.counts.proved ?? 0, note: "under the stated assumptions" });
    facts.push({ label: "Unresolved", value: run.verdict.unresolved, note: "obligations" });
  }
  if (facts.length === 0) return null;
  return (
    <dl className="gallery-result-facts">
      {facts.map((f) => (
        <div key={f.label}>
          <dt>{f.label}</dt>
          <dd className={f.small ? "fact-label-value" : undefined}>{f.value}<span>{f.note}</span></dd>
        </div>
      ))}
    </dl>
  );
}

function RecordedList({ items }: { items: RecordedRunSummary[] }) {
  // Only a handful of recordings ship, so their full records are fetched to describe each card accurately.
  const details = useAsync(async () => {
    const entries = await Promise.all(items.map(async (r) => [r.id, await api.run(r.id).catch(() => null)] as const));
    return Object.fromEntries(entries) as Record<string, Run | null>;
  }, [items.map((r) => r.id).join(",")]);
  const detailOf = (id: string) => (details.status === "ok" ? details.data[id] ?? null : null);
  if (items.length === 0) return <p className="muted">No recorded runs are bundled with this build.</p>;
  const firstFailure = items.find((item) => item.verdict?.headline === "counterexample");
  const base = firstFailure ? [firstFailure, ...items.filter((item) => item.id !== firstFailure.id)] : items;
  const ordered = withCandidatesAfterParents(base, (id) => detailOf(id)?.parent_id ?? null);
  return (
    <div className="gallery-grid">
      {ordered.map((r, index) => {
        const detail = detailOf(r.id);
        return (
          <article key={r.id} className={`gallery-card${r.id === firstFailure?.id ? " gallery-card-featured" : ""}`} aria-labelledby={`case-${r.id}`}>
            <div className="gallery-card-top">
              <span className="gallery-card-number">{String(index + 1).padStart(2, "0")}</span>
              <span className="gallery-card-type">{r.kind === "audit" ? "Check-quality audit" : detail?.parent_id ? "Repair candidate" : "Verification case"}</span>
              <Badge tone="neutral" icon={History}>Recorded</Badge>
            </div>
            <h3 id={`case-${r.id}`} className="gallery-title"><a href={href.run(r.id)}>{r.title}</a></h3>
            <div className="gallery-outcome"><Outcome kind={r.kind} state="complete" verdict={r.verdict} /></div>
            <p className="gallery-description">{caseDescription(r, detail)}</p>
            <CardFacts run={r} detail={detail} />
            <div className="gallery-card-footer">
              <time dateTime={r.created_at} className="gallery-meta">{formatDateTime(r.created_at)}</time>
              <a href={href.run(r.id)} className="gallery-open" aria-label={`Open case file: ${r.title}`}>Open case file <ArrowRight size={18} aria-hidden="true" /></a>
            </div>
            <Disclosure className="gallery-note" summary="Recording notes & provenance">
              <p className="mono small wrap-anywhere">{r.id}</p>
              {r.recorded_note && <p className="muted small">{r.recorded_note}</p>}
              <p className="muted small">Dates, versions, and timings come from the original run. This is recorded evidence, not a new execution.</p>
            </Disclosure>
          </article>
        );
      })}
    </div>
  );
}

/** Place each repair candidate directly after its parent (and after earlier candidates of that parent), keeping the order otherwise. */
export function withCandidatesAfterParents<T extends { id: string }>(items: T[], parentOf: (id: string) => string | null): T[] {
  const ids = new Set(items.map((item) => item.id));
  const children = new Map<string, T[]>();
  for (const item of items) {
    const parent = parentOf(item.id);
    if (parent && parent !== item.id && ids.has(parent)) children.set(parent, [...(children.get(parent) ?? []), item]);
  }
  const out: T[] = [];
  const placed = new Set<string>();
  const place = (item: T) => {
    if (placed.has(item.id)) return;
    placed.add(item.id);
    out.push(item);
    for (const child of children.get(item.id) ?? []) place(child);
  };
  for (const item of items) {
    const parent = parentOf(item.id);
    if (parent && ids.has(parent) && !placed.has(parent)) continue;
    place(item);
  }
  for (const item of items) place(item);
  return out;
}

const PAGE = 12;

/**
 * Evaluation-suite runs and everything descended from them (repair candidates, candidates of candidates).
 * `all` includes recorded runs so a parent outside this list still resolves.
 */
export function evaluationIds(all: RunSummary[]): Set<string> {
  const byId = new Map(all.map((r) => [r.id, r]));
  const memo = new Map<string, boolean>();
  const isEval = (id: string, seen: Set<string>): boolean => {
    const known = memo.get(id);
    if (known !== undefined) return known;
    const r = byId.get(id);
    let result = false;
    if (r) {
      if (r.origin === "evaluation") result = true;
      else if (r.parent_id && !seen.has(r.parent_id)) result = isEval(r.parent_id, new Set(seen).add(id));
    }
    memo.set(id, result);
    return result;
  };
  return new Set(all.filter((r) => isEval(r.id, new Set())).map((r) => r.id));
}

function LocalList({ items, all }: { items: RunSummary[]; all: RunSummary[] }) {
  const [showEvaluation, setShowEvaluation] = useState(false);
  const [limit, setLimit] = useState(PAGE);
  const hidden = useMemo(() => evaluationIds(all), [all]);
  const evaluation = items.filter((r) => hidden.has(r.id)).length;
  const visible = showEvaluation ? items : items.filter((r) => !hidden.has(r.id));
  const shown = visible.slice(0, limit);
  const moreRef = useRef<HTMLTableRowElement>(null);
  const [focusFrom, setFocusFrom] = useState<number | null>(null);

  useEffect(() => {
    // After "Show more", move focus to the first newly shown run so keyboard users continue where they were.
    if (focusFrom === null) return;
    moreRef.current?.querySelector<HTMLAnchorElement>("a")?.focus();
    setFocusFrom(null);
  }, [focusFrom]);

  if (items.length === 0)
    return (
      <p className="muted">
        No runs on this server yet. Start one from <a href={href.setup()}>contract setup</a>.
      </p>
    );
  return (
    <div className="stack">
      <div className="ledger-controls">
        <p className="muted small" aria-live="polite">
          Showing {shown.length} of {visible.length} run{visible.length === 1 ? "" : "s"} on this server
          {!showEvaluation && evaluation > 0 ? ` · ${evaluation} evaluation run${evaluation === 1 ? "" : "s"} hidden` : ""}
        </p>
        {evaluation > 0 && (
          <label className="check-row ledger-toggle">
            <input type="checkbox" checked={showEvaluation} onChange={(e) => { setShowEvaluation(e.target.checked); setLimit(PAGE); }} />
            <span title="Evaluation-suite runs and their repair candidates">Show evaluation runs ({evaluation})</span>
          </label>
        )}
      </div>
      {shown.length === 0 ? (
        <p className="muted">Only evaluation runs exist on this server. Turn on “Show evaluation runs” above to list them.</p>
      ) : (
        <TableScroll label="Runs on this server">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col">Run</th>
                <th scope="col">Created</th>
                <th scope="col">Outcome</th>
              </tr>
            </thead>
            <tbody>
              {shown.map((r, i) => {
                const origin = originLabel(r.origin) ?? (r.kind === "audit" ? "Check-set audit" : null);
                return (
                  <tr key={r.id} ref={i === focusFrom ? moreRef : undefined}>
                    <th scope="row">
                      <a href={href.run(r.id)}>{r.title}</a>
                      <p className="mono small muted">
                        {r.id}
                        {r.example_id ? ` · ${r.example_id}` : ""}
                        {r.depth ? ` · depth ${r.depth}` : ""}
                      </p>
                      {r.parent_id && (
                        <p className="small muted">
                          Repair candidate for <a href={href.run(r.parent_id)} className="mono">{r.parent_id}</a>
                        </p>
                      )}
                    </th>
                    <td className="small">
                      <Badge tone="info" icon={Server}>
                        Run on this server
                      </Badge>
                      {origin && <p className="small muted">{origin}</p>}
                      <p className="mono small">{formatDateTime(r.created_at)}</p>
                    </td>
                    <td>
                      <Outcome kind={r.kind} state={r.state} verdict={r.verdict} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </TableScroll>
      )}
      {visible.length > shown.length && (
        <div className="action-row">
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => {
              setFocusFrom(shown.length);
              setLimit((n) => n + PAGE);
            }}
          >
            Show {Math.min(PAGE, visible.length - shown.length)} more
          </button>
          <span className="muted small">{visible.length - shown.length} older runs not shown</span>
        </div>
      )}
    </div>
  );
}

export function RunsView({ status }: { status: AsyncState<Status> }) {
  useDocumentTitle("Runs");
  const recorded = useAsync(() => api.recorded(), []);
  const runs = useAsync(() => api.runs(), []);
  const local = runs.status === "ok" ? runs.data.filter((r) => !r.recorded) : [];
  const recordedDemo = isRecordedDemo(status);
  return (
    <div className="stack-lg gallery-page">
      <header className="notebook-hero gallery-hero">
        <div>
          <p className="eyebrow">The archive / Runs</p>
          <h1>Every result<br /><em>has a paper trail.</em></h1>
          <p className="lede">Open a case. Follow a sequence. Inspect what the checks established—and the questions they left open.</p>
        </div>
        <aside className="notebook-hero-aside">
          <span className="notebook-margin-label">Your next experiment</span>
          <p>{recordedDemo ? "Use the local test build to verify a bundled FIFO and request a new explanation or repair." : "Choose a bundled FIFO, accept its contract, and create a fresh run."}</p>
          <a className="inline-link" href={recordedDemo ? LOCAL_BUILD_URL : href.setup()}>{recordedDemo ? "Run the local test build" : "Set up a run"} <ArrowRight size={16} aria-hidden="true" /></a>
        </aside>
      </header>
      <section className="gallery-recorded" aria-labelledby="recorded-cases">
        <header className="gallery-section-heading">
          <div><p className="eyebrow">Preserved evidence</p><h2 id="recorded-cases">Recorded case files</h2></div>
          {recorded.status === "ok" && <span className="gallery-count">{recorded.data.length} bundled {recorded.data.length === 1 ? "case" : "cases"}</span>}
        </header>
        <p className="gallery-section-intro">Read-only records with original dates and timings. These development and showcase runs do not constitute an evaluation benchmark.</p>
        {recorded.status === "loading" && <Loading label="Loading recorded runs" />}
        {recorded.status === "error" && <ErrorNotice error={recorded.error} title="Recorded runs unavailable" onRetry={recorded.reload} />}
        {recorded.status === "ok" && <RecordedList items={recorded.data} />}
      </section>
      {!recordedDemo && <Section
        title="Runs on this server"
        eyebrow="The working ledger"
        className="gallery-live"
        actions={<button type="button" className="btn btn-ghost btn-sm" onClick={runs.reload}>Refresh</button>}
      >
        <p className="muted small">New executions and repair candidates stay here, separate from the bundled case files. Newest first.</p>
        {runs.status === "loading" && <Loading label="Loading runs" />}
        {runs.status === "error" && <ErrorNotice error={runs.error} title="Runs unavailable" onRetry={runs.reload} />}
        {runs.status === "ok" && <LocalList items={local} all={runs.data} />}
      </Section>}
    </div>
  );
}
