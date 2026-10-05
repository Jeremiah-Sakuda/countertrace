import { Bot, Container, History, Radio } from "lucide-react";
import type { Status } from "../api/types";
import type { AsyncState } from "../lib/hooks";
import type { Route } from "../lib/route";
import { href } from "../lib/route";
import { Badge } from "./StatusBadge";
import { isRecordedDemo } from "./DeploymentNotice";

export interface RunContextInfo {
  id: string;
  kind: "verification" | "audit";
  recorded: boolean;
  unresolved: number | null;
  state: string;
  /** Why obligations stayed unresolved, when every unresolved obligation records the same cause. */
  unresolvedReason?: string | null;
}

function VerifierPill({ status }: { status: AsyncState<Status> }) {
  if (status.status === "loading") return <Badge tone="neutral" icon={Container}>Verifier: checking</Badge>;
  if (status.status === "error") return <Badge tone="toolerror" icon={Container}>Verifier: status unavailable</Badge>;
  if (isRecordedDemo(status)) return <Badge tone="neutral" icon={Container}>Verifier: local test build</Badge>;
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
  if (isRecordedDemo(status)) return <Badge tone="neutral" icon={Bot}>Model calls: local test build</Badge>;
  const m = status.data.model;
  if (!m.configured)
    return (
      <Badge tone="neutral" icon={Bot} title={m.reason ?? undefined}>
        Model not configured
      </Badge>
    );
  // List every model the server uses, with its role, so no model call is attributed to the wrong one.
  const roles: { id: string; role: string }[] = [];
  const add = (id: string | null | undefined, role: string) => {
    if (!id) return;
    const existing = roles.find((r) => r.id === id);
    if (existing) existing.role = `${existing.role}, ${role}`;
    else roles.push({ id, role });
  };
  add(m.model_id, "explanation, learning coaching");
  add(m.repair_model_id ?? m.model_id, "repair");
  add(m.fast_model_id, "brief interpretation, check-set proposals");
  return (
    <dl className="model-roles" aria-label="Models in use">
      {roles.map((r) => (
        <div key={r.id}>
          <dt>
            <Bot size={13} aria-hidden="true" /> {r.role.charAt(0).toUpperCase() + r.role.slice(1)}
          </dt>
          <dd className="mono">{r.id}</dd>
        </div>
      ))}
      {m.endpoint_host && (
        <div>
          <dt>Endpoint</dt>
          <dd className="mono">{m.endpoint_host}</dd>
        </div>
      )}
    </dl>
  );
}

const NAV: { label: string; to: string; match: (r: Route) => boolean }[] = [
  { label: "Learning labs", to: "#/", match: (r) => r.name === "learn" },
  { label: "Facilitator desk", to: "#/teach", match: (r) => r.name === "teach" },
  { label: "Contract setup", to: href.setup(), match: (r) => r.name === "setup" },
  { label: "Runs", to: href.runs(), match: (r) => r.name === "runs" || r.name === "run" },
  { label: "Check-quality audit", to: href.audit(), match: (r) => r.name === "audit" },
];

export function Header({ status, route, run }: { status: AsyncState<Status>; route: Route; run: RunContextInfo | null }) {
  return (
    <header className="site-header">
      <div className="site-header-inner">
        <a href="#/" className="brand-name" aria-label="Countertrace home">
          <svg viewBox="0 0 40 40" width="40" height="40" aria-hidden="true">
            <path d="M5 10h19v8H13v12h22M5 24h6M29 10h6v14" fill="none" stroke="currentColor" strokeWidth="3" />
            <circle cx="35" cy="30" r="3" fill="currentColor" />
          </svg>
          <span>Countertrace<span className="brand-caption">Learn to question the fix</span></span>
        </a>
      </div>
      <nav className="site-nav" aria-label="Primary">
        <p className="rail-label">The learning notebook</p>
        <ul>
          {NAV.map((item, i) => (
            <li key={item.to}>
              <a href={item.to} aria-current={item.match(route) ? "page" : undefined} className={item.match(route) ? "active" : undefined}>
                <span className="nav-index" aria-hidden="true">0{i + 1}</span>
                <span>{item.label}</span>
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
            <Badge tone="neutral" icon={run.recorded ? History : Radio}>{run.recorded ? "Recorded run" : "Run on this server"}</Badge>
          </div>
        )}
        <details className="service-details">
          <summary>Runtime & model</summary>
          <div className="header-status" aria-label="Service status"><VerifierPill status={status} /><ModelPill status={status} /></div>
        </details>
        <p className="rail-edition">COUNTERTRACE / {isRecordedDemo(status) ? "RECORDED DEMO" : "WORKING EDITION"}</p>
      </div>
    </header>
  );
}
