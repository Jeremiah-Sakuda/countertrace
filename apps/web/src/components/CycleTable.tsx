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

function Mismatch({ children }: { children: React.ReactNode }) {
  return (
    <span className="mismatch">
      <CircleX size={14} aria-hidden="true" />
      <span>{children}</span>
      <span className="mismatch-tag">mismatch</span>
    </span>
  );
}

function FlagCell({ exp, obs, bad }: { exp: boolean; obs: boolean; bad: boolean }) {
  const text = (
    <>
      {bit(exp)} <span aria-hidden="true">/</span>
      <span className="sr-only"> expected, observed </span> {bit(obs)}
    </>
  );
  return <td className={`mono pair${bad ? " cell-mismatch" : ""}`}>{bad ? <Mismatch>{text}</Mismatch> : text}</td>;
}

export interface FocusRequest {
  cycle: number;
  nonce: number;
}

export function CycleTable({
  rows,
  caption,
  requirements,
  markCycle,
  focusRequest,
  onSelect,
  selectedCycle,
}: {
  rows: CycleRow[];
  caption: string;
  requirements: Record<string, Requirement> | undefined;
  /** The finding's first observed mismatch. */
  markCycle?: number;
  focusRequest?: FocusRequest | null;
  onSelect?: (row: CycleRow) => void;
  selectedCycle?: number | null;
}) {
  const [activeCycle, setActiveCycle] = useState(markCycle ?? rows[0]?.cycle);
  // Keep a keyboard entry point when the full trace is collapsed and the active cycle disappears.
  const previousIndex = rows.findIndex((r) => r.cycle === activeCycle);
  const markedIndex = rows.findIndex((r) => r.cycle === markCycle);
  const active = previousIndex >= 0 ? previousIndex : Math.max(0, markedIndex);
  const [flash, setFlash] = useState<number | null>(null);
  const rowRefs = useRef<(HTMLButtonElement | null)[]>([]);

  const focusIndex = (i: number, center = false) => {
    const clamped = Math.max(0, Math.min(rows.length - 1, i));
    setActiveCycle(rows[clamped]?.cycle);
    const el = rowRefs.current[clamped];
    if (el) {
      el.focus({ preventScroll: true });
      el.scrollIntoView({ block: center ? "center" : "nearest", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
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
    focusIndex(i, true);
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
    <TableScroll label={caption}>
      <table className="data-table cycle-table">
        <caption>
          <span className="sr-only">{caption}. </span>
          <span className="caption-hint">Select a cycle to inspect its queue. Use ↑ / ↓, Home, or End to move between cycles. Queues are shown oldest first.</span>
        </caption>
        <thead>
          <tr>
            <th scope="col">Cycle</th>
            <th scope="col" className="bitcol">
              rst
            </th>
            <th scope="col" className="bitcol">
              wr_en
            </th>
            <th scope="col" className="bitcol">
              rd_en
            </th>
            <th scope="col">din</th>
            <th scope="col">Contract row</th>
            <th scope="col">Accepted</th>
            <th scope="col">
              dout <span className="th-sub">exp / obs</span>
            </th>
            <th scope="col">
              empty <span className="th-sub">exp / obs</span>
            </th>
            <th scope="col">
              full <span className="th-sub">exp / obs</span>
            </th>
            <th scope="col">Queue before → after</th>
          </tr>
        </thead>
        <tbody onKeyDown={onKeyDown}>
          {rows.map((row, i) => {
            const bad = new Set(row.mismatches);
            const isMark = row.cycle === markCycle;
            const req = requirements?.[row.row];
            const classes = [
              isMark ? "row-mark" : "",
              bad.size ? "row-bad" : "",
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
                <td className="mono bitcol">{row.rst}</td>
                <td className="mono bitcol">{row.wr_en}</td>
                <td className="mono bitcol">{row.rd_en}</td>
                <td className="mono">{hex(row.din)}</td>
                <td>
                  <span className="row-id" title={req?.text}>
                    {req?.title ?? row.row}
                  </span>
                </td>
                <td>
                  {acceptedText(row)}
                  {row.wraps.length > 0 && <span className="muted small"> · wraps {row.wraps.join(", ")}</span>}
                </td>
                {row.dout_checked ? (
                  <td className={`mono pair${bad.has("read_data") ? " cell-mismatch" : ""}`}>
                    {bad.has("read_data") ? (
                      <Mismatch>
                        {hex(row.expected.dout)} <span aria-hidden="true">/</span>
                        <span className="sr-only"> expected, observed </span> {hex(row.observed.dout)}
                      </Mismatch>
                    ) : (
                      <>
                        {hex(row.expected.dout)} <span aria-hidden="true">/</span>
                        <span className="sr-only"> expected, observed </span> {hex(row.observed.dout)}
                      </>
                    )}
                  </td>
                ) : (
                  <td className="mono unchecked">
                    <span className="unchecked-label">not checked</span> <span aria-hidden="true">/</span>
                    <span className="sr-only">, observed </span> <span className="unchecked-value">{hex(row.observed.dout)}</span>
                  </td>
                )}
                <FlagCell exp={row.expected.empty} obs={row.observed.empty} bad={bad.has("empty_flag")} />
                <FlagCell exp={row.expected.full} obs={row.observed.full} bad={bad.has("full_flag")} />
                <td className="mono queue-cell">
                  {queueText(row.pre_queue)} <span aria-hidden="true">→</span>
                  <span className="sr-only"> becomes </span> {queueText(row.post_queue)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </TableScroll>
  );
}
