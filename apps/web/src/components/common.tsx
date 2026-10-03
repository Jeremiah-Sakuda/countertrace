import { ChevronRight, CircleAlert, Info, LoaderCircle, RefreshCw, TriangleAlert, type LucideIcon } from "lucide-react";
import { useId, type ReactNode } from "react";
import { errorMessage } from "../api/client";

export function Loading({ label = "Loading" }: { label?: string }) {
  return (
    <p className="loading" role="status">
      <LoaderCircle className="spin" size={16} aria-hidden="true" />
      <span>{label}…</span>
    </p>
  );
}

export function ErrorNotice({ error, title = "Could not load", onRetry }: { error: unknown; title?: string; onRetry?: () => void }) {
  return (
    <div className="callout callout-error" role="alert">
      <CircleAlert size={18} aria-hidden="true" />
      <div>
        <p className="callout-title">{title}</p>
        <p>{errorMessage(error)}</p>
        {onRetry && (
          <button type="button" className="btn btn-ghost btn-sm" onClick={onRetry}>
            <RefreshCw size={14} aria-hidden="true" /> Retry
          </button>
        )}
      </div>
    </div>
  );
}

type CalloutKind = "info" | "warn" | "error" | "model";

export function Callout({
  kind = "info",
  title,
  icon,
  children,
  role,
}: {
  kind?: CalloutKind;
  title?: ReactNode;
  icon?: LucideIcon;
  children?: ReactNode;
  role?: "status" | "alert" | "note";
}) {
  const Icon = icon ?? (kind === "warn" ? TriangleAlert : kind === "error" ? CircleAlert : Info);
  return (
    <div className={`callout callout-${kind}`} role={role}>
      <Icon size={18} aria-hidden="true" />
      <div>
        {title && <p className="callout-title">{title}</p>}
        {children}
      </div>
    </div>
  );
}

/** Native details/summary disclosure: keyboard accessible without extra script. */
export function Disclosure({
  summary,
  children,
  defaultOpen,
  className,
  meta,
}: {
  summary: ReactNode;
  children: ReactNode;
  defaultOpen?: boolean;
  className?: string;
  meta?: ReactNode;
}) {
  return (
    <details className={`disclosure ${className ?? ""}`} open={defaultOpen}>
      <summary>
        <ChevronRight className="disclosure-chevron" size={16} aria-hidden="true" />
        <span className="disclosure-title">{summary}</span>
        {meta && <span className="disclosure-meta">{meta}</span>}
      </summary>
      <div className="disclosure-body">{children}</div>
    </details>
  );
}

export function Section({
  title,
  level = 2,
  children,
  actions,
  id,
  className,
  eyebrow,
}: {
  title: ReactNode;
  level?: 2 | 3;
  children: ReactNode;
  actions?: ReactNode;
  id?: string;
  className?: string;
  eyebrow?: ReactNode;
}) {
  const autoId = useId();
  const headingId = id ?? `s-${autoId.replace(/:/g, "")}`;
  const H = level === 2 ? "h2" : "h3";
  return (
    <section className={`panel ${className ?? ""}`} aria-labelledby={headingId}>
      <header className="panel-header">
        <div>
          {eyebrow && <p className="eyebrow">{eyebrow}</p>}
          <H id={headingId} className="panel-title" tabIndex={-1}>
            {title}
          </H>
        </div>
        {actions && <div className="panel-actions">{actions}</div>}
      </header>
      {children}
    </section>
  );
}

/** Horizontal scroll container for wide tables so the page itself never scrolls sideways. */
export function TableScroll({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="table-scroll" role="region" aria-label={label} tabIndex={0}>
      {children}
    </div>
  );
}

export function KeyValue({ items }: { items: [ReactNode, ReactNode][] }) {
  return (
    <dl className="kv">
      {items.map(([k, v], i) => (
        <div key={i} className="kv-row">
          <dt>{k}</dt>
          <dd>{v}</dd>
        </div>
      ))}
    </dl>
  );
}

export function Hash({ value, n = 12 }: { value: string | null | undefined; n?: number }) {
  if (!value) return <span className="muted">—</span>;
  const body = value.includes(":") ? value.slice(value.indexOf(":") + 1) : value;
  return (
    <code className="hash" title={value}>
      {body.slice(0, n)}
      {body.length > n ? "…" : ""}
    </code>
  );
}
