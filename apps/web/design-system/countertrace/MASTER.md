# Countertrace design system

**Direction:** Repair studio · October 5, 2026

The owner requested a complete creative redesign after rejecting the blue and charcoal dashboard treatments. The interface now draws on editorial layouts and laboratory notebooks: warm paper, ink, rust, a pale sage patch exhibit, serif headlines, numbered workflows, and precise data tables. This replaces the earlier generated dark developer-tool preset. UI/UX Pro Max's Editorial Grid / Magazine and Minimalism & Swiss Style guidance informed the layout; Countertrace's evidence rules remain authoritative.

## Evidence semantics

- The model proposes explanations or repairs. Independent tools assign results.
- Keep recorded and live runs visibly distinct. Preserve original dates, timings, provenance, and limits behind clearly labelled disclosures.
- Green status text denotes individual proved properties only. Actions and focus use rust. Pale sage surfaces are neutral visual structure, never a success claim.
- Status badges include words and icons. Preserve separate counterexample, simulation, bounded-check, proof, unresolved, tool-error, and unchecked states.
- Never show an overall “verified” badge, invented progress percentage, or inferred result. The no-finding headline remains “No counterexample found by these methods.”
- The run overview displays the selected finding's actual cycle, signal, expected value, observed value, and trace source. Its cycle is local to that trace, not the earliest cycle across unrelated tests.
- Queue views show the independent reference queue, not invented DUT internals. Source citations, method-specific obligations, hashes, logs, and exports remain available.

## Visual tokens

The implemented source of truth is `src/styles.css` with the repair studio in `src/studio.css`.

| Role | Color |
| --- | --- |
| Page paper | `#F7F5EF` |
| Card paper | `#FFFEFA` |
| Neutral patch exhibit | `#E8ECDF` |
| Ink | `#252824` |
| Secondary text | `#484C43` |
| Muted text | `#66695F` |
| Rust action / focus | `#9A3D20` |
| Rust hover | `#742B17` |
| Rule | `#D8D9CB` |
| Control border | `#A7AA9C` |
| Counterexample | `#A32C29` on `#FAE9E2` |
| Proved | `#27633B` on `#E9F0E4` |
| Bounded | `#206467` on `#E8F1ED` |
| Simulation | `#62438A` on `#F0EAF5` |
| Unresolved | `#80550F` on `#F6EDCE` |
| Tool error | `#953E16` on `#F9EADE` |

Use Newsreader for editorial headings and short explanatory statements, DM Sans for body and controls, and JetBrains Mono for values, IDs, source, and small labels. System serif, sans, and monospace fallbacks remain usable if font delivery is unavailable. Avoid decorative gradients, glass effects, blue background washes, giant rounded cards, and synthetic charts.

## Layout and interaction

- A horizontal masthead links Repair lab, Practice bench, Teach, and Workbench. Runtime details open as a popover. Workbench routes expose their secondary navigation. Actual patch diffs are the primary visual exhibit.
- Smaller screens: a wrapping masthead, stacked patch/judgment panes, full expected/observed edge cards, and no page-level overflow. At widths below 950 px the setup examples use a labelled native select, keeping the chosen input close to its contract.
- Setup: an editorial introduction, three-step workflow, example index, input specimen, contract review, and acceptance before execution. Optional model interpretation is a disclosure.
- Runs: a collection of recorded case cards followed by a live-run ledger. Counts derive from each recorded verdict. Recording notes and original metadata remain available on each card.
- Run detail: case title and result, a sourced failing-cycle card, compact facts, provenance disclosure, section shortcuts, reference queue, trace, explanation, repair, and method-specific evidence.
- Audit: a matching editorial entry, explicit check-set selection, real mutation classifications, and learner exercise. Do not equate its score with design confidence.
- Use thin rules, small 3–5 px radii, measured spacing, and restrained shadows. Data visualizations must represent actual trace values.

## Accessibility and verification

Keep the skip link, landmark and heading structure, visible rust focus outlines, native controls and disclosures, `aria-current` navigation, and pressed-state cycle buttons. Cycle selection supports arrows, Home, and End. Section jumps transfer focus; citation jumps reveal and focus their cycle. Collapsing a trace preserves a visible selection. Touch controls are at least 44 px on narrow screens; text inputs use 16 px text. Wide evidence tables scroll within labelled regions, not the page. Reduced-motion preferences disable animation and smooth scrolling.

Check desktop, tablet, phone, and short landscape layouts after structural changes, along with actual data, acceptance state, citations, and parent/candidate links. Run `make check`, the web regression tests, and the production build. Record observed checks in `docs/STATUS.md`; do not claim screen-reader or learner validation without performing it.

## October 9 complete-case navigation

The home leads with a three-step recorded FIFO case before the broader catalog. A featured case requires a complete promoted FIFO record and both downstream links. Development specifications are visible; reserved evaluation specifications are grouped in a native disclosure. Run outcomes, failure stages and all mutation denominators remain visible. Property code, exact feedback and provenance expand on demand to keep the mobile reading path short. This follows the skill's general forms/feedback and mobile layout guidance; the local search did not yield a specific progressive-disclosure recommendation.
