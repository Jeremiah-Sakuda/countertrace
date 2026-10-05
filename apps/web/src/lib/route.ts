import { useEffect, useState } from "react";

export type Route =
  | { name: "learn"; id: string | null }
  | { name: "teach" }
  | { name: "setup"; exampleId: string | null }
  | { name: "runs" }
  | { name: "run"; id: string }
  | { name: "audit" }
  | { name: "notFound"; hash: string };

export function parseHash(hash: string): Route {
  const path = hash.replace(/^#/, "") || "/";
  const parts = path.split("/").filter(Boolean).map(decodeURIComponent);
  if (parts.length === 0) return { name: "learn", id: null };
  if (parts[0] === "learn" && parts.length <= 2) return { name: "learn", id: parts[1] ?? null };
  if (parts[0] === "teach" && parts.length === 1) return { name: "teach" };
  if (parts[0] === "examples" && parts.length <= 2) return { name: "setup", exampleId: parts[1] ?? null };
  if (parts[0] === "runs" && parts.length === 1) return { name: "runs" };
  if (parts[0] === "runs" && parts.length === 2 && parts[1]) return { name: "run", id: parts[1] };
  if (parts[0] === "audit" && parts.length === 1) return { name: "audit" };
  return { name: "notFound", hash: path };
}

export const href = {
  setup: (exampleId?: string | null) => (exampleId ? `#/examples/${encodeURIComponent(exampleId)}` : "#/examples"),
  runs: () => "#/runs",
  run: (id: string) => `#/runs/${encodeURIComponent(id)}`,
  audit: () => "#/audit",
};

export function navigate(to: string, replace = false): void {
  if (replace) {
    history.replaceState(null, "", to);
    window.dispatchEvent(new HashChangeEvent("hashchange"));
  } else {
    window.location.hash = to.replace(/^#/, "");
  }
}

export function useRoute(): Route {
  const [route, setRoute] = useState<Route>(() => parseHash(window.location.hash));
  useEffect(() => {
    const onChange = () => setRoute(parseHash(window.location.hash));
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return route;
}
