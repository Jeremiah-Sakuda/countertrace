import { useEffect, useRef } from "react";

/** Read-only source listing with line numbers. Highlighted lines get a marker and text label for screen readers. */
export function CodeView({
  source,
  label,
  highlight = [],
  maxHeight,
  only,
}: {
  source: string;
  label: string;
  highlight?: number[];
  maxHeight?: number;
  /** Show only these 1-based lines (with a little context) instead of the whole file. */
  only?: { lines: number[]; context?: number };
}) {
  const lines = source.replace(/\n$/, "").split("\n");
  const marked = new Set(highlight);
  const ref = useRef<HTMLDivElement>(null);

  let visible: number[] = lines.map((_, i) => i + 1);
  if (only && only.lines.length > 0) {
    const ctx = only.context ?? 2;
    const keep = new Set<number>();
    for (const n of only.lines) for (let k = n - ctx; k <= n + ctx; k++) if (k >= 1 && k <= lines.length) keep.add(k);
    visible = [...keep].sort((a, b) => a - b);
  }

  useEffect(() => {
    const first = highlight[0];
    if (first === undefined || !ref.current || only) return;
    const el = ref.current.querySelector<HTMLElement>(`[data-line="${first}"]`);
    if (el) ref.current.scrollTop = Math.max(0, el.offsetTop - 48);
  }, [highlight, only]);

  return (
    <div
      className="code"
      ref={ref}
      role="region"
      aria-label={label}
      tabIndex={0}
      style={maxHeight ? { maxHeight } : undefined}
    >
      <pre>
        <code>
          {visible.map((n, idx) => {
            const gap = idx > 0 && n !== (visible[idx - 1] ?? 0) + 1;
            return (
              <span key={n}>
                {gap && (
                  <span className="code-line code-gap" aria-hidden="true">
                    <span className="code-ln">⋮</span>
                    <span className="code-text" />
                  </span>
                )}
                <span className={`code-line${marked.has(n) ? " code-mark" : ""}`} data-line={n}>
                  <span className="code-ln" aria-hidden="true">
                    {n}
                  </span>
                  {marked.has(n) && <span className="sr-only">Cited line {n}: </span>}
                  <span className="code-text">{lines[n - 1] || " "}</span>
                </span>
              </span>
            );
          })}
        </code>
      </pre>
    </div>
  );
}

/** Unified diff with +/- text markers (not color alone). */
export function DiffView({ diff, label }: { diff: string; label: string }) {
  const lines = diff.replace(/\n$/, "").split("\n");
  return (
    <div className="code diff" role="region" aria-label={label} tabIndex={0}>
      <pre>
        <code>
          {lines.map((line, i) => {
            let kind = "ctx";
            if (line.startsWith("+++") || line.startsWith("---")) kind = "file";
            else if (line.startsWith("@@")) kind = "hunk";
            else if (line.startsWith("+")) kind = "add";
            else if (line.startsWith("-")) kind = "del";
            return (
              <span key={i} className={`diff-line diff-${kind}`}>
                {kind === "add" && <span className="sr-only">Added: </span>}
                {kind === "del" && <span className="sr-only">Removed: </span>}
                {line || " "}
              </span>
            );
          })}
        </code>
      </pre>
    </div>
  );
}
