import { ArrowLeft, ArrowRight, CircleX, Equal, Wrench } from "lucide-react";
import { api } from "../../api/client";
import type { Obligation, Run } from "../../api/types";
import { DiffView } from "../../components/CodeView";
import { Disclosure, ErrorNotice, Loading, Section, TableScroll } from "../../components/common";
import { ModelProvenance } from "../../components/ModelResult";
import { ObligationBadge } from "../../components/StatusBadge";
import { allResolvedWithoutFinding, countStatus, passedAttempt } from "../../lib/evidence";
import { METHOD_LABELS } from "../../lib/format";
import { useAsync } from "../../lib/hooks";
import { href } from "../../lib/route";

/** Shown on a repair candidate run: where it came from, what changed, and the same obligations before and after. */
export function CandidatePanel({ run }: { run: Run }) {
  const parentId = run.parent_id;
  const parent = useAsync(() => (parentId ? api.run(parentId) : Promise.resolve(null)), [parentId]);
  if (!parentId) return null;
  return (
    <Section id="run-candidate" title="What this repair changed" eyebrow="Repair candidate · checked against the parent's frozen contract and checks" className="candidate-panel">
      <p>
        <a href={href.run(parentId)} className="inline-link">
          <ArrowLeft size={14} aria-hidden="true" /> Back to the failing run
          {parent.status === "ok" && parent.data ? `: ${parent.data.title}` : ""}
        </a>
      </p>
      {parent.status === "loading" && <Loading label="Loading the parent run" />}
      {parent.status === "error" && <ErrorNotice error={parent.error} title="Parent run unavailable" onRetry={parent.reload} />}
      {parent.status === "ok" && parent.data && <CandidateComparison run={run} parent={parent.data} />}
    </Section>
  );
}

function CandidateComparison({ run, parent }: { run: Run; parent: Run }) {
  const attempt = parent.repair?.attempts.find((a) => a.candidate_run_id === run.id);
  const before = parent.verification?.obligations ?? [];
  const after = run.verification?.obligations ?? [];
  const ids = [...before.map((o) => o.id), ...after.map((o) => o.id).filter((id) => !before.some((o) => o.id === id))];
  const byId = (list: Obligation[], id: string) => list.find((o) => o.id === id);
  const changed = ids.filter((id) => byId(before, id)?.status !== byId(after, id)?.status).length;
  const active = run.state === "queued" || run.state === "running";

  return (
    <div className="stack">
      {attempt ? (
        <>
          <p className="prose">
            Attempt {attempt.index} of {parent.repair?.max_attempts ?? 3} on <strong>{parent.title}</strong>
            {attempt.origin === "user" ? ", edited by you." : ", proposed by Nemotron."} {attempt.summary}
          </p>
          {attempt.frozen_match !== undefined && attempt.frozen_match !== null && (
            <p className={attempt.frozen_match ? "frozen ok" : "frozen bad"}>
              {attempt.frozen_match ? <Equal size={14} aria-hidden="true" /> : <CircleX size={14} aria-hidden="true" />}
              {attempt.frozen_match
                ? "Same contract, checks, stimulus, and tool configuration as the parent: frozen hashes match."
                : "Frozen hashes differ from the parent, so this comparison is not valid."}
            </p>
          )}
          {attempt.diff ? (
            <div className="stack-sm">
              <h3 className="subhead">The accepted change to dut.v</h3>
              <DiffView diff={attempt.diff} label={`Diff for repair attempt ${attempt.index}`} />
            </div>
          ) : (
            <p className="muted small">No diff was recorded for this attempt.</p>
          )}
          {attempt.rationale && (
            <Disclosure summary="The model's rationale for this change">
              {attempt.origin === "model" && <ModelProvenance task="repair rationale" />}
              <p className="prose">{attempt.rationale}</p>
            </Disclosure>
          )}
        </>
      ) : (
        <p className="muted">
          <Wrench size={14} aria-hidden="true" /> The parent run does not list an attempt for this candidate, so no diff can be shown.
        </p>
      )}

      <h3 className="subhead">Same obligations, before and after</h3>
      <p className="muted small">
        {active
          ? "The candidate is still running; its column fills in as obligations finish."
          : `${changed} of ${ids.length} obligations changed status. ${
              allResolvedWithoutFinding(run)
                ? `Every obligation now has a non-failing result, ${countStatus(after, "proved")} of them unbounded proofs.`
                : "Not every obligation is resolved without a finding."
            }`}
      </p>
      <TableScroll label="Obligation status before and after the repair">
        <table className="data-table compare-table">
          <caption className="sr-only">Each obligation's status in the failing parent run and in this repair candidate</caption>
          <thead>
            <tr>
              <th scope="col">Obligation</th>
              <th scope="col">Failing run (before)</th>
              <th scope="col">This candidate (after)</th>
            </tr>
          </thead>
          <tbody>
            {ids.map((id) => {
              const b = byId(before, id);
              const a = byId(after, id);
              const differs = b?.status !== a?.status;
              return (
                <tr key={id} className={differs ? "row-changed" : undefined}>
                  <th scope="row">
                    <code>{(a ?? b)?.check}</code>
                    <p className="muted small">{METHOD_LABELS[(a ?? b)?.method ?? ""] ?? (a ?? b)?.method}</p>
                  </th>
                  <td>{b ? <ObligationBadge status={b.status} label={b.label} /> : <span className="muted">Not in the parent</span>}</td>
                  <td>
                    <span className="compare-after">
                      {differs && <ArrowRight size={14} aria-hidden="true" className="compare-arrow" />}
                      {a ? <ObligationBadge status={a.status} label={a.label} /> : <span className="muted">Pending</span>}
                      {differs && <span className="sr-only"> (changed)</span>}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </TableScroll>
    </div>
  );
}

/** On a failing run's hero: the payoff when a repair candidate passed. */
export function RepairPayoff({ run }: { run: Run }) {
  const attempt = passedAttempt(run);
  const candidateId = attempt?.candidate_run_id ?? null;
  const candidate = useAsync(() => (candidateId ? api.run(candidateId) : Promise.resolve(null)), [candidateId]);
  if (!attempt || !candidateId) return null;
  const c = candidate.status === "ok" ? candidate.data : null;
  const total = c?.verification?.obligations.length ?? 0;
  const proofs = countStatus(c?.verification?.obligations, "proved");
  const confirmed = c && allResolvedWithoutFinding(c);
  return (
    <a className="repair-payoff" href={href.run(candidateId)}>
      <span className="repair-payoff-label">Repair</span>
      <span>
        {confirmed
          ? `Candidate ${attempt.index} passed all ${total} unchanged obligations${proofs ? `, ${proofs} proved` : ""}`
          : `Candidate ${attempt.index} passed the unchanged checks`}
      </span>
      <ArrowRight size={16} aria-hidden="true" />
    </a>
  );
}
