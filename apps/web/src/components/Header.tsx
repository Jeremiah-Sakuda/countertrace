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
        <a href={href.setup()} className="brand-name" aria-label="Countertrace home">
          <svg viewBox="0 0 40 40" width="40" height="40" aria-hidden="true">
            <path d="M5 10h19v8H13v12h22M5 24h6M29 10h6v14" fill="none" stroke="currentColor" strokeWidth="3" />
            <circle cx="35" cy="30" r="3" fill="currentColor" />
          </svg>
          <span>Countertrace<span className="brand-caption">A hardware evidence notebook</span></span>
        </a>
      </div>
      <nav className="site-nav" aria-label="Primary">
        <p className="rail-label">The workbench</p>
        <ul>
          {NAV.map((item, i) => (
            <li key={item.to}>
              <a href={item.to} aria-current={item.match(route) ? "page" : undefined} className={item.match(route) ? "active" : undefined}>
                <span className="nav-index" aria-hidden="true">0{i + 1}</span>
                <span>{item.label}</span>
                <span className="nav-arrow" aria-hidden="true">↗</span>
              </a>
            </li>
          ))}
        </ul>
      </nav>
      <div className="rail-note">
        <span className="rail-label">Small circuits. Clear answers.</span>
        <p>Follow the evidence,<br /><em>one cycle at a time.</em></p>
        <div className="rail-profile"><span>8-bit words</span><span>Depth 2 or 4</span></div>
        <code>sync-fifo-v1</code>
      </div>
      <div className="rail-bottom">
        {run && (
          <div className="run-context">
            <Badge tone="neutral" icon={run.recorded ? History : Radio}>{run.recorded ? "Recorded run" : "Live run"}</Badge>
            {run.kind === "verification" && <span role="status" aria-atomic="true" className="unresolved-count">
              <Badge tone={run.unresolved ? "unresolved" : "neutral"} icon={CircleHelp}>
                {run.unresolved === null ? "Unresolved: pending" : `${run.unresolved} unresolved obligation${run.unresolved === 1 ? "" : "s"}`}
              </Badge>
            </span>}
          </div>
        )}
        <details className="service-details">
          <summary>Runtime & model</summary>
          <div className="header-status" aria-label="Service status"><VerifierPill status={status} /><ModelPill status={status} /></div>
        </details>
        <p className="rail-edition">COUNTERTRACE / WORKING EDITION</p>
      </div>
    </header>
  );
}
