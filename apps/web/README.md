# Web interface

The Countertrace workbench UI: a Vite + React 18 + TypeScript (strict) single-page app that consumes the control-service JSON API described in [docs/API.md](../../docs/API.md). It has no CSS framework or router dependency; styles are hand-written with CSS custom-property tokens in `src/styles.css`, and routing uses the URL hash.

## Develop and build

Requires Node 20+.

```bash
cd apps/web
npm install
npm run dev       # Vite dev server on http://localhost:5173, proxies /api to http://127.0.0.1:8765
npm run build     # tsc --noEmit, then vite build into apps/web/dist
npm run preview   # serve the built bundle (API calls still need the control service)
```

Start the control service from the repository root with `PYTHONPATH=src python3 -m countertrace serve --port 8765`. After `npm run build`, the service also serves `apps/web/dist` at `http://127.0.0.1:8765/`, falling back to `index.html` for client routes. `dist/` is git-ignored.

Dependencies: `react`, `react-dom`, `lucide-react` (icons). Dev: `vite`, `@vitejs/plugin-react`, `typescript`, `@types/react`, `@types/react-dom`.

## Surfaces

| Route | Surface | What it shows |
| --- | --- | --- |
| `#/` and `#/examples/<id>` | Contract setup | Opens with one value line and a three-step "60-second tour" of the recorded showcase (first mismatch, Nemotron explanation, accepted repair). Every number in the tour is read from `/api/runs/<id>`, and its call to action opens that run. Bundled examples grouped as Showcase and Development, with the author's expected outcome labelled as intent, not a result. The selected example shows its brief, seeded-fault description, line-numbered read-only RTL, the exact contract (requirements, checks, ports, parameters, assumptions, sampling convention), and the PRD depth-2 timing table labelled "Specified expectations (not executed results)". "Interpret brief with Nemotron" shows the decisions table and blocking conflicts; a blocking conflict requires an explicit acknowledgement before acceptance. The user accepts the exact contract version and hash, then starts a live run. |
| `#/runs/<id>` (verification) | Findings | Polls once a second while the run (or its repair) is active. Leads with the violated requirement, failed check, and first observed mismatch, then an expected-versus-observed table and a keyboard-navigable cycle table for the finding window (full trace on demand). A queue view and an SVG waveform are drawn only from recorded trace rows. Formal counterexamples and their replay status are shown separately. Without a finding the page says "No counterexample found by these methods" with per-method statuses, never "verified". Obligations are grouped by method with "What does this mean?" explanations. Expandable evidence: coverage per contract row, cover steps, integrity notes, admission diagnostics, tool versions and batches, frozen hashes, and raw logs/VCDs. |
| `#/runs/<id>` (explanation, repair, export) | Explanation, repair, export | "Explain with Nemotron" renders model output under a model-generated label with clickable cycle citations, citation-check warnings, cited RTL lines, and call metrics. "Propose a repair with Nemotron" shows each attempt (n of 3) with status, rationale, unified diff, frozen-hash comparison, and a link to the candidate run. "Edit RTL yourself" appears only when the server reports uploads enabled. "Download evidence bundle" fetches `/api/runs/<id>/bundle`. Recorded runs hide explain, repair, and cancel. |
| `#/runs/<id>` (audit) and `#/audit` | Check-quality audit | Explains that the audit scores a named supplemental check set, not the user's testbench or design confidence. Lists check sets (model-proposed candidates are labelled "Model-proposed, not reviewed"), offers "Propose a check set with Nemotron" from a description, and runs audits. Results group seeded faults by classification (valid, equivalent, unresolved, invalid, baseline), show core validity separately from supplemental kills, list which requirements the set exercises and checks, and include a short "Which requirement is this check set missing?" exercise. |
| `#/runs` | Runs | Recorded runs (labelled Recorded, with their own dates; cards lead with the first mismatch, explanation, and accepted repair when the record has them), then runs on this server, shown 12 at a time with their origin. Evaluation-suite runs stay hidden until "Show evaluation runs" is checked. |

Every view handles loading, error, and empty states. Endpoints that are missing or failing show their error message instead of placeholder data. When the model is not configured, every model action shows the server's reason and the environment variables to set. It never shows generated text.

Review follow-ups (October 4, 2026): run pages show a "Probable origin" line when the trace shows the observed word was offered at an earlier edge where the contract ignored it (derived from the trace, not the model), and they label simulation and formal findings as distinct first failures. Explanation citations bring the reference queue and the cited row into view, with a "Back to explanation" control. Repair candidates show the parent link, the accepted diff, and the parent-versus-candidate status of each obligation, and the parent's hero links to a passing candidate. The audit hides its answer (missing requirements and the coverage table) until the learner exercise is answered or skipped. On narrow screens the cycle table puts the dout, empty, and full columns first, and its screen-reader text uses sentences such as "dout expected not checked, observed 0xD7".

## Design rules

The design system is persisted in [`design-system/countertrace/MASTER.md`](design-system/countertrace/MASTER.md): an editorial evidence notebook with warm paper, ink, rust actions, a pale sage navigation rail, Newsreader headings, DM Sans body, and JetBrains Mono data. Setup has numbered review steps and a compact example selector on small screens; recorded runs use case cards; run details lead with an actual failing-cycle summary and a reference queue before the table. Runtime details and provenance remain available in labelled disclosures. Its evidence rules apply:

- Green result text appears only on individual passing check statuses. Actions and focus use rust; pale sage surfaces are neutral structure, never a success claim.
- Every status carries an icon and the exact PRD wording, so color is never the only signal.
- No progress percentages, no universal "verified" badge, and no queue or waveform events that are not in the recorded trace.
- Visible focus rings, keyboard-navigable cycle rows (arrow keys, Home, End) and citations, `aria-live` run-state announcements, `prefers-reduced-motion` support, and layouts down to 375 px wide without horizontal page scroll.

## Source layout

```text
src/api/       types.ts (API shapes from docs/API.md), client.ts (fetch wrapper, ApiError)
src/lib/       hash routing, polling and async hooks, formatting
src/components/ status badges, cycle table, queue view, waveform, code and diff views, model-result notices, header
src/views/     SetupView, RunsView, AuditView, run/ (RunView and its panels)
```
