import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api/client";
import { Callout } from "./components/common";
import { Header, type RunContextInfo } from "./components/Header";
import { useAsync } from "./lib/hooks";
import { href, useRoute } from "./lib/route";
import { AuditView } from "./views/AuditView";
import { RunsView } from "./views/RunsView";
import { RunView } from "./views/run/RunView";
import { SetupView } from "./views/SetupView";

export function App() {
  const route = useRoute();
  const status = useAsync(() => api.status(), []);
  const profile = useAsync(() => api.profile(), []);
  const [runContext, setRunContext] = useState<RunContextInfo | null>(null);
  const onContext = useCallback((info: RunContextInfo | null) => setRunContext(info), []);
  const mainRef = useRef<HTMLElement>(null);
  const first = useRef(true);

  // Move focus to the main region on navigation so keyboard and screen-reader users land on the new view.
  const routeKey = route.name === "run" ? `run:${route.id}` : route.name;
  useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    mainRef.current?.focus({ preventScroll: true });
    window.scrollTo({ top: 0 });
  }, [routeKey]);

  return (
    <>
      <a href="#main" className="skip-link" onClick={(e) => { e.preventDefault(); mainRef.current?.focus(); }}>
        Skip to main content
      </a>
      <Header status={status} route={route} run={route.name === "run" ? runContext : null} />
      <main id="main" ref={mainRef} tabIndex={-1} className="main">
        {route.name === "setup" && <SetupView exampleId={route.exampleId} profile={profile} status={status} />}
        {route.name === "runs" && <RunsView />}
        {route.name === "run" && <RunView key={route.id} id={route.id} profile={profile} status={status} onContext={onContext} />}
        {route.name === "audit" && <AuditView profile={profile} />}
        {route.name === "notFound" && (
          <Callout kind="warn" title="Page not found">
            <p>
              Nothing lives at <code>{route.hash}</code>. Go to <a href={href.setup()}>contract setup</a> or the <a href={href.runs()}>runs list</a>.
            </p>
          </Callout>
        )}
      </main>
      <footer className="site-footer">
        <p>
          Countertrace {status.status === "ok" ? `v${status.data.version}` : ""} · Results apply only to the stated contract, parameters,
          assumptions, and methods. Model output is advisory and never authorizes a result.
        </p>
      </footer>
    </>
  );
}
