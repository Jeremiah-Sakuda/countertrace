import {
  Ban,
  Bot,
  CircleCheck,
  CircleHelp,
  CircleX,
  Download,
  Equal,
  LoaderCircle,
  Pencil,
  Unlink,
  User,
  Wrench,
  type LucideIcon,
} from "lucide-react";
import { useState } from "react";
import { api, bundleUrl, errorMessage } from "../../api/client";
import type { AttemptStatus, Repair, RepairAttempt, RepairStatus, Run, Status } from "../../api/types";
import { DiffView } from "../../components/CodeView";
import { Callout, Disclosure, ErrorNotice, Section } from "../../components/common";
import { ModelCalls, ModelProvenance } from "../../components/ModelResult";
import { Badge, type Tone } from "../../components/StatusBadge";
import { formatDateTime } from "../../lib/format";
import type { AsyncState } from "../../lib/hooks";
import { href } from "../../lib/route";

const ATTEMPT: Record<AttemptStatus, { tone: Tone; icon: LucideIcon; label: string }> = {
  model_error: { tone: "toolerror", icon: Wrench, label: "Model error" },
  admission_rejected: { tone: "neutral", icon: Ban, label: "Rejected at admission" },
  interface_changed: { tone: "neutral", icon: Unlink, label: "Interface changed (not comparable)" },
  verifying: { tone: "running", icon: LoaderCircle, label: "Verifying candidate" },
  passed_unchanged_checks: { tone: "sim", icon: CircleCheck, label: "Passed the unchanged checks" },
  failed_checks: { tone: "fail", icon: CircleX, label: "Failed the unchanged checks" },
  error: { tone: "toolerror", icon: Wrench, label: "Error" },
};

const REPAIR: Record<RepairStatus, { tone: Tone; icon: LucideIcon; label: string }> = {
  running: { tone: "running", icon: LoaderCircle, label: "Repair in progress" },
  passed: { tone: "sim", icon: CircleCheck, label: "A candidate passed the unchanged checks" },
  exhausted: { tone: "unresolved", icon: CircleHelp, label: "No candidate passed within the attempt limit" },
  unavailable: { tone: "neutral", icon: Ban, label: "Repair unavailable" },
  error: { tone: "toolerror", icon: Wrench, label: "Repair error" },
};

function Diagnostics({ value }: { value: unknown }) {
  if (value === null || value === undefined) return null;
  if (Array.isArray(value)) {
    if (value.length === 0) return null;
    return (
      <ul className="open-list small">
        {value.map((d, i) => (
          <li key={i} className="mono">
            {typeof d === "string" ? d : JSON.stringify(d)}
          </li>
        ))}
      </ul>
    );
  }
  return <pre className="json">{typeof value === "string" ? value : JSON.stringify(value, null, 2)}</pre>;
}

function Attempt({ attempt, max }: { attempt: RepairAttempt; max: number }) {
  const spec = ATTEMPT[attempt.status] ?? ATTEMPT.error;
  return (
    <li className="attempt">
      <div className="attempt-head">
        <h3 className="attempt-title">
          Attempt {attempt.index} of {max}
        </h3>
        <Badge tone="neutral" icon={attempt.origin === "user" ? User : Bot}>
          {attempt.origin === "user" ? "Your edit" : "Proposed by Nemotron"}
        </Badge>
        <Badge tone={spec.tone} icon={spec.icon} spin={attempt.status === "verifying"}>
          {spec.label}
        </Badge>
      </div>
      <p>{attempt.summary}</p>
      {attempt.frozen_match !== undefined && attempt.frozen_match !== null && (
        <p className={attempt.frozen_match ? "frozen ok" : "frozen bad"}>
          {attempt.frozen_match ? <Equal size={14} aria-hidden="true" /> : <CircleX size={14} aria-hidden="true" />}
          {attempt.frozen_match ? "Unchanged contract and checks: hashes match" : "Contract or checks changed: hashes mismatch (comparison invalid)"}
        </p>
      )}
      {attempt.candidate_run_id && (
        <p className="small">
          Candidate run:{" "}
          <a href={href.run(attempt.candidate_run_id)} className="mono">
            {attempt.candidate_run_id}
          </a>
        </p>
      )}
      {attempt.rationale && (
        <div>
          {attempt.origin === "model" && <ModelProvenance task="repair rationale" />}
          <p className="prose">{attempt.rationale}</p>
        </div>
      )}
      {attempt.diff && (
        <Disclosure summary="Source diff" defaultOpen>
          <DiffView diff={attempt.diff} label={`Diff for attempt ${attempt.index}`} />
        </Disclosure>
      )}
      <Diagnostics value={attempt.diagnostics} />
      {attempt.calls && attempt.calls.length > 0 && (
        <Disclosure summary="Model calls">
          <ModelCalls calls={attempt.calls} />
        </Disclosure>
      )}
    </li>
  );
}

function RepairState({ repair }: { repair: Repair }) {
  const spec = REPAIR[repair.status] ?? REPAIR.error;
  return (
    <div className="stack">
      <div className="action-row">
        <Badge tone={spec.tone} icon={spec.icon} spin={repair.status === "running"} size="md">
          {spec.label}
        </Badge>
        <span className="muted small">
          {repair.attempts.length} of {repair.max_attempts} attempts used
          {repair.started_at ? ` · started ${formatDateTime(repair.started_at)}` : ""}
          {repair.finished_at ? ` · finished ${formatDateTime(repair.finished_at)}` : ""}
        </span>
      </div>
      {repair.detail && <p className="muted">{repair.detail}</p>}
      {repair.status === "passed" && (
        <p className="muted small">
          A candidate passes only when its verification has no findings, no tool errors or unresolved obligations, and its frozen check set is
          identical to this run's. That applies to this contract, these parameters, and these methods only.
        </p>
      )}
      {repair.attempts.length > 0 && (
        <ol className="attempts">
          {repair.attempts.map((a) => (
            <Attempt key={a.index} attempt={a} max={repair.max_attempts} />
          ))}
        </ol>
      )}
    </div>
  );
}

function EditCandidate({ runId, onSubmitted }: { runId: string; onSubmitted: () => void }) {
  const [source, setSource] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [done, setDone] = useState(false);

  const load = () => {
    if (source !== null) return;
    api.file(runId, "dut.v").then(setSource, setLoadError);
  };

  const submit = async () => {
    if (source === null) return;
    setBusy(true);
    setError(null);
    try {
      await api.candidate(runId, source);
      setDone(true);
      onSubmitted();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <details className="disclosure" onToggle={(e) => (e.currentTarget as HTMLDetailsElement).open && load()}>
      <summary>
        <Pencil size={16} aria-hidden="true" />
        <span className="disclosure-title">Edit RTL yourself</span>
      </summary>
      <div className="disclosure-body stack">
        <p className="muted small">
          Your edit is checked against the same frozen contract and checks as this run and appears as an attempt marked “Your edit”.
        </p>
        {loadError ? <ErrorNotice error={loadError} title="Could not load dut.v" /> : null}
        {source !== null && (
          <>
            <label htmlFor={`edit-${runId}`} className="field-label">
              DUT source (dut.v)
            </label>
            <textarea
              id={`edit-${runId}`}
              className="code-input"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              spellCheck={false}
              rows={18}
            />
            <div className="action-row">
              <button type="button" className="btn btn-primary" onClick={submit} disabled={busy} aria-busy={busy}>
                {busy ? <LoaderCircle className="spin" size={16} aria-hidden="true" /> : <CircleCheck size={16} aria-hidden="true" />}
                Check my edit against the unchanged checks
              </button>
              {done && <span role="status">Submitted. The attempt appears below as it runs.</span>}
            </div>
          </>
        )}
        {error ? <ErrorNotice error={error} title="Could not submit the candidate" /> : null}
      </div>
    </details>
  );
}

function BundleButton({ runId, disabled }: { runId: string; disabled: boolean }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const download = async () => {
    setBusy(true);
    setError(null);
    try {
      const response = await fetch(bundleUrl(runId));
      if (!response.ok) {
        let message = `HTTP ${response.status}`;
        try {
          const data = (await response.json()) as { error?: string };
          if (data.error) message = `${data.error} (HTTP ${response.status})`;
        } catch {
          /* not JSON */
        }
        throw new Error(message);
      }
      const blob = await response.blob();
      const disposition = response.headers.get("Content-Disposition") ?? "";
      const match = /filename="?([^";]+)"?/.exec(disposition);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = match?.[1] ?? `countertrace-${runId}.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="stack-sm">
      <button type="button" className="btn btn-secondary" onClick={download} disabled={busy || disabled} aria-busy={busy}>
        {busy ? <LoaderCircle className="spin" size={16} aria-hidden="true" /> : <Download size={16} aria-hidden="true" />}
        Download evidence bundle
      </button>
      {error && (
        <p className="error-text" role="alert">
          Evidence bundle unavailable: {error}
        </p>
      )}
    </div>
  );
}

export function RepairPanel({
  run,
  hasFinding,
  status,
  onUpdated,
}: {
  run: Run;
  hasFinding: boolean;
  status: AsyncState<Status>;
  onUpdated: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [notStarted, setNotStarted] = useState<Repair | null>(null);
  const repair = run.repair ?? notStarted;
  const active = run.state === "queued" || run.state === "running";
  const repairRunning = run.repair?.status === "running";
  const uploads = status.status === "ok" && status.data.uploads_enabled;

  const start = async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await api.repair(run.id);
      if (!res.started && res.repair) setNotStarted(res.repair);
      onUpdated();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Section id="run-repair" title="Repair and export" eyebrow="Candidates are checked against the unchanged contract">
      <div className="stack">
        {!hasFinding && run.state === "complete" && (
          <p className="muted">Repair applies to runs with a counterexample. This run has none from these methods.</p>
        )}
        {hasFinding && !run.recorded && (
          <>
            <div className="action-row">
              <button type="button" className="btn btn-primary" onClick={start} disabled={busy || active || repairRunning} aria-busy={busy}>
                {busy ? <LoaderCircle className="spin" size={16} aria-hidden="true" /> : <Bot size={16} aria-hidden="true" />}
                Propose a repair with Nemotron
              </button>
              <span className="muted small">Up to 3 attempts. Only the DUT source may change; the contract, checks, and tools stay frozen.</span>
            </div>
          </>
        )}
        {hasFinding && run.recorded && <p className="muted small">Recorded runs are read-only. Start a live run of this example to request or check a repair.</p>}
        {error ? <ErrorNotice error={error} title="Repair request failed" /> : null}
        <div aria-live="polite">{repair && <RepairState repair={repair} />}</div>
        {hasFinding &&
          !run.recorded &&
          (uploads ? (
            <EditCandidate runId={run.id} onSubmitted={onUpdated} />
          ) : (
            <Callout kind="info" icon={Pencil} title="Editing RTL yourself is disabled in this build">
              <p className="small">
                User-edited candidates need uploads enabled on a local, owner-controlled server (
                <code>COUNTERTRACE_PUBLIC_UPLOADS_ENABLED=true</code>).
              </p>
            </Callout>
          ))}
        <div className="export">
          <h3 className="subhead">Export</h3>
          <p className="muted small">
            The evidence bundle contains the report and the inputs needed to reproduce the deterministic checks for this run.
          </p>
          <BundleButton runId={run.id} disabled={active} />
        </div>
      </div>
    </Section>
  );
}
