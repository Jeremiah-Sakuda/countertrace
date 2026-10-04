import { ArrowRight, ArrowUpRight, ClipboardCheck, History, Radio } from "lucide-react";
import { api } from "../api/client";
import type { RecordedRunSummary, RunSummary, Verdict } from "../api/types";
import { Disclosure, ErrorNotice, Loading, Section, TableScroll } from "../components/common";
import { Badge, VerdictBadge } from "../components/StatusBadge";
import { formatDateTime } from "../lib/format";
import { useAsync } from "../lib/hooks";
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

function caseDescription(run: RecordedRunSummary): string {
  if (run.kind === "audit") return "See which seeded faults a supplemental check set misses. The mandatory core checks stay independent.";
  if (run.verdict?.headline === "counterexample") return "Follow the failing sequence from its first mismatch to the evidence behind it.";
  if (run.verdict?.headline === "no_counterexample") return "Inspect the individual simulation, bounded-check, and proof results, with their assumptions and limits.";
  return "Read the preserved checks, trace artifacts, and unresolved questions for this run.";
}

function RecordedList({ items }: { items: RecordedRunSummary[] }) {
  if (items.length === 0) return <p className="muted">No recorded runs are bundled with this build.</p>;
  const firstFailure = items.find((item) => item.verdict?.headline === "counterexample");
  const ordered = firstFailure ? [firstFailure, ...items.filter((item) => item.id !== firstFailure.id)] : items;
  return (
    <div className="gallery-grid">
      {ordered.map((r, index) => (
        <article key={r.id} className={`gallery-card${r.id === firstFailure?.id ? " gallery-card-featured" : ""}`} aria-labelledby={`case-${r.id}`}>
          <div className="gallery-card-top">
            <span className="gallery-card-number">{String(index + 1).padStart(2, "0")}</span>
            <span className="gallery-card-type">{r.kind === "audit" ? "Check-quality audit" : "Verification case"}</span>
            <Badge tone="neutral" icon={History}>Recorded</Badge>
          </div>
          <h3 id={`case-${r.id}`} className="gallery-title"><a href={href.run(r.id)}>{r.title}</a></h3>
          <div className="gallery-outcome"><Outcome kind={r.kind} state="complete" verdict={r.verdict} /></div>
          <p className="gallery-description">{caseDescription(r)}</p>
          {r.verdict && (
            <dl className="gallery-result-facts">
              <div><dt>Properties proved</dt><dd>{r.verdict.counts.proved ?? 0}<span>under the stated assumptions</span></dd></div>
              <div><dt>Unresolved</dt><dd>{r.verdict.unresolved}<span>obligations</span></dd></div>
            </dl>
          )}
          <div className="gallery-card-footer">
            <time dateTime={r.created_at} className="gallery-meta">{formatDateTime(r.created_at)}</time>
            <a href={href.run(r.id)} className="gallery-open" aria-label={`Open case file: ${r.title}`}>Open case file <ArrowUpRight size={18} aria-hidden="true" /></a>
          </div>
          <Disclosure className="gallery-note" summary="Recording notes & provenance">
            <p className="mono small wrap-anywhere">{r.id}</p>
            {r.recorded_note && <p className="muted small">{r.recorded_note}</p>}
            <p className="muted small">Dates, versions, and timings come from the original run. This is recorded evidence, not a new execution.</p>
          </Disclosure>
        </article>
      ))}
    </div>
  );
}

function LiveList({ items }: { items: RunSummary[] }) {
  if (items.length === 0)
    return (
      <p className="muted">
        No live runs yet. Start one from <a href={href.setup()}>contract setup</a>.
      </p>
    );
  return (
    <TableScroll label="Live runs">
      <table className="data-table">
        <thead>
          <tr>
            <th scope="col">Run</th>
            <th scope="col">Created</th>
            <th scope="col">Outcome</th>
          </tr>
        </thead>
        <tbody>
          {items.map((r) => (
            <tr key={r.id}>
              <th scope="row">
                <a href={href.run(r.id)}>{r.title}</a>
                <p className="mono small muted">
                  {r.id}
                  {r.example_id ? ` · ${r.example_id}` : ""}
                </p>
                {r.parent_id && (
                  <p className="small muted">
                    Repair candidate for <a href={href.run(r.parent_id)} className="mono">{r.parent_id}</a>
                  </p>
                )}
              </th>
              <td className="small">
                <Badge tone="info" icon={Radio}>
                  Live run
                </Badge>
                <p className="mono small">{formatDateTime(r.created_at)}</p>
              </td>
              <td>
                <Outcome kind={r.kind} state={r.state} verdict={r.verdict} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </TableScroll>
  );
}

export function RunsView() {
  const recorded = useAsync(() => api.recorded(), []);
  const runs = useAsync(() => api.runs(), []);
  const live = runs.status === "ok" ? runs.data.filter((r) => !r.recorded) : [];
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
          <p>Choose a bundled FIFO, accept its contract, and create a fresh run.</p>
          <a className="inline-link" href={href.setup()}>Set up a run <ArrowRight size={16} aria-hidden="true" /></a>
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
      <Section
        title="Live runs on this server"
        eyebrow="The working ledger"
        className="gallery-live"
        actions={<button type="button" className="btn btn-ghost btn-sm" onClick={runs.reload}>Refresh</button>}
      >
        <p className="muted small">New executions and repair candidates stay here, separate from the bundled case files.</p>
        {runs.status === "loading" && <Loading label="Loading runs" />}
        {runs.status === "error" && <ErrorNotice error={runs.error} title="Runs unavailable" onRetry={runs.reload} />}
        {runs.status === "ok" && <LiveList items={live} />}
      </Section>
    </div>
  );
}
