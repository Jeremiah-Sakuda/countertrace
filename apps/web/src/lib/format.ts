/** Two-digit uppercase hex for 8-bit words, e.g. 0x21. */
export function hex(value: number | null | undefined, width = 2): string {
  if (value === null || value === undefined) return "—";
  return `0x${value.toString(16).toUpperCase().padStart(width, "0")}`;
}

export function queueText(queue: number[] | null | undefined): string {
  if (queue === null || queue === undefined) return "unspecified";
  if (queue.length === 0) return "[ ]";
  return `[${queue.map((v) => hex(v)).join(", ")}]`;
}

export function bit(value: boolean | number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return value === true || value === 1 ? "1" : "0";
}

export function parseIso(value: string | null | undefined): number | null {
  if (!value) return null;
  const t = Date.parse(value);
  return Number.isNaN(t) ? null : t;
}

export function formatDateTime(value: string | null | undefined): string {
  const t = parseIso(value);
  if (t === null) return "—";
  return new Date(t).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

/** Seconds between two timestamps, using `now` when the end is missing. */
export function elapsedSeconds(start: string | null | undefined, end: string | null | undefined, now: number): number | null {
  const s = parseIso(start);
  if (s === null) return null;
  const e = parseIso(end) ?? now;
  return Math.max(0, (e - s) / 1000);
}

export function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || Number.isNaN(seconds)) return "—";
  if (seconds < 60) return `${seconds < 10 ? seconds.toFixed(1) : Math.round(seconds)} s`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m} min ${s.toString().padStart(2, "0")} s`;
}

export function shortHash(hash: string | null | undefined, n = 8): string {
  if (!hash) return "—";
  const body = hash.includes(":") ? hash.split(":").pop() ?? hash : hash;
  return body.slice(0, n);
}

export function humanize(id: string): string {
  const s = id.replace(/[_-]+/g, " ").trim();
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export const STAGE_LABELS: Record<string, string> = {
  queued: "Queued",
  validating: "Validating RTL",
  simulating: "Simulating",
  checking_properties: "Checking properties",
  replaying: "Replaying formal trace",
  explaining: "Explaining",
  mutating: "Running seeded faults",
};

export const CHECK_SIGNAL: Record<string, "dout" | "empty" | "full"> = {
  read_data: "dout",
  empty_flag: "empty",
  full_flag: "full",
};

export const METHOD_LABELS: Record<string, string> = {
  simulation: "Simulation",
  bmc: "Bounded model check",
  prove: "Unbounded proof",
  cover: "Reachability",
  admission: "Admission",
};
