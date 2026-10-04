import { CircleCheck, CircleHelp, CircleX, Download, FileCode2, Repeat, Wrench, CircleMinus } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { fileUrl } from "../../api/client";
import type { CycleRow, Finding, Replay, Requirement } from "../../api/types";
import { Disclosure } from "../../components/common";
import { CycleTable, type FocusRequest } from "../../components/CycleTable";
import { QueueView } from "../../components/QueueView";
import { Badge, type Tone } from "../../components/StatusBadge";
import { Waveform } from "../../components/Waveform";
import { bit, CHECK_SIGNAL, hex } from "../../lib/format";

const REPLAY: Record<Replay["status"], { tone: Tone; icon: typeof CircleCheck; label: string }> = {
  reproduced: { tone: "info", icon: Repeat, label: "Reproduced in simulation" },
  not_reproduced: { tone: "unresolved", icon: CircleHelp, label: "Not reproduced in simulation" },
  mismatch: { tone: "fail", icon: CircleX, label: "Engines disagree: replay mismatch" },
  error: { tone: "toolerror", icon: Wrench, label: "Replay error" },
  not_attempted: { tone: "neutral", icon: CircleMinus, label: "Replay not attempted" },
};

export function ReplayBadge({ replay }: { replay: Replay | undefined }) {
  if (!replay) return null;
  const spec = REPLAY[replay.status] ?? REPLAY.not_attempted;
  return (
    <Badge tone={spec.tone} icon={spec.icon}>
      {spec.label}
    </Badge>
  );
}

function testLabel(f: Finding): string {
  if (f.source === "formal") return `the formal ${f.test.replace(/^formal:/, "")} trace`;
  return `test ${f.test}`;
}

function ExpectedObserved({ finding }: { finding: Finding }) {
  const failed = new Set(finding.checks_failed.map((c) => CHECK_SIGNAL[c]).filter(Boolean));
  const signals: ("dout" | "empty" | "full")[] = ["dout", "empty", "full"];
  const fmt = (s: "dout" | "empty" | "full", v: Finding["expected"]) => (s === "dout" ? hex(v.dout) : bit(v[s]));
  return (
    <table className="data-table compact eo-table">
      <caption className="sr-only">Expected versus observed outputs after cycle {finding.cycle}</caption>
      <thead>
        <tr>
          <th scope="col">Signal</th>
          <th scope="col">Expected</th>
          <th scope="col">Observed</th>
          <th scope="col">Result</th>
        </tr>
      </thead>
      <tbody>
        {signals.map((s) => {
          const bad = failed.has(s);
          const unchecked = s === "dout" && finding.expected.dout === null;
          return (
            <tr key={s} className={bad ? "row-bad" : undefined}>
              <th scope="row" className="mono">
                {s}
              </th>
              <td className="mono">{unchecked ? <span className="unchecked-label">not checked</span> : fmt(s, finding.expected)}</td>
              <td className="mono">{fmt(s, finding.observed)}</td>
              <td>
                {bad ? (
                  <span className="mismatch">
                    <CircleX size={14} aria-hidden="true" /> Mismatch
                  </span>
                ) : unchecked ? (
                  <span className="muted">Not checked</span>
                ) : (
                  <span className="muted">Matches</span>
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

function useTraceRows(traces: Record<string, CycleRow[]> | undefined, finding: Finding, showAll: boolean): { rows: CycleRow[]; total: number } {
  return useMemo(() => {
    const all = traces?.[finding.trace] ?? [];
    const rows = showAll ? all : all.filter((r) => r.cycle >= finding.window.start && r.cycle <= finding.window.end);
    return { rows, total: all.length };
  }, [traces, finding, showAll]);
}

export function TraceBlock({
  runId,
  finding,
  traces,
  requirements,
  depth,
  focusRequest,
  caption,
}: {
  runId: string;
  finding: Finding;
  traces: Record<string, CycleRow[]> | undefined;
  requirements: Record<string, Requirement> | undefined;
  depth: number;
  focusRequest?: FocusRequest | null;
  caption: string;
}) {
  const [showAll, setShowAll] = useState(false);
  const { rows, total } = useTraceRows(traces, finding, showAll);
  const [selected, setSelected] = useState<CycleRow | null>(null);

  useEffect(() => {
    if (!focusRequest || showAll) return;
    const inWindow = focusRequest.cycle >= finding.window.start && focusRequest.cycle <= finding.window.end;
    if (!inWindow) setShowAll(true);
  }, [focusRequest, finding, showAll]);

  const current = rows.find((r) => r.cycle === selected?.cycle) ?? rows.find((r) => r.cycle === finding.cycle) ?? rows[0] ?? null;

  if (total === 0)
    return (
      <p className="muted">
        The trace <code>{finding.trace}</code> was not recorded in this run, so no cycle table can be shown.
      </p>
    );

  return (
    <div className="stack">
      <div className="trace-toolbar">
        <p className="muted small">
          {showAll ? `All ${total} recorded cycles of ` : `Cycles ${finding.window.start}–${finding.window.end} of `}
          <code>{finding.trace}</code>
        </p>
        {total > rows.length || showAll ? (
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => setShowAll((v) => !v)} aria-pressed={showAll}>
            {showAll ? "Show the finding window only" : `Show full trace (${total} cycles)`}
          </button>
        ) : null}
      </div>
      {current && <QueueView row={current} depth={depth} />}
      <CycleTable
        rows={rows}
        caption={caption}
        requirements={requirements}
        markCycle={finding.cycle}
        focusRequest={focusRequest}
        onSelect={setSelected}
        selectedCycle={current?.cycle ?? null}
      />
      <Disclosure summary="Waveform (drawn from these trace rows)">
        <Waveform rows={rows} markCycle={finding.cycle} />
      </Disclosure>
      {finding.vcd && (
        <p className="small">
          <a href={fileUrl(runId, finding.vcd)} target="_blank" rel="noreferrer" className="inline-link">
            <Download size={14} aria-hidden="true" /> Raw VCD for this trace
          </a>
        </p>
      )}
    </div>
  );
}

/** The lead finding: violated requirement, failed check, first observed mismatch, and the cycle table. */
export function FindingPanel({
  runId,
  finding,
  traces,
  requirements,
  depth,
  focusRequest,
  onCite,
}: {
  runId: string;
  finding: Finding;
  traces: Record<string, CycleRow[]> | undefined;
  requirements: Record<string, Requirement> | undefined;
  depth: number;
  focusRequest: FocusRequest | null;
  onCite: (cycle: number) => void;
}) {
  return (
    <section className="panel finding" aria-labelledby="run-finding">
      <header className="panel-header">
        <div>
          <p className="eyebrow eyebrow-fail">
            <CircleX size={14} aria-hidden="true" /> Counterexample found · {finding.source === "formal" ? "formal" : "simulation"}
          </p>
          <h2 id="run-finding" className="panel-title" tabIndex={-1}>
            Violated requirement: {finding.requirement_title}
          </h2>
        </div>
      </header>
      <p className="requirement-text">{finding.requirement_text}</p>
      <p className="finding-headline">
        First observed mismatch at <strong>cycle {finding.cycle}</strong> in <strong>{testLabel(finding)}</strong>.
      </p>
      <div className="grid-2 finding-grid">
        <div>
          <h3 className="subhead">Failed check</h3>
          <p>
            <code>{finding.check}</code> {finding.check_text}
          </p>
          {finding.checks_failed.length > 1 && (
            <p className="muted small">
              Also failing at this edge:{" "}
              {finding.checks_failed
                .filter((c) => c !== finding.check)
                .map((c) => (
                  <code key={c}>{c}</code>
                ))}
            </p>
          )}
          <p className="muted small">
            Governing contract row: <code>{finding.requirement_id}</code>
          </p>
          {finding.related_events.length > 0 && (
            <>
              <h3 className="subhead">Related events</h3>
              <ul className="events">
                {finding.related_events.map((e, i) => (
                  <li key={i}>
                    <button type="button" className="cycle-link" onClick={() => onCite(e.cycle)} aria-label={`Show cycle ${e.cycle} in the table`}>
                      cycle {e.cycle}
                    </button>{" "}
                    {e.text}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
        <div>
          <h3 className="subhead">Expected vs observed after cycle {finding.cycle}</h3>
          <ExpectedObserved finding={finding} />
        </div>
      </div>
      <p className="note">
        <FileCode2 size={14} aria-hidden="true" /> {finding.note}
      </p>
      <h3 className="subhead">Cycle table</h3>
      <TraceBlock
        runId={runId}
        finding={finding}
        traces={traces}
        requirements={requirements}
        depth={depth}
        focusRequest={focusRequest}
        caption={`Cycle table for ${testLabel(finding)}`}
      />
    </section>
  );
}

/** A formal counterexample (or a further finding), kept separate from the lead simulation finding, with its replay status. */
export function FormalFindingPanel({
  runId,
  finding,
  traces,
  requirements,
  depth,
}: {
  runId: string;
  finding: Finding;
  traces: Record<string, CycleRow[]> | undefined;
  requirements: Record<string, Requirement> | undefined;
  depth: number;
}) {
  const replay = finding.replay;
  return (
    <section className="panel" aria-labelledby={`formal-${finding.test}`}>
      <header className="panel-header">
        <div>
          <p className="eyebrow eyebrow-fail">
            <CircleX size={14} aria-hidden="true" /> {finding.source === "formal" ? "Formal counterexample" : "Additional simulation finding"} · {finding.test}
          </p>
          <h2 id={`formal-${finding.test}`} className="panel-title">
            {finding.requirement_title}
          </h2>
        </div>
        <div className="panel-actions">
          <ReplayBadge replay={replay} />
        </div>
      </header>
      <p>
        Check <code>{finding.check}</code> failed at application cycle <strong>{finding.cycle}</strong>. {finding.check_text}.
      </p>
      {replay && (
        <p className="muted small">
          {replay.solver_step !== null && replay.application_cycle !== null
            ? `Solver step ${replay.solver_step} maps to application cycle ${replay.application_cycle}${replay.task ? ` (${replay.task})` : ""}. `
            : ""}
          {replay.detail}
        </p>
      )}
      {replay && replay.status !== "reproduced" && (
        <p className="callout-inline">
          <CircleHelp size={14} aria-hidden="true" /> A formal trace that is not reproduced by the independent simulation scoreboard is
          a result to investigate, not proof of a defect on its own.
        </p>
      )}
      <Disclosure summary={`Formal trace cycle table (${finding.trace})`}>
        <TraceBlock
          runId={runId}
          finding={finding}
          traces={traces}
          requirements={requirements}
          depth={depth}
          caption={`Cycle table for formal trace ${finding.trace}`}
        />
      </Disclosure>
      {traces?.["replay"] && traces["replay"].length > 0 && (
        <Disclosure summary="Simulation replay trace">
          <CycleTable rows={traces["replay"]} caption="Simulation replay of the formal trace" requirements={requirements} markCycle={finding.cycle} />
        </Disclosure>
      )}
    </section>
  );
}
