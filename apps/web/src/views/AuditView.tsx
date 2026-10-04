import { Ban, Bot, CircleCheck, CircleHelp, CircleX, Equal, EyeOff, FlaskConical, GraduationCap, LoaderCircle, Play, ScanSearch, ShieldAlert, Wrench, type LucideIcon } from "lucide-react";
import { useMemo, useState } from "react";
import { api } from "../api/client";
import type { Audit, CheckSet, CheckSetProposal, Mutant, MutantClassification, Profile, Run } from "../api/types";
import { Callout, Disclosure, ErrorNotice, KeyValue, Loading, Section, TableScroll } from "../components/common";
import { ModelCalls, ModelStatusNotice } from "../components/ModelResult";
import { Badge, type Tone } from "../components/StatusBadge";
import { formatDateTime, humanize } from "../lib/format";
import { useAsync, type AsyncState } from "../lib/hooks";
import { href, navigate } from "../lib/route";
import { StagesPanel } from "./run/StagesPanel";

type ClassSpec = { title: string; note: string; tone: Tone; icon: LucideIcon };

const CLASSIFICATION: Record<string, ClassSpec> = {
  valid_fault: {
    title: "Valid faults",
    note: "The mandatory core checks caught each of these as a real contract violation. Only these count toward the supplemental set's score.",
    tone: "info",
    icon: ScanSearch,
  },
  equivalent: {
    title: "Equivalent mutants",
    note: "The change does not alter contract-visible behavior. They are excluded from the score; no check should kill them.",
    tone: "neutral",
    icon: Equal,
  },
  unresolved: {
    title: "Unresolved mutants",
    note: "Neither a violation nor equivalence was established (for example a timeout or a bounded result only). Excluded from the score.",
    tone: "unresolved",
    icon: CircleHelp,
  },
  invalid: {
    title: "Invalid mutants",
    note: "The mutant could not be built or admitted, so it says nothing about the check set. Excluded from the score.",
    tone: "toolerror",
    icon: Wrench,
  },
  baseline_clean: {
    title: "Baseline control",
    note: "The unmutated base design. The core found no violation, which shows the harness does not flag a correct design here. Not scored.",
    tone: "neutral",
    icon: FlaskConical,
  },
};

const CLASS_ORDER = ["valid_fault", "equivalent", "unresolved", "invalid", "baseline_clean"];

function classSpec(cls: MutantClassification): ClassSpec {
  return CLASSIFICATION[cls] ?? { title: `Other: ${cls}`, note: "Classification reported by the backend.", tone: "neutral", icon: CircleHelp };
}

export function ReviewedBadge({ set }: { set: Pick<CheckSet, "reviewed"> }) {
  if (set.reviewed === false)
    return (
      <Badge tone="unresolved" icon={Bot}>
        Model-proposed, not reviewed
      </Badge>
    );
  return null;
}

function CoreCell({ m }: { m: Mutant }) {
  if (m.core.status === "killed")
    return (
      <>
        <Badge tone="info" icon={ScanSearch}>
          Core detected it
        </Badge>
        {m.core.first && (
          <p className="muted small">
            <code>{m.core.first.check}</code> at cycle {m.core.first.cycle} in {m.core.first.test}
            {m.core.first.requirement_id ? ` · row ${m.core.first.requirement_id}` : ""}
          </p>
        )}
      </>
    );
  if (m.core.status === "survived")
    return (
      <Badge tone="neutral" icon={Ban}>
        Core found no violation
      </Badge>
    );
  return (
    <Badge tone="toolerror" icon={Wrench}>
      Core error
    </Badge>
  );
}

function SupplementalCell({ m }: { m: Mutant }) {
  if (m.supplemental.status === "killed")
    return (
      <>
        <Badge tone="sim" icon={CircleCheck}>
          Killed by the set
        </Badge>
        <p className="muted small">
          by{" "}
          {m.supplemental.by.map((b, i) => (
            <span key={b}>
              {i > 0 ? ", " : ""}
              <code>{b}</code>
            </span>
          ))}
          {m.supplemental.first_cycle !== null ? ` at cycle ${m.supplemental.first_cycle}` : ""}
        </p>
      </>
    );
  if (m.supplemental.status === "survived")
    return (
      <Badge tone="unresolved" icon={ShieldAlert}>
        Survived the set
      </Badge>
    );
  return <span className="muted">Not applicable</span>;
}

function MutantTable({ mutants, cls, requirements, revealed }: { mutants: Mutant[]; cls: MutantClassification; requirements: Audit["requirements"]; revealed: boolean }) {
  const spec = classSpec(cls);
  return (
    <div className="method-group">
      <h3 className="subhead">
        <Badge tone={spec.tone} icon={spec.icon}>
          {spec.title}
        </Badge>{" "}
        <span className="muted small">{mutants.length}</span>
      </h3>
      <p className="muted small">{spec.note}</p>
      {mutants.length === 0 ? (
        <p className="muted small">None.</p>
      ) : (
        <TableScroll label={spec.title}>
          <table className="data-table mutant-table">
            <thead>
              <tr>
                <th scope="col">Seeded fault</th>
                <th scope="col">Targets</th>
                <th scope="col">Mandatory core (validity)</th>
                <th scope="col">Formal</th>
                <th scope="col">Supplemental set</th>
                <th scope="col">Missing requirements</th>
              </tr>
            </thead>
            <tbody>
              {mutants.map((m) => (
                <tr key={m.fault_id} className={m.supplemental.status === "survived" && cls === "valid_fault" ? "row-warn" : undefined}>
                  <th scope="row">
                    {m.summary}
                    <p className="mono small muted">{m.fault_id}</p>
                    {m.note && <p className="small muted">{m.note}</p>}
                  </th>
                  <td>
                    {m.target_requirement ? requirements[m.target_requirement]?.title ?? m.target_requirement : "—"}
                    <p className="small muted">
                      {humanize(m.category)}
                      {m.class ? ` · ${m.class}` : ""}
                    </p>
                  </td>
                  <td>
                    <CoreCell m={m} />
                  </td>
                  <td className="small">{humanize(m.formal.status)}</td>
                  <td>
                    <SupplementalCell m={m} />
                  </td>
                  <td>
                    {!revealed && m.missing_requirements.length > 0 ? (
                      <span className="muted small hidden-answer">
                        <EyeOff size={14} aria-hidden="true" /> Hidden until you answer the exercise
                      </span>
                    ) : m.missing_requirements.length === 0 ? (
                      <span className="muted">—</span>
                    ) : (
                      <ul className="plain-list">
                        {m.missing_requirements.map((r) => (
                          <li key={r}>{requirements[r]?.title ?? r}</li>
                        ))}
                      </ul>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableScroll>
      )}
    </div>
  );
}

export function exerciseAnswer(audit: Audit): string[] {
  return Object.entries(audit.requirements).filter(([, r]) => !r.covered_by_set && r.surviving_faults.length > 0).map(([id]) => id);
}

/** Feedback for a multi-select answer: which choices were right, which correct ones were missed, and which were wrong. */
export function gradeExercise(answer: string[], chosen: string[]): { correct: string[]; missed: string[]; wrong: string[] } {
  return {
    correct: chosen.filter((id) => answer.includes(id)),
    missed: answer.filter((id) => !chosen.includes(id)),
    wrong: chosen.filter((id) => !answer.includes(id)),
  };
}

function NameList({ ids, titles }: { ids: string[]; titles: Record<string, string> }) {
  return (
    <>
      {ids.map((id, i) => (
        <span key={id}>
          {i > 0 ? (i === ids.length - 1 ? " and " : ", ") : ""}
          <strong>{titles[id] ?? id}</strong>
        </span>
      ))}
    </>
  );
}

function Exercise({
  audit,
  requirementTitles,
  revealed,
  onReveal,
}: {
  audit: Audit;
  requirementTitles: Record<string, string>;
  revealed: boolean;
  onReveal: (value: boolean) => void;
}) {
  const answer = useMemo(() => exerciseAnswer(audit), [audit]);
  const options = Object.keys(requirementTitles);
  const [chosen, setChosen] = useState<string[]>([]);
  const [skipped, setSkipped] = useState(false);
  const setRevealed = (value: boolean) => onReveal(value);
  if (answer.length === 0 || options.length === 0) return null;
  const titles: Record<string, string> = {};
  for (const id of answer) titles[id] = requirementTitles[id] ?? audit.requirements[id]?.title ?? id;
  for (const id of options) titles[id] = requirementTitles[id] ?? id;
  const grade = gradeExercise(answer, chosen);
  const allRight = grade.missed.length === 0 && grade.wrong.length === 0;
  const toggle = (id: string, on: boolean) => setChosen((list) => (on ? [...list.filter((x) => x !== id), id] : list.filter((x) => x !== id)));
  const ordered = (ids: string[]) => options.filter((id) => ids.includes(id)).concat(ids.filter((id) => !options.includes(id)));
  return (
    <Section title="Learner exercise" eyebrow="Answer first: the requirement analysis below stays hidden until you do">
      <form
        className="exercise"
        onSubmit={(e) => {
          e.preventDefault();
          if (chosen.length) setRevealed(true);
        }}
      >
        <fieldset>
          <legend>
            <GraduationCap size={16} aria-hidden="true" /> Which requirements is this check set missing?
          </legend>
          <p className="muted small" id="exercise-hint">
            {audit.summary.supplemental_survived} valid seeded faults survived this check set. Use the seeded-fault tables below as evidence:
            which contract conditions do the survivors target that the set never checks? Select every one that applies; more than one can be
            correct.
          </p>
          <div className="options">
            {options.map((id) => (
              <label key={id} className="option">
                <input
                  type="checkbox"
                  name="missing-req"
                  aria-label={titles[id]}
                  aria-describedby="exercise-hint"
                  checked={chosen.includes(id)}
                  onChange={(e) => toggle(id, e.target.checked)}
                  disabled={revealed}
                />
                <span aria-hidden="true">{titles[id]}</span>
              </label>
            ))}
          </div>
        </fieldset>
        <div className="action-row">
          <button type="submit" className="btn btn-primary" disabled={chosen.length === 0 || revealed}>
            Check my answer
          </button>
          {!revealed && (
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => {
                setSkipped(true);
                setRevealed(true);
              }}
            >
              Skip and show the answer
            </button>
          )}
          {revealed && (
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => {
                setRevealed(false);
                setSkipped(false);
                setChosen([]);
              }}
            >
              Try again
            </button>
          )}
        </div>
        {revealed && (
          <div role="status" className={`exercise-result ${!skipped && allRight ? "ok" : "bad"}`}>
            {skipped ? (
              <p>
                <GraduationCap size={16} aria-hidden="true" /> <strong>The answer.</strong>
              </p>
            ) : (
              <>
                <p>
                  {allRight ? <CircleCheck size={16} aria-hidden="true" /> : <CircleX size={16} aria-hidden="true" />}{" "}
                  <strong>{allRight ? "All correct." : grade.correct.length > 0 ? "Partly right." : "Not quite."}</strong>
                </p>
                <ul className="plain-list exercise-grade">
                  {grade.correct.length > 0 && (
                    <li>
                      Correct: <NameList ids={ordered(grade.correct)} titles={titles} />.
                    </li>
                  )}
                  {grade.missed.length > 0 && (
                    <li>
                      Missed: <NameList ids={ordered(grade.missed)} titles={titles} />. The set never checks {grade.missed.length === 1 ? "it" : "them"}, and valid
                      faults survive there.
                    </li>
                  )}
                  {grade.wrong.length > 0 && (
                    <li>
                      Not missing: <NameList ids={ordered(grade.wrong)} titles={titles} />. The set checks{" "}
                      {grade.wrong.length === 1 ? "it" : "them"}, or no valid fault survives there.
                    </li>
                  )}
                </ul>
              </>
            )}
            <p>
              The set does not cover <NameList ids={ordered(answer)} titles={titles} />, and valid faults survive there:{" "}
              {answer.flatMap((id) => audit.requirements[id]?.surviving_faults ?? []).map((f, i) => (
                <span key={f}>
                  {i > 0 ? ", " : ""}
                  <code>{f}</code>
                </span>
              ))}
              .
            </p>
          </div>
        )}
      </form>
    </Section>
  );
}

export function AuditResult({ run, profile, now }: { run: Run; profile: AsyncState<Profile>; now: number }) {
  const audit = run.audit;
  if (!audit) {
    return run.state === "queued" || run.state === "running" ? (
      <Loading label="Audit starting" />
    ) : (
      <Callout kind="warn" title="No audit data recorded">
        <p>This run has no audit results{run.error ? `: ${run.error}` : "."}</p>
      </Callout>
    );
  }
  return <AuditBody run={run} audit={audit} profile={profile} now={now} />;
}

function AuditBody({ run, audit, profile, now }: { run: Run; audit: Audit; profile: AsyncState<Profile>; now: number }) {
  const [revealed, setRevealed] = useState(false);
  const hasExercise = exerciseAnswer(audit).length > 0;
  const showAnswers = revealed || !hasExercise;
  const s = audit.summary;
  const byClass = (c: MutantClassification) => audit.mutants.filter((m) => m.classification === c);
  const classes = [...CLASS_ORDER, ...new Set(audit.mutants.map((m) => m.classification).filter((c) => !CLASS_ORDER.includes(c)))];
  const requirementTitles: Record<string, string> = {};
  const contractReqs = profile.status === "ok" ? profile.data.contract.requirements : {};
  for (const [id, r] of Object.entries(contractReqs)) requirementTitles[id] = r.title;
  for (const [id, r] of Object.entries(audit.requirements)) requirementTitles[id] = r.title || requirementTitles[id] || id;

  return (
    <div className="stack-lg">
      <AuditScopeNote />
      {(run.state === "queued" || run.state === "running") && (
        <Section title="Stages" eyebrow="Audit progress">
          <StagesPanel stages={audit.stages} now={now} />
        </Section>
      )}
      <Section title={`Check set: ${audit.check_set.label}`} eyebrow={`Seeded fault library ${audit.library_version} · base ${audit.base} · DEPTH ${audit.depth}`}>
        <div className="action-row">
          <ReviewedBadge set={audit.check_set} />
        </div>
        <p className="prose">{audit.check_set.description}</p>
        <p className="muted small">Origin: {audit.check_set.origin}</p>
        <KeyValue
          items={[
            ["Tests the set observes", audit.set_tests && audit.set_tests.length ? audit.set_tests.join(", ") : "All frozen-suite tests"],
            ["Contract rows its tests exercise", audit.set_rows_exercised && audit.set_rows_exercised.length ? audit.set_rows_exercised.join(", ") : "—"],
            ["Frozen stimulus (core)", audit.stimulus && audit.stimulus.length ? `${audit.stimulus.length} tests` : "—"],
          ]}
        />
        <ul className="stat-row">
          <li>
            <span className="stat-value">
              {s.supplemental_killed} of {s.valid_faults}
            </span>
            <span className="stat-label">valid faults killed by the supplemental set</span>
          </li>
          <li>
            <span className="stat-value">{s.supplemental_survived}</span>
            <span className="stat-label">valid faults survived the set</span>
          </li>
          <li>
            <span className="stat-value">{s.equivalent}</span>
            <span className="stat-label">equivalent (excluded)</span>
          </li>
          <li>
            <span className="stat-value">{s.unresolved}</span>
            <span className="stat-label">unresolved (excluded)</span>
          </li>
          <li>
            <span className="stat-value">{s.invalid}</span>
            <span className="stat-label">invalid (excluded)</span>
          </li>
          <li>
            <span className="stat-value">{s.mutants}</span>
            <span className="stat-label">seeded faults in total</span>
          </li>
        </ul>
        <p className="muted small">
          {s.note ??
            "This scores the named supplemental check set only. It is not a design-confidence score, and the mandatory core still decides whether each seeded fault is a real violation."}
        </p>
        {audit.tool_versions && (
          <Disclosure summary="Tool versions">
            <KeyValue items={Object.entries(audit.tool_versions).map(([k, v]) => [k, <code key={k}>{v}</code>])} />
          </Disclosure>
        )}
      </Section>
      <Exercise audit={audit} requirementTitles={requirementTitles} revealed={revealed} onReveal={setRevealed} />
      <Section title="Seeded faults by classification">
        <div className="stack-lg">
          {classes.map((c) => (
            <MutantTable key={c} mutants={byClass(c)} cls={c} requirements={audit.requirements} revealed={showAnswers} />
          ))}
        </div>
      </Section>
      {!(run.state === "queued" || run.state === "running") && (
        <Section title="Stages" eyebrow="Completed stages" className="panel-quiet">
          <StagesPanel stages={audit.stages} now={now} compact />
        </Section>
      )}
      {!showAnswers ? (
        <Section title="Requirements covered by this check set">
          <p className="muted hidden-answer">
            <EyeOff size={16} aria-hidden="true" /> Hidden until you answer the learner exercise above: this table names the requirements the
            set never checks.
          </p>
        </Section>
      ) : (
      <Section title="Requirements covered by this check set">
        <p className="muted small">
          “Exercised” means the set's tests drive that condition; “checked” means the set compares an output there. A requirement can be
          exercised without being checked.
        </p>
        <TableScroll label="Requirement coverage by the check set">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col">Requirement</th>
                <th scope="col">Exercised by the set's tests</th>
                <th scope="col">Checked by the set</th>
                <th scope="col">Surviving valid faults</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(audit.requirements).map(([id, r]) => (
                <tr key={id} className={!r.covered_by_set && r.surviving_faults.length ? "row-warn" : undefined}>
                  <th scope="row">
                    {r.title}
                    <p className="mono small muted">{id}</p>
                  </th>
                  <td>
                    {r.exercised_by_set === undefined ? (
                      <span className="muted">—</span>
                    ) : r.exercised_by_set ? (
                      <span>Exercised</span>
                    ) : (
                      <span className="muted">Never exercised</span>
                    )}
                  </td>
                  <td>
                    {r.covered_by_set ? (
                      <Badge tone="info" icon={CircleCheck}>
                        Covered
                      </Badge>
                    ) : (
                      <Badge tone="unresolved" icon={ShieldAlert}>
                        Not covered
                      </Badge>
                    )}
                  </td>
                  <td>
                    {r.surviving_faults.length === 0 ? (
                      <span className="muted">None</span>
                    ) : (
                      <>
                        {r.surviving_faults.map((f) => (
                          <code key={f} className="chip">
                            {f}
                          </code>
                        ))}
                        {!r.covered_by_set && <p className="small warn-text">Surviving faults point to this missing requirement.</p>}
                        {r.covered_by_set && <p className="small muted">Checked, yet a valid fault survived here.</p>}
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableScroll>
      </Section>
      )}
    </div>
  );
}

function AuditScopeNote() {
  return (
    <Callout kind="info" title="What this audit measures">
      <p>
        It audits a <strong>named supplemental check set</strong> by seeding known faults into a correct FIFO. It does not evaluate your
        testbench and it is not a confidence score for any design. The mandatory core checks still identify every fault; the supplemental set
        is scored only on faults the core confirms are real violations.
      </p>
    </Callout>
  );
}

function CheckSetCard({ set, selected, onSelect }: { set: CheckSet; selected: boolean; onSelect: () => void }) {
  return (
    <li>
      <label className={`checkset${selected ? " active" : ""}`}>
        <input type="radio" name="check-set" checked={selected} onChange={onSelect} />
        <span>
          <span className="checkset-title">{set.label}</span> <ReviewedBadge set={set} />
          <span className="checkset-desc">{set.description}</span>
          <span className="muted small">
            {set.origin}
            {set.tests && set.tests.length ? ` · observes tests: ${set.tests.join(", ")}` : " · observes all frozen-suite tests"}
          </span>
        </span>
      </label>
      {selected && (
        <TableScroll label={`Checks in ${set.label}`}>
          <table className="data-table compact">
            <thead>
              <tr>
                <th scope="col">Check</th>
                <th scope="col">Kind</th>
                <th scope="col">Requirement</th>
                <th scope="col">Rows</th>
                <th scope="col">Text</th>
              </tr>
            </thead>
            <tbody>
              {set.checks.map((c) => (
                <tr key={c.id}>
                  <th scope="row" className="mono small">
                    {c.id}
                  </th>
                  <td className="mono small">{c.check}</td>
                  <td className="mono small">{c.requirement}</td>
                  <td className="mono small">{c.rows ? c.rows.join(", ") : "all"}</td>
                  <td>{c.text}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableScroll>
      )}
    </li>
  );
}

function ProposeCheckSet({ depth, onProposed }: { depth: number; onProposed: (set: CheckSet) => void }) {
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [result, setResult] = useState<CheckSetProposal | null>(null);

  const submit = async () => {
    if (!description.trim()) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.proposeCheckSet(description.trim(), depth);
      setResult(res);
      if (res.check_set) onProposed(res.check_set);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form
      className="stack"
      onSubmit={(e) => {
        e.preventDefault();
        void submit();
      }}
    >
      <p className="muted small">
        Describe the checks your own testbench makes, in words. Nemotron maps the description onto the reviewed check templates, contract rows,
        and frozen-suite tests only; it does not read or run your testbench. The proposal is saved as an unreviewed candidate you can audit like
        any other set.
      </p>
      <label htmlFor="propose-desc" className="field-label">
        Describe your testbench checks
      </label>
      <textarea
        id="propose-desc"
        className="code-input prose-input"
        rows={4}
        value={description}
        maxLength={4000}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="For example: after reset I check empty is high; I fill the FIFO and check full; I read everything back and compare the order."
      />
      <div className="action-row">
        <button type="submit" className="btn btn-secondary" disabled={busy || !description.trim()} aria-busy={busy}>
          {busy ? <LoaderCircle className="spin" size={16} aria-hidden="true" /> : <Bot size={16} aria-hidden="true" />}
          {busy ? "Proposing…" : "Propose a check set with Nemotron"}
        </button>
      </div>
      <div aria-live="polite" className="stack">
        {error ? <ErrorNotice error={error} title="Proposal request failed" /> : null}
        {result && <ModelStatusNotice result={result} what="Check-set proposal" />}
        {result?.check_set && (
          <Callout kind="info" icon={Bot} title={`Proposed: ${result.check_set.label}`} role="status">
            <p>
              Saved as a model-proposed, unreviewed candidate and selected above. Audit it to see which seeded faults it catches; review its
              checks before relying on it.
            </p>
          </Callout>
        )}
        {result && <ModelCalls calls={result.calls} />}
      </div>
    </form>
  );
}

export function AuditView({ profile }: { profile: AsyncState<Profile> }) {
  const sets = useAsync(() => api.checkSets(), []);
  const runs = useAsync(() => api.runs(), []);
  const [chosen, setChosen] = useState<string | null>(null);
  const [depth, setDepth] = useState(4);
  const [launch, setLaunch] = useState<{ busy: boolean; error: unknown }>({ busy: false, error: null });
  const selected =
    chosen ??
    (sets.status === "ok" ? (sets.data.find((s) => s.id === "weak-learner-v1") ?? sets.data[0])?.id ?? null : null);
  const depths = profile.status === "ok" ? profile.data.supported_depths : [2, 4];
  const audits = runs.status === "ok" ? runs.data.filter((r) => r.kind === "audit") : [];

  const start = async () => {
    if (!selected) return;
    setLaunch({ busy: true, error: null });
    try {
      const summary = await api.createAudit(selected, depth);
      navigate(href.run(summary.id));
    } catch (error) {
      setLaunch({ busy: false, error });
    }
  };

  return (
    <div className="stack-lg page-narrow">
      <header className="notebook-hero">
        <div>
          <p className="eyebrow">The second question / Check-quality audit</p>
          <h1>What does this<br /><em>check set miss?</em></h1>
          <p className="lede">
            Seed known faults into a correct FIFO. See which ones a supplemental check set catches, and which requirements it never looks at.
          </p>
        </div>
        <aside className="notebook-hero-aside">
          <span className="notebook-margin-label">A different kind of evidence</span>
          <p>A surviving fault reveals a gap in the named check set. Independent core checks decide whether that fault violates the contract.</p>
          <a className="inline-link" href={href.runs()}>Explore the recorded cases</a>
        </aside>
      </header>
      <AuditScopeNote />
      <Section title="Choose a check set">
        {sets.status === "loading" && <Loading label="Loading check sets" />}
        {sets.status === "error" && <ErrorNotice error={sets.error} title="Check sets are not available from the backend right now" onRetry={sets.reload} />}
        {sets.status === "ok" &&
          (sets.data.length === 0 ? (
            <p className="muted">No supplemental check sets are available.</p>
          ) : (
            <div className="stack">
              <ul className="checkset-list" aria-label="Supplemental check sets">
                {sets.data.map((s) => (
                  <CheckSetCard key={s.id} set={s} selected={s.id === selected} onSelect={() => setChosen(s.id)} />
                ))}
              </ul>
              <div className="action-row">
                <label className="inline-field">
                  <span>DEPTH</span>
                  <select value={depth} onChange={(e) => setDepth(Number(e.target.value))}>
                    {depths.map((d) => (
                      <option key={d} value={d}>
                        {d}
                      </option>
                    ))}
                  </select>
                </label>
                <button type="button" className="btn btn-primary" onClick={start} disabled={!selected || launch.busy} aria-busy={launch.busy}>
                  {launch.busy ? <LoaderCircle className="spin" size={16} aria-hidden="true" /> : <Play size={16} aria-hidden="true" />}
                  Run audit
                </button>
              </div>
              {launch.error ? <ErrorNotice error={launch.error} title="Could not start the audit" /> : null}
            </div>
          ))}
      </Section>
      <Section title="Propose a check set from your description" eyebrow="Optional · model-assisted">
        <ProposeCheckSet
          depth={depth}
          onProposed={(set) => {
            setChosen(set.id);
            sets.reload();
          }}
        />
      </Section>
      <Section title="Earlier audits">
        {runs.status === "loading" && <Loading label="Loading runs" />}
        {runs.status === "error" && <ErrorNotice error={runs.error} onRetry={runs.reload} />}
        {runs.status === "ok" &&
          (audits.length === 0 ? (
            <p className="muted">No audits have been run on this server yet.</p>
          ) : (
            <ul className="link-list">
              {audits.map((a) => (
                <li key={a.id}>
                  <a href={href.run(a.id)}>
                    <span>{a.title}</span> <span className="mono small muted">{formatDateTime(a.created_at)}</span>{" "}
                    <span className="muted small">{a.state}</span>
                  </a>
                </li>
              ))}
            </ul>
          ))}
      </Section>
    </div>
  );
}
