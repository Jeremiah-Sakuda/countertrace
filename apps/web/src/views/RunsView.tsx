import { ClipboardCheck, History, Radio } from "lucide-react";
import { api } from "../api/client";
import type { RecordedRunSummary, RunSummary, Verdict } from "../api/types";
import { ErrorNotice, Loading, Section, TableScroll } from "../components/common";
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

function RecordedList({ items }: { items: RecordedRunSummary[] }) {
  if (items.length === 0) return <p className="muted">No recorded runs are bundled with this build.</p>;
  return (
    <TableScroll label="Recorded runs">
      <table className="data-table">
        <thead>
          <tr>
            <th scope="col">Run</th>
            <th scope="col">Recorded</th>
            <th scope="col">Outcome</th>
          </tr>
        </thead>
        <tbody>
          {items.map((r) => (
            <tr key={r.id}>
              <th scope="row">
                <a href={href.run(r.id)}>{r.title}</a>
                <p className="mono small muted">{r.id}</p>
                {r.recorded_note && <p className="muted small">{r.recorded_note}</p>}
              </th>
              <td className="small">
                <Badge tone="neutral" icon={History}>
                  Recorded run
                </Badge>
                <p className="mono small">{formatDateTime(r.created_at)}</p>
              </td>
              <td>
                <Outcome kind={r.kind} state="complete" verdict={r.verdict} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </TableScroll>
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
    <div className="stack-lg page-narrow">
      <div className="intro">
        <h1>Runs</h1>
        <p className="lede">
          Recorded runs ship with this build and keep their original dates, versions, and timings. Live runs executed on this server are
          listed separately. Outcomes name what was found, never a blanket “verified”.
        </p>
      </div>
      <Section title="Recorded runs">
        {recorded.status === "loading" && <Loading label="Loading recorded runs" />}
        {recorded.status === "error" && <ErrorNotice error={recorded.error} title="Recorded runs unavailable" onRetry={recorded.reload} />}
        {recorded.status === "ok" && <RecordedList items={recorded.data} />}
      </Section>
      <Section
        title="Live runs on this server"
        actions={
          <button type="button" className="btn btn-ghost btn-sm" onClick={runs.reload}>
            Refresh
          </button>
        }
      >
        {runs.status === "loading" && <Loading label="Loading runs" />}
        {runs.status === "error" && <ErrorNotice error={runs.error} title="Runs unavailable" onRetry={runs.reload} />}
        {runs.status === "ok" && <LiveList items={live} />}
      </Section>
    </div>
  );
}
