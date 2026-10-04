import { Bot, CircleCheck, CircleHelp, CircleX, FileCheck2, History, LoaderCircle, Lock, Play, ShieldAlert, Ban, Undo2 } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import type { Contract, Decision, Example, ExampleDetail, Interpretation, Profile, RecordedInterpretation, RunSummary, Status } from "../api/types";
import { CodeView } from "../components/CodeView";
import { Callout, Disclosure, ErrorNotice, Hash, Loading, Section, TableScroll } from "../components/common";
import { ModelCalls, ModelProvenance, ModelStatusNotice } from "../components/ModelResult";
import { ShowcaseTour } from "../components/ShowcaseTour";
import { Badge, VerdictBadge } from "../components/StatusBadge";
import { formatDate, formatDateTime, hex, modelName, shortHash } from "../lib/format";
import { useAsync, useDocumentTitle, type AsyncState } from "../lib/hooks";
import { href, navigate } from "../lib/route";

// ---------------------------------------------------------------------------------------------
function ExamplePicker({ examples, selected }: { examples: Example[]; selected: string | null }) {
  const groups: { split: Example["split"]; title: string; note: string }[] = [
    { split: "showcase", title: "Showcase", note: "Curated examples for a first look." },
    { split: "development", title: "Development", note: "Examples used while building and tuning the workbench." },
  ];
  return (
    <>
    <label className="notebook-example-select">
      <span>Bundled FIFO</span>
      <select value={selected ?? ""} onChange={(event) => navigate(href.setup(event.target.value), false)}>
        {groups.map((group) => (
          <optgroup key={group.split} label={group.title}>
            {examples.filter((example) => example.split === group.split).map((example) => (
              <option key={example.id} value={example.id}>{example.title} · depth {example.depth}</option>
            ))}
          </optgroup>
        ))}
      </select>
    </label>
    <nav className="picker notebook-example-index" aria-label="Bundled examples">
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
    </>
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

function InterpretationView({ result, recorded }: { result: Interpretation; recorded?: RecordedInterpretation }) {
  const blocking = new Set(result.blocking ?? []);
  const needs = new Set(result.needs_decision ?? []);
  const decisions = result.result?.decisions ?? [];
  const conflicts = decisions.filter((d) => d.status === "conflict").length;
  const table = result.result && (
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
          {decisions.map((d, i) => {
            const spec = DECISION[d.status] ?? DECISION.unspecified;
            return (
              <tr key={i} className={blocking.has(d.topic) ? "row-bad" : needs.has(d.topic) ? "row-warn" : undefined}>
                <th scope="row">
                  {d.topic}
                  {blocking.has(d.topic) && <span className="tag tag-fail">blocking</span>}
                  {needs.has(d.topic) && <span className="tag tag-warn">needs decision</span>}
                </th>
                <td>{d.contract}</td>
                <td>{d.brief_says ?? <span className="muted">Not mentioned</span>}</td>
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
  );
  return (
    <div className="stack">
      <ModelStatusNotice result={result} what="Brief interpretation" />
      {result.result && (
        <>
          {recorded ? (
            <p className="model-provenance">
              <History size={16} aria-hidden="true" />
              <span>
                <strong>Recorded model output, read-only.</strong> {modelName(recorded.calls?.[0]?.model_id)} compared this brief with the fixed
                contract{recorded.recorded_at ? ` on ${formatDate(recorded.recorded_at)}` : ""}. It is not part of any verdict and cannot change
                the contract.
              </span>
            </p>
          ) : (
            <ModelProvenance task="interpretation" />
          )}
          <p className="prose">{result.result.summary}</p>
          {blocking.size > 0 && (
            <Callout kind="error" icon={ShieldAlert} title="The brief conflicts with this contract" role={recorded ? undefined : "alert"}>
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
          {recorded ? (
            <Disclosure summary="Decisions by topic" meta={`${decisions.length} topics · ${conflicts} conflict${conflicts === 1 ? "" : "s"}`}>
              {table}
            </Disclosure>
          ) : (
            table
          )}
          {result.result.backend_filled !== undefined && result.result.backend_filled !== null && (
            <Disclosure summary="Fields filled by the backend, not the model">
              <pre className="json">{JSON.stringify(result.result.backend_filled, null, 2)}</pre>
            </Disclosure>
          )}
        </>
      )}
      {recorded ? (
        result.calls && result.calls.length > 0 && (
          <Disclosure summary="Recorded model call">
            <ModelCalls calls={result.calls} />
          </Disclosure>
        )
      ) : (
        <ModelCalls calls={result.calls} />
      )}
    </div>
  );
}

/** The stored interpretation for this example, visible without a model key. */
function RecordedInterpretationView({ recorded }: { recorded: RecordedInterpretation }) {
  const date = recorded.recorded_at ? formatDate(recorded.recorded_at) : null;
  return (
    <section className="recorded-interpretation" aria-labelledby="recorded-interpretation-title">
      <div className="recorded-interpretation-head">
        <History size={16} aria-hidden="true" />
        <h3 id="recorded-interpretation-title" className="subhead">
          Recorded interpretation ({modelName(recorded.calls?.[0]?.model_id)}{date ? `, ${date}` : ""})
        </h3>
      </div>
      <InterpretationView result={recorded} recorded={recorded} />
    </section>
  );
}

// ---------------------------------------------------------------------------------------------
function ExampleDetailView({ detail, profile, status }: { detail: ExampleDetail; profile: AsyncState<Profile>; status: AsyncState<Status> }) {
  const [interp, setInterp] = useState<{ busy: boolean; result: Interpretation | null; error: unknown }>({ busy: false, result: null, error: null });
  const [accepted, setAccepted] = useState<string | null>(null);
  const [ackConflict, setAckConflict] = useState(false);
  // Acceptance swaps the accept button for a stamp; move focus to the control that replaced the one the user pressed.
  const [toggled, setToggled] = useState(0);
  const [accepting, setAccepting] = useState(false);
  const acceptRef = useRef<HTMLButtonElement>(null);
  const withdrawRef = useRef<HTMLButtonElement>(null);
  const [launch, setLaunch] = useState<{ busy: boolean; error: unknown }>({ busy: false, error: null });
  const previous = useAsync(() => api.runs(), [detail.id]);

  useEffect(() => {
    setInterp({ busy: false, result: null, error: null });
    setAccepted(null);
    setAckConflict(false);
    setAccepting(false);
    setLaunch({ busy: false, error: null });
  }, [detail.id]);

  useEffect(() => {
    if (toggled === 0) return;
    (accepted ? withdrawRef : acceptRef).current?.focus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [toggled]);

  // A recorded interpretation counts only when it read this exact brief; a live result replaces it.
  const recorded = detail.recorded_interpretation && (!detail.recorded_interpretation.brief || detail.recorded_interpretation.brief === detail.brief)
    ? detail.recorded_interpretation
    : null;
  const blocking = (interp.result ?? recorded)?.blocking ?? [];
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

  // Pressing accept shows a busy state at once, then the acceptance stamp replaces the button and focus moves to "Withdraw".
  const accept = () => {
    if (accepting) return;
    setAccepting(true);
    const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.setTimeout(() => {
      setAccepting(false);
      setAccepted(detail.contract_hash);
      setToggled((n) => n + 1);
    }, reduce ? 0 : 220);
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
    <div className="stack-lg notebook-steps">
      <Section
        title={detail.title}
        className="notebook-step"
        eyebrow={<><span className="notebook-step-number">01</span> Inspect the input</>}
        actions={
          <Badge tone="neutral" icon={detail.expected === "faulty" ? CircleX : CircleCheck} title="Author's intent, not a result">
            Expected {detail.expected} · author's intent
          </Badge>
        }
      >
        <div className="notebook-specimen-meta">
          <span>{detail.split === "showcase" ? "Showcase" : "Development"} example</span>
          <span className="mono">{detail.id}</span>
          <span>{detail.depth} words × {detail.contract.parameters.WIDTH} bits</span>
        </div>
        <blockquote className="notebook-brief">{detail.brief}</blockquote>
        {detail.fault && (
          <div className="notebook-margin-note">
            <h3 className="subhead">The seeded fault</h3>
            <p>{detail.fault.summary}</p>
            <p className="muted small">This is the author's description. The verifier must establish the actual behavior.</p>
          </div>
        )}
        <Disclosure summary="Inspect the RTL source" meta={<span className="mono">dut.v · read-only</span>}>
          <CodeView source={detail.source} label={`RTL source for ${detail.title}`} maxHeight={400} />
          <p className="muted small">Base design <code>{detail.base}</code> · DEPTH {detail.depth}</p>
          {detail.fault && (
            <p className="muted small">
              Intended consequence: {detail.fault.intended_consequence} · category <code>{detail.fault.category}</code> · class <code>{detail.fault.class}</code>
            </p>
          )}
        </Disclosure>
      </Section>

      <Section
        title="Agree on what correct means."
        className="notebook-step"
        eyebrow={<><span className="notebook-step-number">02</span> Review the contract</>}
      >
        <p className="prose">This run checks contract v{version}, with {detail.contract.parameters.WIDTH}-bit words and a depth of {detail.depth}. These are three of its requirements; open the full reference before accepting.</p>
        <dl className="notebook-contract-summary">
          {["reset", "write_full", "read_not_empty"].map((key) => {
            const requirement = detail.contract.requirements[key];
            return requirement ? <div key={key}><dt>{requirement.title}</dt><dd>{requirement.text}</dd></div> : null;
          })}
        </dl>
        <Disclosure summary="Read the complete contract" meta={`v${version} · ${shortHash(detail.contract_hash)}`}>
          <h3 className="subhead">Exact requirements, ports, checks, and assumptions</h3>
          <ContractView contract={detail.contract} hash={detail.contract_hash} />
        </Disclosure>
        <Disclosure summary="Walk through a depth-2 timing example" meta="Specified expectations">
          <p className="muted small">These expectations illustrate the sampling convention. They are not executed results.</p>
          {profile.status === "ok" ? (
            <TimingExampleTable profile={profile.data} />
          ) : profile.status === "loading" ? (
            <Loading label="Loading timing example" />
          ) : (
            <ErrorNotice error={profile.error} title="Timing example unavailable" />
          )}
        </Disclosure>
        {recorded && <RecordedInterpretationView recorded={recorded} />}
        <Disclosure summary={recorded ? "Interpret the brief live with Nemotron" : "Ask Nemotron to interpret the brief"} meta={recorded ? "Needs a model key" : "Optional"}>
          <p className="prose">
            Compare the brief with the fixed contract to surface matches, conflicts, and open decisions. The model cannot change the contract.
            {recorded ? " A live result appears below and replaces the recorded one for the conflict check." : ""}
          </p>
          <p className="muted small">This sends the brief, RTL, and contract to the model endpoint; see the data notice above.</p>
          <button type="button" className="btn btn-secondary" onClick={interpret} disabled={interp.busy} aria-busy={interp.busy}>
            {interp.busy ? <LoaderCircle className="spin" size={16} aria-hidden="true" /> : <Bot size={16} aria-hidden="true" />}
            {interp.busy ? "Interpreting…" : "Interpret brief with Nemotron"}
          </button>
          <div aria-live="polite">
            {interp.error ? <ErrorNotice error={interp.error} title="Interpretation request failed" /> : null}
            {interp.result && <InterpretationView result={interp.result} />}
          </div>
        </Disclosure>
      </Section>

      <Section
        title="Let the evidence answer."
        className={`notebook-step notebook-launch${isAccepted ? " is-accepted" : ""}`}
        eyebrow={<><span className="notebook-step-number">03</span> Accept & run</>}
      >
        <p className="prose">Accept this exact contract, then run simulation and formal checks in the isolated verifier. The result will show what each method established and what remains unresolved.</p>
        {needsAck && (
          <label className="check-row">
            <input type="checkbox" checked={ackConflict} onChange={(e) => setAckConflict(e.target.checked)} />
            <span>I understand verification checks contract v{version}, which conflicts with the brief on: {blocking.join(", ")}.</span>
          </label>
        )}
        {isAccepted ? (
          <div className="accept-stamp" role="status">
            <Lock size={18} aria-hidden="true" />
            <div>
              <p className="accept-stamp-title">Contract v{version} accepted</p>
              <p className="small">
                Frozen at hash <Hash value={detail.contract_hash} n={16} />. This exact version is what the run checks.
              </p>
            </div>
            <button ref={withdrawRef} type="button" className="btn btn-ghost btn-sm" onClick={() => { setAccepted(null); setToggled((n) => n + 1); }}>
              <Undo2 size={14} aria-hidden="true" /> Withdraw acceptance
            </button>
          </div>
        ) : null}
        <div className="action-row">
          {!isAccepted && (
            <button
              ref={acceptRef}
              type="button"
              className={`btn btn-secondary${accepting ? " is-pressed" : ""}`}
              disabled={needsAck && !ackConflict}
              aria-busy={accepting}
              aria-disabled={accepting || undefined}
              onClick={accept}
            >
              {accepting ? <LoaderCircle className="spin" size={16} aria-hidden="true" /> : <FileCheck2 size={16} aria-hidden="true" />}
              {accepting ? `Accepting contract v${version}…` : `Accept contract v${version} (${shortHash(detail.contract_hash)})`}
            </button>
          )}
          <button type="button" className="btn btn-primary" disabled={!isAccepted || launch.busy || !verifierReady} onClick={run} aria-busy={launch.busy}>
            {launch.busy ? <LoaderCircle className="spin" size={16} aria-hidden="true" /> : <Play size={16} aria-hidden="true" />}
            {launch.busy ? "Starting…" : "Run verification"}
          </button>
        </div>
        {!isAccepted && <p className="muted small">Accept the exact contract version before running. A later contract change creates a new baseline.</p>}
        {!verifierReady && status.status === "ok" && (
          <Callout kind="warn" title="Verifier not ready">
            <p>Docker and the verifier image are required for a live run. <a href={href.runs()}>Recorded case files</a> remain inspectable.</p>
          </Callout>
        )}
        {launch.error ? <ErrorNotice error={launch.error} title="Could not start the run" /> : null}
        {priorRuns.length > 0 && (
          <Disclosure summary="Earlier runs of this example" meta={`${priorRuns.length} recent runs`}>
            <ul className="link-list prior-runs">
              {priorRuns.map((r) => (
                <li key={r.id}>
                  <a href={href.run(r.id)}>
                    <span className="mono small">{formatDateTime(r.created_at)}</span>{" "}
                    <VerdictBadge headline={r.state === "complete" ? r.verdict?.headline : "pending"} />{" "}
                    {r.recorded ? <Badge tone="neutral" icon={History}>Recorded</Badge> : <span className="muted small">{r.state}</span>}
                  </a>
                </li>
              ))}
            </ul>
          </Disclosure>
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
  useDocumentTitle(detail.status === "ok" && detail.data ? detail.data.title : "Contract setup");

  return (
    <div className="notebook-setup">
      <header className="notebook-hero landing-hero">
        <div>
          <p className="eyebrow">Countertrace · synchronous FIFO verification</p>
          <h1>
            Find the exact cycle your FIFO breaks, <em>see why, and check a fix against checks the AI can’t change.</em>
          </h1>
          <p className="lede">
            Simulation and formal tools run in an isolated verifier. NVIDIA Nemotron explains the failure and proposes a fix; independent,
            frozen checks decide whether it passes.
          </p>
        </div>
        <ShowcaseTour profile={profile} />
      </header>
      <div className="setup-intro">
        <h2 className="setup-intro-title">Or run one yourself</h2>
        <p className="muted small">Choose a bundled FIFO, review its contract, accept it, and run it in the local verifier.</p>
        {status.status === "ok" && (
          <p className="data-notice small">
            <ShieldAlert size={14} aria-hidden="true" /> <span>{status.data.data_notice}</span>
          </p>
        )}
      </div>
      <div className="notebook-setup-layout">
        <aside className="notebook-example-sidebar">
          <h2 className="aside-title">Choose your example</h2>
          {examples.status === "loading" && <Loading label="Loading examples" />}
          {examples.status === "error" && <ErrorNotice error={examples.error} title="Examples unavailable" onRetry={examples.reload} />}
          {examples.status === "ok" &&
            (examples.data.length === 0 ? <p className="muted">No bundled examples are available.</p> : <ExamplePicker examples={examples.data} selected={selectedId} />)}
        </aside>
        <div className="notebook-setup-main">
          {!selectedId && examples.status === "ok" && <p className="muted">Select an example.</p>}
          {detail.status === "loading" && selectedId && <Loading label="Loading example" />}
          {detail.status === "error" && <ErrorNotice error={detail.error} title={`Example ${selectedId} unavailable`} onRetry={detail.reload} />}
          {detail.status === "ok" && detail.data && <ExampleDetailView key={detail.data.id} detail={detail.data} profile={profile} status={status} />}
        </div>
      </div>
    </div>
  );
}
