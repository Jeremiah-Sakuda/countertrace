import { useId } from "react";
import type { CycleRow } from "../api/types";
import { hex } from "../lib/format";

const COL = 56;
const LABEL = 76;
const LANE = 30;
const TOP = 26;

type Bit = { kind: "bit"; name: string; value: (r: CycleRow) => number; expected?: (r: CycleRow) => number; check?: string };
type Bus = { kind: "bus"; name: string; value: (r: CycleRow) => string; expected?: (r: CycleRow) => string | null; check?: string };

const SIGNALS: (Bit | Bus)[] = [
  { kind: "bit", name: "rst", value: (r) => r.rst },
  { kind: "bit", name: "wr_en", value: (r) => r.wr_en },
  { kind: "bit", name: "rd_en", value: (r) => r.rd_en },
  { kind: "bus", name: "din", value: (r) => hex(r.din) },
  {
    kind: "bus",
    name: "dout",
    value: (r) => hex(r.observed.dout),
    expected: (r) => (r.dout_checked ? hex(r.expected.dout) : null),
    check: "read_data",
  },
  { kind: "bit", name: "empty", value: (r) => (r.observed.empty ? 1 : 0), expected: (r) => (r.expected.empty ? 1 : 0), check: "empty_flag" },
  { kind: "bit", name: "full", value: (r) => (r.observed.full ? 1 : 0), expected: (r) => (r.expected.full ? 1 : 0), check: "full_flag" },
];

/**
 * A per-edge waveform drawn only from recorded trace rows. Each column is one rising edge:
 * inputs as driven at that edge, outputs as observed after it. No intermediate events are invented.
 */
export function Waveform({ rows, markCycle }: { rows: CycleRow[]; markCycle?: number }) {
  const uid = useId().replace(/:/g, "");
  if (rows.length === 0) return <p className="muted">No trace rows to draw.</p>;
  const width = LABEL + rows.length * COL + 8;
  const height = TOP + SIGNALS.length * LANE + 8;
  const x = (i: number) => LABEL + i * COL;

  return (
    <div className="waveform-scroll" role="region" aria-label="Per-edge waveform" tabIndex={0}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="waveform" role="img" aria-labelledby={`${uid}-t ${uid}-d`}>
        <title id={`${uid}-t`}>Per-edge waveform for cycles {rows[0]?.cycle} to {rows[rows.length - 1]?.cycle}</title>
        <desc id={`${uid}-d`}>
          Drawn from the recorded trace rows. Inputs as driven at each rising edge; outputs as observed after the edge. Mismatching
          cells are outlined and labelled in the cycle table.
        </desc>
        {rows.map((r, i) => {
          const bad = r.mismatches.length > 0;
          return (
            <g key={`col-${r.cycle}`}>
              {(bad || r.cycle === markCycle) && (
                <rect x={x(i)} y={TOP - 4} width={COL} height={SIGNALS.length * LANE + 4} className={bad ? "wf-bad" : "wf-mark"} />
              )}
              <line x1={x(i)} x2={x(i)} y1={TOP - 6} y2={height - 6} className="wf-grid" />
              <text x={x(i) + COL / 2} y={14} className="wf-cycle" textAnchor="middle">
                {r.cycle}
              </text>
            </g>
          );
        })}
        {SIGNALS.map((sig, s) => {
          const y0 = TOP + s * LANE;
          const hi = y0 + 4;
          const lo = y0 + LANE - 8;
          return (
            <g key={sig.name}>
              <text x={8} y={y0 + LANE / 2 + 2} className="wf-label">
                {sig.name}
              </text>
              {sig.kind === "bit" ? (
                <>
                  <path
                    className="wf-bit"
                    d={rows
                      .map((r, i) => {
                        const y = sig.value(r) ? hi : lo;
                        return `${i === 0 ? "M" : "L"}${x(i)},${y} L${x(i) + COL},${y}`;
                      })
                      .join(" ")}
                  />
                  {sig.expected &&
                    rows.map((r, i) =>
                      sig.check && r.mismatches.includes(sig.check) ? (
                        <path
                          key={`exp-${r.cycle}`}
                          className="wf-expected"
                          d={`M${x(i)},${sig.expected!(r) ? hi : lo} L${x(i) + COL},${sig.expected!(r) ? hi : lo}`}
                        />
                      ) : null,
                    )}
                </>
              ) : (
                rows.map((r, i) => {
                  const v = sig.value(r);
                  const exp = sig.expected?.(r);
                  const bad = sig.check ? r.mismatches.includes(sig.check) : false;
                  const unchecked = sig.name === "dout" && !r.dout_checked;
                  return (
                    <g key={`${sig.name}-${r.cycle}`}>
                      <path
                        className={`wf-bus${unchecked ? " wf-dim" : ""}`}
                        d={`M${x(i) + 3},${hi} L${x(i) + COL - 3},${hi} L${x(i) + COL},${(hi + lo) / 2} L${x(i) + COL - 3},${lo} L${x(i) + 3},${lo} L${x(i)},${(hi + lo) / 2} Z`}
                      />
                      <text x={x(i) + COL / 2} y={(hi + lo) / 2 + 4} textAnchor="middle" className={`wf-value${unchecked ? " wf-dim-text" : ""}`}>
                        {v.replace("0x", "")}
                      </text>
                      {bad && exp && (
                        <text x={x(i) + COL / 2} y={lo + 9} textAnchor="middle" className="wf-exp-text">
                          exp {exp.replace("0x", "")}
                        </text>
                      )}
                    </g>
                  );
                })
              )}
            </g>
          );
        })}
      </svg>
      <p className="muted small wf-legend">
        Hex values without the 0x prefix. Dashed segments show the expected flag value where it differs; dimmed dout values were
        not checked (no accepted read). Shaded columns contain a mismatch.
      </p>
    </div>
  );
}
