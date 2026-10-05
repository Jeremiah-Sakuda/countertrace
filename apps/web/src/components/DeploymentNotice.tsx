import type { Status } from "../api/types";
import type { AsyncState } from "../lib/hooks";
import { Callout } from "./common";

export const LOCAL_BUILD_URL = "https://github.com/Jeremiah-Sakuda/countertrace#quick-start";

export function isRecordedDemo(status: AsyncState<Status>): boolean {
  return status.status === "ok" && status.data.deployment?.mode === "recorded";
}

/** Do not offer a write while the deployment's capabilities are still unknown. */
export function liveActionsAvailable(status: AsyncState<Status>): boolean {
  return status.status === "ok" && status.data.deployment?.live_available !== false;
}

export function DeploymentNotice({ status }: { status: AsyncState<Status> }) {
  if (!isRecordedDemo(status) || status.status !== "ok") return null;
  return (
    <div className="deployment-notice">
      <Callout title="Recorded demo">
        <p>{status.data.deployment?.notice}</p>
        <p><a href={LOCAL_BUILD_URL}>Run the local test build</a> to use live verification and model calls.</p>
      </Callout>
    </div>
  );
}
