import { Bot, CircleCheck, CircleHelp, CircleX, FileCheck2, History, LoaderCircle, Play, ShieldAlert, Ban } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type { Contract, Decision, Example, ExampleDetail, Interpretation, Profile, RunSummary, Status } from "../api/types";
import { CodeView } from "../components/CodeView";
import { Callout, Disclosure, ErrorNotice, Hash, Loading, Section, TableScroll } from "../components/common";
import { ModelCalls, ModelProvenance, ModelStatusNotice } from "../components/ModelResult";
import { Badge, VerdictBadge } from "../components/StatusBadge";
import { formatDateTime, hex, shortHash } from "../lib/format";
import { useAsync, type AsyncState } from "../lib/hooks";
import { href, navigate } from "../lib/route";

// ---------------------------------------------------------------------------------------------
function ExamplePicker({ examples, selected }: { examples: Example[]; selected: string | null }) {
  const groups: { split: Example["split"]; title: string; note: string }[] = [
    { split: "showcase", title: "Showcase", note: "Curated examples for a first look." },
    { split: "development", title: "Development", note: "Examples used while building and tuning the workbench." },
  ];
  return (
    <nav className="picker" aria-label="Bundled examples">
      {groups.map((g) => {
        const items = examples.filter((e) => e.split === g.split);
        if (items.length === 0) return null;
        return (
          <div key={g.split} className="picker-group">
            <h3 className="picker-heading">{g.title}</h3>
            <p className="muted small">{g.note}</p>
            <ul>
              {items.map((e) => (
                <li key={e.id}>
                  <a
                    href={href.setup(e.id)}
                    className={`picker-item${selected === e.id ? " active" : ""}`}
                    aria-current={selected === e.id ? "true" : undefined}
                    onClick={(ev) => {
                      ev.preventDefault();
                      navigate(href.setup(e.id), true);
                    }}
                  >
                    <span className="picker-title">{e.title}</span>
                    <span className="picker-meta">
                      depth {e.depth} · expected {e.expected}
                      <span className="sr-only"> (author's intent, not a result)</span>
                    </span>
                    {e.fault && <span className="picker-fault">{e.fault.summary}</span>}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        );
      })}
      <p className="muted small picker-footnote">
        “Expected faulty/correct” is the example author's intent, not a verification result.
      </p>
    </nav>
  );
}

// ---------------------------------------------------------------------------------------------
export function ContractView({ contract, hash }: { contract: Contract; hash?: string }) {
  return (
    <div className="contract">
      <div className="contract-meta">
        <span>
          Profile <code>{contract.profile}</code>
        </span>
        <span>
          Version <code>{contract.version}</code>
        </span>
        {hash && (
          <span>
            Hash <Hash value={hash} n={16} />
          </span>
        )}
        <span>
          Parameters{" "}
          {Object.entries(contract.parameters).map(([k, v]) => (
            <code key={k} className="param">
              {k}={v}
            </code>
          ))}
        </span>
      </div>

      <h4 className="subhead">Requirements</h4>
      <TableScroll label="Contract requirements">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">Row</th>
              <th scope="col">Condition</th>
              <th scope="col">Required behavior</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(contract.requirements).map(([id, r]) => (
              <tr key={id} tabIndex={0}>
                <td className="mono small">{id}</td>
                <th scope="row">{r.title}</th>
                <td>{r.text}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableScroll>

      <div className="grid-2">
        <div>
          <h4 className="subhead">Ports</h4>
          <TableScroll label="Ports">
            <table className="data-table compact">
              <thead>
                <tr>
                  <th scope="col">Port</th>
                  <th scope="col">Direction</th>
                  <th scope="col">Width</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(contract.ports).map(([name, p]) => (
                  <tr key={name}>
                    <th scope="row" className="mono">
                      {name}
                    </th>
                    <td>{p.direction}</td>
                    <td className="mono">
                      {p.width}
                      {typeof p.width === "string" && contract.parameters[p.width] !== undefined ? ` (${contract.parameters[p.width]})` : ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TableScroll>
        </div>
        <div>
          <h4 className="subhead">Checks</h4>
          <ul className="check-list">
            {Object.entries(contract.checks).map(([id, text]) => (
              <li key={id}>
                <code>{id}</code> {text}
              </li>
            ))}
          </ul>
          <h4 className="subhead">Sampling convention</h4>
          <p className="prose">{contract.sampling}</p>
        </div>
      </div>

      <h4 className="subhead">Assumptions</h4>
      <ul className="assumptions">
        {contract.assumptions.map((a) => (
          <li key={a}>{a}</li>
        ))}
      </ul>
    </div>
  );
}

// ---------------------------------------------------------------------------------------------
function TimingExampleTable({ profile }: { profile: Profile }) {
  const t = profile.timing_example;
  const q = (v: string[] | null) => (v === null ? "Unspecified" : v.length === 0 ? "[ ]" : `[${v.join(", ")}]`);
  return (
    <div>
      <p className="muted small">
        DEPTH {t.parameters.DEPTH}, WIDTH {t.parameters.WIDTH}. Symbols:{" "}
        {Object.entries(t.symbols).map(([k, v]) => (
          <span key={k} className="mono symbol">
            {k}={hex(v)}
          </span>
        ))}
        . Queues oldest first.
      </p>
      <TableScroll label="Depth-2 timing example (specified expectations)">
        <table className="data-table compact">
          <thead>
            <tr>
              <th scope="col">Edge</th>
              <th scope="col">Pre-edge queue</th>
              <th scope="col">rst</th>
              <th scope="col">wr_en</th>
              <th scope="col">rd_en</th>
              <th scope="col">din</th>
              <th scope="col">Accepted operation</th>
              <th scope="col">Post-edge queue</th>
              <th scope="col">Checked dout</th>
              <th scope="col">empty / full</th>
            </tr>
          </thead>
          <tbody>
            {t.edges.map((e) => (
              <tr key={e.cycle}>
                <th scope="row" className="mono">
                  {e.cycle}
                </th>
                <td className="mono">{q(e.pre)}</td>
                <td className="mono">{e.rst}</td>
                <td className="mono">{e.wr_en}</td>
                <td className="mono">{e.rd_en}</td>
                <td className="mono">{e.din}</td>
                <td>
                  {e.accepted}
                  <span className="muted small"> · {profile.contract.requirements[e.row]?.title ?? e.row}</span>
                </td>
                <td className="mono">{q(e.post)}</td>
                <td className="mono">{e.dout ?? <span className="muted">Not checked</span>}</td>
                <td className="mono">
                  {e.empty} / {e.full}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableScroll>
      <p className="muted small">{t.source}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------------------------
const DECISION: Record<Decision["status"], { tone: "info" | "fail" | "unresolved" | "neutral"; icon: typeof CircleCheck; label: string }> = {
  matches: { tone: "info", icon: CircleCheck, label: "Matches" },
  conflict: { tone: "fail", icon: CircleX, label: "Conflict" },
  unspecified: { tone: "unresolved", icon: CircleHelp, label: "Unspecified" },
  unsupported: { tone: "neutral", icon: Ban, label: "Unsupported" },
};

function InterpretationView({ result }: { result: Interpretation }) {
  const blocking = new Set(result.blocking ?? []);
  const needs = new Set(result.needs_decision ?? []);
  return (
    <div className="stack">
      <ModelStatusNotice result={result} what="Brief interpretation" />
      {result.result && (
        <>
          <ModelProvenance task="interpretation" />
          <p className="prose">{result.result.summary}</p>
          {blocking.size > 0 && (
            <Callout kind="error" icon={ShieldAlert} title="The brief conflicts with this contract" role="alert">
              <p>
                Blocking topics: <strong>{[...blocking].join(", ")}</strong>. The supported profile cannot change to match. Running
                verification checks this contract, not the brief's request.
              </p>
            </Callout>
          )}
          {needs.size > 0 && (
            <Callout kind="warn" title="Decisions the brief leaves open">
              <p>
                The contract fixes these behaviors; confirm they are what you intend: <strong>{[...needs].join(", ")}</strong>.
              </p>
            </Callout>
          )}
          <TableScroll label="Interpretation decisions">
            <table className="data-table">
              <thead>
                <tr>
                  <th scope="col">Topic</th>
                  <th scope="col">Contract behavior</th>
                  <th scope="col">Brief says</th>
                  <th scope="col">Status</th>
                </tr>
              </thead>
              <tbody>
                {result.result.decisions.map((d, i) => {
                  const spec = DECISION[d.status] ?? DECISION.unspecified;
                  return (
                    <tr key={i} className={blocking.has(d.topic) ? "row-bad" : needs.has(d.topic) ? "row-warn" : undefined}>
                      <th scope="row">
                        {d.topic}
                        {blocking.has(d.topic) && <span className="tag tag-fail">blocking</span>}
                        {needs.has(d.topic) && <span className="tag tag-warn">needs decision</span>}
                      </th>
                      <td>{d.contract}</td>
                      <td>{d.brief_says}</td>
                      <td>
                        <Badge tone={spec.tone} icon={spec.icon}>
                          {spec.label}
                        </Badge>
                        {d.note && <p className="muted small">{d.note}</p>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </TableScroll>
          {result.result.backend_filled !== undefined && result.result.backend_filled !== null && (
            <Disclosure summary="Fields filled by the backend, not the model">
              <pre className="json">{JSON.stringify(result.result.backend_filled, null, 2)}</pre>
            </Disclosure>
          )}
        </>
      )}
      <ModelCalls calls={result.calls} />
    </div>
  );
}

// ---------------------------------------------------------------------------------------------
function ExampleDetailView({ detail, profile, status }: { detail: ExampleDetail; profile: AsyncState<Profile>; status: AsyncState<Status> }) {
  const [interp, setInterp] = useState<{ busy: boolean; result: Interpretation | null; error: unknown }>({ busy: false, result: null, error: null });
  const [accepted, setAccepted] = useState<string | null>(null);
  const [ackConflict, setAckConflict] = useState(false);
  const [launch, setLaunch] = useState<{ busy: boolean; error: unknown }>({ busy: false, error: null });
  const previous = useAsync(() => api.runs(), [detail.id]);

  useEffect(() => {
    setInterp({ busy: false, result: null, error: null });
    setAccepted(null);
    setAckConflict(false);
    setLaunch({ busy: false, error: null });
  }, [detail.id]);

  const blocking = interp.result?.blocking ?? [];
  const needsAck = blocking.length > 0;
  const version = detail.contract.version;
  const isAccepted = accepted === detail.contract_hash;
  const verifierReady = status.status === "ok" && status.data.verifier.docker && status.data.verifier.image_built;

  const interpret = async () => {
    setInterp({ busy: true, result: null, error: null });
    try {
      const result = await api.interpret(detail.id);
      setInterp({ busy: false, result, error: null });
    } catch (error) {
      setInterp({ busy: false, result: null, error });
    }
  };

  const run = async () => {
    if (!isAccepted) return;
    setLaunch({ busy: true, error: null });
    try {
      const summary = await api.createRun(detail.id, detail.contract_hash);
      navigate(href.run(summary.id));
    } catch (error) {
      setLaunch({ busy: false, error });
    }
  };

  const priorRuns: RunSummary[] =
    previous.status === "ok" ? previous.data.filter((r) => r.example_id === detail.id && r.kind === "verification").slice(0, 5) : [];

  return (
    <div className="stack-lg">
      <Section
        title={detail.title}
        eyebrow={`${detail.split === "showcase" ? "Showcase" : "Development"} example · ${detail.id}`}
        actions={
          <Badge tone="neutral" icon={detail.expected === "faulty" ? CircleX : CircleCheck} title="Author's intent, not a result">
            Expected {detail.expected} (author's intent, not a result)
          </Badge>
        }
      >
        <div className="grid-2">
          <div>
            <h3 className="subhead">Brief</h3>
            <blockquote className="brief">{detail.brief}</blockquote>
            {detail.fault && (
              <div className="fault-note">
                <h3 className="subhead">Seeded fault (author's description)</h3>
                <p>{detail.fault.summary}</p>
                <p className="muted small">
                  Intended consequence: {detail.fault.intended_consequence} · category <code>{detail.fault.category}</code> · class{" "}
                  <code>{detail.fault.class}</code>
                </p>
              </div>
            )}
            <p className="muted small">
              Base design <code>{detail.base}</code> · DEPTH {detail.depth}
            </p>
          </div>
          <div>
            <h3 className="subhead">RTL source (read-only)</h3>
            <CodeView source={detail.source} label={`RTL source for ${detail.title}`} maxHeight={360} />
          </div>
        </div>
      </Section>

      <Section title={`Contract v${version} for DEPTH ${detail.depth}`} eyebrow="Exact contract you accept">
        <ContractView contract={detail.contract} hash={detail.contract_hash} />
      </Section>

      <Section title="Depth-2 timing example" eyebrow="Specified expectations (not executed results)">
        {profile.status === "ok" ? (
          <TimingExampleTable profile={profile.data} />
        ) : profile.status === "loading" ? (
          <Loading label="Loading timing example" />
        ) : (
          <ErrorNotice error={profile.error} title="Timing example unavailable" />
        )}
      </Section>

      <Section
        title="Interpret the brief"
        eyebrow="Optional · model-assisted"
        actions={
          <button type="button" className="btn btn-secondary" onClick={interpret} disabled={interp.busy} aria-busy={interp.busy}>
            {interp.busy ? <LoaderCircle className="spin" size={16} aria-hidden="true" /> : <Bot size={16} aria-hidden="true" />}
            {interp.busy ? "Interpreting…" : "Interpret brief with Nemotron"}
          </button>
        }
      >
        <p className="muted">
          Nemotron compares the brief with the fixed contract and lists matches, conflicts, open decisions, and unsupported requests. It
          cannot change the contract.
        </p>
        <div aria-live="polite">
          {interp.error ? <ErrorNotice error={interp.error} title="Interpretation request failed" /> : null}
          {interp.result && <InterpretationView result={interp.result} />}
        </div>
      </Section>

      <Section title="Accept and run" eyebrow="Live run in the isolated verifier">
        {status.status === "ok" && (
          <Callout kind="info" title="Data processing">
            <p>{status.data.data_notice}</p>
          </Callout>
        )}
        {needsAck && (
          <label className="check-row">
            <input type="checkbox" checked={ackConflict} onChange={(e) => setAckConflict(e.target.checked)} />
            <span>
              I understand verification checks contract v{version}, which conflicts with the brief on: {blocking.join(", ")}.
            </span>
          </label>
        )}
        <div className="action-row">
          <button
            type="button"
            className={`btn ${isAccepted ? "btn-secondary" : "btn-primary"}`}
            aria-pressed={isAccepted}
            disabled={needsAck && !ackConflict}
            onClick={() => setAccepted(isAccepted ? null : detail.contract_hash)}
          >
            <FileCheck2 size={16} aria-hidden="true" />
            {isAccepted ? `Accepted contract v${version} (${shortHash(detail.contract_hash)})` : `Accept contract v${version} (${shortHash(detail.contract_hash)})`}
          </button>
          <button type="button" className="btn btn-primary" disabled={!isAccepted || launch.busy || !verifierReady} onClick={run} aria-busy={launch.busy}>
            {launch.busy ? <LoaderCircle className="spin" size={16} aria-hidden="true" /> : <Play size={16} aria-hidden="true" />}
            {launch.busy ? "Starting…" : "Run verification"}
          </button>
        </div>
        {!isAccepted && <p className="muted small">Accept the exact contract version before running. A later contract change creates a new baseline.</p>}
        {!verifierReady && status.status === "ok" && (
          <Callout kind="warn" title="Verifier not ready">
            <p>Docker and the verifier image are required for a live run. Recorded runs remain inspectable.</p>
          </Callout>
        )}
        {launch.error ? <ErrorNotice error={launch.error} title="Could not start the run" /> : null}
        {priorRuns.length > 0 && (
          <div className="prior-runs">
            <h3 className="subhead">Earlier runs of this example</h3>
            <ul className="link-list">
              {priorRuns.map((r) => (
                <li key={r.id}>
                  <a href={href.run(r.id)}>
                    <span className="mono small">{formatDateTime(r.created_at)}</span>
                    <VerdictBadge headline={r.state === "complete" ? r.verdict?.headline : "pending"} />
                    {r.recorded ? (
                      <Badge tone="neutral" icon={History}>
                        Recorded
                      </Badge>
                    ) : (
                      <span className="muted small">{r.state}</span>
                    )}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}
      </Section>
    </div>
  );
}

// ---------------------------------------------------------------------------------------------
export function SetupView({
  exampleId,
  profile,
  status,
}: {
  exampleId: string | null;
  profile: AsyncState<Profile>;
  status: AsyncState<Status>;
}) {
  const examples = useAsync(() => api.examples(), []);
  const fallbackId = useMemo(() => {
    if (examples.status !== "ok") return null;
    return (examples.data.find((e) => e.split === "showcase") ?? examples.data[0])?.id ?? null;
  }, [examples]);
  const selectedId = exampleId ?? fallbackId;
  const detail = useAsync(() => (selectedId ? api.example(selectedId) : Promise.resolve(null)), [selectedId]);

  return (
    <div className="setup-layout">
      <aside className="setup-aside">
        <h2 className="aside-title">Examples</h2>
        {examples.status === "loading" && <Loading label="Loading examples" />}
        {examples.status === "error" && <ErrorNotice error={examples.error} title="Examples unavailable" onRetry={examples.reload} />}
        {examples.status === "ok" &&
          (examples.data.length === 0 ? <p className="muted">No bundled examples are available.</p> : <ExamplePicker examples={examples.data} selected={selectedId} />)}
      </aside>
      <div className="setup-main">
        <div className="intro">
          <h1>Contract setup</h1>
          <p className="lede">
            Pick a bundled FIFO, review the exact contract it will be checked against, then accept that version and run. Countertrace
            shows the first failing cycle sequence and which method found it; it never labels a design “verified”.
          </p>
        </div>
        {!selectedId && examples.status === "ok" && <p className="muted">Select an example.</p>}
        {detail.status === "loading" && selectedId && <Loading label="Loading example" />}
        {detail.status === "error" && <ErrorNotice error={detail.error} title={`Example ${selectedId} unavailable`} onRetry={detail.reload} />}
        {detail.status === "ok" && detail.data && <ExampleDetailView key={detail.data.id} detail={detail.data} profile={profile} status={status} />}
      </div>
    </div>
  );
}

