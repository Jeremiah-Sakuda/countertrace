import { ArrowRight, Bot, LoaderCircle, TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { Explanation, Run } from "../../api/types";
import { CodeView } from "../../components/CodeView";
import { Disclosure, ErrorNotice, Section } from "../../components/common";
import { ModelCalls, ModelProvenance, ModelStatusNotice } from "../../components/ModelResult";
import { formatDuration } from "../../lib/format";
import { useNow } from "../../lib/hooks";
import { href } from "../../lib/route";

type CiteHandler = (cycle: number, origin?: { element: HTMLElement; label: string }) => void;

function ExplanationBody({ explanation, runId, onCite }: { explanation: Explanation; runId: string; onCite: CiteHandler }) {
  const r = explanation.result;
  const check = explanation.citation_check;
  const [source, setSource] = useState<string | null>(null);
  const [sourceError, setSourceError] = useState<unknown>(null);
  const lines = r?.likely_cause?.lines ?? [];

  useEffect(() => {
    if (lines.length === 0) return;
    let live = true;
    api.file(runId, "dut.v").then(
      (s) => live && setSource(s),
      (e: unknown) => live && setSourceError(e),
    );
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId, lines.join(",")]);

  return (
    <div className="stack">
      <ModelStatusNotice result={explanation} what="Explanation" />
      {r && (
        <article className="explanation" aria-label="Model-generated explanation">
          <ModelProvenance task="explanation" />
          {explanation.evidence_notice && <p className="callout-inline warn">{explanation.evidence_notice}</p>}
          {check && check.invalid.length > 0 && (
            <p className="callout-inline warn">
              <TriangleAlert size={14} aria-hidden="true" /> Some citations do not match the recorded evidence and are flagged below.
            </p>
          )}
          <p className="prose explanation-summary">{r.summary}</p>
          <h3 className="subhead">Steps</h3>
          <ol className="steps">
            {r.steps.map((step, i) => (
              <li key={i}>
                <p>{step.text}</p>
                <p className="citations">
                  {step.cycles.map((c) => {
                    const invalid = check?.invalid.some((citation) => citation.step === i && citation.kind === "cycle" && citation.value === c);
                    return invalid ? (
                      <span key={c} className="cite cite-invalid" title="This cycle is not in the recorded evidence for this finding">
                        <TriangleAlert size={12} aria-hidden="true" /> cycle {c} (invalid citation)
                      </span>
                    ) : (
                      <button key={c} type="button" className="cite cycle-link" onClick={(e) => onCite(c, { element: e.currentTarget, label: `Back to explanation step ${i + 1}` })} aria-label={`Show cycle ${c} in the cycle table`}>
                        cycle {c}
                      </button>
                    );
                  })}
                  {step.signals.map((s) => (
                    <code key={s} className="cite-signal">
                      {s}
                    </code>
                  ))}
                  {step.cycles.length === 0 && step.signals.length === 0 && <span className="cite cite-none">no evidence cited</span>}
                </p>
              </li>
            ))}
          </ol>
          <h3 className="subhead">Likely cause</h3>
          <p className="prose">{r.likely_cause.text}</p>
          {lines.length > 0 && (
            <div>
              <p className="muted small">RTL lines cited: {lines.join(", ")}</p>
              {source !== null ? (
                <CodeView source={source} label="Cited RTL lines" highlight={lines} only={{ lines, context: 2 }} />
              ) : sourceError ? (
                <ErrorNotice error={sourceError} title="Could not load dut.v to show the cited lines" />
              ) : null}
            </div>
          )}
          <h3 className="subhead">Suggested next action</h3>
          <p className="prose">{r.next_action}</p>
          <h3 className="subhead">Limits</h3>
          <p className="prose muted">{r.limits}</p>
        </article>
      )}
      {check && check.invalid.length > 0 && (
        <div className="citation-check">
          <h3 className="subhead">Citation check</h3>
          <ul className="open-list">
            {check.invalid.map((c, i) => (
              <li key={i}>
                <TriangleAlert size={14} aria-hidden="true" /> {c.step === null ? "Likely cause" : `Step ${c.step + 1}`}: invalid {c.kind} citation <code>{JSON.stringify(c.value)}</code>
              </li>
            ))}
          </ul>
        </div>
      )}
      {explanation.calls && explanation.calls.length > 0 && (
        <Disclosure summary="Model call details" meta="Model, endpoint, timing, and tokens">
          <ModelCalls calls={explanation.calls} />
        </Disclosure>
      )}
    </div>
  );
}

export function ExplanationPanel({ run, hasFinding, onCite, onUpdated }: { run: Run; hasFinding: boolean; onCite: CiteHandler; onUpdated: () => void }) {
  const [busy, setBusy] = useState(false);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [local, setLocal] = useState<Explanation | null>(null);
  const now = useNow(busy);
  const explanation = local ?? run.explanation ?? null;
  const active = run.state === "queued" || run.state === "running";

  const explain = async () => {
    setBusy(true);
    setError(null);
    setStartedAt(Date.now());
    try {
      const result = await api.explain(run.id);
      setLocal(result);
      onUpdated();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Section
      id="run-explanation"
      title="Explanation"
      eyebrow={run.recorded ? "Recorded model output · read-only · not part of the verdict" : "Model-generated · not part of the verdict"}
      actions={
        run.recorded ? (
          run.example_id && (
            <a className="btn btn-secondary" href={href.setup(run.example_id)}>
              Set up this example <ArrowRight size={16} aria-hidden="true" />
            </a>
          )
        ) : (
          <button type="button" className="btn btn-secondary" onClick={explain} disabled={busy || active || !hasFinding} aria-busy={busy}>
            {busy ? <LoaderCircle className="spin" size={16} aria-hidden="true" /> : <Bot size={16} aria-hidden="true" />}
            {busy ? "Explaining…" : explanation?.result ? "Explain again with Nemotron" : "Explain with Nemotron"}
          </button>
        )
      }
    >
      <div aria-live="polite">
        {!hasFinding && !explanation && <p className="muted">An explanation is available when the run has a counterexample to explain.</p>}
        {hasFinding && !explanation && !busy && !error && !run.recorded && (
          <p className="muted">
            Nemotron reads the recorded finding, trace window, and RTL, then explains the failing sequence with cycle citations. Citations
            are checked against the recorded trace.
          </p>
        )}
        {busy && startedAt !== null && (
          <p className="loading" role="status">
            <LoaderCircle className="spin" size={16} aria-hidden="true" /> Waiting for the model · {formatDuration((now - startedAt) / 1000)} elapsed. This can
            take tens of seconds.
          </p>
        )}
        {error ? <ErrorNotice error={error} title="Explanation request failed" /> : null}
        {explanation && <ExplanationBody explanation={explanation} runId={run.id} onCite={onCite} />}
      </div>
    </Section>
  );
}
