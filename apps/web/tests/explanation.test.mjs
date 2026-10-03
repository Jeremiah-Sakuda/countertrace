import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

test("real backend citation metadata renders and preserves citation warnings", async () => {
  const vite = await createServer({ server: { middlewareMode: true, hmr: false, ws: false, watch: null } });
  try {
    const { ExplanationPanel } = await vite.ssrLoadModule("/src/views/run/ExplanationPanel.tsx");
    const run = JSON.parse(await readFile(new URL("../../../recorded/rec-20261001-193038-ver-de51cd/run.json", import.meta.url), "utf8"));
    const render = (value) => renderToStaticMarkup(createElement(ExplanationPanel, {
      run: value, hasFinding: true, onCite: () => {}, onUpdated: () => {},
    }));
    const html = render(run);
    assert.match(html, /Model-generated explanation/);
    assert.match(html, /Show cycle 5 in the cycle table/);
    assert.match(html, /Show cycle 6 in the cycle table/);
    assert.doesNotMatch(html, /invalid citation|Some citations do not match/);
    assert.match(html, /nvidia\/Nemotron-3-Ultra-550b-a55b/);

    const mixed = structuredClone(run);
    mixed.explanation.result.steps.push({ text: "Unsupported cycle", cycles: [99], signals: [] });
    const invalidStep = mixed.explanation.result.steps.length - 1;
    mixed.explanation.result.steps.push({ text: "Uncited statement", cycles: [], signals: [] });
    mixed.explanation.citation_check.invalid.push({ step: invalidStep, kind: "cycle", value: 99 });
    mixed.explanation.citation_check.uncited_steps = 1;
    const warnings = render(mixed);
    assert.match(warnings, /Some citations do not match/);
    assert.match(warnings, /cycle 99 \(invalid citation\)/);
    assert.doesNotMatch(warnings, /Show cycle 99 in the cycle table/);
    assert.match(warnings, /no evidence cited/);
  } finally {
    await vite.close();
  }
});
