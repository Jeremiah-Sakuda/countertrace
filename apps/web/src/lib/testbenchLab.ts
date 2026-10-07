/**
 * Testbench lab: score a learner-chosen set of suite tests and checked signals
 * against six seeded bugs, using the matrix reparsed from the recorded audit's
 * raw traces (scripts/build_audit_matrix.py). Nothing is executed here.
 */

export type Check = 'empty_flag' | 'full_flag' | 'read_data';
export const CHECK_LABELS: Record<Check, string> = {empty_flag: 'empty flag', full_flag: 'full flag', read_data: 'read data'};

export interface SuiteTest { id: string; edges: number; rows: string[]; description: string }
export interface SeededBug {
  id: string; summary: string; category: string; target: string;
  /** test -> check -> contract row -> first edge where that check disagrees with the reference */
  matrix: Record<string, Partial<Record<Check, Record<string, number>>>>;
}
export interface TestbenchData {
  schema: 'countertrace-testbench-lab-v1';
  source_run: string; depth: number; checks: Check[]; rows: Record<string, string>;
  tests: SuiteTest[]; faults: SeededBug[]; equivalent: {id: string; summary: string}[];
  weak_set: {id: string; tests: string[]; checks: Check[]};
  method: string;
}

const CHECKS: Check[] = ['empty_flag', 'full_flag', 'read_data'];

/** Reject anything that is not the published matrix shape; never score partial data. */
export function parseTestbench(text: string): TestbenchData {
  const d = JSON.parse(text) as TestbenchData;
  const fail = (why: string): never => { throw new Error(`Testbench evidence is invalid: ${why}.`); };
  if (d?.schema !== 'countertrace-testbench-lab-v1') fail('unknown schema');
  if (!Array.isArray(d.tests) || !d.tests.length || !Array.isArray(d.faults) || d.faults.length !== 6) fail('missing tests or bugs');
  if (!Array.isArray(d.checks) || d.checks.length !== 3 || d.checks.some(c => !CHECKS.includes(c))) fail('unknown checks');
  if (!d.rows || typeof d.rows !== 'object') fail('missing contract rows');
  const tests = new Set(d.tests.map(t => t.id));
  if (tests.size !== d.tests.length) fail('duplicate tests');
  for (const t of d.tests) if (!Number.isInteger(t.edges) || t.edges < 1 || !Array.isArray(t.rows) || t.rows.some(r => !(r in d.rows)) || typeof t.description !== 'string') fail(`test ${t.id}`);
  for (const f of d.faults) {
    if (typeof f.id !== 'string' || typeof f.summary !== 'string' || typeof f.target !== 'string' || !f.matrix || !Object.keys(f.matrix).length) fail(`bug ${f.id}`);
    for (const [test, hits] of Object.entries(f.matrix)) {
      if (!tests.has(test)) fail(`bug ${f.id} names an unknown test`);
      for (const [check, rows] of Object.entries(hits)) {
        if (!CHECKS.includes(check as Check)) fail(`bug ${f.id} names an unknown check`);
        for (const [row, cycle] of Object.entries(rows ?? {})) if (!(row in d.rows) || !Number.isInteger(cycle) || cycle < 0) fail(`bug ${f.id} row ${row}`);
      }
    }
  }
  if (!d.weak_set?.tests?.every(t => tests.has(t))) fail('weak set');
  return d;
}

export const isRandom = (test: string) => test.startsWith('random_');
export const RANDOM_GROUP = 'random';
/** Selectable options: each directed test, plus all seeded random tests as one group. */
export function options(d: TestbenchData) {
  const random = d.tests.filter(t => isRandom(t.id));
  return [
    ...d.tests.filter(t => !isRandom(t.id)).map(t => ({id: t.id, label: t.id.replace(/_/g, ' '), description: t.description, edges: t.edges, tests: [t.id]})),
    ...(random.length ? [{id: RANDOM_GROUP, label: 'seeded random traffic', description: `${random.length} seeded runs of mixed reads, writes, and occasional resets.`,
      edges: random.reduce((n, t) => n + t.edges, 0), tests: random.map(t => t.id)}] : []),
  ];
}

export interface Selection { options: string[]; checks: Check[] }
export interface Catch { test: string; check: Check; row: string; cycle: number }
export type Miss = {kind: 'never_driven'; row: string} | {kind: 'not_checked'; checks: Check[]} | {kind: 'not_exposed'};
export interface BugResult { bug: SeededBug; label: string; caught: Catch | null; miss: Miss | null }

export function selectedTests(d: TestbenchData, sel: Selection): string[] {
  return options(d).filter(o => sel.options.includes(o.id)).flatMap(o => o.tests);
}

export function score(d: TestbenchData, sel: Selection) {
  const tests = selectedTests(d, sel);
  const driven = new Set(d.tests.filter(t => tests.includes(t.id)).flatMap(t => t.rows));
  const results: BugResult[] = d.faults.map((bug, i) => {
    let caught: Catch | null = null;
    const otherChecks = new Set<Check>();
    for (const test of tests) {
      for (const [check, rows] of Object.entries(bug.matrix[test] ?? {}) as [Check, Record<string, number>][]) {
        for (const [row, cycle] of Object.entries(rows)) {
          if (!sel.checks.includes(check)) { otherChecks.add(check); continue; }
          if (!caught || cycle < caught.cycle) caught = {test, check, row, cycle};
        }
      }
    }
    let miss: Miss | null = null;
    if (!caught) {
      if (otherChecks.size) miss = {kind: 'not_checked', checks: [...otherChecks].sort()};
      else if (bug.target in d.rows && !driven.has(bug.target) && d.tests.some(t => t.rows.includes(bug.target))) miss = {kind: 'never_driven', row: bug.target};
      else miss = {kind: 'not_exposed'};
    }
    return {bug, label: `Bug ${String.fromCharCode(65 + i)}`, caught, miss};
  });
  return {results, caught: results.filter(r => r.caught).length, edges: options(d).filter(o => sel.options.includes(o.id)).reduce((n, o) => n + o.edges, 0)};
}

export const typicalFirstTestbench = (d: TestbenchData): Selection => ({options: d.weak_set.tests.filter(t => !isRandom(t)), checks: [...d.weak_set.checks]});

export interface Attempt { options: string[]; checks: Check[]; prediction: number; caught: number; edges: number }
export interface TestbenchNotes { schema: 'countertrace-testbench-notes-v1'; attempts: Attempt[]; revealed: string[]; reflection: string }
export const freshTestbenchNotes = (): TestbenchNotes => ({schema: 'countertrace-testbench-notes-v1', attempts: [], revealed: [], reflection: ''});
export function readTestbenchNotes(raw: string | null): TestbenchNotes {
  try {
    const n = JSON.parse(raw ?? 'null');
    if (n?.schema !== 'countertrace-testbench-notes-v1' || !Array.isArray(n.attempts) || n.attempts.length > 200 || !Array.isArray(n.revealed) || typeof n.reflection !== 'string' || n.reflection.length > 2000) return freshTestbenchNotes();
    const ok = n.attempts.every((a: Attempt) => Array.isArray(a.options) && Array.isArray(a.checks) && a.checks.every(c => CHECKS.includes(c))
      && [a.prediction, a.caught, a.edges].every(v => Number.isInteger(v) && v >= 0) && a.prediction <= 6 && a.caught <= 6);
    return ok && n.revealed.every((r: unknown) => typeof r === 'string') ? n : freshTestbenchNotes();
  } catch { return freshTestbenchNotes(); }
}

export function testbenchReport(n: TestbenchNotes): string {
  const rows = n.attempts.map((a, i) => `${i + 1}. Tests: ${a.options.join(', ') || 'none'}. Checks: ${a.checks.map(c => CHECK_LABELS[c]).join(', ') || 'none'}. Predicted ${a.prediction}, caught ${a.caught} of 6, ${a.edges} edges.`);
  return ['# Countertrace: will your testbench catch it?', 'Anonymous, self-reported practice. No measured learning gain.',
    '## Attempts', rows.join('\n') || 'None', '## What I would change in my own testbench', n.reflection || 'Unanswered'].join('\n\n');
}
