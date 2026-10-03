import { FileText } from "lucide-react";
import { fileUrl } from "../../api/client";
import type { Obligation, ObligationMethod } from "../../api/types";
import { Disclosure, Section, TableScroll } from "../../components/common";
import { ObligationBadge } from "../../components/StatusBadge";
import { METHOD_LABELS } from "../../lib/format";

const ORDER: ObligationMethod[] = ["admission", "simulation", "bmc", "prove", "cover"];

export const METHOD_EXPLANATIONS: Record<ObligationMethod, string> = {
  admission:
    "Admission checks that the RTL fits the supported profile (one module, the canonical ports, supported constructs) before anything executes. Rejected input is not checked at all.",
  simulation:
    "Simulation drives named stimulus tests and fixed random seeds through the independent reference scoreboard. “Simulation passed for these runs” means no mismatch occurred in exactly those runs. It is not a proof: other input sequences may still fail.",
  bmc:
    "A bounded model check explores every legal input sequence from reset up to N cycles. “No counterexample within N cycles” says nothing about longer sequences.",
  prove:
    "An unbounded proof shows the property holds in every reachable state, but only for these exact parameters (DEPTH, WIDTH), the listed assumptions, and this toolchain. It does not cover other parameters, X-propagation, timing, or synthesized hardware.",
  cover:
    "Reachability (cover) checks show that named scenarios such as full, wraparound, and simultaneous operations can actually occur under the assumptions. Reaching them reduces the risk that checks pass vacuously; it does not prove the specification is complete or correct.",
};

function ObligationDetail({ o }: { o: Obligation }) {
  const parts: string[] = [];
  if (o.depth !== undefined) parts.push(`depth ${o.depth}`);
  if (o.step !== undefined) parts.push(`solver step ${o.step}`);
  if (o.cycles !== undefined) parts.push(`${o.cycles} cycles`);
  if (o.tests && o.tests.length) parts.push(`${o.tests.length} tests`);
  return (
    <>
      {o.detail && <p className="ob-detail">{o.detail}</p>}
      {parts.length > 0 && <p className="muted small">{parts.join(" · ")}</p>}
      {o.tests && o.tests.length > 0 && (
        <details className="mini-details">
          <summary>Tests and seeds</summary>
          <p className="mono small">{o.tests.join(", ")}</p>
        </details>
      )}
    </>
  );
}

export function ObligationsPanel({ runId, obligations, checks }: { runId: string; obligations: Obligation[]; checks: Record<string, string> | undefined }) {
  const methods = [...ORDER, ...new Set(obligations.map((o) => o.method).filter((m) => !ORDER.includes(m)))];
  const open = obligations.filter((o) => ["unresolved", "tool_error", "not_checked", "unsupported"].includes(o.status));
  return (
    <Section id="run-obligations" title="Obligations by method" eyebrow="What each method established">
      {obligations.length === 0 ? (
        <p className="muted">No obligations have been recorded yet.</p>
      ) : (
        <div className="stack-lg">
          {methods.map((m) => {
            const items = obligations.filter((o) => o.method === m);
            if (items.length === 0) return null;
            return (
              <div key={m} className="method-group">
                <h3 className="subhead method-title">{METHOD_LABELS[m] ?? m}</h3>
                {METHOD_EXPLANATIONS[m] && (
                  <details className="mini-details">
                    <summary>What does this mean?</summary>
                    <p className="prose small">{METHOD_EXPLANATIONS[m]}</p>
                  </details>
                )}
                <TableScroll label={`${METHOD_LABELS[m] ?? m} obligations`}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th scope="col">Check</th>
                        <th scope="col">Result</th>
                        <th scope="col">Detail</th>
                        <th scope="col">Log</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map((o) => (
                        <tr key={o.id}>
                          <th scope="row">
                            <code>{o.check}</code>
                            {checks?.[o.check] && <p className="muted small">{checks[o.check]}</p>}
                          </th>
                          <td>
                            <ObligationBadge status={o.status} label={o.label} />
                          </td>
                          <td>
                            <ObligationDetail o={o} />
                          </td>
                          <td>
                            {o.log ? (
                              <a className="inline-link" href={fileUrl(runId, o.log)} target="_blank" rel="noreferrer" aria-label={`Open log for ${o.id}`}>
                                <FileText size={14} aria-hidden="true" /> log
                              </a>
                            ) : (
                              <span className="muted">—</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </TableScroll>
              </div>
            );
          })}
          <Disclosure summary="Remaining unresolved, tool-error, and unchecked items" meta={`${open.length}`} defaultOpen={open.length > 0 && open.length <= 6}>
            {open.length === 0 ? (
              <p className="muted">Every listed obligation has a result from its method. This does not make the design correct beyond those methods.</p>
            ) : (
              <ul className="open-list">
                {open.map((o) => (
                  <li key={o.id}>
                    <ObligationBadge status={o.status} label={o.label} /> <code>{o.id}</code>
                    {o.detail && <span className="muted"> — {o.detail}</span>}
                  </li>
                ))}
              </ul>
            )}
          </Disclosure>
        </div>
      )}
    </Section>
  );
}
