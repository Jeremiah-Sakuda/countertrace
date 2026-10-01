import { ArrowRight } from "lucide-react";
import type { CycleRow } from "../api/types";
import { hex } from "../lib/format";
import { acceptedText } from "./CycleTable";

function Slots({ queue, depth, label, removedHead, appended }: { queue: number[] | null; depth: number; label: string; removedHead?: boolean; appended?: boolean }) {
  const slots = Array.from({ length: depth }, (_, i) => queue?.[i]);
  return (
    <figure className="queue">
      <figcaption>{label}</figcaption>
      {queue === null ? (
        <p className="queue-unspecified">Unspecified (before first reset)</p>
      ) : (
        <ol className="queue-slots" aria-label={`${label}: ${queue.length} of ${depth} slots occupied, oldest first`}>
          {slots.map((v, i) => {
            const isHeadOut = removedHead && i === 0;
            const isNew = appended && i === queue.length - 1;
            return (
              <li key={i} className={`slot${v === undefined ? " slot-empty" : ""}${isHeadOut ? " slot-out" : ""}${isNew ? " slot-new" : ""}`}>
                <span className="slot-pos">{i === 0 ? "head" : i + 1}</span>
                <span className="slot-val">{v === undefined ? "empty" : hex(v)}</span>
                {isHeadOut && <span className="slot-tag">read</span>}
                {isNew && <span className="slot-tag">written</span>}
              </li>
            );
          })}
        </ol>
      )}
    </figure>
  );
}

/** The reference queue before and after one recorded edge. Driven only by the selected trace row. */
export function QueueView({ row, depth }: { row: CycleRow; depth: number }) {
  const read = row.accepted.read && !row.accepted.reset;
  const write = row.accepted.write && !row.accepted.reset;
  return (
    <div className="queue-view">
      <p className="queue-view-title">
        Reference queue at cycle <span className="mono">{row.cycle}</span> · accepted: <strong>{acceptedText(row)}</strong>
      </p>
      <div className="queue-pair">
        <Slots queue={row.pre_queue} depth={depth} label="Before the edge" removedHead={read} />
        <ArrowRight className="queue-arrow" size={20} aria-hidden="true" />
        <Slots queue={row.post_queue} depth={depth} label="After the edge" appended={write} />
      </div>
    </div>
  );
}
