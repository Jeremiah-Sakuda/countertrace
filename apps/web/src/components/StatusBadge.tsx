import {
  Ban,
  CircleCheck,
  CircleDashed,
  CircleHelp,
  CircleMinus,
  CircleX,
  FlaskConical,
  LoaderCircle,
  ScanSearch,
  Timer,
  Wrench,
  type LucideIcon,
} from "lucide-react";
import type { ObligationStatus, StageStatus, VerdictHeadline } from "../api/types";

/** Status tones map to CSS classes; every badge renders text and an icon, never color alone. */
export type Tone = "fail" | "proved" | "bounded" | "sim" | "unresolved" | "toolerror" | "neutral" | "info" | "running";

interface Spec {
  tone: Tone;
  icon: LucideIcon;
  label: string;
}

/** Fallback labels follow the PRD result table; obligation.label from the backend wins when present. */
export const OBLIGATION_STATUS: Record<ObligationStatus, Spec> = {
  counterexample: { tone: "fail", icon: CircleX, label: "Counterexample found" },
  proved: { tone: "proved", icon: CircleCheck, label: "Property proved under these assumptions" },
  bounded_pass: { tone: "bounded", icon: Timer, label: "No counterexample within N cycles" },
  simulation_passed: { tone: "sim", icon: FlaskConical, label: "Simulation passed for these runs" },
  unresolved: { tone: "unresolved", icon: CircleHelp, label: "Unresolved" },
  tool_error: { tone: "toolerror", icon: Wrench, label: "Tool error" },
  not_checked: { tone: "neutral", icon: CircleMinus, label: "Not checked" },
  unsupported: { tone: "neutral", icon: Ban, label: "Unsupported" },
};

export const VERDICT: Record<VerdictHeadline, Spec> = {
  pending: { tone: "running", icon: LoaderCircle, label: "Pending" },
  counterexample: { tone: "fail", icon: CircleX, label: "Counterexample found" },
  no_counterexample: { tone: "info", icon: ScanSearch, label: "No counterexample found by these methods" },
  unresolved: { tone: "unresolved", icon: CircleHelp, label: "Unresolved" },
  tool_error: { tone: "toolerror", icon: Wrench, label: "Tool error" },
  unsupported: { tone: "neutral", icon: Ban, label: "Unsupported" },
};

export const STAGE_STATUS: Record<StageStatus, Spec> = {
  pending: { tone: "neutral", icon: CircleDashed, label: "Pending" },
  running: { tone: "running", icon: LoaderCircle, label: "Running" },
  done: { tone: "info", icon: CircleCheck, label: "Done" },
  error: { tone: "toolerror", icon: Wrench, label: "Error" },
  skipped: { tone: "neutral", icon: CircleMinus, label: "Skipped" },
  cancelled: { tone: "neutral", icon: Ban, label: "Cancelled" },
};

interface BadgeProps {
  tone: Tone;
  icon: LucideIcon;
  children: React.ReactNode;
  spin?: boolean;
  size?: "sm" | "md";
  title?: string;
}

export function Badge({ tone, icon: Icon, children, spin, size = "sm", title }: BadgeProps) {
  return (
    <span className={`badge badge-${tone} badge-${size}`} title={title}>
      <Icon aria-hidden="true" className={spin ? "spin" : undefined} size={size === "md" ? 18 : 14} strokeWidth={2.25} />
      <span>{children}</span>
    </span>
  );
}

export function ObligationBadge({ status, label }: { status: ObligationStatus; label?: string | null }) {
  const spec = OBLIGATION_STATUS[status] ?? OBLIGATION_STATUS.not_checked;
  return (
    <Badge tone={spec.tone} icon={spec.icon}>
      {label || spec.label}
    </Badge>
  );
}

export function VerdictBadge({ headline, size = "sm" }: { headline: VerdictHeadline | null | undefined; size?: "sm" | "md" }) {
  const spec = (headline && VERDICT[headline]) || VERDICT.pending;
  return (
    <Badge tone={spec.tone} icon={spec.icon} size={size} spin={headline === "pending"}>
      {spec.label}
    </Badge>
  );
}

export function StageBadge({ status }: { status: StageStatus }) {
  const spec = STAGE_STATUS[status] ?? STAGE_STATUS.pending;
  return (
    <Badge tone={spec.tone} icon={spec.icon} spin={status === "running"}>
      {spec.label}
    </Badge>
  );
}
