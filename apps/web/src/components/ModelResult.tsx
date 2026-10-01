import { Bot, CircleAlert, PlugZap } from "lucide-react";
import type { ModelCall, ModelResult, ModelStatus } from "../api/types";
import { Callout, TableScroll } from "./common";

const STATUS_TEXT: Record<ModelStatus, string> = {
  ok: "Model output received",
  ok_with_invalid_citations: "Model output received with invalid citations",
  schema_error: "Model output did not match the required schema",
  unavailable: "Model unavailable",
  input_too_large: "Input too large for the model limit",
  error: "Model call failed",
  not_applicable: "Not applicable",
};

/** The banner shown above any model-generated content. */
export function ModelProvenance({ task }: { task: string }) {
  return (
    <p className="model-provenance">
      <Bot size={16} aria-hidden="true" />
      <span>
        <strong>Model-generated {task}.</strong> NVIDIA Nemotron proposed this text from the recorded evidence. It is not part
        of the verdict and cannot change any check result.
      </span>
    </p>
  );
}

/** Honest non-ok states. Returns null when the status is ok or ok_with_invalid_citations. */
export function ModelStatusNotice({ result, what }: { result: ModelResult<unknown>; what: string }) {
  if (result.status === "ok" || result.status === "ok_with_invalid_citations") return null;
  if (result.status === "unavailable") {
    return (
      <Callout kind="model" icon={PlugZap} title={`${what} is unavailable`} role="status">
        <p>{result.detail || "The model is not configured on this server."}</p>
        <p className="muted small">
          To enable it, set <code>NEBIUS_API_KEY</code>, <code>NEBIUS_BASE_URL</code>, and <code>NEBIUS_MODEL_ID</code> in the
          server environment and restart <code>countertrace serve</code>. Verification results never depend on the model, and nothing has been generated in its place.
        </p>
      </Callout>
    );
  }
  if (result.status === "not_applicable") {
    return (
      <Callout kind="info" title={`${what}: not applicable`} role="status">
        <p>{result.detail || "There is nothing for the model to work on for this run."}</p>
      </Callout>
    );
  }
  return (
    <Callout kind="error" icon={CircleAlert} title={`${what}: ${STATUS_TEXT[result.status] ?? result.status}`} role="alert">
      <p>{result.detail || "No usable model output was produced. Nothing is shown in its place."}</p>
    </Callout>
  );
}

export function ModelCalls({ calls }: { calls: ModelCall[] | undefined }) {
  if (!calls || calls.length === 0) return null;
  return (
    <TableScroll label="Model calls">
      <table className="data-table compact">
        <caption className="sr-only">Model calls</caption>
        <thead>
          <tr>
            <th scope="col">Task</th>
            <th scope="col">Model</th>
            <th scope="col">Endpoint</th>
            <th scope="col" className="num">
              Latency
            </th>
            <th scope="col" className="num">
              Prompt tokens
            </th>
            <th scope="col" className="num">
              Completion tokens
            </th>
            <th scope="col" className="num">
              Attempts
            </th>
            <th scope="col">Status</th>
          </tr>
        </thead>
        <tbody>
          {calls.map((c, i) => (
            <tr key={i}>
              <td>{c.task}</td>
              <td className="mono">{c.model_id ?? "—"}</td>
              <td className="mono">{c.endpoint_host ?? "—"}</td>
              <td className="num mono">{c.latency_ms != null ? `${(c.latency_ms / 1000).toFixed(1)} s` : "—"}</td>
              <td className="num mono">{c.prompt_tokens ?? "—"}</td>
              <td className="num mono">{c.completion_tokens ?? "—"}</td>
              <td className="num mono">{c.attempts ?? "—"}</td>
              <td>
                {c.status}
                {c.schema_error ? <span className="muted"> · {c.schema_error}</span> : null}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </TableScroll>
  );
}
