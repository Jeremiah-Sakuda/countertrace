import { CircleCheck, CircleHelp, ExternalLink } from "lucide-react";
import { fileUrl } from "../../api/client";
import type { Requirement, Run } from "../../api/types";
import { Disclosure, Hash, KeyValue, Section, TableScroll } from "../../components/common";
import { Badge } from "../../components/StatusBadge";
import { formatDuration, humanize } from "../../lib/format";

function rawFiles(run: Run): { path: string; label: string }[] {
  const v = run.verification;
  const files = new Map<string, string>();
  files.set("dut.v", "DUT source (dut.v)");
  files.set("contract.json", "Accepted contract (contract.json)");
  files.set("run.json", "Run record (run.json)");
  for (const f of v?.findings ?? []) if (f.vcd) files.set(f.vcd, `VCD · ${f.test}`);
  for (const o of v?.obligations ?? []) if (o.log && !files.has(o.log)) files.set(o.log, `Log · ${o.method}`);
  for (const [name, b] of Object.entries(v?.batches ?? {}))
    for (const s of b.steps ?? []) if (s.log && b.out_dir) files.set(`${b.out_dir}/${s.log}`, `Step log · ${name} · ${s.id}`);
  return [...files.entries()].map(([path, label]) => ({ path, label }));
}

export function EvidencePanel({ run, requirements }: { run: Run; requirements: Record<string, Requirement> | undefined }) {
  const v = run.verification;
  if (!v) return null;
  const coverage = Object.entries(v.coverage ?? {});
  const covers = Object.entries(v.formal_covers ?? {});
  const tools = new Map<string, Set<string>>();
  for (const b of Object.values(v.batches ?? {}))
    for (const [tool, ver] of Object.entries(b.tool_versions ?? {})) {
      if (!tools.has(tool)) tools.set(tool, new Set());
      tools.get(tool)!.add(ver);
    }
  const frozen = v.frozen;

  return (
    <Section id="run-evidence" title="Evidence details" eyebrow="Expandable">
      <div className="stack">
        <Disclosure summary="Coverage counts per contract row" meta={`${coverage.length} rows`}>
          {coverage.length === 0 ? (
            <p className="muted">No coverage counts were recorded.</p>
          ) : (
            <TableScroll label="Coverage counts">
              <table className="data-table compact">
                <thead>
                  <tr>
                    <th scope="col">Row or scenario</th>
                    <th scope="col">Condition</th>
                    <th scope="col" className="num">
                      Edges exercised in simulation
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {coverage.map(([row, n]) => (
                    <tr key={row} className={n === 0 ? "row-warn" : undefined}>
                      <th scope="row" className="mono">
                        {row}
                      </th>
                      <td>{requirements?.[row]?.title ?? humanize(row)}</td>
                      <td className="num mono">
                        {n}
                        {n === 0 && <span className="tag tag-warn">not exercised</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TableScroll>
          )}
        </Disclosure>

        <Disclosure summary="Formal reachability (cover) steps" meta={`${covers.filter(([, c]) => c.reached).length} of ${covers.length} reached`}>
          {covers.length === 0 ? (
            <p className="muted">No cover results were recorded.</p>
          ) : (
            <TableScroll label="Formal cover results">
              <table className="data-table compact">
                <thead>
                  <tr>
                    <th scope="col">Cover</th>
                    <th scope="col">Result</th>
                    <th scope="col" className="num">
                      Solver step
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {covers.map(([label, c]) => (
                    <tr key={label}>
                      <th scope="row" className="mono">
                        {label}
                      </th>
                      <td>
                        {c.reached ? (
                          <Badge tone="bounded" icon={CircleCheck}>
                            Reached
                          </Badge>
                        ) : (
                          <Badge tone="unresolved" icon={CircleHelp}>
                            Not reached
                          </Badge>
                        )}
                      </td>
                      <td className="num mono">{c.step ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TableScroll>
          )}
        </Disclosure>

        <Disclosure summary="Integrity notes" meta={`${v.integrity?.length ?? 0}`} defaultOpen={(v.integrity?.length ?? 0) > 0}>
          {v.integrity && v.integrity.length > 0 ? (
            <ul className="open-list">
              {v.integrity.map((n, i) => (
                <li key={i} className="mono small">
                  {n}
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">
              No integrity problems recorded
              {v.integrity_checked?.length ? ` (checked: ${v.integrity_checked.join(", ")})` : ""}.
            </p>
          )}
        </Disclosure>

        <Disclosure summary="Admission" meta={v.admission ? (v.admission.accepted ? "accepted" : "rejected") : "not recorded"}>
          {v.admission ? (
            <div className="stack">
              <KeyValue
                items={[
                  ["Accepted", v.admission.accepted ? "Yes" : "No"],
                  ["Module", <code key="m">{v.admission.module ?? "—"}</code>],
                  ["Parameters", v.admission.parameters.join(", ") || "—"],
                  ["Ports", Object.entries(v.admission.ports).map(([p, d]) => `${p} (${d.direction}${d.range ? ` ${d.range}` : ""})`).join(", ")],
                ]}
              />
              {v.admission.diagnostics.length === 0 ? (
                <p className="muted">No admission diagnostics.</p>
              ) : (
                <TableScroll label="Admission diagnostics">
                  <table className="data-table compact">
                    <thead>
                      <tr>
                        <th scope="col">Code</th>
                        <th scope="col">Message</th>
                        <th scope="col">Line</th>
                        <th scope="col">Alternative</th>
                      </tr>
                    </thead>
                    <tbody>
                      {v.admission.diagnostics.map((d, i) => (
                        <tr key={i}>
                          <td className="mono">{d.code}</td>
                          <td>{d.message}</td>
                          <td className="mono">{d.line ?? "—"}</td>
                          <td>{d.alternative ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </TableScroll>
              )}
            </div>
          ) : (
            <p className="muted">No admission record.</p>
          )}
        </Disclosure>

        <Disclosure summary="Tool versions and verifier batches" meta={`${Object.keys(v.batches ?? {}).length} batches`}>
          <div className="stack">
            {run.image && (
              <KeyValue
                items={[
                  ["Verifier image", <code key="t">{run.image.tag}</code>],
                  ["Image id", <Hash key="i" value={run.image.image_id} n={20} />],
                  ["Verifier digest", <code key="d">{run.image.verifier_digest}</code>],
                ]}
              />
            )}
            {tools.size > 0 && (
              <TableScroll label="Tool versions">
                <table className="data-table compact">
                  <thead>
                    <tr>
                      <th scope="col">Tool</th>
                      <th scope="col">Version</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...tools.entries()].map(([tool, vers]) => (
                      <tr key={tool}>
                        <th scope="row">{tool}</th>
                        <td className="mono small">{[...vers].join(" | ")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </TableScroll>
            )}
            {Object.entries(v.batches ?? {}).map(([name, b]) => (
              <details key={name} className="mini-details">
                <summary>
                  Batch <code>{name}</code> · {formatDuration(b.wall_s ?? null)} · exit {b.container_returncode ?? "—"}
                  {b.timed_out ? " · timed out" : ""}
                  {b.cancelled ? " · cancelled" : ""} · network {b.network ?? "—"}
                </summary>
                {b.steps && b.steps.length > 0 && (
                  <TableScroll label={`Steps in batch ${name}`}>
                    <table className="data-table compact">
                      <thead>
                        <tr>
                          <th scope="col">Step</th>
                          <th scope="col">Command</th>
                          <th scope="col" className="num">
                            Exit
                          </th>
                          <th scope="col" className="num">
                            Duration
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {b.steps.map((s) => (
                          <tr key={s.id}>
                            <th scope="row" className="mono small">
                              {s.id}
                            </th>
                            <td className="mono small wrap-anywhere">{s.argv.join(" ")}</td>
                            <td className="num mono">
                              {s.returncode ?? "—"}
                              {s.timed_out ? " (timeout)" : ""}
                            </td>
                            <td className="num mono">{formatDuration(s.duration_s)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </TableScroll>
                )}
              </details>
            ))}
          </div>
        </Disclosure>

        <Disclosure summary="Frozen contract, checks, and configuration">
          {frozen ? (
            <div className="stack">
              <p className="muted small">
                These hashes identify what was held fixed for this run. A repair comparison is valid only when they are identical.
              </p>
              <KeyValue
                items={[
                  ["Contract", <Hash key="c" value={frozen.contract} n={24} />],
                  ["DUT source", <Hash key="s" value={v.source_hash} n={24} />],
                  ["Verifier digest", <code key="v">{frozen.verifier_digest}</code>],
                  ["Stimulus version", <code key="sv">{frozen.stimulus_version}</code>],
                  ["Formal tasks", frozen.formal_tasks.join(", ")],
                  ["Expected properties", Object.entries(frozen.expected_properties).map(([k, n]) => `${n} ${k}`).join(", ")],
                  ["Limits", Object.entries(frozen.limits).map(([k, n]) => `${k}=${n}`).join(", ")],
                ]}
              />
              <TableScroll label="Frozen harness and stimulus hashes">
                <table className="data-table compact">
                  <thead>
                    <tr>
                      <th scope="col">Artifact</th>
                      <th scope="col">Hash</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(frozen.harness).map(([f, h]) => (
                      <tr key={`h-${f}`}>
                        <th scope="row" className="mono small">
                          harness/{f}
                        </th>
                        <td>
                          <Hash value={h} n={24} />
                        </td>
                      </tr>
                    ))}
                    {Object.entries(frozen.stimulus).map(([t, h]) => (
                      <tr key={`s-${t}`}>
                        <th scope="row" className="mono small">
                          stimulus/{t}
                        </th>
                        <td>
                          <Hash value={h} n={24} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </TableScroll>
            </div>
          ) : (
            <p className="muted">No frozen configuration was recorded for this run.</p>
          )}
        </Disclosure>

        <Disclosure summary="Raw logs, traces, and sources">
          <ul className="link-list files">
            {rawFiles(run).map((f) => (
              <li key={f.path}>
                <a href={fileUrl(run.id, f.path)} target="_blank" rel="noreferrer" className="inline-link">
                  <ExternalLink size={14} aria-hidden="true" /> {f.label}
                </a>
                <span className="mono small muted wrap-anywhere"> {f.path}</span>
              </li>
            ))}
          </ul>
          <p className="muted small">Files open as text from the run directory. A link fails if that artifact was not produced.</p>
        </Disclosure>
      </div>
    </Section>
  );
}
