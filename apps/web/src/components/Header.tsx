import { Bot, CircleHelp, Container, History, Radio } from "lucide-react";
import type { Status } from "../api/types";
import type { AsyncState } from "../lib/hooks";
import type { Route } from "../lib/route";
import { href } from "../lib/route";
import { Badge } from "./StatusBadge";

export interface RunContextInfo {
  id: string;
  kind: "verification" | "audit";
  recorded: boolean;
  unresolved: number | null;
  state: string;
}

function VerifierPill({ status }: { status: AsyncState<Status> }) {
  if (status.status === "loading") return <Badge tone="neutral" icon={Container}>Verifier: checking</Badge>;
  if (status.status === "error") return <Badge tone="toolerror" icon={Container}>Verifier: status unavailable</Badge>;
  const v = status.data.verifier;
  if (!v.docker)
    return (
      <Badge tone="unresolved" icon={Container} title={v.docker_detail ?? undefined}>
        Verifier: Docker unavailable
      </Badge>
    );
  if (!v.image_built)
    return (
      <Badge tone="unresolved" icon={Container} title={v.image_tag ?? undefined}>
        Verifier: image not built
      </Badge>
    );
  return (
    <Badge tone="info" icon={Container} title={`${v.image_tag ?? ""} · network ${v.network}`}>
      Verifier ready · Docker {v.docker_detail} · network {v.network}
    </Badge>
  );
}

function ModelPill({ status }: { status: AsyncState<Status> }) {
  if (status.status !== "ok") return <Badge tone="neutral" icon={Bot}>Model: {status.status === "loading" ? "checking" : "status unavailable"}</Badge>;
  const m = status.data.model;
  if (!m.configured)
    return (
      <Badge tone="neutral" icon={Bot} title={m.reason ?? undefined}>
        Model not configured
      </Badge>
    );
  return (
    <Badge tone="info" icon={Bot} title={m.endpoint_host ?? undefined}>
      Model: {m.model_id ?? "configured"}
    </Badge>
  );
}

const NAV: { label: string; to: string; match: (r: Route) => boolean }[] = [
  { label: "Contract setup", to: href.setup(), match: (r) => r.name === "setup" },
  { label: "Runs", to: href.runs(), match: (r) => r.name === "runs" || r.name === "run" },
  { label: "Check-quality audit", to: href.audit(), match: (r) => r.name === "audit" },
];

export function Header({ status, route, run }: { status: AsyncState<Status>; route: Route; run: RunContextInfo | null }) {
  return (
    <header className="site-header">
      <div className="site-header-inner">
        <div className="brand">
          <a href={href.setup()} className="brand-name">
            <svg viewBox="0 0 32 32" width="22" height="22" aria-hidden="true">
              <path d="M3 22h6V10h7v12h7V10h6" fill="none" stroke="currentColor" strokeWidth="2.75" strokeLinejoin="round" />
            </svg>
            Countertrace
          </a>
          <p className="scope-line">Synchronous FIFO profile sync-fifo-v1 · 8-bit · depth 2 or 4</p>
        </div>
        <div className="header-status" aria-label="Service status">
          <VerifierPill status={status} />
          <ModelPill status={status} />
        </div>
      </div>
      <nav className="site-nav" aria-label="Primary">
        <ul>
          {NAV.map((item) => {
            const active = item.match(route);
            return (
              <li key={item.to}>
                <a href={item.to} aria-current={active ? "page" : undefined} className={active ? "active" : undefined}>
                  {item.label}
                </a>
              </li>
            );
          })}
        </ul>
        {run && (
          <div className="run-context">
            {run.recorded ? (
              <Badge tone="neutral" icon={History}>
                Recorded run
              </Badge>
            ) : (
              <Badge tone="info" icon={Radio}>
                Live run
              </Badge>
            )}
            {run.kind === "verification" && (
              <span role="status" aria-atomic="true" className="unresolved-count">
                <Badge tone={run.unresolved ? "unresolved" : "neutral"} icon={CircleHelp}>
                  {run.unresolved === null ? "Unresolved obligations: pending" : `${run.unresolved} unresolved obligation${run.unresolved === 1 ? "" : "s"}`}
                </Badge>
              </span>
            )}
          </div>
        )}
      </nav>
    </header>
  );
}
