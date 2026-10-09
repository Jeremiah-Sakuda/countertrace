import type {
  CatalogModule,
  CheckSet,
  CheckSetProposal,
  Example,
  ExampleDetail,
  Explanation,
  Interpretation,
  Profile,
  RecordedRunSummary,
  RepairStartResponse,
  Run,
  RunSummary,
  Status,
} from "./types";

/** An API failure with the HTTP status and the server's `{error}` message when present. */
export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
  /** True when the endpoint does not exist (yet) in this backend build. */
  get missing(): boolean {
    return this.status === 404 || this.status === 405 || this.status === 501;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      ...init,
      headers: { Accept: "application/json", ...(init?.body ? { "Content-Type": "application/json" } : {}), ...init?.headers },
    });
  } catch (err) {
    throw new ApiError(0, `Could not reach the control service (${err instanceof Error ? err.message : String(err)}).`);
  }
  const text = await response.text();
  let data: unknown = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }
  if (!response.ok) {
    const message =
      data && typeof data === "object" && "error" in data && typeof (data as { error: unknown }).error === "string"
        ? (data as { error: string }).error
        : `HTTP ${response.status} ${response.statusText}`.trim();
    throw new ApiError(response.status, message);
  }
  if (data === null) throw new ApiError(response.status, "The control service returned a response that is not JSON.");
  return data as T;
}

const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body === undefined ? "{}" : JSON.stringify(body) });

export const api = {
  modules: () => request<CatalogModule[]>("/api/modules"),
  module: (id: string) => request<CatalogModule>(`/api/modules/${encodeURIComponent(id)}`),
  hunt: (id: string, exampleId: string) => post<RunSummary>(`/api/runs/${encodeURIComponent(id)}/hunt`, { example_id: exampleId }),
  createChecks: (moduleId: string) => post<RunSummary>("/api/check-runs", { module_id: moduleId }),
  status: () => request<Status>("/api/status"),
  profile: () => request<Profile>("/api/profile"),
  examples: () => request<Example[]>("/api/examples"),
  example: (id: string) => request<ExampleDetail>(`/api/examples/${encodeURIComponent(id)}`),
  checkSets: () => request<CheckSet[]>("/api/check-sets"),
  recorded: () => request<RecordedRunSummary[]>("/api/recorded"),
  runs: () => request<RunSummary[]>("/api/runs"),
  run: (id: string) => request<Run>(`/api/runs/${encodeURIComponent(id)}`),
  createRun: (exampleId: string, acceptedContractHash: string) =>
    post<RunSummary>("/api/runs", { example_id: exampleId, accepted_contract_hash: acceptedContractHash }),
  cancel: (id: string) => post<{ cancelled: boolean }>(`/api/runs/${encodeURIComponent(id)}/cancel`),
  explain: (id: string) => post<Explanation>(`/api/runs/${encodeURIComponent(id)}/explain`),
  repair: (id: string) => post<RepairStartResponse>(`/api/runs/${encodeURIComponent(id)}/repair`),
  candidate: (id: string, source: string) => post<unknown>(`/api/runs/${encodeURIComponent(id)}/candidates`, { source }),
  interpret: (exampleId: string) => post<Interpretation>("/api/interpret", { example_id: exampleId }),
  proposeCheckSet: (description: string, depth: number) => post<CheckSetProposal>("/api/check-sets/propose", { description, depth }),
  createAudit: (checkSet: string, depth: number) => post<RunSummary>("/api/audits", { check_set: checkSet, depth }),
  /** Raw run artifact as text (logs, VCD, source). */
  async file(id: string, path: string): Promise<string> {
    const response = await fetch(fileUrl(id, path));
    if (!response.ok) {
      let message = `HTTP ${response.status}`;
      try {
        const data = (await response.json()) as { error?: string };
        if (data.error) message = data.error;
      } catch {
        /* not JSON */
      }
      throw new ApiError(response.status, message);
    }
    return response.text();
  },
};

export function fileUrl(runId: string, path: string): string {
  const clean = path.replace(/^\/+/, "").split("/").map(encodeURIComponent).join("/");
  return `/api/runs/${encodeURIComponent(runId)}/files/${clean}`;
}

export function bundleUrl(runId: string): string {
  return `/api/runs/${encodeURIComponent(runId)}/bundle`;
}

export function errorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 0) return err.message;
    if (err.missing) return `Not available in this backend build (${err.status}: ${err.message}).`;
    return `${err.message} (HTTP ${err.status})`;
  }
  return err instanceof Error ? err.message : String(err);
}
