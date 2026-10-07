import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api/client";
import { Callout } from "./components/common";
import { DeploymentNotice } from "./components/DeploymentNotice";
import { Header, type RunContextInfo } from "./components/Header";
import { useAsync, useDocumentTitle } from "./lib/hooks";
import { href, useRoute } from "./lib/route";
import { AuditView } from "./views/AuditView";
import { RunsView } from "./views/RunsView";
import { RunView } from "./views/run/RunView";
import { LearnHome, LearnView, TeachView } from "./views/LearnView";
import { RepairLabView } from "./views/RepairLabView";
import { SetupView } from "./views/SetupView";

function NotFound({ hash }: { hash: string }) {
  useDocumentTitle("Page not found");
  return (
    <Callout kind="warn" title="Page not found">
      <p>
        Nothing lives at <code>{hash}</code>. Go to <a href={href.setup()}>contract setup</a> or the <a href={href.runs()}>runs list</a>.
      </p>
    </Callout>
  );
}

export function App() {
  const route = useRoute();
  const status = useAsync(() => api.status(), []);
  const profile = useAsync(() => api.profile(), []);
  const [runContext, setRunContext] = useState<RunContextInfo | null>(null);
  const onContext = useCallback((info: RunContextInfo | null) => setRunContext(info), []);
  const mainRef = useRef<HTMLElement>(null);
  const first = useRef(true);

  // Move focus to the main region on navigation so keyboard and screen-reader users land on the new view.
  const routeKey = route.name === "run" || route.name === "learn" ? `${route.name}:${route.id}` : route.name;

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
        {route.name !== "home" && route.name !== "repair" && route.name !== "learn" && route.name !== "teach" && <DeploymentNotice status={status} />}
        {(route.name === "home" || route.name === "repair") && <RepairLabView home={route.name === "home"} caseId={route.name === "repair" ? route.caseId : null} />}
        {route.name === "learn" && (route.id ? <LearnView key={route.id} id={route.id} status={status} /> : <LearnHome />)}
        {route.name === "teach" && <TeachView />}
        {route.name === "setup" && <SetupView exampleId={route.exampleId} profile={profile} status={status} />}
        {route.name === "runs" && <RunsView status={status} />}
        {route.name === "run" && <RunView key={route.id} id={route.id} profile={profile} status={status} onContext={onContext} />}
        {route.name === "audit" && <AuditView profile={profile} status={status} />}
        {route.name === "notFound" && <NotFound hash={route.hash} />}
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
