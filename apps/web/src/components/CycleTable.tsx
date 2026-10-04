import { CircleX, Crosshair } from "lucide-react";
import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import type { CycleRow, Requirement } from "../api/types";
import { bit, hex, queueText } from "../lib/format";
import { TableScroll } from "./common";

export function acceptedText(row: CycleRow): string {
  if (row.accepted.reset) return "Reset";
  if (row.accepted.read && row.accepted.write) return "Read + write";
  if (row.accepted.read) return "Read";
  if (row.accepted.write) return "Write";
  return "None";
}

/** Visible "expected / observed" text is hidden from assistive technology; a plain sentence replaces it. */
function Pair({ signal, expected, observed, bad }: { signal: string; expected: string | null; observed: string; bad: boolean }) {
  const spoken = `${signal} expected ${expected ?? "not checked"}, observed ${observed}${bad ? ", mismatch" : ""}`;
  const visible = (
    <span aria-hidden="true">
      {expected === null ? <span className="unchecked-label">not checked</span> : expected} /{" "}
      {expected === null ? <span className="unchecked-value">{observed}</span> : observed}
    </span>
  );
  return (
    <td className={`mono pair${bad ? " cell-mismatch" : ""}${expected === null ? " unchecked" : ""}`}>
      {bad ? (
        <span className="mismatch">
          <CircleX size={14} aria-hidden="true" />
          {visible}
          <span className="mismatch-tag" aria-hidden="true">mismatch</span>
        </span>
      ) : (
        visible
      )}
      <span className="sr-only">{spoken}</span>
    </td>
  );
}

function spokenQueue(queue: number[] | null): string {
  if (queue === null) return "unspecified";
  if (queue.length === 0) return "empty";
  return queue.map((v) => hex(v)).join(", ");
}

/** Narrow screens put the outputs next to the sticky cycle column so the mismatch is visible without scrolling. */
function useNarrow(query = "(max-width: 759px)"): boolean {
  const [narrow, setNarrow] = useState(() => typeof window !== "undefined" && typeof window.matchMedia === "function" && window.matchMedia(query).matches);
  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const mq = window.matchMedia(query);
    const on = () => setNarrow(mq.matches);
    on();
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, [query]);
  return narrow;
}

type ColumnKey = "rst" | "wr_en" | "rd_en" | "din" | "row" | "accepted" | "dout" | "empty" | "full" | "queue";
const INPUTS: ColumnKey[] = ["rst", "wr_en", "rd_en", "din", "row", "accepted"];
const OUTPUTS: ColumnKey[] = ["dout", "empty", "full"];

function ColumnHeader({ col }: { col: ColumnKey }) {
  switch (col) {
    case "rst":
    case "wr_en":
    case "rd_en":
      return <th scope="col" className="bitcol">{col}</th>;
    case "din":
      return <th scope="col">din</th>;
    case "row":
      return <th scope="col">Contract row</th>;
    case "accepted":
      return <th scope="col">Accepted</th>;
    case "dout":
    case "empty":
    case "full":
      return (
        <th scope="col">
          {col} <span className="th-sub">exp / obs</span>
        </th>
      );
    case "queue":
      return <th scope="col">Queue before → after</th>;
  }
}

function Cell({ col, row, requirements }: { col: ColumnKey; row: CycleRow; requirements: Record<string, Requirement> | undefined }) {
  const bad = row.mismatches;
  switch (col) {
    case "rst":
    case "wr_en":
    case "rd_en":
      return <td className="mono bitcol">{row[col]}</td>;
    case "din":
      return <td className="mono">{hex(row.din)}</td>;
    case "row": {
      const req = requirements?.[row.row];
      return (
        <td>
          <span className="row-id" title={req?.text}>
            {req?.title ?? row.row}
          </span>
        </td>
      );
    }
    case "accepted":
      return (
        <td>
          {acceptedText(row)}
          {row.wraps.length > 0 && <span className="muted small"> · wraps {row.wraps.join(", ")}</span>}
        </td>
      );
    case "dout":
      if (!row.dout_checked && !bad.includes("read_data"))
        // No accepted read: the contract does not check dout here, so the cell stays quiet instead of repeating the stale value.
        return (
          <td className="mono pair unchecked dout-unchecked" title={`dout not checked (no accepted read); the port showed ${hex(row.observed.dout)}`}>
            <span aria-hidden="true" className="dim-dash">—</span>
            <span className="sr-only">dout not checked</span>
          </td>
        );
      return <Pair signal="dout" expected={row.dout_checked ? hex(row.expected.dout) : null} observed={hex(row.observed.dout)} bad={bad.includes("read_data")} />;
    case "empty":
      return <Pair signal="empty" expected={bit(row.expected.empty)} observed={bit(row.observed.empty)} bad={bad.includes("empty_flag")} />;
    case "full":
      return <Pair signal="full" expected={bit(row.expected.full)} observed={bit(row.observed.full)} bad={bad.includes("full_flag")} />;
    case "queue":
      return (
        <td className="mono queue-cell">
          <span aria-hidden="true">
            {queueText(row.pre_queue)} → {queueText(row.post_queue)}
          </span>
          <span className="sr-only">
            queue before {spokenQueue(row.pre_queue)}; after {spokenQueue(row.post_queue)}
          </span>
        </td>
      );
  }
}

export interface FocusRequest {
  cycle: number;
  nonce: number;
  /** The control that asked for the jump (for example an explanation citation), so focus can return to it. */
  returnTo?: HTMLElement | null;
  returnLabel?: string;
}

export function CycleTable({
  rows,
  caption,
  requirements,
  markCycle,
  focusRequest,
  onSelect,
  selectedCycle,
  onFocusRequestHandled,
}: {
  rows: CycleRow[];
  caption: string;
  requirements: Record<string, Requirement> | undefined;
  /** The finding's first observed mismatch. */
  markCycle?: number;
  focusRequest?: FocusRequest | null;
  onSelect?: (row: CycleRow) => void;
  selectedCycle?: number | null;
  /** When set, a focus request focuses the row without scrolling and the parent decides what to bring into view. */
  onFocusRequestHandled?: (row: HTMLElement, request: FocusRequest) => void;
}) {
  const [activeCycle, setActiveCycle] = useState(markCycle ?? rows[0]?.cycle);
  // Keep a keyboard entry point when the full trace is collapsed and the active cycle disappears.
  const previousIndex = rows.findIndex((r) => r.cycle === activeCycle);
  const markedIndex = rows.findIndex((r) => r.cycle === markCycle);
  const active = previousIndex >= 0 ? previousIndex : Math.max(0, markedIndex);
  const [flash, setFlash] = useState<number | null>(null);
  const rowRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const narrow = useNarrow();
  const columns: ColumnKey[] = narrow ? [...OUTPUTS, ...INPUTS, "queue"] : [...INPUTS, ...OUTPUTS, "queue"];

  const focusIndex = (i: number, scroll: "nearest" | "center" | "none" = "nearest") => {
    const clamped = Math.max(0, Math.min(rows.length - 1, i));
    setActiveCycle(rows[clamped]?.cycle);
    const el = rowRefs.current[clamped];
    if (el) {
      el.focus({ preventScroll: true });
      if (scroll !== "none")
        el.scrollIntoView({ block: scroll, inline: "nearest", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    }
    const row = rows[clamped];
    if (row && onSelect) onSelect(row);
  };

  const handledNonce = useRef<number | null>(null);
  useEffect(() => {
    if (!focusRequest || handledNonce.current === focusRequest.nonce) return;
    const i = rows.findIndex((r) => r.cycle === focusRequest.cycle);
    if (i < 0) return; // the parent may widen the rows; retry when they change
    handledNonce.current = focusRequest.nonce;
    if (onFocusRequestHandled) {
      focusIndex(i, "none");
      const el = rowRefs.current[i]?.closest("tr");
      if (el) onFocusRequestHandled(el, focusRequest);
    } else focusIndex(i, "center");
    setFlash(focusRequest.cycle);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusRequest, rows]);

  useEffect(() => {
    if (flash === null) return;
    const t = window.setTimeout(() => setFlash(null), 2000);
    return () => window.clearTimeout(t);
  }, [flash]);

  const onKeyDown = (e: KeyboardEvent<HTMLTableSectionElement>) => {
    const keys: Record<string, number> = { ArrowDown: active + 1, ArrowUp: active - 1, Home: 0, End: rows.length - 1 };
    const next = keys[e.key];
    if (next === undefined) return;
    e.preventDefault();
    focusIndex(next);
  };

  return (
    <div className="stack-sm">
    <p className="caption-hint muted small">
      Select a cycle to inspect its queue. Use ↑ / ↓, Home, or End to move between cycles. Queues are shown oldest first. A dash in the
      dout column means no read was accepted, so dout is not checked on that cycle.
      {narrow ? <> Outputs come first on small screens; <span className="scroll-hint">scroll sideways for inputs and the queue →</span></> : null}
    </p>
    <TableScroll label={caption}>
      <table className="data-table cycle-table">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr>
            <th scope="col">Cycle</th>
            {columns.map((col) => (
              <ColumnHeader key={col} col={col} />
            ))}
          </tr>
        </thead>
        <tbody onKeyDown={onKeyDown}>
          {rows.map((row, i) => {
            const isMark = row.cycle === markCycle;
            const classes = [
              isMark ? "row-mark" : "",
              row.mismatches.length ? "row-bad" : "",
              flash === row.cycle ? "row-flash" : "",
              selectedCycle === row.cycle ? "row-selected" : "",
            ]
              .filter(Boolean)
              .join(" ");
            return (
              <tr
                key={row.cycle}
                data-cycle={row.cycle}
                className={classes}
                onClick={() => focusIndex(i)}
              >
                <th scope="row" className="mono">
                  <button
                    type="button"
                    className="cycle-select"
                    ref={(el) => { rowRefs.current[i] = el; }}
                    tabIndex={i === active ? 0 : -1}
                    aria-label={`Inspect cycle ${row.cycle}${isMark ? " (first observed mismatch)" : ""}`}
                    aria-pressed={selectedCycle === row.cycle}
                    onFocus={() => {
                      setActiveCycle(row.cycle);
                      onSelect?.(row);
                    }}
                  >
                    {row.cycle}
                    {isMark && <Crosshair size={13} aria-hidden="true" />}
                  </button>
                </th>
                {columns.map((col) => (
                  <Cell key={col} col={col} row={row} requirements={requirements} />
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </TableScroll>
    </div>
  );
}
