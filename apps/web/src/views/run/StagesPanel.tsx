import type { Stage } from "../../api/types";
import { StageBadge } from "../../components/StatusBadge";
import { elapsedSeconds, formatDuration, STAGE_LABELS } from "../../lib/format";

/** Actual stages with real status and elapsed time. No progress percentages are shown or estimated. */
export function StagesPanel({ stages, now, compact }: { stages: Stage[]; now: number; compact?: boolean }) {
  if (stages.length === 0) return <p className="muted">No stages reported yet.</p>;
  const finished = stages.filter((s) => s.status === "done" || s.status === "skipped").length;
  return (
    <div className={`stages${compact ? " stages-compact" : ""}`}>
      <p className="muted small">
        {finished} of {stages.length} stages finished (done or skipped). Stages may run concurrently.
      </p>
      <ol className="stage-list">
        {stages.map((s) => {
          const secs = s.started_at ? elapsedSeconds(s.started_at, s.finished_at, now) : null;
          return (
            <li key={s.id} className={`stage stage-${s.status}`}>
              <div className="stage-head">
                <span className="stage-name">{STAGE_LABELS[s.id] ?? s.id}</span>
                <StageBadge status={s.status} />
              </div>
              <p className="stage-meta">
                <span className="mono">{secs === null ? "not started" : formatDuration(secs)}</span>
                {s.status === "running" && <span className="muted"> elapsed</span>}
              </p>
              {s.detail && <p className="stage-detail">{s.detail}</p>}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
