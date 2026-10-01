import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "../api/client";

export type AsyncState<T> =
  | { status: "loading"; data?: undefined; error?: undefined }
  | { status: "ok"; data: T; error?: undefined }
  | { status: "error"; data?: undefined; error: unknown };

/** Load once per dependency change; exposes reload. */
export function useAsync<T>(load: () => Promise<T>, deps: unknown[]): AsyncState<T> & { reload: () => void } {
  const [state, setState] = useState<AsyncState<T>>({ status: "loading" });
  const [nonce, setNonce] = useState(0);
  useEffect(() => {
    let live = true;
    setState((prev) => (prev.status === "ok" && nonce > 0 ? prev : { status: "loading" }));
    load().then(
      (data) => live && setState({ status: "ok", data }),
      (error: unknown) => live && setState({ status: "error", error }),
    );
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce]);
  const reload = useCallback(() => setNonce((n) => n + 1), []);
  return { ...state, reload };
}

/** A clock that ticks every `ms` while `active`; returns Date.now(). */
export function useNow(active: boolean, ms = 1000): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    setNow(Date.now());
    if (!active) return;
    const t = window.setInterval(() => setNow(Date.now()), ms);
    return () => window.clearInterval(t);
  }, [active, ms]);
  return now;
}

/**
 * Poll `load` every `intervalMs` while `shouldContinue(data)` is true.
 * Keeps the last good data on transient errors and reports the error separately.
 */
export function usePolling<T>(
  load: () => Promise<T>,
  shouldContinue: (data: T) => boolean,
  deps: unknown[],
  intervalMs = 1000,
): { data: T | null; error: unknown; loading: boolean; refresh: () => void } {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const [kick, setKick] = useState(0);
  const loadRef = useRef(load);
  const contRef = useRef(shouldContinue);
  loadRef.current = load;
  contRef.current = shouldContinue;

  useEffect(() => {
    setData(null);
    setLoading(true);
    setError(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    let live = true;
    let timer: number | undefined;
    const tick = async () => {
      try {
        const next = await loadRef.current();
        if (!live) return;
        setData(next);
        setError(null);
        setLoading(false);
        if (contRef.current(next)) timer = window.setTimeout(tick, intervalMs);
      } catch (err) {
        if (!live) return;
        setError(err);
        setLoading(false);
        // A missing resource will not appear by retrying; transient failures are retried more slowly.
        if (!(err instanceof ApiError && err.status === 404)) timer = window.setTimeout(tick, Math.max(intervalMs * 3, 3000));
      }
    };
    void tick();
    return () => {
      live = false;
      if (timer !== undefined) window.clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, kick, intervalMs]);

  const refresh = useCallback(() => setKick((k) => k + 1), []);
  return { data, error, loading, refresh };
}
