import assert from "node:assert/strict";
import test from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

test("recorded deployments explain their limits and never offer live model or audit actions", async () => {
  const vite = await createServer({ server: { middlewareMode: true, hmr: false, ws: false, watch: null } });
  try {
    const { DeploymentNotice, liveActionsAvailable } = await vite.ssrLoadModule("/src/components/DeploymentNotice.tsx");
    const { Header } = await vite.ssrLoadModule("/src/components/Header.tsx");
    const { AuditView } = await vite.ssrLoadModule("/src/views/AuditView.tsx");
    const data = {
      verifier: { docker: false, docker_detail: null, image_built: false },
      model: { configured: false, reason: "Local model credentials are not configured." },
      deployment: { mode: "recorded", live_available: false, notice: "Recorded evidence demo. Live actions use the local test build." },
    };
    const recorded = { status: "ok", data };
    const render = (component, props) => renderToStaticMarkup(createElement(component, props));

    assert.equal(liveActionsAvailable(recorded), false);
    assert.equal(liveActionsAvailable({ status: "loading" }), false);
    assert.equal(liveActionsAvailable({ status: "error", error: new Error("status unavailable") }), false);
    assert.match(render(DeploymentNotice, { status: recorded }), /Recorded demo/);
    assert.match(render(DeploymentNotice, { status: recorded }), /github.com\/Jeremiah-Sakuda\/countertrace#quick-start/);
    const header = render(Header, { status: recorded, route: { name: "audit" }, run: null });
    assert.doesNotMatch(header, /Docker unavailable|image not built|Model not configured/);
    assert.match(header, /Recorded edition/);
    const audit = render(AuditView, { profile: { status: "loading" }, status: recorded });
    assert.match(audit, /<textarea[^>]*disabled=""/);
    assert.match(audit, /<button[^>]*disabled=""[^>]*>[\s\S]*?Propose a check set with Nemotron/);
    assert.match(audit, /Model proposals are unavailable in this recorded demo/);

    const { deployment: _deployment, ...localData } = data;
    const local = { status: "ok", data: localData };
    assert.equal(liveActionsAvailable(local), true);
    assert.equal(render(DeploymentNotice, { status: local }), "");
    assert.match(render(Header, { status: local, route: { name: "audit" }, run: null }), /Docker unavailable/);
  } finally {
    await vite.close();
  }
});
